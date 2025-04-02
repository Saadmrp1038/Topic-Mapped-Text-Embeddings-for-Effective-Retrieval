from langchain_community.retrievers import TFIDFRetriever
import os
from typing import List, Dict, Any

# Constants
PICKLE_DIR = "preprocess/tfidf/pickle_files"

def load_retriever(structure_num: int) -> TFIDFRetriever:
    """Load a TF-IDF retriever for a specific structure number."""
    pickle_path = os.path.join(PICKLE_DIR, f"tfidf_structure_{structure_num}.pkl")
    return TFIDFRetriever.load_local(pickle_path)

def get_top_image_metadata(query: str, structure_num: int) -> Dict[str, Any]:
    """
    Get the metadata of the top image for a given query using a specific structure.
    
    Args:
        query (str): The search query
        structure_num (int): The structure number (1-5)
        
    Returns:
        Dict[str, Any]: Metadata of the top image
    """
    retriever = load_retriever(structure_num)
    docs = retriever.get_relevant_documents(query, k=1)
    
    if not docs:
        return {}
        
    return docs[0].metadata

def get_top_image_metadata_all_structures(query: str) -> Dict[int, Dict[str, Any]]:
    """
    Get the metadata of the top image for a given query using all structures.
    
    Args:
        query (str): The search query
        
    Returns:
        Dict[int, Dict[str, Any]]: Dictionary mapping structure numbers to their top image metadata
    """
    results = {}
    for structure_num in range(1, 6):
        results[structure_num] = get_top_image_metadata(query, structure_num)
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
    retriever = load_retriever(structure_num)
    docs = retriever.get_relevant_documents(query, k=k)
    return [doc.metadata for doc in docs]

def get_multiple_images_metadata_all_structures(query: str, k: int = 5) -> Dict[int, List[Dict[str, Any]]]:
    """
    Get the metadata of multiple top images for a given query using all structures.
    
    Args:
        query (str): The search query
        k (int): Number of results to return per structure
        
    Returns:
        Dict[int, List[Dict[str, Any]]]: Dictionary mapping structure numbers to their top k image metadata
    """
    results = {}
    for structure_num in range(1, 6):
        results[structure_num] = get_multiple_images_metadata(query, structure_num, k)
    return results
