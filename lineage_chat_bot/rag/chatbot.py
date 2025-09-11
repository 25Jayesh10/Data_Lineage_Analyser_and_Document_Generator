import os
from openai import OpenAI
from dotenv import load_dotenv
from query import retrieve

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o")

openai_client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = "You are a helpful assistant that answers questions based on data lineage."


def build_prompt(system_prompt, context_chunks, user_query):
    context = "\n\n".join([chunk["document"] for chunk in context_chunks])
    prompt = f"{system_prompt}\n\nContext:\n{context}\n\nUser Query: {user_query}"
    return prompt


def chat(user_query, k=3):
    context_chunks = retrieve(user_query, k)
    if not context_chunks or all(not chunk["document"] for chunk in context_chunks):
        return "I couldn’t find this information in the lineage data."
    prompt = build_prompt(SYSTEM_PROMPT, context_chunks, user_query)
    response = openai_client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )
    return response.choices[0].message.content.strip()

if __name__ == "__main__":
    user_query = input("Ask your lineage question: ")
    answer = chat(user_query)
    print("Assistant:", answer)
