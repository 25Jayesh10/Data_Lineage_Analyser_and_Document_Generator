import streamlit as st
from streamlit_mermaid import st_mermaid
import json
from pathlib import Path
import re

# ======================================================================================
# Page Configuration
# ======================================================================================
st.set_page_config(
    page_title="Analytics Dashboard",
    page_icon="📊",
    layout="wide"
)

# ======================================================================================
# Data Loading
# ======================================================================================

def load_json_file(file_path):
    """Loads a JSON file with error handling."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"🚨 Error: The file was not found at '{file_path}'. Please make sure it exists.")
        st.stop()
    except json.JSONDecodeError:
        st.error(f"🚨 Error: The file at '{file_path}' is not a valid JSON file.")
        st.stop()

def load_text_file(file_path):
    """Loads a plain text file (used for Mermaid diagrams / markdown)."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        st.error(f"🚨 Error: The file was not found at '{file_path}'. Please make sure it exists.")
        st.stop()

# ======================================================================================
# Dynamic Mermaid Renderer
# ======================================================================================

def render_mermaid_dynamic(mermaid_code: str, base_height: int = 200, multiplier: int = 30, max_height: int = 1000):
    """Render a Mermaid diagram with dynamic height adjustment."""
    line_count = len(mermaid_code.splitlines())
    height = min(max_height, base_height + line_count * multiplier)
    st_mermaid(mermaid_code.strip(), height=f"{height}px")

def render_markdown_with_mermaid(md_text: str):
    """Render markdown with embedded mermaid diagrams dynamically."""
    blocks = re.split(r"```mermaid|```", md_text)
    for i, block in enumerate(blocks):
        if i % 2 == 1:  # Mermaid block
            render_mermaid_dynamic(block)
        else:  # Markdown block
            st.markdown(block)

# ======================================================================================
# PATH LOGIC
# ======================================================================================
app_dir = Path(__file__).resolve().parent
project_root = app_dir.parent.resolve()
output_dir = project_root / "output"

# Find all lineage JSON files
lineage_files = sorted(output_dir.glob("lineage*.json"))

# Find all Mermaid diagram files
diagram_dir = output_dir / "diagrams"
diagram_files = sorted(diagram_dir.glob("*.mmd"))

# Find documentation files
docs_dir = output_dir / "documents"
doc_files = sorted(docs_dir.glob("*.md"))

# ======================================================================================
# Sidebar File Selection
# ======================================================================================
st.sidebar.title("📄 File Selection")

# --- JSON selection ---
if not lineage_files:
    st.sidebar.warning("No 'lineage*.json' files found in the 'output' directory.")
    st.warning("Please add lineage JSON files to the 'output' folder to begin.")
    st.stop()

file_options = {file.name: file for file in lineage_files}
selected_file_name = st.sidebar.selectbox(
    "Choose a lineage JSON file:",
    options=file_options.keys()
)
selected_file_path = file_options[selected_file_name]
lineage_data = load_json_file(selected_file_path)

# --- Mermaid selection ---
diagram_content = None
selected_diagram_name = None
if diagram_files:
    diagram_options = {file.name: file for file in diagram_files}
    selected_diagram_name = st.sidebar.selectbox(
        "Choose a Mermaid diagram:",
        options=diagram_options.keys()
    )
    selected_diagram_path = diagram_options[selected_diagram_name]
    diagram_content = load_text_file(selected_diagram_path)
else:
    st.sidebar.info("No Mermaid diagram files found in 'output/diagrams'.")

# --- Documentation selection ---
doc_content = None
selected_doc_name = None
if doc_files:
    doc_options = {file.name: file for file in doc_files}
    selected_doc_name = st.sidebar.selectbox(
        "Choose documentation file:",
        options=doc_options.keys()
    )
    selected_doc_path = doc_options[selected_doc_name]
    doc_content = load_text_file(selected_doc_path)
else:
    st.sidebar.info("No documentation files found in 'output/docs'.")

# ======================================================================================
# Main Dashboard UI
# ======================================================================================

st.title("📊 Analytics Dashboard")
st.caption(f"Displaying data from: **{selected_file_name}**")
st.divider()

# --- Top section with two columns ---
col1, col2 = st.columns([1, 2])  # JSON smaller, Mermaid bigger

with col1:
    st.header("Lineage JSON Data")
    st.json(lineage_data, expanded=True)

with col2:
    if diagram_content:
        st.header("📈 Mermaid Diagram (Dynamic Preview)")
        st.caption(f"Diagram: {selected_diagram_name}")
        render_mermaid_dynamic(diagram_content)

# --- Full-width Mermaid section ---
if diagram_content:
    st.header("📈 Mermaid Diagram (Full Width)")
    st.markdown("Below is the selected Mermaid diagram rendered in full width with dynamic sizing:")
    render_mermaid_dynamic(diagram_content, base_height=300, multiplier=40, max_height=1200)

# --- Documentation Section ---
if doc_content:
    st.header("📑 Documentation")
    st.caption(f"From file: {selected_doc_name}")
    render_markdown_with_mermaid(doc_content)

# ======================================================================================
# Chat Assistant
# ======================================================================================
st.header("🤖 Dashboard Assistant")
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! Ask me about the currently loaded lineage data."}]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask about the loaded data..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response = ""
        if "id" in prompt.lower():
            item_id = lineage_data.get("id", "N/A")
            response = f"The 'id' from this file is **{item_id}**."
        elif "author" in prompt.lower():
            author_name = lineage_data.get("author", {}).get("name", "not specified")
            response = f"The author listed in this file is **{author_name}**."
        else:
            response = "I can answer questions about the 'id' or 'author' fields from the selected JSON file."
        
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})
