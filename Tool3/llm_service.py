import os
import google.generativeai as genai
import openai
import anthropic
from dotenv import load_dotenv

# Load all environment variables from a .env file
load_dotenv()


def _initialize_gemini():
    """Initializes and returns the Gemini model client."""
    try:
        api_key = os.environ["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        return genai.GenerativeModel('gemini-1.5-flash')
    except KeyError:
        print("❌ Error: GEMINI_API_KEY not found in .env file.")
        return None


def _initialize_azure():
    """Initializes and returns the Azure OpenAI client."""
    try:
        return openai.AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),  # default if not set
        )
    except KeyError as e:
        print(f"❌ Error: {e} not found in .env file for Azure configuration.")
        return None



def _initialize_anthropic():
    """Initializes and returns the Anthropic client."""
    try:
        return anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    except KeyError:
        print("❌ Error: ANTHROPIC_API_KEY not found in .env file.")
        return None


def _initialize_openrouter():
    """Initializes and returns the OpenRouter API key."""
    try:
        api_key = os.getenv("OPEN_ROUTER")
        if not api_key:
            raise KeyError("OPEN_ROUTER")
        return api_key
    except KeyError:
        print("❌ Error: OPENROUTER_API_KEY not found in .env file.")
        return None

def _initialize_openai():
    """Initializes and returns the standard OpenAI client."""
    try:
        # The library can infer the key from the environment, but we check explicitly for a better error message.
        if not os.getenv("OPENAI_API_KEY"):
            raise KeyError
        return openai.OpenAI() # Automatically uses OPENAI_API_KEY from .env
    except KeyError:
        print("❌ Error: OPENAI_API_KEY not found in .env file.")
        return None

def _generate_with_gemini(prompt: str) -> str:
    """Generates content using Google Gemini."""
    model = _initialize_gemini()
    
    if not model:
        return "Description generation failed due to missing Gemini API key."
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Description could not be generated due to a Gemini API error: {e}"


def _generate_with_azure(prompt: str) -> str:
    """Generates content using Azure OpenAI."""
    azure_client = _initialize_azure()
    deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

    if not azure_client:
        return "Description generation failed due to missing Azure API key or endpoint."

    try:
        response = azure_client.chat.completions.create(
            model=deployment_name,  # 👈 deployment name used here
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Description could not be generated due to an Azure API error: {e}"



def _generate_with_anthropic(prompt: str) -> str:
    """Generates content using Anthropic Claude."""
    anthropic_client = _initialize_anthropic()
    if not anthropic_client:
        return "Description generation failed due to missing Anthropic API key."
    try:
        response = anthropic_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text.strip()
    except Exception as e:
        return f"Description could not be generated due to an Anthropic API error: {e}"


def _generate_with_openrouter(prompt: str, model: str = "mistralai/mistral-small-3.2-24b-instruct:free") -> str:
    """Generates content using OpenRouter."""
    api_key = _initialize_openrouter()
    if not api_key:
        return "Description generation failed due to missing OpenRouter API key."
    try:
        import requests
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"Description could not be generated due to an OpenRouter API error: {e}"

def _generate_with_openai(prompt: str) -> str:
    """Generates content using OpenAI."""
    openai_client = _initialize_openai()
    if not openai_client:
        return "Description generation failed due to missing OpenAI API key."

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",  # You can specify other models like "gpt-3.5-turbo"
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Description could not be generated due to an OpenAI API error: {e}"
    
def generate_business_logic(proc_name: str, params: list, tables: list, sql_code: str, llm_provider: str) -> str:
    """
    Crafts a detailed prompt and gets a business logic description from the selected LLM provider.
    This function acts as a dispatcher based on the user's runtime choice.
    """
    prompt = f"""
    You are a Senior Business Analyst with deep SQL expertise. Your task is to analyze the provided SQL stored procedure and write a comprehensive, easy-to-understand description of its business logic for a non-technical audience.

    **CONTEXT:**
    - **Object Name:** {proc_name}
    - **Parameters:** {params}
    - **Tables Involved:** {tables}
    - **SQL Source Code:**
    ```sql
    {sql_code}
    ```

    **INSTRUCTION:**
    Based on all the provided context, please generate a detailed business logic description. Do not just describe what the code does, but explain *why* it does it from a business process perspective. Structure your response as follows:
    1.  **Overall Purpose:** Start with a high-level summary. What is the primary business goal of this procedure?
    2.  **Process Breakdown:** Describe the step-by-step business process this procedure automates. Explain the significance of key calculations, conditions (like IF/ELSE or CASE statements), and the data flow.
    3.  **Key Business Rules:** Explicitly list and explain any important business rules embedded in the logic. For example, "A 10% bonus is applied to employees with 5 or more years of service."
    4.  **Inputs and Outputs:** Briefly describe what business information the procedure needs to run (Inputs) and what it produces (Outputs).

    **Output Format:**
    Provide the response in plain text. Use numbered lists or simple headers for each section as outlined in the instructions. Avoid using markdown, code blocks, or any other special formatting.

    """

    if llm_provider == "azure":
        return _generate_with_azure(prompt)
    elif llm_provider == "anthropic":
        return _generate_with_anthropic(prompt)
    elif llm_provider == "gemini":
        return _generate_with_gemini(prompt)
    elif llm_provider == "openai": # 👈 ADDED THIS NEW PROVIDER
        return _generate_with_openai(prompt)
    elif llm_provider == "openrouter":
        return _generate_with_openrouter(prompt)
    else:
        return "Error: Unknown LLM provider specified."
