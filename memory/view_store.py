# memory/view_store.py
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import chromadb

client = chromadb.PersistentClient(path="chroma_db")
collections = client.list_collections()

print(f"\nCollections found: {len(collections)}")

for c in collections:
    col = client.get_collection(c.name)
    count = col.count()
    print(f"\n{'='*60}")
    print(f"Collection: {c.name} ({count} entries)")
    print(f"{'='*60}")

    results = col.get()
    for i, doc in enumerate(results["documents"]):
        print(f"\n[Entry {i+1}]")
        print(f"ID:       {results['ids'][i]}")
        print(f"Metadata: {results['metadatas'][i]}")
        print(f"Content:  {doc[:200]}...")