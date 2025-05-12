import os
import json
import zlib
from argparse import ArgumentParser
from typing import List, Dict
from datetime import datetime
import docx
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
import random
import requests
from PIL import Image
import io
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import googleapiclient.discovery
from bs4 import BeautifulSoup
import re
from dotenv import load_dotenv
import google.generativeai as genai
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import torch
import torch.distributed as dist
from transformers import AutoTokenizer
from safetensors.torch import load_model

from model import Transformer, ModelArgs

app = Flask(__name__)
CORS(app)

# Carica le variabili d'ambiente
load_dotenv()

# Configurazione API Google
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', 'AIzaSyCWkP0oZmmS2LP79tH3VHMGKy7XypGb_f4')
genai.configure(api_key=GOOGLE_API_KEY)

# Configurazione del modello Gemini
model = genai.GenerativeModel('gemini-pro')

def sample(logits, temperature: float = 1.0):
    """
    Samples a token from the logits using temperature scaling.

    Args:
        logits (torch.Tensor): The logits tensor for token predictions.
        temperature (float, optional): Temperature for scaling logits. Defaults to 1.0.

    Returns:
        torch.Tensor: The sampled token.
    """
    logits = logits / max(temperature, 1e-5)
    probs = torch.softmax(logits, dim=-1)
    return probs.div_(torch.empty_like(probs).exponential_(1)).argmax(dim=-1)


@torch.inference_mode()
def generate(
    model: Transformer,
    prompt_tokens: List[List[int]],
    max_new_tokens: int,
    eos_id: int,
    temperature: float = 1.0
) -> List[List[int]]:
    """
    Generates new tokens based on the given prompt tokens using the specified model.

    Args:
        model (Transformer): The transformer model used for token generation.
        prompt_tokens (List[List[int]]): A list of lists containing the prompt tokens for each sequence.
        max_new_tokens (int): The maximum number of new tokens to generate.
        eos_id (int): The end-of-sequence token ID.
        temperature (float, optional): The temperature value for sampling. Defaults to 1.0.

    Returns:
        List[List[int]]: A list of lists containing the generated tokens for each sequence.
    """
    prompt_lens = [len(t) for t in prompt_tokens]
    total_len = max_new_tokens + max(prompt_lens)
    tokens = torch.full((len(prompt_tokens), total_len), -1, dtype=torch.long, device="cuda")
    for i, t in enumerate(prompt_tokens):
        tokens[i, :len(t)] = torch.tensor(t, dtype=torch.long, device="cuda")
    prev_pos = 0
    finished = torch.tensor([False] * len(prompt_tokens), device="cuda")
    prompt_mask = tokens != -1
    for cur_pos in range(min(prompt_lens), total_len):
        logits = model.forward(tokens[:, prev_pos:cur_pos], prev_pos)
        if temperature > 0:
            next_token = sample(logits, temperature)
        else:
            next_token = logits.argmax(dim=-1)
        next_token = torch.where(prompt_mask[:, cur_pos], tokens[:, cur_pos], next_token)
        tokens[:, cur_pos] = next_token
        finished |= torch.logical_and(~prompt_mask[:, cur_pos], next_token == eos_id)
        prev_pos = cur_pos
        if finished.all():
            break
    completion_tokens = []
    for i, toks in enumerate(tokens.tolist()):
        toks = toks[prompt_lens[i]:prompt_lens[i]+max_new_tokens]
        if eos_id in toks:
            toks = toks[:toks.index(eos_id)]
        completion_tokens.append(toks)
    return completion_tokens


def save_book(content: str, title: str = None) -> str:
    """
    Salva il contenuto generato come libro compresso usando zlib.
    
    Args:
        content (str): Il contenuto del libro da salvare
        title (str, optional): Il titolo del libro. Se None, viene generato automaticamente
        
    Returns:
        str: Il percorso del file salvato
    """
    if title is None:
        title = f"book_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Crea la directory books se non esiste
    os.makedirs("books", exist_ok=True)
    
    # Comprimi il contenuto
    compressed_content = zlib.compress(content.encode('utf-8'))
    
    # Salva il file
    file_path = os.path.join("books", f"{title}.zlib")
    with open(file_path, 'wb') as f:
        f.write(compressed_content)
    
    return file_path


