import faiss
import json
import os
from typing import List, Dict, Any
import numpy as np
import clip
import torch
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
CLIP_DIR = "preprocess/clip/image_embedding"
CLIP_INDEX_PATH = os.path.join(CLIP_DIR, "clip_index.faiss")
CLIP_METADATA_PATH = os.path.join(CLIP_DIR, "clip_metadata.json")
MODEL_NAME = "ViT-B/32"

class CLIPRetriever:
    def __init__(self):
        """Initialize CLIP retriever with model, processor, index and metadata."""
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model, self.preprocess = clip.load(MODEL_NAME, device=self.device)
        
        # Load FAISS index
        self.index = faiss.read_index(CLIP_INDEX_PATH)
        
        # Load metadata
        with open(CLIP_METADATA_PATH, 'r') as f:
            self.metadata = json.load(f)
            
    def _get_text_embedding(self, query: str) -> np.ndarray:
        """Get text embedding for the query using CLIP."""
        text = clip.tokenize([query]).to(self.device)
        
        with torch.no_grad():
            text_features = self.model.encode_text(text)
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            text_features = text_features.cpu().numpy()
            
        return text_features.astype('float32')
    
    def get_top_image_metadata(self, query: str, k: int = 1) -> List[Dict[str, Any]]:
        """
        Get the metadata of the top k images for a given query.
        
        Args:
            query (str): The search query
            k (int): Number of results to return
            
        Returns:
            List[Dict[str, Any]]: List of metadata for top k images
        """
        try:
            # Get text embedding
            query_embedding = self._get_text_embedding(query)
            
            # Search in FAISS index
            distances, indices = self.index.search(query_embedding, k)
            
            # Get metadata for the retrieved indices
            results = []
            for idx in indices[0]:
                if idx < len(self.metadata):
                    results.append(self.metadata[idx])
                    
            return results
        except Exception as e:
            logger.error(f"Error retrieving images for query '{query}': {str(e)}")
            return []

def get_top_image_metadata(query: str, k: int = 1) -> List[Dict[str, Any]]:
    """
    Get the metadata of the top k images for a given query.
    
    Args:
        query (str): The search query
        k (int): Number of results to return
        
    Returns:
        List[Dict[str, Any]]: List of metadata for top k images
    """
    retriever = CLIPRetriever()
    return retriever.get_top_image_metadata(query, k)

def get_multiple_images_metadata(query: str, k: int = 5) -> List[Dict[str, Any]]:
    """
    Get the metadata of multiple top images for a given query.
    
    Args:
        query (str): The search query
        k (int): Number of results to return
        
    Returns:
        List[Dict[str, Any]]: List of metadata for top k images
    """
    return get_top_image_metadata(query, k)
