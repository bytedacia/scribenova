# ScribeNova

Sistema unificato per generare, rifinire e pubblicare libri in locale.

## Panoramica
- Generazione principale con DeepSeek‑V3 (capitoli lunghi, nessun limite pratico di caratteri)
- Umanizzazione/correzione con Qwen3
- Titolo e sinossi con Llama 3 (poi umanizzati da Qwen3)
- SEO con Gemma (keywords, meta, categorie)
- Copertina con FLUX (diffusers)
- Export Word e Wattpad
- Ricerca editori (Google CSE) ed email di proposta con allegati

## Modelli utilizzati
- DeepSeek‑V3 (generatore principale) — [deepseek-ai/DeepSeek-V3](https://github.com/deepseek-ai/DeepSeek-V3.git)
- Qwen3 — [QwenLM/Qwen3](https://github.com/QwenLM/Qwen3.git)
- Llama 3 — [meta-llama/llama3](https://github.com/meta-llama/llama3.git)
- Gemma — [google-deepmind/gemma](https://github.com/google-deepmind/gemma.git)
- FLUX — [black-forest-labs/flux](https://github.com/black-forest-labs/flux.git)

Tutti i pesi sono scaricati da Hugging Face al primo avvio o via script.

## Requisiti
- Python 3.9+
- GPU NVIDIA consigliata (CUDA) per performance e qualità
- Dipendenze principali: `torch`, `transformers`, `diffusers`, `accelerate`, `huggingface_hub`, `flask`, `python-docx`, `beautifulsoup4`, `requests`, `python-dotenv`

## Installazione
```bash
git clone https://github.com/bytedacia/scribenova.git
cd scribenova
python -m venv venv
./venv/Scripts/activate  # Windows
# source venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
```

Facoltativo: token Hugging Face se richiesto dai repo (modelli soggetti ad accesso):
```bash
setx HF_TOKEN "hf_xxx"  # Windows
# export HF_TOKEN=hf_xxx   # Linux/macOS
```

Scarico modelli (opzionale, altrimenti auto-download al primo avvio):
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\download_models.ps1
```

## Variabili ambiente utili
- Autore/Email: `AUTHOR_NAME`, `AUTHOR_EMAIL`
- SMTP: `SMTP_HOST`, `SMTP_PORT` (587), `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM`
- Google CSE: `GOOGLE_CSE_API_KEY`, `GOOGLE_CSE_CX`
- Modelli (override opzionali):
  - `DEEPSEEK_LOCAL_PATH`, `DEEPSEEK_REPO_ID`, `DEEPSEEK_REVISION`, `DEEPSEEK_MAX_NEW_TOKENS` (default 4096)
  - `QWEN_LOCAL_MODEL_PATH`, `QWEN_REPO_ID`, `QWEN_REVISION`
  - `LLAMA_LOCAL_MODEL_PATH`, `LLAMA_REPO_ID`, `LLAMA_REVISION`
  - `GEMMA_LOCAL_MODEL_PATH`, `GEMMA_REPO_ID`, `GEMMA_REVISION`
  - `FLUX_MODEL_ID`, `FLUX_LOCAL_MODEL_PATH`, `FLUX_REPO_ID`, `FLUX_REVISION`
- Hugging Face token: `HF_TOKEN` o `HUGGINGFACE_HUB_TOKEN`

## Avvio rapido (orchestratore unico)
```python
from inference.orchestrator import UnifiedScribe

us = UnifiedScribe()  # scarica i modelli se mancanti
result = us.run({
    "title": "",
    "genre": "fiction",
    "chapter_structure": "misto",
    "target_pages": 500
})
print(result["book_structure"]["title"], result["word_path"], result["cover_path"]) 
```

## Interfaccia web (Flask)
```bash
python inference/generate.py
# apri http://localhost:5000
```

## Note
- DeepSeek‑V3 è il modello principale per la generazione dei capitoli. Gli altri modelli sono perfezionatori.
- Su CPU funziona, ma è consigliata una GPU per tempi ragionevoli.
- Evita di fare commit dei pesi: la cartella `models/` è ignorata nel repo.

## Licenza
MIT (codice). L’uso dei modelli segue le rispettive licenze.

## Ringraziamenti
- DeepSeek‑V3 — generazione long‑form
- Qwen3 — umanizzazione/proof
- Llama 3 — titolo e sinossi
- Gemma — SEO
- FLUX — copertina
