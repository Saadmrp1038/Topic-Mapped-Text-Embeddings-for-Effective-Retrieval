import pickle
from rank_bm25 import BM25Okapi
import os
from typing import List, Dict, Any, Literal

# Constants
PICKLE_DIR = "preprocess/bm25/pickle_files"
VARIANT_DIRS = {
    "with_stopwords": "with_stopwords",
    "without_stopwords": "without_stopwords"
}

def load_retriever(structure_num: int, variant: Literal["with_stopwords", "without_stopwords"] = "with_stopwords") -> BM25Okapi:
    """
    Load a BM25 retriever for a specific structure number and variant.
    
    Args:
        structure_num (int): The structure number (1-5)
        variant (str): Either "with_stopwords" or "without_stopwords"
        
    Returns:
        BM25Okapi: The loaded BM25 retriever
    """
    variant_dir = VARIANT_DIRS[variant]
    pickle_path = os.path.join(PICKLE_DIR, variant_dir, f"{variant}_structure_{structure_num}.pkl")
    
    # Check if structure-specific file exists
    if not os.path.exists(pickle_path):
        # If the file is not found, try the variant-only file as a fallback
        fallback_path = os.path.join(PICKLE_DIR, variant_dir, f"{variant}.pkl")
        if not os.path.exists(fallback_path):
            raise FileNotFoundError(f"BM25 pickle files not found: {pickle_path} or {fallback_path}")
        pickle_path = fallback_path
    
    # Load the file
    with open(pickle_path, 'rb') as f:
        data = pickle.load(f)
    
    # Check the structure of the loaded data
    if isinstance(data, BM25Okapi):
        # If data is already a BM25Okapi instance, return it directly
        return data
    elif isinstance(data, dict) and 'corpus' in data:
        # If data is a dictionary with a corpus field, create a BM25Okapi instance
        corpus = data['corpus']
        # Check if pre-tokenized
        if all(isinstance(doc, list) for doc in corpus):
            # Already tokenized corpus
            tokenized_corpus = corpus
        else:
            # Tokenize the corpus only if items are strings
            tokenized_corpus = []
            for doc in corpus:
                if isinstance(doc, str):
                    tokenized_corpus.append(doc.lower().split())
                elif isinstance(doc, list):
                    # Already tokenized or list format
                    tokenized_corpus.append(doc)
                else:
                    raise ValueError(f"Unsupported document type in corpus: {type(doc)}")
        
        # Create BM25Okapi model with optimized parameters
        bm25 = BM25Okapi(tokenized_corpus, k1=1.5, b=0.75)
        
        # Add metadata to the model if it exists in the loaded data
        if 'metadata' in data:
            bm25.metadata = data['metadata']
        
        return bm25
    elif isinstance(data, list) and len(data) > 0:
        # If data is a list of documents, extract content and create BM25Okapi
        if isinstance(data[0], dict) and 'page_content' in data[0]:
            # List of documents with page_content
            corpus = [doc['page_content'] for doc in data]
            
            # Check if page_content is already tokenized
            tokenized_corpus = []
            for content in corpus:
                if isinstance(content, str):
                    tokenized_corpus.append(content.lower().split())
                elif isinstance(content, list):
                    # Already tokenized
                    tokenized_corpus.append(content)
                else:
                    raise ValueError(f"Unsupported page_content type: {type(content)}")
            
            # Create BM25Okapi model
            bm25 = BM25Okapi(tokenized_corpus, k1=1.5, b=0.75)
            
            # Store metadata from the documents
            bm25.metadata = [doc.get('metadata', {}) for doc in data]
            
            return bm25
        else:
            # List of text, create BM25Okapi directly
            tokenized_corpus = []
            for doc in data:
                if isinstance(doc, str):
                    tokenized_corpus.append(doc.lower().split())
                elif isinstance(doc, list):
                    tokenized_corpus.append(doc)
                else:
                    raise ValueError(f"Unsupported document type: {type(doc)}")
            
            return BM25Okapi(tokenized_corpus, k1=1.5, b=0.75)
    else:
        raise ValueError(f"Unsupported data format in pickle file: {type(data)}")

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
    bm25_model = load_retriever(structure_num, variant)
    tokenized_query = query.lower().split()
    
    # Check if the BM25 model has metadata attribute
    if not hasattr(bm25_model, 'metadata'):
        print(f"Warning: BM25 model doesn't have metadata attribute for structure {structure_num}, variant {variant}")
        return {}
    
    # Get document scores
    doc_scores = bm25_model.get_scores(tokenized_query)
    if len(doc_scores) == 0:
        print(f"No matching documents found for query: {query}")
        return {}
    
    # Get top index and corresponding metadata
    top_idx = doc_scores.argmax()
    
    # Safely access metadata
    if top_idx < len(bm25_model.metadata):
        return bm25_model.metadata[top_idx]
    else:
        print(f"Warning: Top index {top_idx} is out of bounds for metadata length {len(bm25_model.metadata)}")
        return {}

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
    bm25_model = load_retriever(structure_num, variant)
    tokenized_query = query.lower().split()
    
    if hasattr(bm25_model, 'metadata'):
        doc_scores = bm25_model.get_scores(tokenized_query)
        
        # Get the top k indices
        top_indices = doc_scores.argsort()[-k:][::-1]
        
        # Return metadata for the top k documents
        return [bm25_model.metadata[idx] for idx in top_indices if idx < len(bm25_model.metadata)]
    else:
        print("Warning: BM25 model doesn't have metadata attribute. Check your pickle structure.")
        return []

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

# if __name__ == "__main__":
#     print(get_top_image_metadata_all_variants("H bond", 1))