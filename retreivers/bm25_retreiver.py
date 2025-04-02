from langchain_community.retrievers import BM25Retriever
import os
from typing import List, Dict, Any, Literal

# Constants
PICKLE_DIR = "preprocess/bm25/pickle_files"
VARIANT_DIRS = {
    "with_stopwords": "with_stopwords",
    "without_stopwords": "without_stopwords"
}

def load_retriever(structure_num: int, variant: Literal["with_stopwords", "without_stopwords"] = "with_stopwords") -> BM25Retriever:
    """
    Load a BM25 retriever for a specific structure number and variant.
    
    Args:
        structure_num (int): The structure number (1-5)
        variant (str): Either "with_stopwords" or "without_stopwords"
        
    Returns:
        BM25Retriever: The loaded BM25 retriever
    """
    variant_dir = VARIANT_DIRS[variant]
    pickle_path = os.path.join(PICKLE_DIR, variant_dir, f"bm25_structure_{structure_num}.pkl")
    return BM25Retriever.load_local(pickle_path)

def get_top_image_metadata(
    query: str, 
    structure_num: int,
    variant: Literal["with_stopwords", "without_stopwords"] = "with_stopwords"
) -> Dict[str, Any]:
    """
    Get the metadata of the top image for a given query using a specific structure and variant.
    
    Args:
        query (str): The search query
        structure_num (int): The structure number (1-5)
        variant (str): Either "with_stopwords" or "without_stopwords"
        
    Returns:
        Dict[str, Any]: Metadata of the top image
    """
    retriever = load_retriever(structure_num, variant)
    docs = retriever.get_relevant_documents(query, k=1)
    
    if not docs:
        return {}
        
    return docs[0].metadata

def get_top_image_metadata_all_structures(
    query: str,
    variant: Literal["with_stopwords", "without_stopwords"] = "with_stopwords"
) -> Dict[int, Dict[str, Any]]:
    """
    Get the metadata of the top image for a given query using all structures.
    
    Args:
        query (str): The search query
        variant (str): Either "with_stopwords" or "without_stopwords"
        
    Returns:
        Dict[int, Dict[str, Any]]: Dictionary mapping structure numbers to their top image metadata
    """
    results = {}
    for structure_num in range(1, 6):
        results[structure_num] = get_top_image_metadata(query, structure_num, variant)
    return results

def get_multiple_images_metadata(
    query: str, 
    structure_num: int,
    variant: Literal["with_stopwords", "without_stopwords"] = "with_stopwords",
    k: int = 5
) -> List[Dict[str, Any]]:
    """
    Get the metadata of multiple top images for a given query using a specific structure.
    
    Args:
        query (str): The search query
        structure_num (int): The structure number (1-5)
        variant (str): Either "with_stopwords" or "without_stopwords"
        k (int): Number of results to return
        
    Returns:
        List[Dict[str, Any]]: List of metadata for top k images
    """
    retriever = load_retriever(structure_num, variant)
    docs = retriever.get_relevant_documents(query, k=k)
    return [doc.metadata for doc in docs]

def get_multiple_images_metadata_all_structures(
    query: str,
    variant: Literal["with_stopwords", "without_stopwords"] = "with_stopwords",
    k: int = 5
) -> Dict[int, List[Dict[str, Any]]]:
    """
    Get the metadata of multiple top images for a given query using all structures.
    
    Args:
        query (str): The search query
        variant (str): Either "with_stopwords" or "without_stopwords"
        k (int): Number of results to return per structure
        
    Returns:
        Dict[int, List[Dict[str, Any]]]: Dictionary mapping structure numbers to their top k image metadata
    """
    results = {}
    for structure_num in range(1, 6):
        results[structure_num] = get_multiple_images_metadata(query, structure_num, variant, k)
    return results

def get_top_image_metadata_all_variants(query: str, structure_num: int) -> Dict[str, Dict[str, Any]]:
    """
    Get the metadata of the top image for a given query using both variants (with and without stopwords).
    
    Args:
        query (str): The search query
        structure_num (int): The structure number (1-5)
        
    Returns:
        Dict[str, Dict[str, Any]]: Dictionary mapping variants to their top image metadata
    """
    results = {}
    for variant in ["with_stopwords", "without_stopwords"]:
        results[variant] = get_top_image_metadata(query, structure_num, variant)
    return results

def get_multiple_images_metadata_all_variants(
    query: str,
    structure_num: int,
    k: int = 5
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get the metadata of multiple top images for a given query using both variants.
    
    Args:
        query (str): The search query
        structure_num (int): The structure number (1-5)
        k (int): Number of results to return per variant
        
    Returns:
        Dict[str, List[Dict[str, Any]]]: Dictionary mapping variants to their top k image metadata
    """
    results = {}
    for variant in ["with_stopwords", "without_stopwords"]:
        results[variant] = get_multiple_images_metadata(query, structure_num, variant, k)
    return results 