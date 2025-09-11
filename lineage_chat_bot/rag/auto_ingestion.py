import os
import json
import hashlib
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

# Initialize Chroma client with persistent storage
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(CHROMA_COLLECTION)

# Initialize OpenAI client
openai_client = OpenAI(api_key=OPENAI_API_KEY)

def get_file_hash(file_path):
    """Calculate MD5 hash of a file to detect changes."""
    if not os.path.exists(file_path):
        return None
    
    with open(file_path, 'rb') as f:
        content = f.read()
        return hashlib.md5(content).hexdigest()

def get_stored_metadata():
    """Get metadata about the last ingested file."""
    try:
        metadata_file = "./chroma_db/ingestion_metadata.json"
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r') as f:
                return json.load(f)
    except:
        pass
    return {}

def save_ingestion_metadata(file_path, file_hash, chunk_count):
    """Save metadata about the current ingestion."""
    metadata = {
        "last_ingested_file": file_path,
        "file_hash": file_hash,
        "chunk_count": chunk_count,
        "ingestion_timestamp": str(__import__('datetime').datetime.now())
    }
    
    metadata_file = "./chroma_db/ingestion_metadata.json"
    os.makedirs(os.path.dirname(metadata_file), exist_ok=True)
    
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)

def needs_reingestion():
    """Check if re-ingestion is needed."""
    current_hash = get_file_hash(LINEAGE_PATH)
    if current_hash is None:
        print(f"❌ Error: Lineage file not found: {LINEAGE_PATH}")
        return False
    
    stored_metadata = get_stored_metadata()
    stored_file = stored_metadata.get("last_ingested_file")
    stored_hash = stored_metadata.get("file_hash")
    
    # Check if file path changed
    if stored_file != LINEAGE_PATH:
        print(f"📄 File path changed: {stored_file} → {LINEAGE_PATH}")
        return True
    
    # Check if file content changed
    if stored_hash != current_hash:
        print(f"🔄 File content changed (hash: {stored_hash} → {current_hash})")
        return True
    
    print(f"✅ Data is up-to-date for: {LINEAGE_PATH}")
    return False

def embed_text(text):
    """Generate embeddings for text."""
    response = openai_client.embeddings.create(
        input=text,
        model=EMBED_MODEL
    )
    return response.data[0].embedding

def clear_collection():
    """Clear the existing collection data."""
    # Delete all documents in the collection
    try:
        # Get all IDs
        all_data = collection.get()
        if all_data['ids']:
            collection.delete(ids=all_data['ids'])
            print(f"🗑️  Cleared {len(all_data['ids'])} existing documents")
    except Exception as e:
        print(f"⚠️  Could not clear collection: {e}")

def auto_ingest():
    """Automatically ingest data if needed."""
    print("🔍 Checking if ingestion is needed...")
    
    if not needs_reingestion():
        print("✅ No ingestion needed - data is current")
        return True
    
    print("🚀 Starting automatic ingestion...")
    
    try:
        # Clear existing data
        clear_collection()
        
        # Load and convert lineage JSON to text chunks
        with open(LINEAGE_PATH, "r", encoding="utf-8") as f:
            lineage_json = json.load(f)
        
        text_chunks = convert_json_to_text_chunks(lineage_json)
        print(f"📝 Converted JSON to {len(text_chunks)} text chunks")
        
        # Process each chunk
        for i, chunk in enumerate(text_chunks, 1):
            embedding = embed_text(chunk["text"])
            safe_metadata = {"id": chunk["id"]}
            
            collection.add(
                ids=[chunk["id"]],
                embeddings=[embedding],
                documents=[chunk["text"]],
                metadatas=[safe_metadata]
            )
            
            if i % 3 == 0:  # Progress indicator
                print(f"📊 Processed {i}/{len(text_chunks)} chunks...")
        
        # Save metadata
        file_hash = get_file_hash(LINEAGE_PATH)
        save_ingestion_metadata(LINEAGE_PATH, file_hash, len(text_chunks))
        
        print(f"✅ Successfully ingested {len(text_chunks)} chunks from {LINEAGE_PATH}")
        print(f"🗄️  Collection '{CHROMA_COLLECTION}' is ready for queries")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during ingestion: {e}")
        return False

if __name__ == "__main__":
    success = auto_ingest()
    if success:
        print("\n🎉 Auto-ingestion completed successfully!")
    else:
        print("\n💥 Auto-ingestion failed!")