def analyze_book_structure(book_content: str) -> Dict:
    """
    Analizza la struttura di un libro per estrarre informazioni utili.
    
    Args:
        book_content (str): Il contenuto del libro da analizzare
        
    Returns:
        Dict: Dizionario con le informazioni estratte
    """
    # Qui il modello analizzerà il libro per estrarre:
    # - Struttura dei capitoli
    # - Stile di scrittura
    # - Personaggi principali
    # - Trama
    # - Temi
    # - Atmosfera
    return {
        "structure": "analisi della struttura",
        "style": "analisi dello stile",
        "characters": "analisi dei personaggi",
        "plot": "analisi della trama",
        "themes": "analisi dei temi",
        "atmosphere": "analisi dell'atmosfera"
    }


def generate_book_outline(prompt: str, book_analysis: Dict) -> str:
    """
    Genera una struttura dettagliata per il nuovo libro basata sull'analisi.
    
    Args:
        prompt (str): La richiesta dell'utente
        book_analysis (Dict): L'analisi del libro di riferimento
        
    Returns:
        str: La struttura del nuovo libro
    """
    # Il modello genererà una struttura dettagliata per il nuovo libro
    return "Struttura dettagliata del nuovo libro..."


def write_book_chapter(chapter_outline: str, style_guide: Dict) -> str:
    """
    Scrive un capitolo completo del libro senza limiti di lunghezza.
    """
    # Il modello genererà il capitolo completo senza restrizioni
    return "Contenuto del capitolo senza limiti..."


