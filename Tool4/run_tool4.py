# import json
# import os
# from src.analyze_lineage import analyze_lineage
# from src.generate_mermaid import generate_mermaid_with_hybrid_links
# from src.convert_mmd_to_md import convert_mmd_to_md
# from src.validation_script import validate
# from src.lineage_to_index import generate_index
# from src.logging_styles import Colours


# def main():
#     # Define file paths
#     input_dir = "input"
#     output_dir = "output"
#     diagram_dir = "output/diagrams"

#     index_path = os.path.join(input_dir, "index.json")   # Tool 1 output (already exists)
#     ast_path = os.path.join(input_dir, "ast.json")       # Tool 2 output (already exists)
#     output_path = os.path.join(output_dir, "lineage.json")  # Tool 4 output
#     mermaid_path = os.path.join(diagram_dir, "lineage.mmd") # Mermaid diagram output
#     markdown_path = os.path.join(diagram_dir, "lineage.md") # Mermaid .md file
#     generated_index_path = os.path.join(output_dir, "generated_index.json")

#     # ✅ Validation before running Tool 4
#     print(Colours.YELLOW + "Validating index.json against schema..." + Colours.RESET)
#     if not validate(index_path, ast_path):
#         print(Colours.RED + "Validation failed. Exiting tool." + Colours.RESET)
#         return

#     print(Colours.GREEN + "Validation passed. Proceeding to Data Lineage Analysis." + Colours.RESET)

#     # ✅ Tool 4: Data Lineage Analysis
#     print(Colours.GREEN + "Starting Data Lineage Analysis..." + Colours.RESET)
#     analyze_lineage(index_path, ast_path, output_path)
#     print(Colours.GREEN + "Data Lineage Analysis complete." + Colours.RESET)

#     # Load lineage.json
#     try:
#         with open(output_path, 'r') as f:
#             lineage_data = json.load(f)
#     except Exception as e:
#         print(Colours.RED + f"Error while reading lineage.json: {e}" + Colours.RESET)
#         return

#     # Pretty print lineage.json
#     print(json.dumps(lineage_data, indent=2))

#     # ✅ Tool 4: Generate Mermaid + Markdown
#     print(Colours.YELLOW + "Generating Mermaid diagram..." + Colours.RESET)
#     generate_mermaid_with_hybrid_links(output_path, mermaid_path)
#     convert_mmd_to_md(mermaid_path, markdown_path)
#     print(Colours.GREEN + "Mermaid diagram and Markdown generated." + Colours.RESET)

#     # ✅ Tool 4 Extension: Generate generated_index.json
#     print(Colours.YELLOW + "Generating new index.json from lineage + Mermaid..." + Colours.RESET)
#     success = generate_index(output_path, mermaid_path, generated_index_path)
#     if success:
#         print(Colours.GREEN + "Generated index.json successfully." + Colours.RESET)
#     else:
#         print(Colours.RED + "Failed to generate index.json from lineage." + Colours.RESET)


# if __name__ == "__main__":
#     main()


import os
from src.analyze_lineage import analyze_lineage
from src.validation_script import validate
from src.logging_styles import Colours


def main():
    # Define file paths
    input_dir = "input"
    output_dir = "output"

    index_path = os.path.join(input_dir, "index", "index3.json")  # Tool 1 output (already exists)
    ast_path = os.path.join(input_dir, "ast", "ast3.json")      # Tool 2 output (already exists)
    output_path = os.path.join(output_dir, "lineage3.json")  # Tool 4 output

    # ✅ Validation before running Tool 4
    print(Colours.YELLOW + "Validating index.json and ast.json against schemas..." + Colours.RESET)
    if not validate(index_path, ast_path):
        print(Colours.RED + "Validation failed. Exiting tool." + Colours.RESET)
        return

    print(Colours.GREEN + "Validation passed. Proceeding to Data Lineage Analysis." + Colours.RESET)

    # ✅ Tool 4: Data Lineage Analysis
    print(Colours.GREEN + "Starting Data Lineage Analysis..." + Colours.RESET)
    analyze_lineage(index_path, ast_path, output_path)
    print(Colours.GREEN + "Data Lineage Analysis complete." + Colours.RESET)


if __name__ == "__main__":
    main()