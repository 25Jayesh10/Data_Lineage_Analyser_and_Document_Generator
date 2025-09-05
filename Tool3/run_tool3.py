import os
import json
from logging_styles import Colours
from doc_generator import generate_docs, prompt_for_llm_provider


def main():
    # Define file paths
    input_dir = "input/index"
    document_dir = "output/documents"
    index_path = os.path.join(input_dir, "index3.json")

    # ✅ Tool 3: Generate Markdown documentation
    try:
        print(Colours.YELLOW + "Generating Markdown documentation..." + Colours.RESET)
        llm_choice = prompt_for_llm_provider()
        generate_docs(index_path, output_dir=document_dir, output_file="procedures3.md", llm_provider=llm_choice)
        print(Colours.GREEN + "Documentation generated in 'document/procedures3.md'" + Colours.RESET)
    except Exception as e:
        print(Colours.RED + f"Error generating documentation: {e}" + Colours.RESET)
        return


if __name__ == "__main__":
    main()