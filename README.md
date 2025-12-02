# AI-Driven News Research & Idea Generator  
Backend: FastAPI + Python  
Frontend: HTML + JavaScript  
Database: Supabase PostgreSQL  
LLM: Gemini API  

---

## 🚀 Features
- Expand user keywords using Gemini
- Scrape real news articles (RSS + HTML fallback)
- Store scraped articles in Supabase
- Generate fresh news article ideas using LLM
- Clean frontend UI to test backend
- Fully async, optimized, production-ready

---

## 🧩 Tech Stack
- Python 3.9+
- FastAPI
- Uvicorn
- Supabase (PostgreSQL)
- Gemini API
- httpx, BeautifulSoup4, feedparser
- Frontend: HTML + CSS + JS (no framework)

---

## 📁 Project Structure

```
ai-news-generator/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── api/v1/endpoints.py
│   └── services/
│       ├── scraper.py
│       ├── idea_generator.py
│       ├── llm_client.py
│       └── supabase_client.py
├── frontend/
│   ├── index.html
│   ├── script.js
│   └── style.css
├── .env
├── .env.example
├── requirements.txt
└── README.md
```

---

## 🔧 Setup

### 1. Clone the repo
```sh
git clone https://github.com/yourname/ai-news-generator.git
cd ai-news-generator
```

### 2. Create virtual environment
```sh
python -m venv venv
venv\Scripts\activate   # Windows
```

### 3. Install dependencies
```sh
pip install -r requirements.txt
```

### 4. Add environment variables  
Copy `.env.example` → `.env`

```
SUPABASE_URL=your-url
SUPABASE_KEY=your-key
GEMINI_API_KEY=your-gemini-key
```

---

## ▶️ Run Backend

```sh
uvicorn app.main:app --reload
```

Backend runs on:
```
http://127.0.0.1:8000
```

Swagger docs:
```
http://127.0.0.1:8000/docs
```

---

## ▶️ Run Frontend

Go to the `frontend` folder:

```sh
cd frontend
python -m http.server 5500
```

Open browser:
```
http://127.0.0.1:5500
```

---

## 🧪 API Endpoints

| Endpoint | Description |
|---------|-------------|
| POST `/api/v1/expand` | Expand keywords using Gemini |
| POST `/api/v1/scrape` | Scrape articles only |
| POST `/api/v1/scrape-and-generate` | Full pipeline: expand → scrape → save → ideas |
| GET `/api/v1/articles` | Fetch stored articles |
| GET `/api/v1/ideas` | Generate ideas from stored data |

---

## 🗂 SQL Schema

```
id SERIAL PRIMARY KEY
url TEXT UNIQUE
title TEXT
summary TEXT
snippet TEXT
raw_html TEXT
created_at TIMESTAMP DEFAULT NOW()
```

---

## 🎯 Notes
- RSS + HTML fallback scraper used for stable results.
- RLS disabled on table (required for REST insert).
- Duplicate URLs auto-skip to avoid noise.
- Summaries + HTML trimmed for speed optimization.

---

## 📜 License
MIT
