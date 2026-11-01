# NewsLens AI: News Summarizer with Fact Check Notes

## Problem Statement

In today's digital age, the volume of news articles and online information is overwhelming, making it difficult to keep up with daily events. More importantly, the rise of misinformation and unverified claims requires readers to constantly fact-check what they read. Manually verifying every claim is time-consuming and often neglected, leading to the spread of fake news.

## Proposed Solution

NewsLens AI is an AI-powered web application that extracts news content, generates a concise summary, identifies key factual claims, and uses an automated Retrieval-Augmented Generation (RAG) pipeline to verify those claims against live web sources. It gives a fact-check verdict and a short note for each claim, with the sources behind it, so users can judge the credibility of what they read.

## Features

- **News Extraction**: Extracts article text from a URL (multiple fallback strategies) or from pasted text.
- **AI Summarization**: Generates a short summary and key points using the Gemini API.
- **Claim Extraction**: Identifies verifiable factual claims and ignores opinions.
- **Automated Evidence Search**: Uses the Tavily API to search the web for evidence for each claim.
- **RAG Pipeline**: Chunks the evidence, embeds it, stores it in a FAISS vector index, and retrieves the most relevant chunks for each claim.
- **Fact-Check Engine**: Judges each claim only against the retrieved evidence and returns one of five verdicts: Supported, Partially Supported, Contradicted, Insufficient Evidence, Unable to Verify.
- **Source Quality**: Shows source domains and a trust level for each.
- **Reliability**: Automatic retries and a fallback model when the AI service is busy.
- **History Tracking**: Stores past analyses in a database for later review.

## Architecture

1. **Frontend**: HTML5, CSS3, vanilla JavaScript (no frameworks)
2. **Backend**: Python, Flask REST API
3. **Database**: SQLite by default (via SQLAlchemy ORM); PostgreSQL is supported by changing `DATABASE_URL`
4. **Generative AI**: Google Gemini API, called through its OpenAI-compatible endpoint, used for summarization, claim extraction and fact-check verdicts
5. **RAG & Search**: Tavily API for web search, LangChain for orchestration and chunking, Gemini embeddings (`gemini-embedding-001`), FAISS for vector storage and similarity search

### Pipeline

```
URL / Text -> Article Extractor
           -> Summarizer (LLM)
           -> Claim Extractor (LLM)
           -> for each claim:
                Tavily web search
                -> chunk + embed (gemini-embedding-001)
                -> FAISS similarity search (top chunks)
                -> Fact Checker (LLM, evidence only)
           -> Save to database -> Frontend
```

## Technologies

- **Frontend**: HTML5, CSS3, JavaScript
- **Backend**: Python 3, Flask, Flask-CORS, SQLAlchemy
- **AI / NLP**: Gemini API (OpenAI-compatible endpoint), LangChain
- **Vector DB**: FAISS (faiss-cpu)
- **Search**: Tavily
- **Article extraction**: newspaper3k, BeautifulSoup4, requests
- **Config**: python-dotenv

---

## Installation

### 1. Clone and set up the environment

```bash
git clone https://github.com/srk333/News-Summarizer-with-Fact-Check-Notes.git
cd News-Summarizer-with-Fact-Check-Notes

# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

### 2. Environment variables

Copy `.env.example` to `.env` and fill in your own keys. **Never commit `.env`.**

```env
OPENAI_API_KEY=your_google_ai_studio_key
OPENAI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
OPENAI_MODEL_NAME=gemini-3.5-flash-lite
FALLBACK_MODEL_NAME=gemini-3.8-flash
EMBEDDING_MODEL_NAME=gemini-embedding-001
TAVILY_API_KEY=your_tavily_key
DATABASE_URL=sqlite:///newslens.db
MAX_CLAIMS=5
```

Notes:

- The variable is named `OPENAI_API_KEY` because Gemini is called through its OpenAI-compatible endpoint. It holds a **Google AI Studio key** (free at aistudio.google.com).
- Gemini model names change often. If you get a "model not found" error, pick a current model from the AI Studio model list.
- For PostgreSQL, use `DATABASE_URL=postgresql://user:password@localhost:5432/newslens`.
- Keep the SQLite file outside cloud-synced folders such as OneDrive, which can lock it ("database is locked").

### 3. Run the application

**Backend** (from the project root):

```bash
python run.py
```

The server starts at `http://localhost:5000`, and the database tables are created on the first run.

**Frontend** (second terminal):

```bash
cd frontend
python -m http.server 8000
```

Open `http://localhost:8000` in your browser.

### 4. Run the tests

```bash
python -m unittest discover -s tests
```

---

## API Documentation

### `POST /api/analyze`

Analyzes a news article.

- **Request body**: `{"url": "https://..."}` or `{"text": "News content..."}`
- **Response**: JSON with summary, key points, claims, evidence, sources and verdicts.

### `GET /api/history`

Returns a list of previously analyzed articles.

### `GET /api/history/<id>`

Returns the details of one past analysis.

---

## How It Works

### How RAG works

Retrieval-Augmented Generation grounds the LLM in real evidence instead of its memory.

1. **Retrieval**: Tavily fetches live web pages related to a claim.
2. **Augmentation**: The pages are split into chunks, converted into embeddings, and stored in a FAISS index. A similarity search finds the chunks closest in meaning to the claim.
3. **Generation**: The LLM reads only those chunks and decides whether the claim is supported.

### How fact checking works

1. The LLM extracts verifiable factual claims from the article (opinions are ignored).
2. Each claim is used as a web search query.
3. The search results go through the RAG pipeline above.
4. The LLM is instructed to judge the claim only against the provided evidence and never use its own knowledge.
5. The result is one of `SUPPORTED`, `PARTIALLY SUPPORTED`, `CONTRADICTED`, `INSUFFICIENT EVIDENCE` or `UNABLE TO VERIFY`, with a short note.

### Why RAG and not fine-tuning

News changes daily, so a fine-tuned model would be out of date quickly, and it can't show its sources. RAG uses fresh evidence at question time and makes every verdict traceable.

---

## Limitations

- **Search scope**: Search results can be incomplete or miss paywalled information.
- **Scraping issues**: Some websites block automated extraction. Use the Paste Text option for these.
- **AI errors**: The model can misinterpret evidence.
- **Evidence quality**: Trust levels are based on domain names, and a reliable domain can still publish errors.
- **No evidence is not "false"**: If no evidence is found, the claim is marked "Insufficient Evidence", not false.
- **Free-tier limits**: The Gemini free tier has rate limits and can be temporarily busy, so analyses may be slow.
- **Not a replacement**: The system assists human judgment and does not replace professional fact-checkers.

## Future Enhancements

- Multilingual news support
- Browser extension for real-time fact-checking
- Image/video misinformation detection
- More advanced citation verification
- User authentication and personalized history
- Fine-tuning a smaller model on labeled claim-evidence-verdict data
