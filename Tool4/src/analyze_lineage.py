import json
from collections import defaultdict
import re
import os
import jsonschema

# A simple class to hold color codes for terminal output.
# If the dependency is not available, it will default to no color.
try:
    from src.logging_styles import Colours
except ImportError:
    class Colours:
        YELLOW = ""
        RESET = ""
        GREEN = ""
        RED = ""

def analyze_lineage(index_file: str, ast_file: str, output_file: str):
    """
    Analyzes database object dependencies from an index file and an AST file
    to produce a detailed data lineage report, including table and column usage.
    """

    def extract_tables_from_query(query: str):
        """
        Extracts all table names from a raw SQL query using regex,
        including those in JOIN clauses. Returns a list of unique table names.
        """
        if not query:
            return []
        # This regex looks for tables after FROM or JOIN clauses.
        # It handles optional schema names (e.g., dbo.MyTable) and quoted identifiers.
        pattern = r'\b(?:FROM|JOIN)\s+([a-zA-Z0-9_."\[\]]+)'
        tables = re.findall(pattern, query, re.IGNORECASE)
        
        # Clean up names: remove quotes, semicolons, and filter out variables.
        cleaned_tables = [
            t.strip('[];"') for t in tables 
            if not t.startswith('@')
        ]
        return list(set(cleaned_tables))

    def extract_columns_bruteforce(query: str, stmt_type: str):
        """
        Brute force extraction of column names for UPDATE, INSERT statements.
        """
        if not query or not stmt_type:
            return ["*"]

        if stmt_type == "UPDATE":
            match = re.search(r"\bSET\b(.+?)(\bWHERE\b|$)", query, re.IGNORECASE | re.DOTALL)
            if match:
                set_clause = match.group(1)
                # Extracts the column name (left side of the '=')
                columns = [c.split('=')[0].strip() for c in set_clause.split(',') if '=' in c]
                return columns or ["*"]

        elif stmt_type == "INSERT":
            # Extracts columns from an INSERT INTO table (col1, col2) ... statement
            match = re.search(r"\bINSERT\s+INTO\s+\S+\s*\((.*?)\)", query, re.IGNORECASE | re.DOTALL)
            if match:
                cols_str = match.group(1)
                columns = [c.strip() for c in cols_str.split(',') if c.strip()]
                return columns or ["*"]

        elif stmt_type == "DELETE":
            # DELETE affects all columns implicitly.
            return ["*"]

        return ["*"]

    def extract_columns_from_select_query(query: str):
        """Crude extraction of column names from a SELECT clause in a raw query string."""
        if not query:
            return ["*"]
        try:
            select_index = query.upper().find("SELECT")
            from_index = query.upper().find("FROM")
            if select_index == -1 or from_index == -1 or from_index < select_index:
                return ["*"]

            cols_str = query[select_index + 6:from_index].strip()
            if not cols_str or cols_str == '*':
                return ["*"]
            
            # Handle aliases like 'col as alias' and extract the final column name/alias
            return [c.split(' as ')[-1].strip() for c in cols_str.split(',')]
        except Exception:
            return ["*"]
            
    def process_expression_condition(proc, expr, table_usage, lineage):
        """Recursively processes expression conditions to find subqueries."""
        if not expr or not isinstance(expr, dict):
            return
        
        expr_type = expr.get("type", "").upper()
        if expr_type == "RAW_EXPRESSION":
            sql = expr.get("expression", "")
            if re.search(r"\bselect\b", sql, re.IGNORECASE):
                tables = extract_tables_from_query(sql)
                columns = extract_columns_from_select_query(sql)
                for table in tables:
                    lineage[table]["type"] = "table"
                    lineage[table]["calls"].add(proc)
                    table_usage[table][proc].append({"op": "read", "cols": columns})
        elif "op" in expr:
            process_expression_condition(proc, expr.get("left"), table_usage, lineage)
            process_expression_condition(proc, expr.get("right"), table_usage, lineage)

    def process_statements(proc: str, stmts: list, table_usage: defaultdict, lineage: defaultdict):
        """Recursively processes AST statements to find table and column usage."""
        if not stmts:
            return

        for stmt in stmts:
            stmt_type = stmt.get("type", "").upper()

            # --- Structured DML Statements ---
            if stmt_type == "SELECT":
                table = stmt.get("from")
                if table and table not in ["DUMMY_TABLE", "NO_TABLE"]:
                    columns = stmt.get("columns", ["*"])
                    lineage[table]["type"] = "table"
                    lineage[table]["calls"].add(proc)
                    table_usage[table][proc].append({"op": "read", "cols": columns})
            
            elif stmt_type == "SELECT_INTO":
                query_obj = stmt.get("query", {})
                tables, columns = [], ["*"]
                if isinstance(query_obj, dict):
                    table = query_obj.get("from")
                    if table: tables.append(table)
                    columns = query_obj.get("columns", ["*"])
                else: 
                    tables = extract_tables_from_query(str(query_obj))
                    columns = extract_columns_from_select_query(str(query_obj))

                for table in tables:
                    lineage[table]["type"] = "table"
                    lineage[table]["calls"].add(proc)
                    table_usage[table][proc].append({"op": "read", "cols": columns})

            elif stmt_type == "UPDATE":
                table = stmt.get("table")
                if table:
                    columns = list(stmt.get("set", {}).keys()) or ["*"]
                    lineage[table]["type"] = "table"
                    lineage[table]["calls"].add(proc)
                    table_usage[table][proc].append({"op": "write", "cols": columns})
            
            elif stmt_type == "INSERT":
                table = stmt.get("table")
                if table:
                    columns = stmt.get("columns", ["*"])
                    lineage[table]["type"] = "table"
                    lineage[table]["calls"].add(proc)
                    table_usage[table][proc].append({"op": "write", "cols": columns})
                if "select_statement" in stmt:
                    process_statements(proc, [stmt["select_statement"]], table_usage, lineage)

            elif stmt_type == "DELETE":
                table = stmt.get("table")
                if table:
                    lineage[table]["type"] = "table"
                    lineage[table]["calls"].add(proc)
                    table_usage[table][proc].append({"op": "write", "cols": ["*"]})

            # --- Raw SQL String Parsing ---
            elif stmt_type in ("RAW_EXPRESSION", "RAW_SQL"):
                sql = stmt.get("sql") or stmt.get("query") or stmt.get("expression", "")
                if not sql: continue

                if re.search(r"\bselect\b", sql, re.IGNORECASE):
                    tables = extract_tables_from_query(sql)
                    columns = extract_columns_from_select_query(sql)
                    for table in tables:
                        lineage[table]["type"] = "table"
                        lineage[table]["calls"].add(proc)
                        table_usage[table][proc].append({"op": "read", "cols": columns})
                
                elif re.search(r"\bupdate\b", sql, re.IGNORECASE):
                    tables = extract_tables_from_query(sql)
                    columns = extract_columns_bruteforce(sql, "UPDATE")
                    if tables:
                        # Assume first table in a raw UPDATE is the one being modified
                        table_to_update = tables[0]
                        lineage[table_to_update]["type"] = "table"
                        lineage[table_to_update]["calls"].add(proc)
                        table_usage[table_to_update][proc].append({"op": "write", "cols": columns})

                elif re.search(r"\binsert\b", sql, re.IGNORECASE):
                    match = re.search(r'\bINTO\s+([a-zA-Z0-9_."\[\]]+)', sql, re.IGNORECASE)
                    if match:
                        table = match.group(1).strip('[];"')
                        columns = extract_columns_bruteforce(sql, "INSERT")
                        lineage[table]["type"] = "table"
                        lineage[table]["calls"].add(proc)
                        table_usage[table][proc].append({"op": "write", "cols": columns})

                elif re.search(r"\bdelete\b", sql, re.IGNORECASE):
                    tables = extract_tables_from_query(sql)
                    if tables:
                        # Assume first table in a raw DELETE is the one being modified
                        table_to_delete = tables[0]
                        columns = extract_columns_bruteforce(sql, "DELETE")
                        lineage[table_to_delete]["type"] = "table"
                        lineage[table_to_delete]["calls"].add(proc)
                        table_usage[table_to_delete][proc].append({"op": "write", "cols": columns})

            # --- Recursive Processing for Control Flow ---
            if "condition" in stmt:
                process_expression_condition(proc, stmt["condition"], table_usage, lineage)

            for key in ["then", "else", "body"]:
                if key in stmt and isinstance(stmt.get(key), list):
                    process_statements(proc, stmt[key], table_usage, lineage)
            
            if stmt_type == "WITH_CTE":
                for cte in stmt.get("cte_list", []):
                    if "query" in cte:
                        process_statements(proc, [cte["query"]], table_usage, lineage)
                if "main_query" in stmt:
                    process_statements(proc, [stmt["main_query"]], table_usage, lineage)
            
            if stmt_type == "CASE":
                for when_clause in stmt.get("when_clauses", []):
                    if "then" in when_clause and isinstance(when_clause.get("then"), list):
                        process_statements(proc, when_clause["then"], table_usage, lineage)

            if "catch" in stmt:
                for handler in stmt.get("catch", []):
                    if "body" in handler and isinstance(handler.get("body"), list):
                        process_statements(proc, handler["body"], table_usage, lineage)

    # --- Main Execution ---
    try:
        with open(index_file) as f:
            index_data = json.load(f)
        with open(ast_file) as f:
            ast_data = json.load(f)
    except FileNotFoundError as e:
        print(f"{Colours.RED}Error: Could not open file {e.filename}{Colours.RESET}")
        return
    except json.JSONDecodeError:
        print(f"{Colours.RED}Error: Could not decode JSON from input files.{Colours.RESET}")
        return

    lineage = defaultdict(lambda: {"type": "", "calls": set()})
    table_usage = defaultdict(lambda: defaultdict(list))
    all_db_objects = {}

    # 1. Populate all known database objects from index and AST files
    for obj_type, container in index_data.items():
        if obj_type in ["procedures", "functions", "triggers"]:
            for name in container.keys():
                all_db_objects[name] = {"type": obj_type[:-1]}

    key_map = {"procedures": "proc_name", "functions": "func_name", "triggers": "trigger_name"}
    for obj_type, container in ast_data.items():
        if obj_type in key_map:
            for item in container:
                name = item.get(key_map[obj_type])
                if name:
                    all_db_objects[name] = {"type": obj_type[:-1]}

    # 2. Build initial dependencies from the index file (proc-to-proc, proc-to-table)
    for obj_type, container in index_data.items():
        if obj_type in ["procedures", "functions", "triggers"]:
            for name, meta in container.items():
                lineage[name]["type"] = all_db_objects[name]["type"]
                for called in meta.get("calls", []):
                    lineage[name]["calls"].add(called)
                for table in meta.get("tables", []):
                    lineage[table]["type"] = "table"
                    lineage[table]["calls"].add(name)

    # 3. Create a map for easy AST lookup
    ast_map = {}
    for obj_type, key_name in key_map.items():
        for item in ast_data.get(obj_type, []):
            name = item.get(key_name)
            if name:
                ast_map[name] = item
    
    # 4. Process the AST for each object to find detailed column-level lineage
    for name, ast in ast_map.items():
        # This is the key fix: 'statements' is the correct key for the AST body.
        process_statements(name, ast.get("statements", []), table_usage, lineage)

    # 5. Build the reverse mapping (called_by)
    called_by_map = defaultdict(lambda: defaultdict(set))
    for source_name, source_meta in lineage.items():
        source_type = source_meta.get("type")
        if not source_type or source_type == "table":
            continue
        for target_name in source_meta.get("calls", set()):
            called_by_map[target_name][source_type].add(source_name)

    # 6. Ensure all tables found during AST processing are in the final object list
    for name, meta in lineage.items():
        if meta.get("type") == "table" and name not in all_db_objects:
            all_db_objects[name] = {"type": "table"}

    # 7. Format the final output JSON
    formatted_lineage = {}
    # Sort object names for consistent output order
    object_names = sorted(all_db_objects.keys())

    for name in object_names:
        meta = all_db_objects[name]
        obj_type = meta["type"]
        entry = {"type": obj_type}

        if obj_type == "table":
            entry["called_by"] = sorted(list(lineage[name].get("calls", set())))
            columns_list = []
            if name in table_usage:
                for caller_name, ops_list in table_usage[name].items():
                    caller_type = all_db_objects.get(caller_name, {}).get("type")
                    if not caller_type: continue

                    for op_info in ops_list:
                        for col_name in op_info.get('cols', []):
                            col_entry = {
                                "name": col_name.strip(),
                                "usage": op_info.get("op"),
                                "caller": caller_name,
                                "caller_type": caller_type
                            }
                            if col_entry not in columns_list:
                                columns_list.append(col_entry)
            # Sort columns for consistent output
            entry["columns"] = sorted(columns_list, key=lambda x: (x['name'], x['caller']))
        
        elif obj_type in ["procedure", "function"]:
            entry["calls"] = sorted(list(lineage[name].get("calls", set())))
            reverse_calls = called_by_map.get(name, {})
            entry["called_by_procedure"] = sorted(list(reverse_calls.get("procedure", set())))
            entry["called_by_function"] = sorted(list(reverse_calls.get("function", set())))
            entry["called_by_trigger"] = sorted(list(reverse_calls.get("trigger", set())))

        elif obj_type == "trigger":
            trigger_info = index_data.get("triggers", {}).get(name, {})
            entry["on_table"] = trigger_info.get("on_table")
            entry["event"] = trigger_info.get("event")
            entry["calls"] = sorted(list(lineage[name].get("calls", set())))

        formatted_lineage[name] = entry
    
    # 8. Validate against schema and write to file
    print(f"\n{Colours.YELLOW}--- Validating Generated Lineage Against Schema ---{Colours.RESET}")
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
            # sort_keys=True ensures the top-level object names are alphabetical
            json.dump(formatted_lineage, f, indent=2, sort_keys=True)
        print(f"\n{Colours.GREEN}✅ Lineage written to {output_file}{Colours.RESET}")

    except FileNotFoundError:
        print(f"{Colours.RED}Error: Could not find lineage_Schema.json in the expected path: '{schema_dir}'{Colours.RESET}")
    except jsonschema.exceptions.ValidationError as e:
        print(f"{Colours.RED}Generated lineage schema validation FAILED!{Colours.RESET}")
        print(f"{Colours.RED}Error: {e.message} in object: '{'.'.join(map(str, e.path))}'{Colours.RESET}")
    except Exception as e:
        print(f"{Colours.RED}An unexpected error occurred during final validation or writing: {e}{Colours.RESET}")
