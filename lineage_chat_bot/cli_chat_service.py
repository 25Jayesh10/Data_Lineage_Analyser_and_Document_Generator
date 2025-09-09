import os
import json
import openai
from dotenv import load_dotenv

def _initialize_openai():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found in .env file.")
        return None
    return openai.OpenAI(api_key=api_key)

def _initialize_gemini():
    try:
        from google import genai
        # API key is picked up from GEMINI_API_KEY env var
        client = genai.Client()
        return client
    except Exception:
        print("❌ Error: google-genai not installed or GEMINI_API_KEY not set.")
        return None

def _initialize_azure():
    try:
        return openai.AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
    except Exception as e:
        print(f"❌ Error: {e} in Azure configuration.")
        return None

def _initialize_openrouter():
    api_key = os.getenv("OPEN_ROUTER")
    if not api_key:
        print("❌ Error: OPEN_ROUTER not found in .env file.")
        return None
    return api_key

from lineage_chat_bot.cli_chat import prompt_user_for_llm_client as select_llm_provider, select_model_name

def run_command_line_chat(lineage_path="./output/lineage1.json"):
    load_dotenv()
    llm_choice = select_llm_provider()
    model = select_model_name(llm_choice)
    # Initialize client
    if llm_choice == "openai":
        client = _initialize_openai()
    elif llm_choice == "gemini":
        client = _initialize_gemini()
    elif llm_choice == "azure openai":
        client = _initialize_azure()
    elif llm_choice == "openrouter":
        client = _initialize_openrouter()
    else:
        print("Unknown LLM provider.")
        return
    try:
        with open(lineage_path, "r", encoding="utf-8") as f:
            data = f.read()
            _ = json.loads(data)  # Validate JSON
    except Exception as e:
        raise RuntimeError(f"Failed to read or parse {lineage_path}: {e}")

    print(f"Welcome to the Lineage-Analysis Chatbot ({llm_choice.capitalize()})")
    messages = [
        {"role": "system", "content": "You are a helpful assistant that answers questions based on the lineage data. Your purpose is to help the user gain better insights from the lineage. Help him undersatnd what effects any chnages will have and In general how the data flows. Do not answer any queries outside your scope, politely refuse when asked. Try to be concise and give accurate answers. Explain in detail only when explicitly asked on when it is absolutely necessary"},
        {"role": "user", "content": f"Here is the data lineage in JSON:\n {data}"}
    ]
    while True:
        question = input("Ask Your Question About The Lineage Or Type ('exit'): ")
        if question.strip().lower() == "exit":
            break
        messages.append({"role": "user", "content": question})
        try:
            if llm_choice == "openai":
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    stream=False
                )
                answer = response.choices[0].message.content
            elif llm_choice == "azure openai":
                    azure_deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
                    if azure_deployment_name:
                    # Use deployment name for Azure OpenAI
                        response = client.chat.completions.create(
                            model=azure_deployment_name,
                            messages=messages,
                            stream=False
                        )
                    answer = response.choices[0].message.content
            elif llm_choice == "gemini":
                # Gemini expects a single string prompt, so concatenate context
                prompt = '\n'.join([m['content'] for m in messages if m['role'] in ['user', 'assistant']])
                response = client.models.generate_content(
                    model=model,
                    contents=prompt
                )
                answer = response.text
            elif llm_choice == "openrouter":
                import requests
                api_key = client
                headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                payload = {"model": model, "messages": messages, "temperature": 0.7}
                resp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                answer = data["choices"][0]["message"]["content"]
            else:
                answer = "Unknown LLM provider."
            print("\nAnswer:", answer.strip())
            messages.append({"role": "assistant", "content": answer.strip()})
        except Exception as e:
            print(f"Error from {llm_choice.capitalize()}: {e}")
