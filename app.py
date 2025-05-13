import os
from dotenv import load_dotenv
import google.generativeai as genai
import torch
from transformers import AutoTokenizer
from model import Transformer, ModelArgs
import json
import gradio as gr

# Carica le variabili d'ambiente
load_dotenv()

# Configurazione API Google
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)

# Configurazione del modello Gemini
gemini_model = genai.GenerativeModel('gemini-pro')

# Configurazione del modello DeepSeek
def load_deepseek_model(model_path, config_path):
    with open(config_path) as f:
        args = ModelArgs(**json.load(f))
    model = Transformer(args)
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    return model, tokenizer

# Carica il modello DeepSeek
model_path = "models/deepseek-coder-33b-instruct"
config_path = "inference/configs/config_33B.json"
deepseek_model, tokenizer = load_deepseek_model(model_path, config_path)

def generate_text(prompt, style, content_type):
    # Genera il testo usando entrambi i modelli
    gemini_response = gemini_model.generate_content(prompt)
    deepseek_response = generate(deepseek_model, [tokenizer.encode(prompt)], float('inf'), tokenizer.eos_token_id, 1.0)[0]
    
    # Combina le risposte
    combined_response = f"{gemini_response.text}\n\n{tokenizer.decode(deepseek_response)}"
    return combined_response

def analyze_style(text):
    # Analizza lo stile usando Gemini
    prompt = f"Analizza lo stile del seguente testo e fornisci suggerimenti per migliorarlo:\n\n{text}"
    response = gemini_model.generate_content(prompt)
    return response.text

def generate_book(title, genre, style, content_type):
    # Genera il libro usando entrambi i modelli
    prompt = f"Scrivi un libro intitolato '{title}' nel genere {genre}. Stile: {style}. Tipo di contenuto: {content_type}"
    
    gemini_response = gemini_model.generate_content(prompt)
    deepseek_response = generate(deepseek_model, [tokenizer.encode(prompt)], float('inf'), tokenizer.eos_token_id, 1.0)[0]
    
    # Combina le risposte
    combined_response = f"{gemini_response.text}\n\n{tokenizer.decode(deepseek_response)}"
    return combined_response

# Creazione dell'interfaccia Gradio
with gr.Blocks(title="ScribeNova - AI Writing Assistant") as demo:
    gr.Markdown("# ScribeNova - AI Writing Assistant")
    
    with gr.Tab("Generazione Testo"):
        with gr.Row():
            with gr.Column():
                prompt = gr.Textbox(label="Prompt", placeholder="Inserisci il tuo prompt qui...")
                style = gr.Dropdown(["naturale", "formale", "creativo"], label="Stile", value="naturale")
                content_type = gr.Dropdown(["qualsiasi", "articolo", "storia", "poesia"], label="Tipo di Contenuto", value="qualsiasi")
                generate_btn = gr.Button("Genera")
            with gr.Column():
                output = gr.Textbox(label="Risultato", lines=10)
        generate_btn.click(generate_text, inputs=[prompt, style, content_type], outputs=output)
    
    with gr.Tab("Analisi Stile"):
        with gr.Row():
            with gr.Column():
                text_input = gr.Textbox(label="Testo da Analizzare", lines=5)
                analyze_btn = gr.Button("Analizza")
            with gr.Column():
                analysis_output = gr.Textbox(label="Analisi", lines=10)
        analyze_btn.click(analyze_style, inputs=text_input, outputs=analysis_output)
    
    with gr.Tab("Generazione Libro"):
        with gr.Row():
            with gr.Column():
                title = gr.Textbox(label="Titolo")
                genre = gr.Dropdown(["fiction", "non-fiction", "fantasy", "sci-fi"], label="Genere", value="fiction")
                book_style = gr.Dropdown(["naturale", "formale", "creativo"], label="Stile", value="naturale")
                book_content_type = gr.Dropdown(["qualsiasi", "romanzo", "racconto", "saggio"], label="Tipo di Contenuto", value="qualsiasi")
                book_generate_btn = gr.Button("Genera Libro")
            with gr.Column():
                book_output = gr.Textbox(label="Libro Generato", lines=15)
        book_generate_btn.click(generate_book, inputs=[title, genre, book_style, book_content_type], outputs=book_output)

demo.launch(server_name="0.0.0.0", server_port=7860) 