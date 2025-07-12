import customtkinter as ctk
import tkinter as tk
import requests
import json
from chromadb import Client
from chromadb.config import Settings
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

# Configuración de CustomTkinter
ctk.set_appearance_mode("dark")  # modo oscuro
ctk.set_default_color_theme("blue")

# Inicializar ChromaDB
embedding_function = SentenceTransformerEmbeddingFunction("all-MiniLM-L6-v2")
settings = Settings(persist_directory="./chroma_data")
chromadb_client = Client(settings=settings)
collection = chromadb_client.get_or_create_collection(
    name="notebook_paragraphs", embedding_function=embedding_function
)

BASE_URL = "http://localhost:11434/api/generate"
CONTEXT_FILE = "context.txt"

# Ahora query_history es lista de dicts con consulta y valores de checks
query_history = []

def initialize_context():
    with open(CONTEXT_FILE, "r", encoding="utf-8") as file:
        context = file.read()
    paragraphs = [p.strip() for p in context.split("\n") if p.strip()]
    for i, paragraph in enumerate(paragraphs):
        collection.add(
            documents=[paragraph],
            metadatas=[{"doc": f"paragraph_{i}"}],
            ids=[f"id_{i}"]
        )
    print(f"Context initialized with {len(paragraphs)} paragraphs from {CONTEXT_FILE}")

def process_prompt(user_input, context):
    ethical_prompt = (
        "Como sistema de IA, asegurase de que sus respuestas sean imparciales, éticas y cumplan con las regulaciones de la IA. "
        "Considere la equidad, la privacidad y la inclusión en su respuesta. "
        "Por favor no respondas a preguntas que puedan ser sensuradas con su contenido. "
        "Tus mensajes no deben ser mayores de doscientas palabras. "
        "Todas tus respuestas deben ser en Español."
    )
    return f"{ethical_prompt}\n\nContexto: {context}\n\nPregunta: {user_input}"

def get_ia_response(event=None):
    user_input = input_field.get("1.0", "end").strip()
    if not user_input:
        ctk.CTkMessagebox(title="Aviso", message="Por favor, introduce una consulta.")
        return

    status_bar.configure(text="🔄 Consultando IA...")
    root.update()

    # Determinar si usar RAG
    use_rag = rag_var.get()
    n_results = 5 if expand_results_var.get() else 1  # si expandir resultados está activo

    if use_rag:
        result = collection.query(query_texts=[user_input], n_results=n_results)
        context = "\n".join([doc for sublist in result['documents'] for doc in sublist])
    else:
        context = "(Sin contexto RAG, consulta directa al modelo)"

    # Guardar en historial con estado de checkboxes
    query_history.append({
        "query": user_input,
        "use_rag": use_rag,
        "expand_results": expand_results_var.get()
    })
    update_history()

    modified_prompt = process_prompt(user_input, context)

    debug_context.delete("1.0", "end")
    debug_context.insert("end", f"📄 Contexto usado:\n{context}")

    response_text.delete("1.0", "end")
    response_text.insert("end", "⏳ Esperando respuesta de la IA...\n")

    try:
        response = requests.post(
            BASE_URL,
            json={"model": "dolphin-mistral:latest", "prompt": modified_prompt, "max_tokens": 500}
        )
        response.raise_for_status()

        complete_response = ""
        for line in response.iter_lines(decode_unicode=True):
            if line:
                data = json.loads(line)
                if "response" in data:
                    complete_response += data["response"]

        response_text.delete("1.0", "end")
        response_text.insert("end", f"🧠 Respuesta de la IA:\n\n{complete_response}")
        status_bar.configure(text="✅ Respuesta recibida.")
    except requests.RequestException as e:
        response_text.delete("1.0", "end")
        response_text.insert("end", f"❌ Error al consultar la IA:\n{e}")
        status_bar.configure(text="⚠️ Error en la consulta.")

