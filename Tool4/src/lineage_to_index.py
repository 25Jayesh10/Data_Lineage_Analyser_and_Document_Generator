import json
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

def generate_index(lineage_path, mermaid_path, output_path):
    logger.info("📥 Loading lineage.json and lineage.mmd...")

    try:
        with open(lineage_path, "r") as f:
            lineage_data = json.load(f)
        logger.debug("✅ lineage.json loaded.")
        with open(mermaid_path, "r") as f:
            mermaid_lines = f.readlines()
        logger.debug("✅ lineage.mmd loaded.")
    except Exception as e:
        logger.error(f"❌ Failed to load files: {e}")
        return False

    index = {}

    logger.debug("🔄 Iterating over lineage items...")
    for name, item in lineage_data.items():
        if item.get("type") != "procedure":
            logger.debug(f"Skipping non-procedure: {name}")
            continue

        logger.debug(f"Processing procedure: {name}")

        # ✅ Start with tables and calls already present in lineage.json
        index_entry = {
            "calls": list(item.get("calls", [])),
            "tables": list(item.get("tables", []))
        }

        # ✅ Add additional tables inferred from usage section
        for other_name, other_item in lineage_data.items():
            if other_item.get("type") == "table":
                usage = other_item.get("usage", {})
                if name in usage and other_name not in index_entry["tables"]:
                    logger.debug(f"📎 Procedure '{name}' uses table '{other_name}' (from lineage.json usage)")
                    index_entry["tables"].append(other_name)

        index[name] = index_entry

    # ✅ Augment with Mermaid connections
    logger.debug("🔍 Parsing Mermaid connections for calls and table usage...")
    for line in mermaid_lines:
        line = line.strip()
        if "-->" in line and not line.startswith("%%"):
            parts = line.split("-->")
            if len(parts) == 2:
                caller = parts[0].strip()
                callee = parts[1].strip()

                if caller in index:
                    callee_type = lineage_data.get(callee, {}).get("type")
                    if callee_type == "procedure":
                        if callee not in index[caller]["calls"]:
                            logger.debug(f"🔗 Adding call from '{caller}' to procedure '{callee}' (from Mermaid)")
                            index[caller]["calls"].append(callee)
                    elif callee_type == "table":
                        if callee not in index[caller]["tables"]:
                            logger.debug(f"📎 Adding usage of table '{callee}' by procedure '{caller}' (from Mermaid)")
                            index[caller]["tables"].append(callee)

    # 🖨️ Print final result BEFORE writing
    logger.info("🖨️ Final Generated Index:")
    print(json.dumps(index, indent=2))

    try:
        logger.info(f"💾 Writing generated index to {output_path}...")
        with open(output_path, "w") as f:
            json.dump(index, f, indent=2)
        logger.info(f"✅ Index successfully written to: {output_path}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to write generated index file: {e}")
        return False
