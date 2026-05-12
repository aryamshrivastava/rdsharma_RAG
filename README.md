# RD Sharma RAG Tutor

RD Sharma RAG Tutor is a local FastAPI application that answers math questions with retrieval-augmented context from an RD Sharma PDF, optional OCR/Vision fallbacks, and step-by-step solutions in the browser.

## Features

- FastAPI backend with a browser UI.
- Hybrid retrieval using SQLite metadata, FAISS embeddings, and reranking.
- OCR ingestion for scanned pages.
- Image-based question handling and diagram-aware geometry support.
- Session-style chat in the frontend.

## Project Layout

- `backend/app.py` - FastAPI app and chat endpoints.
- `backend/rag/` - retrieval, OCR, embedding, reranking, and answer-generation logic.
- `backend/scripts/01_ingest_pdf.py` - extracts text or OCR from the source PDF.
- `backend/scripts/02_build_index.py` - builds the SQLite chunk store and FAISS index.
- `templates/index.html` - main UI shell.
- `static/app.js` and `static/styles.css` - frontend behavior and styling.

## Requirements

- Python 3.10 or newer.
- A local RD Sharma PDF for ingestion.
- Optional but recommended local services/models used by the app, depending on your setup:
  - an LLM endpoint such as Ollama
  - a VLM endpoint for image fallback handling

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
cd backend
pip install -r requirements.txt
```

3. Put your source PDF in `backend/data/raw/`.

## Ingest and Build the Index

Run the ingestion script first to extract text or OCR pages:

```bash
cd backend
python scripts/01_ingest_pdf.py
```

Then build the chunk database and FAISS index:

```bash
cd backend
python scripts/02_build_index.py
```

By default, generated OCR, database, and FAISS files are written outside the repository under your local app data directory. That keeps the GitHub repo clean and small.

## Run the App

Start the API from the `backend` directory:

```bash
cd backend
uvicorn app:app --reload
```

Then open the browser at `http://127.0.0.1:8000`.

## Configuration

The app can be configured with environment variables or `backend/.env.local`.

Common settings:

- `RAW_DIR` - location of the source PDF folder.
- `LOCAL_DATA_DIR` - where OCR, SQLite, and FAISS outputs are stored.
- `LLM_URL` - local LLM endpoint.
- `LLM_MODEL` - model name for the LLM endpoint.
- `VLM_URL` - local vision-model endpoint.
- `REDIS_URL` - session storage backend.
- `APP_HOST` and `APP_PORT` - local host and port values.

## GitHub Upload

This repository is ready to commit after you initialize Git locally. If you want to push it to your GitHub account, create a repository under your profile and add it as the remote, for example:

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/aryamshrivastava/<repo-name>.git
git push -u origin main
```

Replace `<repo-name>` with the GitHub repository you create.

## Notes

- Do not commit the source PDF, OCR output, FAISS index, or local environment files.
- The `.gitignore` in this repo already excludes those generated and machine-specific files.