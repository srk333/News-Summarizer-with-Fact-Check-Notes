# News Summarizer with Fact Check Notes

## Problem Statement
In today's digital age, the volume of news articles and online information is overwhelming, making it difficult to keep up with daily events. More importantly, the rise of misinformation and unverified claims requires readers to constantly fact-check what they read. Manually verifying every claim is time-consuming and often neglected, leading to the spread of fake news.

## Proposed Solution
NewsLens AI is an AI-powered application that automatically extracts news content, generates a concise summary, identifies key factual claims, and uses an automated Retrieval-Augmented Generation (RAG) pipeline to verify those claims against reliable external sources on the web. It provides a fact-check verdict and a brief note for each claim, helping users evaluate the credibility of the news they read.

## Features
- **News Extraction**: Automatically extracts text from news article URLs or pasted text.
- **AI Summarization**: Generates short summaries and key points using OpenAI.
- **Claim Extraction**: Identifies factual claims that require verification, ignoring opinions.
- **Automated Evidence Search**: Uses Tavily API to search the web for external evidence.
- **RAG Pipeline**: Retrieves and processes web evidence into vectors (Chroma) and provides context to the LLM.
- **Fact-Check Engine**: Evaluates claims against evidence and outputs one of five verdicts (Supported, Partially Supported, Contradicted, Insufficient Evidence, Unable to Verify).
- **Quality Assessment**: Highlights source domains and trust levels.
- **History Tracking**: Stores past analyses in a PostgreSQL database for future review.

## Architecture
1. **Frontend**: HTML5, CSS3, JavaScript (Vanilla, no frameworks)
2. **Backend**: Python, Flask REST API
3. **Database**: PostgreSQL (via SQLAlchemy ORM)
4. **Generative AI**: OpenAI (gpt-4o-mini) for summarization and logic
5. **RAG & Search**: Tavily API for search, LangChain for chunking, OpenAI Embeddings, Chroma for vector storage.

## Technologies
- **Frontend**: HTML5, CSS3, JavaScript, Chart.js (optional)
- **Backend**: Flask, SQLAlchemy
- **AI/NLP**: LangChain, OpenAI
- **Vector DB**: FAISS
- **Search**: Tavily

---

## Installation

### 1. Clone & Setup Environment
```bash
# Create project folder
mkdir news-summarizer-fact-check
cd news-summarizer-fact-check

# Create virtual environment (Windows)
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Setup (PostgreSQL)
Ensure you have PostgreSQL installed.
1. Create a database named `newslens` in pgAdmin or via psql:
   ```sql
   CREATE DATABASE newslens;
   ```
2. Update the `DATABASE_URL` in your `.env` file to match your credentials. If no `DATABASE_URL` is provided, the application will fallback to a local SQLite database (`newslens.db`) for testing purposes.

### 3. Environment Variables
Copy `.env.example` to `.env` and fill in your keys:
```env
OPENAI_API_KEY=your_actual_openai_key
TAVILY_API_KEY=your_actual_tavily_key
DATABASE_URL=postgresql://postgres:password@localhost:5432/newslens
OPENAI_MODEL_NAME=gpt-4o-mini
```

### 4. Running the Application

**Run the Backend Server:**
```bash
python backend/app.py
```
The server will start on `http://localhost:5000`. The database tables will be created automatically on the first run.

**Run the Frontend:**
Since the frontend uses basic HTML/JS, you can simply open `frontend/index.html` in your web browser. 
Alternatively, use a simple HTTP server:
```bash
cd frontend
python -m http.server 8000
```
Then visit `http://localhost:8000` in your browser.

### 5. Running Tests
To run the automated unit tests:
```bash
python -m unittest discover -s tests
```

---

## API Documentation

### `POST /api/analyze`
Analyzes a news article.
- **Request Body**: `{"url": "https://..."}` OR `{"text": "News content..."}`
- **Response**: Complete analysis JSON including summary, claims, evidence, and verdicts.

### `GET /api/history`
Returns a list of previously analyzed articles.

### `GET /api/history/<id>`
Returns details of a specific past analysis.

---

## How it Works

### How RAG Works
Retrieval-Augmented Generation (RAG) grounds the LLM's responses in factual data. 
1. **Retrieval**: We fetch live articles via Tavily.
2. **Augmentation**: We split the long documents into smaller text chunks, convert them to vectors (Embeddings), and store them in ChromaDB. We then perform a similarity search to find the top 4 chunks most relevant to the extracted claim.
3. **Generation**: The LLM reads only these retrieved chunks and decides if the claim is supported.

### How Fact Checking Works
1. The article is parsed by OpenAI to extract `FACTUAL CLAIMS` (excluding opinions).
2. Each claim generates a web search query.
3. Relevant search results are fetched and processed via RAG.
4. The LLM is prompted strictly to evaluate the claim *only* against the provided evidence chunks.
5. The result is classified into statuses like `SUPPORTED` or `CONTRADICTED`.

---

## Limitations
- **Search Scope**: Search results can be incomplete or miss paywalled information.
- **Scraping Issues**: Some websites block automated extraction.
- **AI Hallucination**: AI can occasionally misinterpret evidence.
- **Evidence Quality**: The system assigns trust based on domain names, but a reliable domain can still publish errors.
- **Lack of Evidence != False**: If no evidence is found, the claim is marked "Insufficient Evidence", not false.
- **Not a Replacement**: The system is an assistant, not a replacement for human fact-checking.

## Future Enhancements
- Multilingual news support
- Browser extension for real-time fact-checking
- Image/video misinformation detection
- More advanced citation verification
- User authentication and personalized history
