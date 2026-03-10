import chromadb
import os

DB_PATH = r"c:\Users\HP Victus 16\.nanobot\workspace\chroma_db"
COLLECTION_NAME = "finance_knowledge"

def inspect_db():
    if not os.path.exists(DB_PATH):
        print(f"Database path not found: {DB_PATH}")
        return

    try:
        client = chromadb.PersistentClient(path=DB_PATH)
        print(f"Connected to ChromaDB at {DB_PATH}")
        
        try:
            collection = client.get_collection(name=COLLECTION_NAME)
            count = collection.count()
            print(f"Collection '{COLLECTION_NAME}' found with {count} documents.")
            
            if count > 0:
                print("\nCannot retrieve all items efficiently without embedding, but checking first few...")
                # Peek returns top N items
                results = collection.peek(limit=5)
                
                print("\n--- Document Preview ---")
                ids = results['ids']
                documents = results['documents']
                metadatas = results['metadatas']
                
                for i in range(len(ids)):
                    print(f"\nDocument ID: {ids[i]}")
                    print(f"Metadata: {metadatas[i]}")
                    print(f"Content (first 200 chars): {documents[i][:200]}...")
            else:
                print("\nCollection is empty.")
                
        except ValueError:
             print(f"Collection '{COLLECTION_NAME}' does not exist.")
             # List available collections
             print("Available collections:")
             for col in client.list_collections():
                 print(f" - {col.name}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    inspect_db()
