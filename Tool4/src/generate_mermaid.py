import json
import os
import re

def sanitize_for_mermaid(node_name):
    """Sanitizes a string to be a valid Mermaid.js node ID."""
    if not isinstance(node_name, str):
        return ""
    # Replace any sequence of invalid characters with a single underscore
    return re.sub(r'[^a-zA-Z0-9_]+', '_', node_name)

def generate_mermaid_with_hybrid_links(lineage_path, output_path):
    """
    Generates a Mermaid diagram with direct column links, but falls back
    to linking to the table block if no columns are specified.

    Args:
        lineage_path (str): The path to the input lineage.json file.
        output_path (str): The path to the output .md file for the Mermaid diagram.
    """
    # Load the lineage.json content
    try:
        with open(lineage_path, "r", encoding="utf-8") as f:
            lineage = json.load(f)
    except FileNotFoundError:
        print(f"Error: The file '{lineage_path}' was not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{lineage_path}'. Check for syntax errors.")
        return

    # Start building the Mermaid diagram
    lines = ["graph TD\n"]

    # Define styles for different node types
    lines.append("    %% Node styles\n")
    lines.append("    classDef table fill:#f96,stroke:#333,stroke-width:2px,color:#000,font-weight:bold;\n")
    lines.append("    classDef stored_proc fill:#9cf,stroke:#333,stroke-width:2px,color:#000,font-weight:bold;\n")
    lines.append("    classDef column fill:#fff,stroke:#333,stroke-width:1px,color:#000;\n\n")

    edges = set()
    node_definitions = {}

    # First, define all nodes and subgraphs, then collect the specific edges
    for name, meta in lineage.items():
        node_type = meta.get("type")
        sanitized_name = sanitize_for_mermaid(name)

        if not sanitized_name:
            continue

        if node_type == "procedure":
            # Define the stored procedure node itself
            node_definitions[sanitized_name] = f'    {sanitized_name}("{name}");\n    class {sanitized_name} stored_proc;\n'

            # Iterate through each table this procedure accesses
            for table_name in meta.get("tables", []):
                table_meta = lineage.get(table_name)
                if not table_meta or table_meta.get("type") != "table":
                    continue

                # <--- MODIFIED: Added fallback logic for tables with no columns
                columns_data = table_meta.get("columns", [])
                
                # Check if there is valid, actionable column data
                has_valid_columns = any(c.get("name") and c.get("usage") for c in columns_data)

                if has_valid_columns:
                    # If columns are specified, link directly to them
                    for col_info in columns_data:
                        column_name = col_info.get("name")
                        usage = col_info.get("usage")
                        if not column_name or not usage:
                            continue
                        
                        sanitized_col_id = sanitize_for_mermaid(f"{table_name}_{column_name}")
                        edge = f'    {sanitized_name} -- "{usage}" --> {sanitized_col_id};\n'
                        edges.add(edge)
                else:
                    # FALLBACK: If no columns are specified, link to the table block itself
                    sanitized_table = sanitize_for_mermaid(table_name)
                    edge = f'    {sanitized_name} -- "accesses" --> {sanitized_table};\n'
                    edges.add(edge)

        elif node_type == "table":
            # This part remains the same, defining the table's visual structure
            table_lines = [f'\n    subgraph {sanitized_name}["{name}"]\n']
            column_names = sorted(list(set(c.get("name") for c in meta.get("columns", []) if c.get("name"))))

            if column_names:
                for col_name in column_names:
                    sanitized_col_id = sanitize_for_mermaid(f"{name}_{col_name}")
                    table_lines.append(f'        {sanitized_col_id}["{col_name}"];\n')
                    table_lines.append(f"        class {sanitized_col_id} column;\n")
            else:
                placeholder_id = f"{sanitized_name}_placeholder"
                table_lines.append(f'        {placeholder_id}["(no columns specified)"];\n')
                table_lines.append(f"        class {placeholder_id} column;\n")

            table_lines.append("    end\n")
            node_definitions[sanitized_name] = "".join(table_lines)

    # Write all definitions and edges to the file
    lines.extend(sorted(node_definitions.values()))
    if edges:
        lines.append("\n    %% Relationships\n")
        lines.extend(sorted(list(edges)))

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print(f"✅ Mermaid diagram with hybrid links saved to {output_path}")


if __name__ == "__main__":
    project_root = os.path.dirname(os.path.abspath(__file__))
    lineage_path = os.path.join(project_root, "data", "lineage.json")
    mermaid_output_path = os.path.join(project_root, "diagrams", "lineage_diagram_hybrid_links.md")

    generate_mermaid_with_hybrid_links(lineage_path, mermaid_output_path)