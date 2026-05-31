import pandas as pd
import chromadb
import logging
import os
import requests
from services.embedder import Embedder
from models.schemas import MovieResult
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
load_dotenv()
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

logger = logging.getLogger(__name__)

class MovieService:
    def __init__(self):
        try:
            self.embedder = Embedder()
            self.client = chromadb.PersistentClient(path="./chroma_db")
            self.collection = self.client.get_or_create_collection(
                name="movies",
                metadata={"hnsw:space": "cosine"}
            )
            self._poster_cache = {}
            logger.info("MovieService initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize MovieService: {e}")
            raise RuntimeError(f"Could not initialize MovieService: {e}")
    def get_poster_url(self, movie_id: str) -> str:
        try:
            url = f"https://api.themoviedb.org/3/movie/{movie_id}"
            params = {"api_key": TMDB_API_KEY}
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            poster_path = data.get("poster_path", "")
            if poster_path:
                return f"https://image.tmdb.org/t/p/w500{poster_path}"
            return None
        except Exception as e:
            logger.warning(f"Could not fetch poster for movie {movie_id}: {e}")
            return None
        
    def get_movie_keywords(self, movie_id: str) -> list[str]:
        try:
            url = f"https://api.themoviedb.org/3/movie/{movie_id}/keywords"
            params = {"api_key": TMDB_API_KEY}
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            keywords = [kw['name'] for kw in data.get('keywords', [])[:5]]
            return keywords
        except Exception as e:
            logger.warning(f"Could not fetch keywords for movie {movie_id}: {e}")
            return []

    def build_reason(self, movie_id: str, genres: str, vote_average: float) -> str:
        try:
            keywords = self.get_movie_keywords(movie_id)
            
            genre_list = []
            try:
                import json
                parsed = json.loads(genres.replace("'", '"'))
                genre_list = [g['name'] for g in parsed[:2]]
            except Exception:
                pass

            parts = []

            if genre_list:
                parts.append(f"{' & '.join(genre_list)} film")

            if keywords:
                parts.append(f"themes of {', '.join(keywords[:3])}")

            if vote_average >= 8.0:
                parts.append("critically acclaimed")
            elif vote_average >= 7.0:
                parts.append("highly rated")

            if parts:
                return "A " + " — ".join(parts)
            return "A great match for your search"

        except Exception as e:
            logger.warning(f"Could not build reason: {e}")
            return "A great match for your search" 
           
    def load_and_index(self, csv_path: str) -> int:
        try:
            df = pd.read_csv(csv_path)
            if df.empty:
                raise ValueError("CSV file is empty")

            df = df.dropna(subset=['overview'])
            df = df.head(5000)

            if len(df) == 0:
                raise ValueError("No valid movies found after filtering")

            texts = []
            ids = []
            metadatas = []

            for _, row in df.iterrows():
                try:
                    genres_text = ''
                    try:
                        import json
                        parsed = json.loads(row.get('genres', '[]').replace("'", '"'))
                        genres_text = ', '.join([g['name'] for g in parsed])
                    except Exception:
                        pass

                    keywords_text = ''
                    try:
                        parsed_kw = json.loads(row.get('keywords', '[]').replace("'", '"'))
                        keywords_text = ', '.join([k['name'] for k in parsed_kw[:10]])
                    except Exception:
                        pass

                    text = f"{row['title']}. {row['overview']}. Genres: {genres_text}. Keywords: {keywords_text}"
                    texts.append(text)
                    ids.append(str(row['id']))
                    metadatas.append({
                        "title": str(row['title']),
                        "overview": str(row['overview']),
                        "genres": str(row.get('genres', '')),
                        "release_date": str(row.get('release_date', '')),
                        "vote_average": float(row.get('vote_average', 0)),
                        "poster_path": str(row.get('poster_path', '')),
                    })
                except Exception as e:
                    logger.warning(f"Skipping row due to error: {e}")
                    continue

            if not texts:
                raise ValueError("No valid movies could be processed")

            logger.info(f"Embedding {len(texts)} movies...")
            embeddings = self.embedder.embed_many(texts)

            self.collection.upsert(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=texts
            )

            logger.info(f"Successfully indexed {len(ids)} movies")
            return len(ids)

        except FileNotFoundError:
            logger.error(f"CSV file not found: {csv_path}")
            raise
        except ValueError as e:
            logger.error(f"Data validation error: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to index movies: {e}")
            raise RuntimeError(f"Indexing failed: {e}")

    def search(self, query: str, n_results: int = 6) -> list[MovieResult]:
        try:
            if not query or not query.strip():
                raise ValueError("Search query cannot be empty")

            if self.collection.count() == 0:
                raise RuntimeError("No movies indexed yet. Please run indexing first")

            query_vector = self.embedder.embed(query)

            results = self.collection.query(
                query_embeddings=[query_vector],
                n_results=n_results
            )

            if not results['ids'][0]:
                logger.warning("No results found for query")
                return []

            ids = results['ids'][0]
            metadatas = results['metadatas'][0]
            distances = results['distances'][0]

            def process_movie(i):
                try:
                    meta = metadatas[i]
                    score = 1 - distances[i]

                    if score < 0.3:
                        return None

                    with ThreadPoolExecutor(max_workers=2) as executor:
                        poster_future = executor.submit(self.get_poster_url, ids[i])
                        reason_future = executor.submit(
                            self.build_reason, ids[i],
                            meta.get('genres', ''),
                            float(meta.get('vote_average', 0))
                        )
                        poster_url = poster_future.result()
                        reason = reason_future.result()

                    return MovieResult(
                        id=ids[i],
                        title=meta['title'],
                        overview=meta['overview'],
                        genres=meta.get('genres', ''),
                        release_date=meta.get('release_date', ''),
                        vote_average=float(meta.get('vote_average', 0)),
                        poster_path=meta.get('poster_path', ''),
                        poster_url=poster_url,
                        similarity_score=round(score, 2),
                        reason=reason,
                    )
                except Exception as e:
                    logger.warning(f"Skipping result due to error: {e}")
                    return None

            with ThreadPoolExecutor(max_workers=6) as executor:
                results_list = list(executor.map(process_movie, range(len(ids))))

            movies = [m for m in results_list if m is not None]
            return movies

        except ValueError as e:
            logger.error(f"Invalid search query: {e}")
            raise
        except RuntimeError as e:
            logger.error(f"Search failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during search: {e}")
            raise RuntimeError(f"Search failed: {e}")

    def get_total_indexed(self) -> int:
        try:
            return self.collection.count()
        except Exception as e:
            logger.error(f"Failed to get collection count: {e}")
            raise RuntimeError(f"Could not get total indexed: {e}")
        
    def get_poster_url(self, movie_id: str) -> str:
        try:
            if movie_id in self._poster_cache:
                return self._poster_cache[movie_id]

            url = f"https://api.themoviedb.org/3/movie/{movie_id}"
            params = {"api_key": TMDB_API_KEY}
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            poster_path = data.get("poster_path", "")
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None

            self._poster_cache[movie_id] = poster_url
            return poster_url
        except Exception as e:
            logger.warning(f"Could not fetch poster for movie {movie_id}: {e}")
            return None    