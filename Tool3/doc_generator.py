import json
import os
from collections import Counter
import re
from llm_service import generate_business_logic


def slugify(text):
    # Converts text to a GitHub-compatible anchor
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = text.replace(" ", "-")
    return text

# Load the SQL file
with open("input/test/test2.sql", "r") as f:
    sql_text = f.read()

# Simple regex to extract stored procedure blocks (you can improve this as needed)
procedure_blocks = re.findall(r"CREATE\s+PROCEDURE\s+.*?AS\s+BEGIN(.*?)END", sql_text, re.DOTALL | re.IGNORECASE)

def generate_markdown(proc_name, details, llm_provider):
    anchor = slugify(proc_name)
    md = []
    md.append(f"## Stored Procedure: {proc_name}\n<a name=\"{anchor}\"></a>\n\n---\n")

    # Parameters
    md.append("### Parameters\n")
    md.append("| Name | Type |\n|------|------|")
    for param in details.get("params", []):
        md.append(f"| {param['name']} | {param['type']} |")
    md.append("\n---\n")

    # Tables
    md.append("### Tables\n")
    for table in details.get("tables", []):
        md.append(f"- {table}")
    md.append("\n---\n")

    # Called Procedures
    md.append("### Called Procedures\n")
    for proc in details.get("calls", []):
        md.append(f"- {proc}")
    md.append("\n---\n")

    # Call Graph - Mermaid
    md.append("### Call Graph\n")
    md.append("```mermaid\ngraph TD")
    for proc in details.get("calls", []):
        md.append(f"    {proc_name} --> {proc}")
    for table in details.get("tables", []):
        md.append(f"    {proc_name} --> {table}")
    md.append("```\n\n---\n")

    # # Business Logic via Gemini LLM
    # md.append("### Business Logic\n")
    # try:
    #     sql_code = details.get("sql", "")
    #     params_list = [f"@{p['name']}" for p in details.get("params", [])]
    #     description = generate_business_logic(proc_name, params_list, details.get("tables", []), sql_code)
    #     md.append(description)
    # except Exception as e:
    #     md.append("Description could not be generated due to an error.\n")
    #     print(f"⚠️ Error generating description for {proc_name}: {e}")

    # Business Logic via LLM
    md.append("### Business Logic\n")
    try:
        sql_code = details.get("sql", "")
        params_list = [f"@{p['name']}" for p in details.get("params", [])]
        
        # PASS llm_provider to the final function call
        description = generate_business_logic(
            proc_name, 
            params_list, 
            details.get("tables", []), 
            sql_code, 
            llm_provider  # The missing argument
        )
        md.append(description)
    except Exception as e:
        md.append("Description could not be generated due to an error.\n")
        print(f"⚠️ Error generating description for {proc_name}: {e}")

    md.append("\n---\n\n")
    return "\n".join(md)

def generate_summary(data):
    total_procedures = len(data)
    
    # Collect unique tables
    all_tables = set()
    for details in data.values():
        all_tables.update(details.get("tables", []))
    total_tables = len(all_tables)

    # Count how many times each proc is called
    call_counter = Counter()
    for details in data.values():
        call_counter.update(details.get("calls", []))

    most_called_proc = call_counter.most_common(1)[0][0] if call_counter else "N/A"

    summary = [
        "# Summary\n",
        f"- **Total Procedures**: {total_procedures}",
        f"- **Total Tables**: {total_tables}",
        f"- **Most Called Procedure**: `{most_called_proc}`",
        "\n---\n"
    ]
    return "\n".join(summary)

def generate_toc(data):
    toc_lines = ["# Table of Contents\n"]
    for proc_name in data:
        anchor = slugify(proc_name)
        toc_lines.append(f"- [{proc_name}](#{anchor})")
    toc_lines.append("\n---\n")
    return "\n".join(toc_lines)

def extract_sql_blocks(sql_text):
    proc_blocks = {}
    pattern = re.compile(r"CREATE\s+PROCEDURE\s+(\w+).*?AS\s+BEGIN(.*?)END", re.DOTALL | re.IGNORECASE)
    for match in pattern.finditer(sql_text):
        proc_name = match.group(1)
        sql_body = match.group(0)  # Full block including CREATE ... END
        proc_blocks[proc_name] = sql_body.strip()
    return proc_blocks


