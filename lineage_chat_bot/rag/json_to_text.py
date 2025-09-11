import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
LINEAGE_PATH = os.getenv("LINEAGE_PATH", "output/lineage1.json")
OUTPUT_PATH = os.getenv("LINEAGE_TEXT_PATH", "output/lineage_text_chunks.json")


def summarize_table(name, obj):
    lines = [f"Table: {name}"]
    if "called_by" in obj:
        lines.append(f"  Called by: {', '.join(obj['called_by'])}")
    if "columns" in obj:
        col_lines = []
        for col in obj["columns"]:
            col_lines.append(f"    - {col['name']} ({col['usage']}) by {col['caller']} [{col['caller_type']}]")
        lines.append("  Columns:\n" + "\n".join(col_lines))
    if "type" in obj:
        lines.append(f"  Type: {obj['type']}")
    return "\n".join(lines)


def summarize_procedure(name, obj):
    lines = [f"Procedure: {name}"]
    for key in ["called_by_function", "called_by_procedure", "called_by_trigger", "calls"]:
        if key in obj and obj[key]:
            lines.append(f"  {key.replace('_', ' ').title()}: {', '.join(obj[key])}")
    if "type" in obj:
        lines.append(f"  Type: {obj['type']}")
    return "\n".join(lines)



def convert_json_to_text_chunks(lineage_json):
    text_chunks = []
    for name, obj in lineage_json.items():
        if obj.get("type") == "table":
            text = summarize_table(name, obj)
        elif obj.get("type") == "procedure":
            text = summarize_procedure(name, obj)
        else:
            text = f"{name}: {json.dumps(obj)}"
        text_chunks.append({"id": name, "text": text})
    return text_chunks

# Keep main for standalone usage
if __name__ == "__main__":
    import os
    import json
    from dotenv import load_dotenv
    load_dotenv()
    LINEAGE_PATH = os.getenv("LINEAGE_PATH", "output/lineage1.json")
    OUTPUT_PATH = os.getenv("LINEAGE_TEXT_PATH", "output/lineage_text_chunks.json")
    with open(LINEAGE_PATH, "r", encoding="utf-8") as f:
        lineage_json = json.load(f)
    text_chunks = convert_json_to_text_chunks(lineage_json)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(text_chunks, f, indent=2)
    print(f"Saved {len(text_chunks)} text chunks to {OUTPUT_PATH}")
