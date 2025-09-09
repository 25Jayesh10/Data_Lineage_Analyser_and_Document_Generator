import streamlit as st
import sys
import os
import json
from dotenv import load_dotenv
load_dotenv()
# The llm calls which are happening here can happen in a seperate service file

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from lineage_chat_bot.cli_chat_service import (
    _initialize_openai, _initialize_gemini, _initialize_azure, _initialize_openrouter
)
from lineage_chat_bot.cli_chat import prompt_user_for_llm_client, select_model_name

st.set_page_config(page_title="Lineage Chatbot", layout="centered")
st.title("Lineage Chatbot")

# Load lineage data
LINEAGE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../output/lineage1.json'))
try:
    with open(LINEAGE_PATH, "r", encoding="utf-8") as f:
        lineage_data = f.read()
except Exception as e:
    st.error(f"Failed to load lineage data: {e}")
    st.stop()

# Step 1: Provider selection
providers = {"Gemini": "gemini", "Azure OpenAI": "azure openai", "OpenAI": "openai", "OpenRouter": "openrouter"}
provider_display = list(providers.keys())
selected_provider = st.selectbox("Select LLM Provider:", provider_display)

# Step 2: Model selection (dynamic, using CLI logic)
def get_models_for_provider(llm_choice):
    # Use the same logic as select_model_name in cli_chat.py
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

selected_model = st.selectbox("Select Model:", get_models_for_provider(providers[selected_provider]))

if st.button("Submit"):
    st.session_state["provider"] = providers[selected_provider]
    st.session_state["model"] = selected_model
    st.session_state["chat_started"] = True
    # Initialize messages with lineage context
    st.session_state["messages"] = [
        {"role": "system", "content": "You are a helpful assistant that answers questions based on the lineage data. Your purpose is to help the user gain better insights from the lineage. Help him understand what effects any changes will have and in general how the data flows. Do not answer any queries outside your scope, politely refuse when asked. Try to be concise and give accurate answers. Explain in detail only when explicitly asked or when it is absolutely necessary."},
        {"role": "user", "content": f"Here is the data lineage in JSON:\n {lineage_data}"}
    ]

# Step 3: Chatbot UI
if st.session_state.get("chat_started"):
    st.subheader(f"Chatbot - {selected_provider} ({selected_model})")
    # Only show actual chat (skip system and initial lineage context)
    for msg in st.session_state["messages"][2:]:
        st.write(f"{msg['role'].capitalize()}: {msg['content']}")

    user_input = st.text_input("Ask your question:", key="user_input")
    if st.button("Send") and user_input:
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
                      stream_container.write(f"Assistant: {answer}")
            elif provider == "azure openai":
                client = _initialize_azure()
                azure_deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
                response = client.chat.completions.create(
                    model=azure_deployment_name,
                    messages=st.session_state["messages"],
                    stream=False
                )
                answer = response.choices[0].message.content
                st.write(f"Assistant: {answer}")
            elif provider == "gemini":
                client = _initialize_gemini()
                prompt = '\n'.join([m['content'] for m in st.session_state["messages"] if m['role'] in ['user', 'assistant']])
                response = client.models.generate_content(
                    model=model,
                    contents=prompt
                )
                answer = response.text
            elif provider == "openrouter":
                import requests
                api_key = _initialize_openrouter()
                if not api_key:
                    answer = "Description generation failed due to missing OpenRouter API key."
                else:
                    headers = {
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    }
                    payload = {
                        "model": model,
                        "messages": st.session_state["messages"],
                        "temperature": 0.7
                    }
                    try:
                        resp = requests.post(
                            url="https://openrouter.ai/api/v1/chat/completions",
                            headers=headers,
                            json=payload
                        )
                        resp.raise_for_status()
                        data = resp.json()
                        answer = data["choices"][0]["message"]["content"].strip()
                    except Exception as e:
                        answer = f"Description could not be generated due to an OpenRouter API error: {e}"
            else:
                answer = "Unknown LLM provider."
        except Exception as e:
            answer = f"Error: {e}"
        print(f"LLM Response: {answer}")  # Log response to terminal
        st.session_state["messages"].append({"role": "assistant", "content": answer.strip()})
        st.rerun()