def prompt_for_llm_provider():
    """Interactively prompts the user to select an LLM provider."""
    providers = {"1": "gemini", "2": "azure", "3": "anthropic", "4": "openrouter"}
    print("\nPlease select an LLM provider to generate descriptions:")
    for key, value in providers.items():
        print(f"  {key}: {value.capitalize()}")
    
    while True:
        choice = input("Enter the number for your choice (1/2/3/4): ")
        if choice in providers:
            return providers[choice]
        else:
            print("❌ Invalid selection. Please enter 1, 2, or 3.")


def generate_docs(json_path,  llm_provider, output_dir="docs", output_file="procedures.md"):
    with open(json_path) as f:
        data = json.load(f)

    sql_blocks = extract_sql_blocks(sql_text)

    os.makedirs(output_dir, exist_ok=True)

    all_markdown = []

     # Announce which LLM is being used based on user's choice
    print(f"✅ Using [{llm_provider.upper()}] to generate business logic descriptions.")

    # Add summary
    all_markdown.append(generate_summary(data))

    # Add TOC
    all_markdown.append(generate_toc(data))

    # Add procedure markdown blocks
    for proc_name, details in data.items():
        # Attach SQL block before passing to markdown generator
        details["sql"] = sql_blocks.get(proc_name, "")
        markdown = generate_markdown(proc_name, details, llm_provider)
        all_markdown.append(markdown)

    full_doc = "\n".join(all_markdown)
    output_path = os.path.join(output_dir, output_file)
    with open(output_path, "w") as f:
        f.write(full_doc)

    print(f"Generated: {output_path}")
    
import json
import os
from collections import Counter
import re
from llm_service import generate_business_logic


def slugify(text):
    # Converts text to a GitHub-compatible anchor
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = text.replace(" ", "-")
    return text

# Load the SQL file
with open("input/test/test2.sql", "r") as f:
    sql_text = f.read()

# Simple regex to extract stored procedure blocks (you can improve this as needed)
procedure_blocks = re.findall(r"CREATE\s+PROCEDURE\s+.*?AS\s+BEGIN(.*?)END", sql_text, re.DOTALL | re.IGNORECASE)

def generate_markdown(obj_name, details, llm_provider, obj_type="procedure"):
    """Generates markdown documentation for procedures, functions, or triggers."""
    anchor = slugify(obj_name)
    md = []
    md.append(f"## {obj_type.capitalize()}: {obj_name}\n<a name=\"{anchor}\"></a>\n\n---\n")

    # Parameters
    if obj_type in ["procedure", "function"]:
        md.append("### Parameters\n")
        md.append("| Name | Type |\n|------|------|")
        for param in details.get("params", []):
            md.append(f"| {param['name']} | {param['type']} |")
        md.append("\n---\n")

    # Tables
    md.append("### Tables\n")
    for table in details.get("tables", []):
        md.append(f"- {table}")
    md.append("\n---\n")

    # Called Procedures/Functions
    md.append("### Calls\n")
    for proc in details.get("calls", []):
        md.append(f"- {proc}")
    md.append("\n---\n")

    # Call Graph - Mermaid
    md.append("### Call Graph\n")
    md.append("```mermaid\ngraph TD")
    for proc in details.get("calls", []):
        md.append(f"    {obj_name} --> {proc}")
    for table in details.get("tables", []):
        md.append(f"    {obj_name} --> {table}")
    md.append("```\n\n---\n")

    # Business Logic via LLM
    md.append("### Business Logic\n")
    try:
        sql_code = details.get("sql", "")
        params_list = [f"@{p['name']}" for p in details.get("params", [])]

        description = generate_business_logic(
            obj_name,
            params_list,
            details.get("tables", []),
            sql_code,
            llm_provider
        )
        md.append(description)
    except Exception as e:
        md.append("Description could not be generated due to an error.\n")
        print(f"⚠️ Error generating description for {obj_name}: {e}")

    md.append("\n---\n\n")
    return "\n".join(md)

