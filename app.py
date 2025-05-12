from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
import google.generativeai as genai
import torch
from transformers import AutoTokenizer
from model import Transformer, ModelArgs
import json

app = Flask(__name__)
CORS(app)

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

@app.route('/')
def home():
    return render_template('mobile.html')

@app.route('/api/generate', methods=['POST'])
def generate_text():
    data = request.json
    prompt = data.get('prompt', '')
    style = data.get('style', 'natural')
    content_type = data.get('content_type', 'any')
    
    # Genera il testo usando entrambi i modelli
    gemini_response = gemini_model.generate_content(prompt)
    deepseek_response = generate(deepseek_model, [tokenizer.encode(prompt)], float('inf'), tokenizer.eos_token_id, 1.0)[0]
    
    # Combina le risposte
    combined_response = f"{gemini_response.text}\n\n{tokenizer.decode(deepseek_response)}"
    
    return jsonify({
        'success': True,
        'response': combined_response
    })

@app.route('/api/analyze_style', methods=['POST'])
def analyze_style():
    data = request.json
    text = data.get('text', '')
    
    # Analizza lo stile usando Gemini
    prompt = f"Analizza lo stile del seguente testo e fornisci suggerimenti per migliorarlo:\n\n{text}"
    response = gemini_model.generate_content(prompt)
    
    return jsonify({
        'success': True,
        'analysis': response.text
    })

@app.route('/api/generate_book', methods=['POST'])
def generate_book():
    data = request.json
    title = data.get('title', '')
    genre = data.get('genre', 'fiction')
    style = data.get('style', 'natural')
    content_type = data.get('content_type', 'any')
    
    # Genera il libro usando entrambi i modelli
    prompt = f"Scrivi un libro intitolato '{title}' nel genere {genre}. Stile: {style}. Tipo di contenuto: {content_type}"
    
    gemini_response = gemini_model.generate_content(prompt)
    deepseek_response = generate(deepseek_model, [tokenizer.encode(prompt)], float('inf'), tokenizer.eos_token_id, 1.0)[0]
    
    # Combina le risposte
    combined_response = f"{gemini_response.text}\n\n{tokenizer.decode(deepseek_response)}"
    
    return jsonify({
        'success': True,
        'book': combined_response
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 