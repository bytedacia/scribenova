# ScribeNova

Sistema di generazione di libri basato su DeepSeek e Google Gemini.

## Caratteristiche principali
- Generazione completa di libri
- Analisi e imitazione dello stile di autori o libri
- Interfaccia web intuitiva
- Sistema di bozze e anteprima in tempo reale
- Generazione di testo naturale senza limiti di lunghezza
- Personalizzazione avanzata (genere, tono, struttura, elementi speciali)

## Requisiti
- Python 3.8+
- PyTorch
- Flask
- Transformers
- python-docx
- requests
- Pillow (PIL)
- google-generativeai
- google-api-python-client
- beautifulsoup4
- python-dotenv

## Installazione
```bash
git clone https://github.com/bytedacia/scribenova.git
cd scribenova
python -m venv venv
source venv/bin/activate  # oppure .\venv\Scripts\activate su Windows
pip install -r requirements.txt
```

Crea un file `.env` nella root del progetto con il tuo Google API Key:
```
GOOGLE_API_KEY=la_tua_chiave_api
```

## Utilizzo
```bash
python inference/generate.py
```
Poi apri il browser su `http://localhost:5000`.

## Funzionalità avanzate
- Analisi online dello stile tramite Google Gemini
- Generazione di libri in stile personalizzato
- Nessun limite di caratteri o pagine
- Gestione bozze e anteprima

## Esempio di utilizzo Python
```python
from inference.generate import generate_long_book
book = generate_long_book({
    'title': 'Il Nome della Rosa',
    'genre': 'storico',
    'plot': 'Un mistero in un monastero medievale...',
    'main_character': 'Guglielmo da Baskerville',
    'tone': 'misterioso',
    'target_pages': 500,
    'chapter_structure': 'Capitoli lunghi e dettagliati',
    'special_elements': 'Indagini, enigmi, colpi di scena',
    'references': 'Umberto Eco'
})
```

## Contribuire
Pull request e suggerimenti sono benvenuti!

## Licenza
MIT

## Contatti
- [GitHub](https://github.com/bytedacia/scribenova)

## Ringraziamenti
- DeepSeek
- Google Gemini
