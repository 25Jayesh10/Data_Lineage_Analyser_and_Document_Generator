
import os
import json
import chromadb
from chromadb.config import Settings
from openai import OpenAI
from dotenv import load_dotenv
from json_to_text import convert_json_to_text_chunks

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
LINEAGE_PATH = os.getenv("LINEAGE_PATH", "output/lineage1.json")
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "lineage_chunks")
LINEAGE_TEXT_PATH = os.getenv("LINEAGE_TEXT_PATH", "output/lineage_text_chunks.json")

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

def sanitize_metadata(metadata):
    # Convert lists/dicts to strings for Chroma compatibility
    return {k: (json.dumps(v) if isinstance(v, (list, dict)) else v) for k, v in metadata.items()}

def main():
    # Load and convert lineage JSON to text chunks
    with open(LINEAGE_PATH, "r", encoding="utf-8") as f:
        lineage_json = json.load(f)
    text_chunks = convert_json_to_text_chunks(lineage_json)
    print(text_chunks)
    for chunk in text_chunks:
        embedding = embed_text(chunk["text"])
        safe_metadata = {"id": chunk["id"]}
        collection.add(
            ids=[chunk["id"]],
            embeddings=[embedding],
            documents=[chunk["text"]],
            metadatas=[safe_metadata]
        )
    print(f"Ingested {len(text_chunks)} text chunks into Chroma collection '{CHROMA_COLLECTION}'.")

if __name__ == "__main__":
    main()
