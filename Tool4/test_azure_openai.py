import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

def test_azure_openai_chat():
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION")
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    assert api_key and api_version and azure_endpoint and deployment_name, "Azure OpenAI environment variables not set."

    client = AzureOpenAI(
        api_key=api_key,
        api_version=api_version,
        azure_endpoint=azure_endpoint
    )
    messages = [
        {"role": "user", "content": "Hello, are you working?"}
    ]
    response = client.chat.completions.create(
        model=deployment_name,
        messages=messages,
        stream=False
    )
    answer = response.choices[0].message.content
    print("Azure OpenAI response:", answer)
    assert answer, "No response from Azure OpenAI."

if __name__ == "__main__":
    test_azure_openai_chat()