def generate_book_cover(title: str, genre: str = "fiction") -> str:
    """
    Genera una copertina per un libro usando GPT-Image-1.
    
    Args:
        title (str): Titolo del libro
        genre (str): Genere del libro (fiction, fantasy, romance, thriller, etc.)
        
    Returns:
        str: Percorso dell'immagine della copertina
    """
    # Configurazione per GPT-Image-1
    api_url = "https://api.gpt-image-1.com/v1/images/generations"
    headers = {
        "Authorization": f"Bearer {os.getenv('GPT_IMAGE_API_KEY')}",
        "Content-Type": "application/json"
    }
    
    # Stili di copertina per genere
    genre_styles = {
        "fiction": "elegante e minimalista, con elementi tipografici moderni",
        "fantasy": "magica e onirica, con elementi di fantasia e colori vivaci",
        "romance": "romantica e delicata, con colori pastello e elementi floreali",
        "thriller": "drammatica e misteriosa, con contrasti forti e ombre",
        "historical": "vintage e classica, con elementi d'epoca",
        "sci-fi": "futuristica e tecnologica, con elementi di design moderno",
        "horror": "inquietante e dark, con elementi gotici",
        "biography": "sofisticata e professionale, con elementi minimalisti"
    }
    
    # Crea il prompt per la copertina
    style = genre_styles.get(genre.lower(), genre_styles["fiction"])
    prompt = f"Copertina di libro per '{title}', {style}. La copertina deve essere professionale e adatta a un libro pubblicato. Includi spazio per il titolo e l'autore. Stile: copertina di libro professionale, alta qualità, risoluzione 4K"
    
    # Chiamata API
    response = requests.post(
        api_url,
        headers=headers,
        json={
            "prompt": prompt,
            "n": 1,
            "size": "1024x1024",
            "response_format": "url"
        }
    )
    
    if response.status_code == 200:
        image_url = response.json()["data"][0]["url"]
        
        # Scarica l'immagine
        image_response = requests.get(image_url)
        if image_response.status_code == 200:
            # Crea la directory per le copertine se non esiste
            os.makedirs("book_covers", exist_ok=True)
            
            # Salva l'immagine
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            image_path = os.path.join("book_covers", f"cover_{safe_title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            with open(image_path, "wb") as f:
                f.write(image_response.content)
            
            return image_path
    
    return None


def add_image_to_document(doc: docx.Document, image_path: str, caption: str = None):
    """
    Aggiunge un'immagine al documento Word con una didascalia opzionale.
    """
    doc.add_picture(image_path, width=Inches(6))
    if caption:
        caption_paragraph = doc.add_paragraph(caption)
        caption_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        caption_paragraph.style = 'Caption'


def save_as_word(book_content: Dict, title: str) -> str:
    """
    Salva il libro in formato Word con formattazione professionale.
    """
    doc = docx.Document()
    
    # Imposta lo stile del titolo
    title_style = doc.styles['Title']
    title_style.font.size = Pt(24)
    title_style.font.bold = True
    title_style.font.name = 'Times New Roman'
    
    # Aggiunge il titolo
    doc.add_heading(title, 0)
    
    # Aggiunge i capitoli
    for chapter in book_content['chapters']:
        doc.add_heading(chapter['title'], level=1)
        
        for subchapter in chapter['subchapters']:
            doc.add_heading(subchapter['title'], level=2)
            
            # Aggiunge il contenuto del sottocapitolo
            paragraphs = subchapter['content'].split('\n\n')
            for para in paragraphs:
                p = doc.add_paragraph(para)
                p.style = 'Normal'
                p.style.font.name = 'Times New Roman'
                p.style.font.size = Pt(12)
    
    # Salva il documento
    os.makedirs("generated_books", exist_ok=True)
    file_path = os.path.join("generated_books", f"{title}.docx")
    doc.save(file_path)
    
    return file_path


def analyze_western_style(book_content: str) -> Dict:
    """
    Analizza lo stile occidentale di un libro, con focus su elementi italiani e rumeni.
    
    Args:
        book_content (str): Il contenuto del libro da analizzare
        
    Returns:
        Dict: Dizionario con le informazioni estratte
    """
    return {
        "structure": "analisi della struttura occidentale",
        "style": "analisi dello stile letterario europeo",
        "characters": "analisi dei personaggi in stile occidentale",
        "plot": "analisi della trama con elementi culturali europei",
        "themes": "analisi dei temi occidentali",
        "cultural_elements": {
            "italian": "elementi culturali italiani",
            "romanian": "elementi culturali rumeni",
            "european": "elementi culturali europei"
        }
    }


def generate_western_outline(prompt: str, book_analysis: Dict) -> str:
    """
    Genera una struttura per un libro in stile occidentale.
    
    Args:
        prompt (str): La richiesta dell'utente
        book_analysis (Dict): L'analisi del libro di riferimento
        
    Returns:
        str: La struttura del nuovo libro
    """
    return "Struttura dettagliata del libro in stile occidentale..."


def write_western_chapter(chapter_outline: str, style_guide: Dict) -> str:
    """
    Scrive un capitolo in stile occidentale, incorporando elementi culturali italiani e rumeni.
    
    Args:
        chapter_outline (str): La struttura del capitolo
        style_guide (Dict): Guida allo stile basata sull'analisi
        
    Returns:
        str: Il capitolo completo
    """
    return "Contenuto del capitolo in stile occidentale..."


def write_human_style_chapter(chapter_outline: str, style_guide: Dict) -> str:
    """
    Scrive un capitolo in uno stile più umano e naturale, includendo:
    - Variazioni nel ritmo della narrazione
    - Errori di battitura occasionali
    - Espressioni personali
    - Riflessioni spontanee
    - Cambiamenti di umore nella scrittura
    """
    # Simula variazioni nel ritmo della narrazione
    writing_pace = random.choice(['lento', 'medio', 'veloce'])
    
    # Aggiunge occasionalmente errori di battitura
    def add_typos(text: str) -> str:
        if random.random() < 0.05:  # 5% di probabilità di errore
            words = text.split()
            if words:
                idx = random.randint(0, len(words)-1)
                words[idx] = words[idx][:-1] + random.choice('qwertyuiopasdfghjklzxcvbnm')
            return ' '.join(words)
        return text
    
    # Aggiunge espressioni personali
    personal_expressions = [
        "Mi chiedo se...",
        "A volte penso che...",
        "Non so perché, ma...",
        "Mi viene in mente che...",
        "Curiosamente..."
    ]
    
    # Genera il contenuto base del capitolo
    content = write_western_chapter(chapter_outline, style_guide)
    
    # Applica le modifiche per renderlo più umano
    paragraphs = content.split('\n\n')
    humanized_paragraphs = []
    
    for i, para in enumerate(paragraphs):
        # Aggiunge occasionalmente espressioni personali
        if random.random() < 0.1:  # 10% di probabilità
            para = random.choice(personal_expressions) + " " + para
        
        # Aggiunge errori di battitura
        para = add_typos(para)
        
        # Varia il ritmo della narrazione
        if writing_pace == 'lento':
            para = para.replace('.', '...').replace('!', '...!')
        elif writing_pace == 'veloce':
            para = para.replace('.', '!').replace('...', '!')
        
        humanized_paragraphs.append(para)
    
    return '\n\n'.join(humanized_paragraphs)


def analyze_zlib_book(book_content: str) -> Dict:
    """
    Analizza un libro da Z-Library per estrarre lo stile e la struttura.
    
    Args:
        book_content (str): Contenuto del libro da analizzare
        
    Returns:
        Dict: Informazioni sullo stile e la struttura
    """
    return {
        "writing_style": {
            "pacing": "naturale e fluido",
            "tone": "professionale ma accessibile",
            "vocabulary": "ricco ma comprensibile",
            "paragraph_structure": "variabile e dinamica"
        },
        "chapter_structure": {
            "average_length": "20-30 pagine",
            "transitions": "fluide e naturali",
            "scene_breaks": "strategici"
        },
        "narrative_elements": {
            "descriptions": "dettagliate ma non eccessive",
            "dialogue": "naturale e caratteristica",
            "internal_monologue": "profondo e riflessivo"
        }
    }


def conduct_book_interview() -> Dict:
    """
    Conduce un'intervista per definire i dettagli del libro da scrivere.
    
    Returns:
        Dict: Dettagli del libro raccolti dall'intervista
    """
    print("\n=== INTERVISTA PER LA CREAZIONE DEL LIBRO ===\n")
    
    book_details = {}
    
    # Titolo e genere
    print("1. Informazioni di base:")
    book_details["title"] = input("Titolo del libro: ").strip()
    print("\nGeneri disponibili:")
    print("1. Fiction")
    print("2. Fantasy")
    print("3. Romance")
    print("4. Thriller")
    print("5. Storico")
    print("6. Sci-Fi")
    print("7. Horror")
    print("8. Biografia")
    genre_choice = input("\nScegli il genere (1-8): ").strip()
    genre_map = {
        "1": "fiction",
        "2": "fantasy",
        "3": "romance",
        "4": "thriller",
        "5": "historical",
        "6": "sci-fi",
        "7": "horror",
        "8": "biography"
    }
    book_details["genre"] = genre_map.get(genre_choice, "fiction")
    
    # Trama e personaggi
    print("\n2. Trama e personaggi:")
    book_details["plot"] = input("Descrivi la trama principale del libro: ").strip()
    book_details["main_character"] = input("Descrivi il personaggio principale: ").strip()
    book_details["supporting_characters"] = input("Descrivi i personaggi secondari (separati da virgola): ").strip()
    
    # Ambientazione
    print("\n3. Ambientazione:")
    book_details["setting"] = input("Dove e quando è ambientata la storia? ").strip()
    book_details["world_building"] = input("Ci sono elementi particolari dell'ambientazione da includere? ").strip()
    
    # Stile e tono
    print("\n4. Stile e tono:")
    print("Scegli il tono principale della narrazione:")
    print("1. Serio e drammatico")
    print("2. Leggero e umoristico")
    print("3. Misterioso e intrigante")
    print("4. Romantico e sentimentale")
    print("5. Avventuroso e dinamico")
    tone_choice = input("\nScegli il tono (1-5): ").strip()
    tone_map = {
        "1": "serio",
        "2": "leggero",
        "3": "misterioso",
        "4": "romantico",
        "5": "avventuroso"
    }
    book_details["tone"] = tone_map.get(tone_choice, "serio")
    
    # Lunghezza e struttura
    print("\n5. Lunghezza e struttura:")
    book_details["target_pages"] = int(input("Numero di pagine desiderato (default 500): ").strip() or "500")
    print("\nScegli la struttura dei capitoli:")
    print("1. Capitoli brevi e dinamici")
    print("2. Capitoli lunghi e dettagliati")
    print("3. Misto (capitoli di lunghezza variabile)")
    structure_choice = input("\nScegli la struttura (1-3): ").strip()
    structure_map = {
        "1": "breve",
        "2": "lungo",
        "3": "misto"
    }
    book_details["chapter_structure"] = structure_map.get(structure_choice, "misto")
    
    # Elementi speciali
    print("\n6. Elementi speciali:")
    book_details["special_elements"] = input("Ci sono elementi speciali da includere? (es. flashback, narrazione multipla, etc.): ").strip()
    
    # Riferimenti
    print("\n7. Riferimenti:")
    book_details["references"] = input("Ci sono libri o autori che ti ispirano per questo progetto? ").strip()
    
    print("\n=== INTERVISTA COMPLETATA ===\n")
    return book_details


def generate_long_book(book_details: Dict) -> Dict:
    """
    Genera un libro lungo basato sui dettagli raccolti dall'intervista.
    
    Args:
        book_details (Dict): Dettagli del libro raccolti dall'intervista
        
    Returns:
        Dict: Struttura del libro generato
    """
    # Calcola il numero di capitoli in base alla struttura scelta
    avg_chapter_pages = {
        "breve": 15,
        "lungo": 35,
        "misto": 25
    }[book_details["chapter_structure"]]
    
    num_chapters = book_details["target_pages"] // avg_chapter_pages
    
    # Genera la struttura del libro
    book_structure = {
        "title": book_details["title"],
        "genre": book_details["genre"],
        "chapters": []
    }
    
    # Genera i capitoli
    for i in range(num_chapters):
        chapter = {
            "title": f"Capitolo {i+1}",
            "content": "",
            "subchapters": []
        }
        
        # Genera sottocapitoli in base alla struttura
        num_subchapters = {
            "breve": random.randint(2, 3),
            "lungo": random.randint(4, 6),
            "misto": random.randint(3, 5)
        }[book_details["chapter_structure"]]
        
        for j in range(num_subchapters):
            subchapter = {
                "title": f"Sezione {j+1}",
                "content": ""
            }
            chapter["subchapters"].append(subchapter)
        
        book_structure["chapters"].append(chapter)
    
    return book_structure


def write_natural_chapter(chapter_outline: Dict, style_guide: Dict) -> str:
    """
    Scrive un capitolo in stile naturale, ispirato a Z-Library.
    """
    content = []
    
    # Aggiunge un'introduzione al capitolo
    content.append(f"# {chapter_outline['title']}\n\n")
    
    # Genera i sottocapitoli
    for subchapter in chapter_outline["subchapters"]:
        content.append(f"## {subchapter['title']}\n\n")
        
        # Genera il contenuto del sottocapitolo
        paragraphs = []
        num_paragraphs = random.randint(8, 12)  # 8-12 paragrafi per sottocapitolo
        
        for _ in range(num_paragraphs):
            # Varia la lunghezza dei paragrafi
            paragraph_length = random.randint(3, 7)  # 3-7 frasi per paragrafo
            paragraph = []
            
            for _ in range(paragraph_length):
                # Aggiunge variazioni naturali nella scrittura
                if random.random() < 0.1:  # 10% di probabilità
                    paragraph.append(random.choice([
                        "Mi chiedo se...",
                        "A volte penso che...",
                        "Non so perché, ma...",
                        "Curiosamente..."
                    ]))
                
                # Genera una frase
                sentence = write_natural_sentence(style_guide)
                paragraph.append(sentence)
            
            paragraphs.append(" ".join(paragraph))
        
        content.append("\n\n".join(paragraphs))
        content.append("\n\n")
    
    return "\n".join(content)


def write_natural_sentence(style_guide: Dict) -> str:
    """
    Genera una singola frase in stile naturale.
    """
    # Qui il modello genererà una frase naturale
    # Per ora usiamo un placeholder
    return "Questa è una frase generata in stile naturale."


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/generate', methods=['POST'])
def api_generate():
    data = request.json
    book_details = data.get('book_details', {})
    
    # Genera il libro
    book_structure = generate_long_book(book_details)
    
    # Genera i capitoli
    for chapter in book_structure['chapters']:
        chapter_content = write_natural_chapter(chapter, book_analysis)
        chapter['content'] = chapter_content
    
    # Salva il libro
    file_path = save_as_word(book_structure, book_structure['title'])
    
    return jsonify({
        'success': True,
        'file_path': file_path,
        'book_structure': book_structure
    })

@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    data = request.json
    file_path = data.get('file_path')
    
    with open(file_path, 'r', encoding='utf-8') as f:
        book_content = f.read()
    book_analysis = analyze_zlib_book(book_content)
    
    return jsonify({
        'success': True,
        'analysis': book_analysis
    })

def analyze_author_style(author_name: str) -> Dict:
    """
    Analizza lo stile di uno scrittore usando Gemini.
    
    Args:
        author_name (str): Nome dello scrittore da analizzare
        
    Returns:
        Dict: Informazioni sullo stile dello scrittore
    """
    prompt = f"""
    Analizza lo stile di scrittura di {author_name}. Fornisci:
    1. Caratteristiche principali del vocabolario
    2. Struttura tipica delle frasi
    3. Temi ricorrenti
    4. Tecniche narrative utilizzate
    
    Formatta la risposta come JSON con le seguenti chiavi:
    - vocabulary: lista di parole/espressioni caratteristiche
    - sentence_structure: lista di esempi di strutture frasali
    - themes: lista di temi principali
    - techniques: lista di tecniche narrative
    """
    
    try:
        response = model.generate_content(prompt)
        style_info = json.loads(response.text)
        return style_info
    except Exception as e:
        print(f"Errore nell'analisi dello stile: {e}")
        return {
            "vocabulary": [],
            "sentence_structure": [],
            "themes": [],
            "techniques": []
        }

def analyze_book_style(book_title: str) -> Dict:
    """
    Analizza lo stile di un libro usando Gemini.
    
    Args:
        book_title (str): Titolo del libro da analizzare
        
    Returns:
        Dict: Informazioni sullo stile del libro
    """
    prompt = f"""
    Analizza lo stile del libro "{book_title}". Fornisci:
    1. Caratteristiche principali del vocabolario
    2. Struttura tipica delle frasi
    3. Temi ricorrenti
    4. Tecniche narrative utilizzate
    
    Formatta la risposta come JSON con le seguenti chiavi:
    - vocabulary: lista di parole/espressioni caratteristiche
    - sentence_structure: lista di esempi di strutture frasali
    - themes: lista di temi principali
    - techniques: lista di tecniche narrative
    """
    
    try:
        response = model.generate_content(prompt)
        style_info = json.loads(response.text)
        return style_info
    except Exception as e:
        print(f"Errore nell'analisi dello stile: {e}")
        return {
            "vocabulary": [],
            "sentence_structure": [],
            "themes": [],
            "techniques": []
        }

def generate_style_guided_text(prompt: str, style_guide: Dict) -> str:
    """
    Genera testo seguendo una guida di stile specifica.
    
    Args:
        prompt (str): Il prompt per la generazione
        style_guide (Dict): La guida di stile da seguire
        
    Returns:
        str: Testo generato nello stile specificato
    """
    # Adatta il prompt per includere elementi stilistici
    style_prompt = f"""
    Scrivi nel seguente stile:
    - Vocabolario: {', '.join(style_guide['vocabulary'][:5])}
    - Struttura delle frasi: {style_guide['sentence_structure'][0] if style_guide['sentence_structure'] else 'standard'}
    - Temi: {', '.join(style_guide['themes'][:3])}
    - Tecniche: {', '.join(style_guide['techniques'][:3])}
    
    Prompt originale: {prompt}
    """
    
    # Genera il testo usando il modello
    return generate(model, [tokenizer.encode(style_prompt)], max_new_tokens, tokenizer.eos_token_id, temperature)[0]

def write_style_guided_chapter(chapter_outline: Dict, style_guide: Dict) -> str:
    """
    Scrive un capitolo seguendo una guida di stile specifica.
    
    Args:
        chapter_outline (Dict): La struttura del capitolo
        style_guide (Dict): La guida di stile da seguire
        
    Returns:
        str: Capitolo generato nello stile specificato
    """
    content = []
    
    # Aggiunge un'introduzione al capitolo
    content.append(f"# {chapter_outline['title']}\n\n")
    
    # Genera i sottocapitoli
    for subchapter in chapter_outline["subchapters"]:
        content.append(f"## {subchapter['title']}\n\n")
        
        # Genera il contenuto del sottocapitolo nello stile specificato
        subchapter_content = generate_style_guided_text(
            f"Scrivi un sottocapitolo intitolato '{subchapter['title']}'",
            style_guide
        )
        
        content.append(subchapter_content)
        content.append("\n\n")
    
    return "\n".join(content)

@app.route('/api/analyze_style', methods=['POST'])
def api_analyze_style():
    data = request.json
    style_type = data.get('style_type')  # 'author' o 'book'
    name = data.get('name')
    
    if style_type == 'author':
        style_guide = analyze_author_style(name)
    else:
        style_guide = analyze_book_style(name)
    
    return jsonify({
        'success': True,
        'style_guide': style_guide
    })

def main(
    ckpt_path: str,
    config: str,
    input_file: str = "",
    interactive: bool = True,
    max_new_tokens: int = 1048576,
    temperature: float = 1.0,
) -> None:
    """
    Main function to load the model and start the web interface.
    """
    world_size = int(os.getenv("WORLD_SIZE", "1"))
    rank = int(os.getenv("RANK", "0"))
    local_rank = int(os.getenv("LOCAL_RANK", "0"))
    if world_size > 1:
        dist.init_process_group("nccl")
    global print
    if rank != 0:
        print = lambda *_, **__: None
    torch.cuda.set_device(local_rank)
    torch.set_default_dtype(torch.bfloat16)
    torch.set_num_threads(8)
    torch.manual_seed(965)
    with open(config) as f:
        args = ModelArgs(**json.load(f))
    print(args)
    with torch.device("cuda"):
        model = Transformer(args)
    tokenizer = AutoTokenizer.from_pretrained(ckpt_path)
    tokenizer.decode(generate(model, [tokenizer.encode("ScribeNova")], 2, -1, 1.)[0])
    load_model(model, os.path.join(ckpt_path, f"model{rank}-mp{world_size}.safetensors"))

    if interactive:
        # Avvia il server web
        app.run(host='0.0.0.0', port=5000, debug=True)
    else:
        with open(input_file) as f:
            prompts = [line.strip() for line in f.readlines()]
        assert len(prompts) <= args.max_batch_size, f"Number of prompts exceeds maximum batch size ({args.max_batch_size})"
        prompt_tokens = [tokenizer.apply_chat_template([{"role": "user", "content": prompt}], add_generation_prompt=True) for prompt in prompts]
        completion_tokens = generate(model, prompt_tokens, max_new_tokens, tokenizer.eos_token_id, temperature)
        completions = tokenizer.batch_decode(completion_tokens, skip_special_tokens=True)
        for prompt, completion in zip(prompts, completions):
            print("Prompt:", prompt)
            print("Completion:", completion)
            print()

    if world_size > 1:
        dist.destroy_process_group()


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--ckpt-path", type=str, required=True)
    parser.add_argument("--config", type=str, required=True)
    parser.add_argument("--input-file", type=str, default="")
    parser.add_argument("--interactive", action="store_true")
    parser.add_argument("--max-new-tokens", type=int, default=1048576)
    parser.add_argument("--temperature", type=float, default=1.0)
    args = parser.parse_args()
    assert args.input_file or args.interactive, "Either input-file or interactive mode must be specified"
    main(args.ckpt_path, args.config, args.input_file, args.interactive, args.max_new_tokens, args.temperature)
