import faiss
import json
import os
from typing import List, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
BGE_DIR = "preprocess/bge/text_embedding"
MODEL_NAME = "BAAI/bge-small-en-v1.5"

# Global variables for model and indices
_model = None
_indices = {}
_metadata = {}

def _load_model():
    """Load the BGE model if not already loaded."""
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model

def _load_indices_and_metadata():
    """Load FAISS indices and metadata for each structure if not already loaded."""
    global _indices, _metadata
    
    if not _indices:
        for structure_num in range(1, 6):
            index_path = os.path.join(BGE_DIR, f"text_index_structure_{structure_num}.faiss")
            metadata_path = os.path.join(BGE_DIR, f"text_metadata_structure_{structure_num}.json")
            
            if os.path.exists(index_path) and os.path.exists(metadata_path):
                _indices[structure_num] = faiss.read_index(index_path)
                with open(metadata_path, 'r') as f:
                    _metadata[structure_num] = json.load(f)
            else:
                logger.warning(f"Missing index or metadata for structure {structure_num}")

def _get_text_embedding(query: str) -> np.ndarray:
    """Get text embedding for the query using BGE."""
    model = _load_model()
    embedding = model.encode(query, normalize_embeddings=True)
    return embedding.astype('float32')

def get_top_image_metadata(query: str, structure_num: int, k: int = 1) -> List[Dict[str, Any]]:
    """
    Get the metadata of the top k images for a given query using a specific structure.
    
    Args:
        query (str): The search query
        structure_num (int): The structure number (1-5)
        k (int): Number of results to return
        
    Returns:
        List[Dict[str, Any]]: List of metadata for top k images
    """
    try:
        _load_indices_and_metadata()
        
        if structure_num not in _indices or structure_num not in _metadata:
            logger.error(f"Structure {structure_num} not available")
            return []
            
        # Get text embedding
        query_embedding = _get_text_embedding(query)
        
        # Search in FAISS index
        distances, indices = _indices[structure_num].search(
            query_embedding.reshape(1, -1), k
        )
        
        # Get metadata for the retrieved indices
        results = []
        for idx in indices[0]:
            if idx < len(_metadata[structure_num]):
                results.append(_metadata[structure_num][idx])
                
        return results
    except Exception as e:
        logger.error(f"Error retrieving images for query '{query}' with structure {structure_num}: {str(e)}")
        return []

def get_top_image_metadata_all_structures(query: str, k: int = 1) -> Dict[int, List[Dict[str, Any]]]:
    """
    Get the metadata of the top k images for a given query using all structures.
    
    Args:
        query (str): The search query
        k (int): Number of results to return per structure
        
    Returns:
        Dict[int, List[Dict[str, Any]]]: Dictionary mapping structure numbers to their top k image metadata
    """
    results = {}
    for structure_num in range(1, 6):
        results[structure_num] = get_top_image_metadata(query, structure_num, k)
    return results

def get_multiple_images_metadata(query: str, structure_num: int, k: int = 5) -> List[Dict[str, Any]]:
    """
    Get the metadata of multiple top images for a given query using a specific structure.
    
    Args:
        query (str): The search query
        structure_num (int): The structure number (1-5)
        k (int): Number of results to return
        
    Returns:
        List[Dict[str, Any]]: List of metadata for top k images
    """
    return get_top_image_metadata(query, structure_num, k)

def get_multiple_images_metadata_all_structures(query: str, k: int = 5) -> Dict[int, List[Dict[str, Any]]]:
    """
    Get the metadata of multiple top images for a given query using all structures.
    
    Args:
        query (str): The search query
        k (int): Number of results to return per structure
        
    Returns:
        Dict[int, List[Dict[str, Any]]]: Dictionary mapping structure numbers to their top k image metadata
    """
    return get_top_image_metadata_all_structures(query, k) 