#This is a validation script that checks if the AST is consistent with the index.json file

# import os
# import json

# def validate(index_path :str,ast_path :str ):
   
#     try:
#         with open(index_path,"r") as f:
#             index_data=json.load(f)
#         with open(ast_path,"r") as f:
#             ast_data=json.load(f)
#     except Exception as e:
#         print(f"Error while opening the file- {e}")
    
#     #most naive proc_name based validation
#     index_proc_set=set(index_data.keys()) # set of all proc_names in the index
#     ast_proc_set=set()
#     # set of all procs in ast
#     for item in ast_data:
#         ast_proc_set.add(item.get("proc_name","not_defined"))
#     if "not_defined" in index_proc_set or "not_defined" in ast_proc_set:
#         print('\033[91m'+ "Inconsistency between AST and Index file detected! Please Check your Inputs\n Error Type- one of the procedure names has not been defined in either of the files"+'\033[0m') #These escape sequence characters have been added to colour the text on the terminal and can be removed.
#         return False
    
#     if index_proc_set == ast_proc_set:
#         print('\033[92m'+"Naive Validation Done"+'\033[0m')
#         return True
#     else:
#         print('\033[91m'+ "Inconsistency between AST and Index file detected! Please Check your Inputs\n Error Type- Some procedures have been found which are present in the one of the files but not in the other"+'\033[0m')
#         return False
    
import os
import json
import jsonschema
from src.logging_styles import Colours

def validate(index_path: str, ast_path: str) -> bool:
    """
    Validates the ast.json and index.json files against their schemas
    and checks for consistency between them.

    Args:
        index_path (str): The file path for the index.json file.
        ast_path (str): The file path for the ast.json file.

    Returns:
        bool: True if both validation and consistency checks pass, False otherwise.
    """
    # --- Corrected Path Resolution ---
    # Get the directory of the current script (src)
    src_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up one level to the main tool directory (Tool4)
    tool_dir = os.path.dirname(src_dir)
    # Define the absolute path to the schemas directory
    schema_dir = os.path.join(tool_dir, "schemas")
    
    ast_schema_path = os.path.join(schema_dir, "ast_Schema.json")
    # Corrected filename to match capitalization in screenshot
    index_schema_path = os.path.join(schema_dir, "index_Schema.json")

    try:
        # Load all necessary files
        with open(index_path, "r") as f:
            index_data = json.load(f)
        with open(ast_path, "r") as f:
            ast_data = json.load(f)
        with open(ast_schema_path, "r") as f:
            ast_schema = json.load(f)
        with open(index_schema_path, "r") as f:
            index_schema = json.load(f)

    except FileNotFoundError as e:
        print(f"{Colours.RED}Error: Missing a required file: {e.filename}{Colours.RESET}")
        return False
    except json.JSONDecodeError as e:
        print(f"{Colours.RED}Error: Invalid JSON in file: {e.doc}. Details: {e.msg}{Colours.RESET}")
        return False

    # 1. Validate against JSON Schemas
    try:
        print("Validating ast.json against its schema...")
        jsonschema.validate(instance=ast_data, schema=ast_schema)
        print(f"{Colours.GREEN}AST schema validation successful.{Colours.RESET}")

        print("Validating index.json against its schema...")
        jsonschema.validate(instance=index_data, schema=index_schema)
        print(f"{Colours.GREEN}Index schema validation successful.{Colours.RESET}")

    except jsonschema.exceptions.ValidationError as e:
        print(f"{Colours.RED}Schema validation failed: {e.message} in '{'.'.join(map(str, e.path))}'{Colours.RESET}")
        return False

    # 2. Check for name consistency across all object types
    all_consistent = True
    key_map = {
        "procedures": "proc_name",
        "functions": "func_name",
        "triggers": "trigger_name"
    }

    print(f"\n{Colours.YELLOW}--- Starting Consistency Check ---{Colours.RESET}")
    for obj_type, name_key in key_map.items():
        index_names = set(index_data.get(obj_type, {}).keys())
        ast_names = {item.get(name_key) for item in ast_data.get(obj_type, []) if item.get(name_key)}

        # Debugging statements to show what is being compared
        print(f"\n{Colours.YELLOW}Checking consistency for {obj_type}...{Colours.RESET}")
        print(f"Found in index.json: {sorted(list(index_names)) if index_names else '[]'}")
        print(f"Found in ast.json:   {sorted(list(ast_names)) if ast_names else '[]'}")

        if index_names != ast_names:
            all_consistent = False
            missing_in_ast = index_names - ast_names
            missing_in_index = ast_names - index_names
            if missing_in_ast:
                print(f"{Colours.RED}Inconsistency Found: The following {obj_type} are in index.json but missing from ast.json: {', '.join(missing_in_ast)}{Colours.RESET}")
            if missing_in_index:
                print(f"{Colours.RED}Inconsistency Found: The following {obj_type} are in ast.json but missing from index.json: {', '.join(missing_in_index)}{Colours.RESET}")
        else:
            print(f"{Colours.GREEN}Consistency for {obj_type} passed.{Colours.RESET}")

    print(f"\n{Colours.YELLOW}--- Consistency Check Complete ---{Colours.RESET}")
    if all_consistent:
        print(f"{Colours.GREEN}Overall name consistency check passed.{Colours.RESET}")
        return True
    else:
        print(f"{Colours.RED}Overall name consistency check failed.{Colours.RESET}")
        return False
