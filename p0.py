import chromadb
from chromadb.utils import embedding_functions

client = chromadb.Client()

collection = client.create_collection(name="clase3")

#print(collection)

list = client.list_collections()
client.delete_collection(name="clase3")

collection.add(
    documents=["Primer artículo", "Segundo Artículo", "España está siendo invadida por los aliens", "Israel invade palestina"],
    metadatas=[{"doc": "ciencias"}, {"doc": "Ficción"}, {"doc": "actualidad"}, {"doc": "actualidad"}],
    ids=["id1", "id2", "id3", "id4"]
)

#results = collection.query(query_texts=["invasión"], n_results=1)
'''

embedding_functions.DefaultEmbeddingFunction()
print("Embedding function created successfully.")

#sentence_embedding = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
sentence_embedding = embedding_functions.SentenceTransformerEmbeddingFunction("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

embedding_vector = sentence_embedding.get_embeddings("invasión")

collection.add(
    documents=["Israel invade palestina"],
    metadatas=[{"doc": "actualidad"}],
    ids=["id4"],
    embeddings=[embedding_vector])
'''
results = collection.query(
    query_embeddings=[embedding_vector], n_results=1)
print(results)