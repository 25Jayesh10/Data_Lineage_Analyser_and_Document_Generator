import json
from collections import defaultdict
import re
import os
import jsonschema

# A simple class to hold color codes for terminal output.
# If the dependency is not available, it will default to no color.
try:
    # Assuming a local file for color styling
    class Colours:
        YELLOW, RESET, GREEN, RED = "\033[93m", "\033[0m", "\033[92m", "\033[91m"
except ImportError:
    class Colours:
        YELLOW, RESET, GREEN, RED = "", "", "", ""

def analyze_lineage(index_file: str, ast_file: str, output_file: str):
    """
    Analyzes database object dependencies from an index file and an AST file
    to produce a detailed data lineage report, including table and column usage.
    """
    SQL_KEYWORDS = {
        'SELECT', 'FROM', 'WHERE', 'INSERT', 'INTO', 'VALUES', 'UPDATE', 'SET', 'DELETE',
        'JOIN', 'INNER', 'LEFT', 'RIGHT', 'OUTER', 'ON', 'GROUP', 'BY', 'ORDER', 'HAVING',
        'AS', 'DISTINCT', 'TOP', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END', 'AND', 'OR', 'NOT',
        'CREATE', 'TABLE', 'PROCEDURE', 'FUNCTION', 'TRIGGER', 'VIEW', 'INDEX', 'ALTER',
        'DROP', 'TRUNCATE', 'DECLARE', 'EXEC', 'EXECUTE', 'CURSOR', 'FOR', 'OPEN', 'FETCH',
        'CLOSE', 'DEALLOCATE', 'BEGIN', 'COMMIT', 'ROLLBACK', 'TRANSACTION', 'GO', 'PRINT',
        'SUM', 'AVG', 'MAX', 'MIN', 'COUNT', 'CAST', 'CONVERT', 'GETDATE', 'YEAR', 'OVER',
        'PARTITION', 'ROWS', 'BETWEEN', 'UNBOUNDED', 'PRECEDING', 'CURRENT', 'ROW', 'IS', 'NULL',
        'RAISERROR', 'RETURN', 'WHILE', 'WITH', 'CTE', 'IN'
    }

    # NEW: Helper function to recursively extract all string values from a nested AST node.
    def get_strings_from_node(node):
        """Recursively extracts all string values from a nested AST node."""
        strings = []
        if isinstance(node, dict):
            for value in node.values():
                strings.extend(get_strings_from_node(value))
        elif isinstance(node, list):
            for item in node:
                strings.extend(get_strings_from_node(item))
        elif isinstance(node, str):
            strings.append(node)
        return strings

    def extract_referenced_columns(sql_string: str, objects_to_exclude: set):
        """Extracts potential column names from a targeted SQL string."""
        if not sql_string: return ["*"]
        potential_identifiers = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', sql_string)
        
        actual_columns = {
            col for col in potential_identifiers 
            if col.upper() not in SQL_KEYWORDS 
            and not col.startswith('@')
            and col not in objects_to_exclude
        }
        return sorted(list(actual_columns)) or ["*"]

    def extract_calls_from_expression(expression):
        if not isinstance(expression, str): return []
        pattern = r'\b(?:[a-zA-Z0-9_]+\.)?([a-zA-Z0-9_]+)\s*\('
        calls = re.findall(pattern, expression)
        return list(set([c.split('.')[-1] for c in calls]))

    def process_expression_condition(proc, expr, table_usage, lineage):
        if isinstance(expr, str):
            for called_obj in extract_calls_from_expression(expr):
                if called_obj != proc: lineage[proc]["calls"].add(called_obj)
            return
        if not isinstance(expr, dict): return

        if "op" in expr:
            process_expression_condition(proc, expr.get("left"), table_usage, lineage)
            process_expression_condition(proc, expr.get("right"), table_usage, lineage)

    def process_statements(proc: str, stmts: list, table_usage: defaultdict, lineage: defaultdict, cte_names=None):
        if not stmts: return
        if cte_names is None: cte_names = set()

        for stmt in stmts:
            stmt_type = stmt.get("type", "").upper()

            if stmt_type == "EXECUTE_PROCEDURE":
                if proc_name := stmt.get("name"):
                    lineage[proc]["calls"].add(proc_name.split('.')[-1])

            elif stmt_type == "SET" and "value" in stmt:
                process_expression_condition(proc, stmt["value"], table_usage, lineage)

            elif stmt_type == "WITH_CTE":
                local_cte_names = {cte.get("name") for cte in stmt.get("cte_list", [])}
                for cte in stmt.get("cte_list", []):
                    if "query" in cte and isinstance(query := cte.get("query"), dict):
                        process_statements(proc, [query], table_usage, lineage, cte_names | local_cte_names)
                if "main_query" in stmt and isinstance(main_query := stmt.get("main_query"), dict):
                    process_statements(proc, [main_query], table_usage, lineage, cte_names | local_cte_names)

            elif stmt_type == "DECLARE_CURSOR":
                if "select_statement" in stmt and isinstance(cursor_query := stmt.get("select_statement"), dict):
                    process_statements(proc, [cursor_query], table_usage, lineage, cte_names)
            
            # --- MODIFIED BLOCK START ---
            elif stmt_type in ("SELECT", "SELECT_INTO"):
                query_obj = stmt if stmt_type == "SELECT" else stmt.get("query", {})
                
                if isinstance(query_obj, dict):
                    from_clause = query_obj.get("from")
                    tables = [from_clause] if isinstance(from_clause, str) else []
                    
                    # Precisely collect strings only from column and where clauses
                    strings_to_analyze = []
                    strings_to_analyze.extend(query_obj.get("columns", []))
                    strings_to_analyze.extend(get_strings_from_node(query_obj.get("where", {})))
                    full_query_str = " ".join(strings_to_analyze)

                    # Identify aliases in the SELECT list to exclude them as source columns
                    aliases = {
                        match.group(1)
                        for col_expr in query_obj.get("columns", [])
                        if (match := re.search(r'\bAS\s+([a-zA-Z_][a-zA-Z0-9_]*)\b', col_expr, re.IGNORECASE))
                    }
                    
                    objects_to_exclude = set(tables) | cte_names | aliases
                    columns = extract_referenced_columns(full_query_str, objects_to_exclude)
                    
                    for table in tables:
                        if table and table not in ["DUMMY_TABLE", "NO_TABLE"] and table not in cte_names:
                            lineage[table]["type"] = "table"
                            table_usage[table][proc].append({"op": "read", "cols": columns})
            # --- MODIFIED BLOCK END ---
            
            elif stmt_type == "UPDATE":
                if table := stmt.get("table"):
                    set_cols = list(stmt.get("set", {}).keys())
                    # Precisely collect strings from the where clause
                    where_strings = get_strings_from_node(stmt.get("where", {}))
                    where_cols = extract_referenced_columns(" ".join(where_strings), {table})
                    all_cols = sorted(list(set(set_cols + where_cols)))
                    
                    lineage[table]["type"] = "table"
                    table_usage[table][proc].append({"op": "write", "cols": all_cols})

            elif stmt_type == "INSERT":
                if table := stmt.get("table"):
                    columns = stmt.get("columns", ["*"])
                    lineage[table]["type"] = "table"
                    table_usage[table][proc].append({"op": "write", "cols": columns})
                if "select_statement" in stmt:
                    process_statements(proc, [stmt["select_statement"]], table_usage, lineage, cte_names)

            elif stmt_type == "DELETE":
                if table := stmt.get("table"):
                    # Precisely collect strings from the where clause
                    where_strings = get_strings_from_node(stmt.get("where", {}))
                    columns = extract_referenced_columns(" ".join(where_strings), {table})
                    lineage[table]["type"] = "table"
                    table_usage[table][proc].append({"op": "write", "cols": columns})

            if "condition" in stmt:
                process_expression_condition(proc, stmt["condition"], table_usage, lineage)
            for key in ["then", "else", "body"]:
                if key in stmt and isinstance(stmt.get(key), list):
                    process_statements(proc, stmt[key], table_usage, lineage, cte_names)
    
    # --- Main Execution (No changes from here down) ---
    try:
        with open(index_file, 'r') as f: index_data = json.load(f)
        with open(ast_file, 'r') as f: ast_data = json.load(f)
    except Exception as e:
        print(f"{Colours.RED}Error opening or parsing input files: {e}{Colours.RESET}")
        return

    lineage = defaultdict(lambda: {"type": "", "calls": set()})
    table_usage = defaultdict(lambda: defaultdict(list))
    all_db_objects = {}

    key_map = {"procedures": "proc_name", "functions": "func_name", "triggers": "trigger_name"}
    for obj_type, container in index_data.items():
        if obj_type in key_map:
            for name in container.keys(): all_db_objects[name] = {"type": obj_type[:-1]}
            
    # Also discover tables from the AST that might not be in the index
    for proc_def in ast_data.get("procedures", []):
        for stmt in proc_def.get("statements", []):
            if table_name := stmt.get("table"):
                if table_name not in all_db_objects:
                    all_db_objects[table_name] = {"type": "table"}

    ast_map = {item.get(key): item for type, key in key_map.items() for item in ast_data.get(type, []) if item.get(key)}
    for name, ast in ast_map.items():
        process_statements(name, ast.get("statements", []), table_usage, lineage)

    for name, meta in lineage.items():
        if meta.get("type") == "table" and name not in all_db_objects:
            all_db_objects[name] = {"type": "table"}

    called_by_map = defaultdict(lambda: defaultdict(set))
    for name, obj_data in all_db_objects.items():
        if obj_data["type"] != "table":
            for called in lineage.get(name, {}).get("calls", set()):
                called_by_map[called.split('.')[-1]][obj_data["type"]].add(name)
    
    formatted_lineage = {}
    for name in sorted(all_db_objects.keys()):
        meta = all_db_objects.get(name, {})
        obj_type = meta.get("type")
        if not obj_type: continue

        entry = {"type": obj_type}

        if obj_type == "table":
            direct_callers = {c for c in table_usage.get(name, {})}
            entry["called_by"] = sorted(list(direct_callers))

            columns_list = []
            if name in table_usage:
                for caller, ops in table_usage[name].items():
                    caller_type = all_db_objects.get(caller, {}).get("type")
                    if not caller_type: continue
                    for op_info in ops:
                        unique_cols = sorted(list(set(op_info.get('cols', []))))
                        for col in unique_cols:
                            if col == "*": continue
                            col_entry = {"name": col.strip(), "usage": op_info.get("op"), "caller": caller, "caller_type": caller_type}
                            if col_entry not in columns_list: columns_list.append(col_entry)
            entry["columns"] = sorted(columns_list, key=lambda x: (x['name'], x['caller']))

        elif obj_type in ["procedure", "function"]:
            entry["calls"] = sorted([c.split('.')[-1] for c in lineage[name].get("calls", set())])
            calls = called_by_map.get(name, {})
            entry["called_by_procedure"] = sorted(list(calls.get("procedure", set())))
            entry["called_by_function"] = sorted(list(calls.get("function", set())))
            entry["called_by_trigger"] = sorted(list(calls.get("trigger", set())))

        elif obj_type == "trigger":
            info = index_data.get("triggers", {}).get(name, {})
            entry["on_table"] = info.get("on_table")
            entry["event"] = info.get("event")
            entry["calls"] = sorted([c.split('.')[-1] for c in lineage[name].get("calls", set())])
        
        formatted_lineage[name] = entry

    # --- Validation and File Write ---
    print(f"\n{Colours.YELLOW}--- Validating and Writing Lineage ---{Colours.RESET}")
    try:
        script_path = os.path.abspath(__file__)
        src_dir = os.path.dirname(script_path)
        # Assumes schemas directory is a sibling of the 'src' directory
        schema_dir = os.path.join(os.path.dirname(src_dir), "schemas")
        lineage_schema_path = os.path.join(schema_dir, "lineage_Schema.json")

        with open(lineage_schema_path, "r") as f:
            lineage_schema = json.load(f)
        
        print("Validating generated lineage data against its schema...")
        jsonschema.validate(instance=formatted_lineage, schema=lineage_schema)
        print(f"{Colours.GREEN}Generated lineage schema validation successful.{Colours.RESET}")

        with open(output_file, "w") as f:
            json.dump(formatted_lineage, f, indent=2, sort_keys=True)
        print(f"\n{Colours.GREEN}✅ Lineage written to {output_file}{Colours.RESET}")

    except FileNotFoundError:
        print(f"{Colours.RED}Error: Could not find lineage_Schema.json in the expected path: '{schema_dir}'{Colours.RESET}")
    except jsonschema.exceptions.ValidationError as e:
        print(f"{Colours.RED}Generated lineage schema validation FAILED!{Colours.RESET}")
        print(f"{Colours.RED}Error: {e.message} in object: '{'.'.join(map(str, e.path))}'{Colours.RESET}")
    except Exception as e:
        print(f"{Colours.RED}An unexpected error occurred during final validation or writing: {e}{Colours.RESET}")