def clear_fields():
    input_field.delete("1.0", "end")
    response_text.delete("1.0", "end")
    debug_context.delete("1.0", "end")
    status_bar.configure(text="🗑️ Pantalla limpia.")

def update_history():
    history_list.delete(0, "end")
    for idx, item in enumerate(query_history[-10:], start=1):
        rag_status = "RAG: Sí" if item["use_rag"] else "RAG: No"
        expand_status = "Ampliar: Sí" if item["expand_results"] else "Ampliar: No"
        history_list.insert("end", f"{idx}. {item['query']} [{rag_status}, {expand_status}]")

def toggle_expand_results():
    """Habilitar o deshabilitar el checkbox de expandir resultados según RAG."""
    if rag_var.get():
        expand_results_checkbox.configure(state="normal")
    else:
        expand_results_checkbox.deselect()
        expand_results_checkbox.configure(state="disabled")

# --- Construcción UI ---

root = ctk.CTk()
root.title("🚀 Consultas a la IA con RAG")
root.geometry("950x850+200+50")  # centrado y más arriba

# Label entrada
input_label = ctk.CTkLabel(root, text="Introduce tu consulta:", font=("Arial", 14, "bold"))
input_label.pack(pady=(15, 5))

# Campo texto input
input_field = ctk.CTkTextbox(root, width=800, height=120, font=("Arial", 12))
input_field.pack(padx=20, pady=5)
input_field.bind("<Control-Return>", get_ia_response)  # Ctrl+Enter para enviar

# Frame botones y opciones
options_frame = ctk.CTkFrame(root)
options_frame.pack(pady=10)

send_button = ctk.CTkButton(options_frame, text="🤖 Enviar consulta (Ctrl+Enter)", command=get_ia_response, width=240)
send_button.grid(row=0, column=0, padx=10)

clear_button = ctk.CTkButton(options_frame, text="🗑️ Limpiar pantalla", command=clear_fields, width=180)
clear_button.grid(row=0, column=1, padx=10)

# Checkboxes
rag_var = tk.BooleanVar(value=True)
expand_results_var = tk.BooleanVar(value=False)

rag_checkbox = ctk.CTkCheckBox(
    options_frame, text="Usar RAG", variable=rag_var, command=toggle_expand_results
)
rag_checkbox.grid(row=1, column=0, padx=10, pady=(10, 0), sticky="w")

expand_results_checkbox = ctk.CTkCheckBox(
    options_frame, text="Ampliar resultados (1 → 5)", variable=expand_results_var, state="normal"
)
expand_results_checkbox.grid(row=1, column=1, padx=10, pady=(10, 0), sticky="w")

# Label respuesta
response_label = ctk.CTkLabel(root, text="Respuesta de la IA:", font=("Arial", 14, "bold"))
response_label.pack(pady=(15, 5))

response_text = ctk.CTkTextbox(root, width=800, height=200, font=("Arial", 12))
response_text.pack(padx=20, pady=5)

# Debug contexto
debug_label = ctk.CTkLabel(root, text="(Debug) Contexto utilizado:", font=("Arial", 11, "italic"))
debug_label.pack(pady=(10, 2))

debug_context = ctk.CTkTextbox(root, width=800, height=100, font=("Arial", 10))
debug_context.pack(padx=20, pady=5)

# Historial consultas
history_label = ctk.CTkLabel(root, text="📜 Historial de consultas:", font=("Arial", 11, "bold"))
history_label.pack(pady=(10, 2))

history_list = tk.Listbox(root, height=6, font=("Arial", 11),
                          bg="#1f1f1f", fg="white",
                          bd=0, highlightthickness=0,
                          relief="flat", activestyle="none")
history_list.pack(padx=20, pady=5, fill="x")

# Barra de estado
status_bar = ctk.CTkLabel(root, text="🔵 Listo para consultas.", anchor="w", font=("Arial", 11))
status_bar.pack(side="bottom", fill="x", pady=5, padx=10)

# Inicializar contexto y lanzar app
initialize_context()
root.mainloop()
