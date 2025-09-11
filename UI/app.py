import sys
import os
import streamlit as st
from streamlit_mermaid import st_mermaid
import json
from pathlib import Path
import re
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

# --- FIX: Add project root (Data_Lineage) to sys.path ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(project_root)

# Now imports will work
from lineage_chat_bot.cli_chat_service import (
    _initialize_openai, _initialize_gemini, _initialize_azure, _initialize_openrouter
)


# ======================================================================================
# Page Configuration
# ======================================================================================
st.set_page_config(
    page_title="Analytics Dashboard",
    page_icon="📊",
    layout="wide"
)

# ======================================================================================
# Custom Styling (Dark Dashboard Theme)
# ======================================================================================
st.markdown(
    """
    <style>
        .stApp {
            background-color: #0e1117;
            color: #fafafa;
        }
        h1, h2, h3, h4 {
            color: #f9fafb;
        }
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        .stChatMessage {
            background: #262730;
            border-radius: 10px;
            padding: 12px;
            margin-bottom: 7px;
        }
    </style>
    """,
    unsafe_allow_html=True
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

def render_mermaid_dynamic(mermaid_code: str, base_height: int = 400, multiplier: int = 50, max_height: int = 1500):
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
st.sidebar.title("📂 File Selection")
st.sidebar.markdown("Choose input files for the dashboard:")

# --- JSON selection ---
if not lineage_files:
    st.sidebar.warning("No 'lineage*.json' files found in the 'output' directory.")
    st.warning("Please add lineage JSON files to the 'output' folder to begin.")
    st.stop()

file_options = {file.name: file for file in lineage_files}
selected_file_name = st.sidebar.selectbox("📄 Lineage JSON:", options=file_options.keys())
selected_file_path = file_options[selected_file_name]
lineage_data = load_json_file(selected_file_path)

# --- Mermaid selection ---
diagram_content = None
selected_diagram_name = None
if diagram_files:
    diagram_options = {file.name: file for file in diagram_files}
    selected_diagram_name = st.sidebar.selectbox("🔗 Mermaid Diagram:", options=diagram_options.keys())
    selected_diagram_path = diagram_options[selected_diagram_name]
    diagram_content = load_text_file(selected_diagram_path)
else:
    st.sidebar.info("No Mermaid diagram files found in 'output/diagrams'.")

# --- Documentation selection ---
doc_content = None
selected_doc_name = None
if doc_files:
    doc_options = {file.name: file for file in doc_files}
    selected_doc_name = st.sidebar.selectbox("📘 Documentation:", options=doc_options.keys())
    selected_doc_path = doc_options[selected_doc_name]
    doc_content = load_text_file(selected_doc_path)
else:
    st.sidebar.info("No documentation files found in 'output/docs'.")

st.sidebar.divider()
st.sidebar.info("💡 Tip: You can switch between JSON, Mermaid diagrams, and documentation.")

# ======================================================================================
# Main Dashboard UI
# ======================================================================================

st.title("📊 Analytics Dashboard")
st.caption(f"Displaying data from: **{selected_file_name}**")
st.divider()

# --- Top section with two columns ---
col1, col2 = st.columns([1, 2])  # JSON smaller, Mermaid bigger

with col1:
    st.subheader("📊 Lineage JSON Data")
    st.json(lineage_data, expanded=True)

with col2:
    if diagram_content:
        st.subheader("🔗 Mermaid Diagram (Preview)")
        render_mermaid_dynamic(diagram_content)

# --- Full-width Mermaid section ---
if diagram_content:
    st.divider()
    st.subheader("📈 Mermaid Diagram (Full Width)")
    render_mermaid_dynamic(diagram_content, base_height=800, multiplier=60, max_height=2000)

# ======================================================================================
# Documentation & Chat Assistant Section
# ======================================================================================
st.divider()

doc_col, chat_col = st.columns(2, gap="large")

with doc_col:
    st.subheader("📘 Business Logic Documentation")
    with st.container(border=True):
        if doc_content:
            st.caption(f"From file: {selected_doc_name}")
            render_markdown_with_mermaid(doc_content)
        else:
            st.info("No documentation file selected. Content will appear here.")

with chat_col:
    st.subheader("🤖 Dashboard Assistant")

    with st.container(border=True):
        # Step 1: Provider selection
        providers = {
            "Gemini": "gemini",
            "Azure OpenAI": "azure openai",
            "OpenAI": "openai",
            "OpenRouter": "openrouter"
        }
        provider_display = list(providers.keys())
        selected_provider = st.selectbox("Select LLM Provider:", provider_display, key="provider_select")

        # Step 2: Model selection
        def get_models_for_provider(llm_choice):
            if llm_choice == "gemini":
                return ["gemini-2.0-flash", "gemini-1.5-flash"]
            elif llm_choice == "azure openai":
                return [os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME") or "Set deployment name in .env"]
            elif llm_choice == "openai":
                return ["gpt-4o", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"]
            elif llm_choice == "openrouter":
                return ["mistralai/mistral-small-3.2-24b-instruct:free"]
            else:
                return []

        selected_model = st.selectbox("Select Model:", get_models_for_provider(providers[selected_provider]), key="model_select")

        # Step 3: Start chat
        if st.button("Start Chat", key="start_chat"):
            st.session_state["provider"] = providers[selected_provider]
            st.session_state["model"] = selected_model
            st.session_state["chat_started"] = True
            st.session_state["messages"] = [
                {"role": "system", "content": (
                    "You are a helpful assistant that answers questions based on the lineage data. "
                    "Your purpose is to help the user gain better insights from the lineage. "
                    "Help them understand what effects any changes will have and in general how the data flows. "
                    "Do not answer any queries outside your scope; politely refuse when asked. "
                    "Try to be concise and give accurate answers. Explain in detail only when explicitly asked "
                    "or when it is absolutely necessary."
                )},
                {"role": "user", "content": f"Here is the data lineage in JSON:\n {json.dumps(lineage_data, indent=2)}"}
            ]

        # Step 4: Chat UI
        if st.session_state.get("chat_started"):
            st.markdown(f"**Provider:** {selected_provider} | **Model:** {selected_model}")
            st.divider()

            # Display conversation (skip system + lineage context)
            for msg in st.session_state["messages"][2:]:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

            # Chat input
            if user_input := st.chat_input("Ask your question..."):
                st.session_state["messages"].append({"role": "user", "content": user_input})
                provider = st.session_state["provider"]
                model = st.session_state["model"]
                answer = ""

                try:
                    if provider == "openai":
                        client = _initialize_openai()
                        response_stream = client.chat.completions.create(
                            model=model,
                            messages=st.session_state["messages"],
                            stream=True
                        )
                        answer = ""
                        stream_container = st.empty()
                        for chunk in response_stream:
                            delta = getattr(chunk.choices[0].delta, "content", "")
                            if delta is not None:
                                answer += delta
                                stream_container.markdown(f"**Assistant:** {answer}")

                    elif provider == "azure openai":
                        client = _initialize_azure()
                        azure_deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
                        response = client.chat.completions.create(
                            model=azure_deployment_name,
                            messages=st.session_state["messages"],
                            stream=False
                        )
                        answer = response.choices[0].message.content
                        st.markdown(f"**Assistant:** {answer}")

                    elif provider == "gemini":
                        client = _initialize_gemini()
                        prompt = '\n'.join([m['content'] for m in st.session_state["messages"] if m['role'] in ['user', 'assistant']])
                        response = client.models.generate_content(
                            model=model,
                            contents=prompt
                        )
                        answer = response.text
                        st.markdown(f"**Assistant:** {answer}")

                    elif provider == "openrouter":
                        api_key = _initialize_openrouter()
                        if not api_key:
                            answer = "⚠️ Missing OpenRouter API key."
                        else:
                            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                            payload = {"model": model, "messages": st.session_state["messages"], "temperature": 0.7}
                            resp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
                            resp.raise_for_status()
                            data = resp.json()
                            answer = data["choices"][0]["message"]["content"].strip()
                            st.markdown(f"**Assistant:** {answer}")

                    else:
                        answer = "Unknown LLM provider."

                except Exception as e:
                    answer = f"❌ Error: {e}"

                # Save assistant response
                st.session_state["messages"].append({"role": "assistant", "content": answer.strip()})
                st.rerun()
