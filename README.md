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

### Requisiti hardware (per esecuzione locale)

GPU supportate

- NVIDIA RTX 50 Series
  - RTX 5090 (Prestazioni ottimali)
  - RTX 5080
  - RTX 5070
- NVIDIA RTX 40 Series
  - RTX 4090
  - RTX 4080 Super
  - RTX 4080
  - RTX 4070 Ti Super
  - RTX 4070 Ti
  - RTX 4070 Super
  - RTX 4070
- NVIDIA RTX 30 Series
  - RTX 3090 Ti
  - RTX 3090
  - RTX 3080 Ti
  - RTX 3080
  - RTX 3070 Ti
  - RTX 3070
- AMD e Apple Silicon
  - AMD RX 7900 XTX
  - AMD RX 7900 XT
  - Apple M3 Max / M3 Pro
  - Apple M2 Ultra

GPU con supporto limitato

- RTX 4060 Ti (supportata ma con prestazioni ridotte)
- RTX 3060 Ti (supportata ma con prestazioni ridotte)

GPU non supportate

- NVIDIA serie x50/x60: RTX 5060, RTX 5050, RTX 4060, RTX 4050, RTX 3060, RTX 3050
- Serie RTX 20 e precedenti (RTX 2080 Ti e inferiori)
- Tutte le GPU GTX e GPU integrate Intel

CPU consigliate

- Intel 12th Gen e successive (consigliata)
  - i9-13900K/KF, i9-12900K/KF, i7-13700K/KF, i7-12700K/KF
- Intel 11th Gen (minimo)
  - i9-11900K, i7-11700K
- AMD Ryzen 7000 (consigliata)
  - 7950X, 7900X, 7800X3D, 7700X
- AMD Ryzen 5000 (minimo)
  - 5950X, 5900X, 5800X3D, 5800X
- Apple Silicon
  - Serie M3 (consigliata): M3 Max/Pro/M3
  - Serie M2 (supportata): M2 Ultra/Max/Pro/M2

Memoria

- DDR5: minimo DDR5-5200, consigliato DDR5-6000+

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

### Sicurezza (consigliato)
- `API_SECRET`: abilita autenticazione via header `X-API-KEY`
- `CORS_ORIGINS`: lista di origin consentiti, separati da virgola
- `MAX_CONTENT_LENGTH_MB`: limite dimensione richiesta (default 10)
- `RATE_LIMIT` e `RATE_WINDOW_SEC`: rate limiting per IP (default 30 richieste/10 min)
- `ALLOW_TRUST_REMOTE_CODE`: per sicurezza è disattivato; abilitalo solo se necessario

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
