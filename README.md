# RD Sharma RAG Tutor 📘

A focused math tutor that turns an RD Sharma book into a searchable, step-by-step assistant. Upload a question, ask from the browser, or send an image and the app retrieves book context, reasons over it, and returns an exam-style solution.

> Built for the common case where you want fast explanations from the book, not a generic chatbot answer.

![FastAPI](https://img.shields.io/badge/FastAPI-0F766E?style=for-the-badge&logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![RAG](https://img.shields.io/badge/RAG-111827?style=for-the-badge)
![OCR](https://img.shields.io/badge/OCR-7C3AED?style=for-the-badge)
![Vision](https://img.shields.io/badge/Vision-0EA5E9?style=for-the-badge)

## Preview 👀

This project is built like a focused study companion: a clean chat interface, book-aware retrieval, image input support, and geometry-friendly output that keeps the answers practical and exam-ready.

## Why It Stands Out ✨

- FastAPI backend with a clean browser UI.
- Hybrid retrieval across SQLite metadata, FAISS embeddings, and reranking.
- OCR ingestion for scanned pages and image-based questions.
- Diagram-aware geometry support for visual math problems.
- Session-style chat so the conversation feels continuous, not one-off.

## Quick Start 🚀

```bash
cd backend
pip install -r requirements.txt
```

Put your source PDF in `backend/data/raw/`, then build the index:

```bash
python scripts/01_ingest_pdf.py
python scripts/02_build_index.py
```

Run the app:

```bash
uvicorn app:app --reload
```

Open `http://127.0.0.1:8000` in your browser.

## What It Does 🧠

The app is designed for RD Sharma problem solving with a local-first workflow:

- Reads the source PDF and extracts text where possible.
- Falls back to OCR when a page is scanned or image-heavy.
- Builds a searchable chunk store and FAISS index.
- Retrieves relevant context before generating a final answer.
- Handles image uploads and geometry-style questions with diagram support.

## Project Structure 🗂️

- `backend/app.py` - FastAPI app and chat endpoints.
- `backend/rag/` - retrieval, OCR, embedding, reranking, and answer-generation logic.
- `backend/scripts/01_ingest_pdf.py` - extracts text or OCR from the source PDF.
- `backend/scripts/02_build_index.py` - builds the SQLite chunk store and FAISS index.
- `templates/index.html` - main UI shell.
- `static/app.js` and `static/styles.css` - frontend behavior and styling.

## Requirements ✅

- Python 3.10 or newer.
- An RD Sharma PDF placed in `backend/data/raw/`.
- Optional local services/models depending on your setup:
  - an LLM endpoint such as Ollama
  - a VLM endpoint for image fallback handling

## Configuration ⚙️

The app can be configured with environment variables or `backend/.env.local`.

Common settings:

- `RAW_DIR` - location of the source PDF folder.
- `LOCAL_DATA_DIR` - where OCR, SQLite, and FAISS outputs are stored.
- `LLM_URL` - local LLM endpoint.
- `LLM_MODEL` - model name for the LLM endpoint.
- `VLM_URL` - local vision-model endpoint.
- `REDIS_URL` - session storage backend.
- `APP_HOST` and `APP_PORT` - local host and port values.

## GitHub Upload 🌐

This repo is already set up for GitHub. If you need to reconnect it to a fresh remote, use:

```bash
git branch -M main
git remote add origin https://github.com/aryamshrivastava/rdsharma_RAG.git
git push -u origin main
```

## Notes 📝

- Do not commit the source PDF, OCR output, FAISS index, or local environment files.
- The `.gitignore` already excludes those generated and machine-specific files.