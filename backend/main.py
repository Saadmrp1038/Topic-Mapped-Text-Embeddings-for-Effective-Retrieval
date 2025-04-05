import fastapi
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import os
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Any
from retreivers.bge_retreiver import get_multiple_images_metadata_all_structures as get_bge_images
from retreivers.clip_retreiver import get_multiple_images_metadata as get_clip_images
from retreivers.tfidf_retreiver import get_multiple_images_metadata_all_structures as get_tfidf_images
from retreivers.bm25_retreiver import get_multiple_images_metadata_all_structures as get_bm25_images


app = fastapi.FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants
RESULTS_DIR = "evaluation_results"
RESULTS_FILE = os.path.join(RESULTS_DIR, "evaluation_results.json")

# Ensure results directory exists
os.makedirs(RESULTS_DIR, exist_ok=True)

# Pydantic model for evaluation results
class EvaluationResults(BaseModel):
    queries: List[str] = []
    results: Dict[str, Any] = {}

@app.get("/get-images")
async def get_images(query: str, k: int = 1):
    """
    Get images matching the query using multiple retrieval methods.
    
    Args:
        query: The search query
        k: Number of results to return per method (default: 1)
    """
    # Run CPU-intensive retrieval functions in thread pool
    bge_results, clip_results, tfidf_results, bm25_with_stopwords, bm25_without_stopwords = await asyncio.gather(
        asyncio.to_thread(get_bge_images, query, k),
        asyncio.to_thread(get_clip_images, query, k),
        asyncio.to_thread(get_tfidf_images, query, k),
        asyncio.to_thread(get_bm25_images, query, "with_stopwords", k),
        asyncio.to_thread(get_bm25_images, query, "without_stopwords", k)
    )
    
    # Combine all results
    return {
        "query": query,
        "results": {
            "bge": bge_results,
            "clip": clip_results, 
            "tfidf": tfidf_results,
            "bm25_with_stopwords": bm25_with_stopwords,
            "bm25_without_stopwords": bm25_without_stopwords
        }
    }

@app.get("/evaluation-results")
async def get_evaluation_results():
    """
    Get all evaluation results from the JSON file.
    """
    if os.path.exists(RESULTS_FILE):
        try:
            with open(RESULTS_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return EvaluationResults().dict()
    else:
        return EvaluationResults().dict()

@app.post("/evaluation-results")
async def save_evaluation_results(results: EvaluationResults):
    """
    Save evaluation results to the JSON file.
    """
    try:
        with open(RESULTS_FILE, 'w') as f:
            json.dump(results.dict(), f, indent=2)
        return JSONResponse(status_code=200, content={"message": "Results saved successfully"})
    except Exception as e:
        return JSONResponse(
            status_code=500, 
            content={"message": f"Failed to save results: {str(e)}"}
        )
