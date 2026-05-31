# 🎬 CineMatch — AI-Powered Movie Recommender

> Describe a feeling. Discover your next favorite film.

CineMatch is a semantic movie search engine powered by a **Vector Database**. Instead of searching by title or genre, you describe a vibe, emotion, or story — and CineMatch finds the most semantically similar films using AI embeddings.

---

## ✨ Features

- 🔍 **Semantic Search** — Search by feeling, not keywords
- 🎭 **Mood Discovery** — Pick a mood and get instant recommendations  
- 💕 **Watchlist** — Save your favorite films
- 🕐 **Recent Searches** — Quick access to past searches
- 🎯 **Similarity Scores** — See how well each film matches your search
- 🌌 **Space UI** — Cinematic dark theme with smooth animations

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + Tailwind CSS + Framer Motion |
| Backend | FastAPI (Python) |
| Vector Database | ChromaDB |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| Movie Data | TMDB API + TMDB 5000 Dataset |

---

## 🚀 How It Works
User types: "sad movie about friendship and loss"
↓
sentence-transformers converts text → 384-dimensional vector
↓
ChromaDB performs cosine similarity search across 4,500+ films
↓
Top matches returned with similarity scores + explanations

---

## 📁 Project Structure
cinematch/
├── backend/
│   ├── main.py              # FastAPI app & endpoints
│   ├── services/
│   │   ├── movie_service.py # ChromaDB logic + TMDB API
│   │   └── embedder.py      # sentence-transformers
│   ├── models/
│   │   └── schemas.py       # Pydantic data models
│   ├── data/
│   │   └── tmdb_5000_movies.csv
│   └── requirements.txt
└── frontend/
└── src/
├── components/
│   ├── LandingPage.jsx
│   ├── Sidebar.jsx
│   ├── HeroSection.jsx
│   ├── SearchBar.jsx
│   ├── MovieCard.jsx
│   ├── MovieModal.jsx
│   ├── ResultsGrid.jsx
│   ├── DiscoverPage.jsx
│   ├── SavedPage.jsx
│   ├── SkeletonCard.jsx
│   └── StarField.jsx
└── api/
└── movies.js

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.10+
- Node.js 18+
- TMDB API Key (free at [themoviedb.org](https://www.themoviedb.org/signup))

### Backend

```bash
cd backend
pip install -r requirements.txt
```

Create `.env` file:
TMDB_API_KEY=your_api_key_here

Start the server:
```bash
uvicorn main:app --reload
```

Index the movies (first time only):
POST http://localhost:8000/index

### Frontend

```bash
cd frontend
npm install
npm start
```

---

## 🔗 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Server status + indexed movies count |
| POST | `/index` | Index movies into ChromaDB |
| POST | `/search` | Semantic search |

### Search Request
```json
{
  "query": "sad movie about friendship and loss",
  "n_results": 6
}
```

---

## 👤 Author

**Abdallah Ahmed** — Data Analyst & AI Enthusiast

[![Kaggle](https://img.shields.io/badge/Kaggle-abdallahahmed701-blue)](https://www.kaggle.com/abdallahahmed701)
[![GitHub](https://img.shields.io/badge/GitHub-Abdallahahmed156-black)](https://github.com/Abdallahahmed156)

---

