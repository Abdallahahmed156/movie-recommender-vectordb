from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
from models.schemas import SearchRequest, SearchResponse
from services.movie_service import MovieService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="CineMatch API",
    description="AI-Powered Movie Recommender using Vector Database",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    service = MovieService()
    logger.info("MovieService initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize MovieService: {e}")
    raise

@app.get("/health")
def health_check():
    try:
        total = service.get_total_indexed()
        return {
            "status": "ok",
            "movies_indexed": total
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/index")
def index_movies():
    try:
        total = service.load_and_index("./data/tmdb_5000_movies.csv")
        return {
            "message": "Indexing completed successfully",
            "indexed": total
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset file not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Indexing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search", response_model=SearchResponse)
def search_movies(request: SearchRequest):
    try:
        results = service.search(
            query=request.query,
            n_results=request.n_results
        )
        return SearchResponse(
            results=results,
            query=request.query,
            total=len(results)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))