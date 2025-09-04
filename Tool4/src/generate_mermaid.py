import json
import os
import re

def sanitize_for_mermaid(node_name):
    """Sanitizes a string to be a valid Mermaid.js node ID."""
    if not isinstance(node_name, str):
        return ""
    # Replace any sequence of invalid characters with a single underscore
    return re.sub(r'[^a-zA-Z0-9_]+', '_', node_name)

def generate_lineage_diagram(lineage_path, output_path):
    """
    Generates a Mermaid diagram from a database lineage JSON file.
    """
    try:
        with open(lineage_path, "r", encoding="utf-8") as f:
            lineage = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: The file '{lineage_path}' was not found.")
        return
    except json.JSONDecodeError:
        print(f"❌ Error: Could not decode JSON from '{lineage_path}'. Check for syntax errors.")
        return

    lines = ["graph TD\n"]
    
    # Define styles for different node types
    lines.append("    %% --- Styles --- %%")
    lines.append("    classDef table fill:#f96,stroke:#333,stroke-width:2px,color:#000;")
    lines.append("    classDef function fill:#9f6,stroke:#333,stroke-width:2px,color:#000,font-weight:bold;")
    lines.append("    classDef trigger fill:#fa0,stroke:#333,stroke-width:2px,color:#000,font-weight:bold;")
    lines.append("    classDef procedure fill:#9cf,stroke:#333,stroke-width:2px,color:#000,font-weight:bold;")
    lines.append("    classDef column fill:#fff,stroke:#333,stroke-width:1px,color:#000,font-size:12px;\n")

    node_definitions = {}
    edges = set()
    
    # Lists to hold node names for visual ranking
    function_nodes, trigger_nodes, procedure_nodes = [], [], []

    # 1. First Pass: Define all nodes and subgraphs
    for name, meta in lineage.items():
        node_type = meta.get("type")
        sanitized_name = sanitize_for_mermaid(name)
        
        if node_type == "table":
            # Use a unique subgraph ID so Mermaid doesn’t confuse it with node IDs
            subgraph_id = f"sg_{sanitized_name}"
            table_lines = [f'\n    subgraph {subgraph_id}["{name}"]']
            
            # Get unique column names from the 'columns' list
            column_names = sorted(list(set(c.get("name") for c in meta.get("columns", []) if c.get("name"))))
            if column_names:
                for col_name in column_names:
                    sanitized_col_id = sanitize_for_mermaid(f"{name}_{col_name}")
                    table_lines.append(f'        {sanitized_col_id}["{col_name}"];')
                    table_lines.append(f"        class {sanitized_col_id} column;")
            else:
                 table_lines.append(f'        {sanitized_name}_placeholder["(no columns)"];')
            
            table_lines.append("    end")
            # Style the subgraph container, not the original sanitized name
            table_lines.append(f"    class {subgraph_id} table;")
            
            node_definitions[name] = "\n".join(table_lines)
        
        elif node_type in ["procedure", "function", "trigger"]:
            node_definitions[name] = f'    {sanitized_name}("{name}");'
            if node_type == "function":
                function_nodes.append(sanitized_name)
                node_definitions[name] += f"\n    class {sanitized_name} function;"
            elif node_type == "trigger":
                trigger_nodes.append(sanitized_name)
                node_definitions[name] += f"\n    class {sanitized_name} trigger;"
            else: # procedure
                procedure_nodes.append(sanitized_name)
                node_definitions[name] += f"\n    class {sanitized_name} procedure;"

    # 2. Second Pass: Define all relationships (edges)
    for name, meta in lineage.items():
        caller_name = name
        sanitized_caller = sanitize_for_mermaid(caller_name)
        node_type = meta.get("type")

        # Object-to-Object calls
        if node_type in ["procedure", "function", "trigger"]:
            for callee_name in meta.get("calls", []):
                sanitized_callee = sanitize_for_mermaid(callee_name)
                edges.add(f'    {sanitized_caller} -->|calls| {sanitized_callee};')

        # Trigger-to-Table attachment
        if node_type == "trigger":
            table_name = meta.get("on_table")
            event = meta.get("event", "on event")
            if table_name:
                sanitized_table = sanitize_for_mermaid(table_name)
                edges.add(f'    {sanitized_table} -.->|{event}| {sanitized_caller};')

        # Object-to-Column access (defined in the table's schema)
        if node_type == "table":
            table_name = name
            for col_info in meta.get("columns", []):
                col_name = col_info.get("name")
                usage = col_info.get("usage")
                accessing_caller = col_info.get("caller")
                if all([col_name, usage, accessing_caller]):
                    sanitized_accessing_caller = sanitize_for_mermaid(accessing_caller)
                    sanitized_col_id = sanitize_for_mermaid(f"{table_name}_{col_name}")
                    edges.add(f'    {sanitized_accessing_caller} -- "{usage}" --> {sanitized_col_id};')

    # 3. Assemble the final Mermaid script
    lines.append("\n    %% --- Visual Hierarchy --- %%")
    if function_nodes:
        lines.append("    subgraph Functions")
        for fn in function_nodes:
            lines.append(f"        {fn}")
        lines.append("    end\n")

    if trigger_nodes:
        lines.append("    subgraph Triggers")
        for tn in trigger_nodes:
            lines.append(f"        {tn}")
        lines.append("    end\n")

    if procedure_nodes:
        lines.append("    subgraph Procedures")
        for pn in procedure_nodes:
            lines.append(f"        {pn}")
        lines.append("    end\n")

    lines.append("\n    %% --- Node Definitions --- %%")
    lines.extend(sorted(node_definitions.values()))
    
    lines.append("\n    %% --- Relationships --- %%")
    lines.extend(sorted(list(edges)))

    # Write the output file
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    
    print(f"✅ Mermaid diagram successfully generated at: {output_path}")

if __name__ == "__main__":
    # Define the input and output file paths
    project_root = os.path.dirname(os.path.abspath(__file__))
    lineage_file_path = os.path.join(project_root, "lineage.json")
    mermaid_output_file_path = os.path.join(project_root, "diagrams", "database_lineage.mmd")

    # Generate the diagram
    generate_lineage_diagram(lineage_file_path, mermaid_output_file_path)
