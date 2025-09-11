import os
import chromadb
from chromadb.config import Settings
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "lineage_chunks")

# Initialize Chroma client with persistent storage
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(CHROMA_COLLECTION)

# Initialize OpenAI client
openai_client = OpenAI(api_key=OPENAI_API_KEY)

def embed_text(text):
    response = openai_client.embeddings.create(
        input=text,
        model=EMBED_MODEL
    )
    return response.data[0].embedding

def retrieve(query, k=3):
    query_embedding = embed_text(query)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=k
    )
    # Return top-k chunks (documents and metadata) - flatten the nested lists
    chunks = []
    if results["documents"] and results["metadatas"]:
        documents = results["documents"][0]  # First (and only) query result
        metadatas = results["metadatas"][0]   # First (and only) query result
        for doc, meta in zip(documents, metadatas):
            chunks.append({"document": doc, "metadata": meta})
    return chunks

if __name__ == "__main__":
    # Example usage
    user_query = input("Enter your query: ")
    top_chunks = retrieve(user_query, k=3)
    print(f"\nFound {len(top_chunks)} relevant chunks:")
    for i, chunk in enumerate(top_chunks, 1):
        print(f"\nChunk {i}: {chunk['document']}")
        print(f"ID: {chunk['metadata']['id']}")
        print("-" * 50)