def generate_summary(data):
    total_procedures = len(data.get("procedures", {}))
    total_functions = len(data.get("functions", {}))
    total_triggers = len(data.get("triggers", {}))
    
    # Collect unique tables
    all_tables = set()
    for section in ["procedures", "functions", "triggers"]:
        for details in data.get(section, {}).values():
            all_tables.update(details.get("tables", []))
    total_tables = len(all_tables)

    # Count how many times each proc is called
    call_counter = Counter()
    for section in ["procedures", "functions", "triggers"]:
        for details in data.get(section, {}).values():
            call_counter.update(details.get("calls", []))

    most_called = call_counter.most_common(1)[0][0] if call_counter else "N/A"

    summary = [
        "# Summary\n",
        f"- **Total Procedures**: {total_procedures}",
        f"- **Total Functions**: {total_functions}",
        f"- **Total Triggers**: {total_triggers}",
        f"- **Total Tables**: {total_tables}",
        f"- **Most Called Object**: `{most_called}`",
        "\n---\n"
    ]
    return "\n".join(summary)

def generate_toc(data):
    toc_lines = ["# Table of Contents\n"]

    for section, label in [("procedures", "Procedure"), ("functions", "Function"), ("triggers", "Trigger")]:
        for obj_name in data.get(section, {}):
            anchor = slugify(obj_name)
            toc_lines.append(f"- {label}: [{obj_name}](#{anchor})")

    toc_lines.append("\n---\n")
    return "\n".join(toc_lines)

def extract_sql_blocks(sql_text):
    proc_blocks = {}

    patterns = {
        "procedures": re.compile(r"CREATE\s+PROCEDURE\s+(\w+).*?AS\s+BEGIN(.*?)END", re.DOTALL | re.IGNORECASE),
        "functions": re.compile(r"CREATE\s+FUNCTION\s+(\w+).*?AS\s+BEGIN(.*?)END", re.DOTALL | re.IGNORECASE),
        "triggers": re.compile(r"CREATE\s+TRIGGER\s+(\w+).*?AS\s+BEGIN(.*?)END", re.DOTALL | re.IGNORECASE),
    }

    results = {"procedures": {}, "functions": {}, "triggers": {}}

    for key, pattern in patterns.items():
        for match in pattern.finditer(sql_text):
            name = match.group(1)
            sql_body = match.group(0)
            results[key][name] = sql_body.strip()

    return results


def prompt_for_llm_provider():
    """Interactively prompts the user to select an LLM provider."""
    providers = {"1": "gemini", "2": "azure", "3": "anthropic", "4": "openrouter"}
    print("\nPlease select an LLM provider to generate descriptions:")
    for key, value in providers.items():
        print(f"  {key}: {value.capitalize()}")
    
    while True:
        choice = input("Enter the number for your choice (1/2/3/4): ")
        if choice in providers:
            return providers[choice]
        else:
            print("❌ Invalid selection. Please enter 1, 2, or 3.")


def generate_docs(json_path,  llm_provider, output_dir="docs", output_file="procedures.md"):
    with open(json_path) as f:
        data = json.load(f)

    sql_blocks = extract_sql_blocks(sql_text)

    os.makedirs(output_dir, exist_ok=True)

    all_markdown = []

     # Announce which LLM is being used based on user's choice
    print(f"✅ Using [{llm_provider.upper()}] to generate business logic descriptions.")

    # Add summary
    all_markdown.append(generate_summary(data))

    # Add TOC
    all_markdown.append(generate_toc(data))

    # Add procedure markdown blocks
    # for proc_name, details in data.items():
    #     # Attach SQL block before passing to markdown generator
    #     details["sql"] = sql_blocks.get(proc_name, "")
    #     markdown = generate_markdown(proc_name, details, llm_provider)
    #     all_markdown.append(markdown)

    for section, obj_type in [("procedures", "procedure"), ("functions", "function"), ("triggers", "trigger")]:
        for obj_name, details in data.get(section, {}).items():
            details["sql"] = sql_blocks.get(section, {}).get(obj_name, "")
            markdown = generate_markdown(obj_name, details, llm_provider, obj_type=obj_type)
            all_markdown.append(markdown)

    full_doc = "\n".join(all_markdown)
    output_path = os.path.join(output_dir, output_file)
    with open(output_path, "w") as f:
        f.write(full_doc)

    print(f"Generated: {output_path}")