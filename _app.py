import tkinter as tk
from tkinter import messagebox
from tkinter import scrolledtext
import requests
import json
from chromadb import Client
from chromadb.config import Settings
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction 

embedding_function = SentenceTransformerEmbeddingFunction("all-MiniLM-L6-v2")
settings = Settings(
    persist_directory="./chroma_data",)

chromadb_client = Client(settings=settings)
collection = chromadb_client.get_or_create_collection(name="notebook_paragraphs", embedding_function=embedding_function)

BASE_URL = "http://localhost:11434/api/generate"
CONTEXT_FILE = "context.txt"

def initialize_context():
    with open(CONTEXT_FILE, "r") as file:
        context = file.read()
    
    paragraphs = [p.strip() for p in context.split("\n") if p.strip()]
    for i, paragraph in enumerate(paragraphs):
        collection.add(
            documents=[paragraph],
            metadatas=[{"doc": f"paragraph_{i}"}],
            ids=[f"id_{i}"]
        )
    print(f"Context initialized with {len(paragraphs)} paragraphs. from {CONTEXT_FILE}")

def process_prompt(user_input, context):
    ethical_prompt = ("Como sistema de IA, asegurase de que sus respuestas sean imparciales, éticas y cumplan con las regulaciones de la IA. "
        "Considere la equidad, la privacidad y la inclusión en su respuesta. "
        "Por favor no respondas a preguntas que puedan ser sensuradas con su contenido. "
        "Tus mensajes no deben ser mayores de doscientas palabras. "
        "Todas tus respuestas deben ser en Español")
    
    return f"{ethical_prompt} Contexto: {context} Pregunta: {user_input}"


def get_ia_response():
    user_input = input_field.get("1.0", tk.END).strip()
    if not user_input:
        messagebox.showwarning("Aviso", "Por favor, introduce una consulta.")
        return
    
    result = collection.query(
        query_texts=[user_input],
        n_results=2
    )

    context = "\n".join(result['documents'][0])

    modified_prompt = process_prompt(user_input, context)

    response_text.delete("1.0", tk.END)  # Clear previous response
    response_text.insert(tk.END, "Consultando IA...\n")

    response = requests.post(BASE_URL, 
                             json={"model": "dolphin-mistral:latest",
                                   "prompt": modified_prompt,
                                   "max_tokens": 500})
    complete_response = ""

    for line in response.iter_lines(decode_unicode=True):
        if line:
            data = json.loads(line)
            if "response" in data:
                complete_response += data["response"]
            
    response_text.delete("1.0", tk.END)  # Clear previous response
    response_text.insert(tk.END, f"Respuesta de la IA:\n{complete_response}")


initialize_context()

root = tk.Tk()
root.title("Consultas a la IA con RAG")

input_label = tk.Label(root, text="Introduce tu consulta:")
input_label.pack(pady=5)

input_field = scrolledtext.ScrolledText(root, wrap=tk.WORD,  width=60, height=10)
input_field.pack(pady=5)

button = tk.Button(root, text="Enviar consulta", command=lambda: get_ia_response())
button.pack(pady=5)

response_label = tk.Label(root, text="Respuesta de la IA:")
response_label.pack(pady=5) 

response_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=60, height=10)
response_text.pack(pady=5)


root.mainloop()
