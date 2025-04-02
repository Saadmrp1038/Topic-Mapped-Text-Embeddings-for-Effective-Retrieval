import torch
import clip
import faiss
import requests
import json
import os
from PIL import Image
from io import BytesIO
import numpy as np
from typing import List, Dict, Any
import logging
from tqdm import tqdm

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_clip_model() -> tuple:
    """
    Initialize and load the CLIP model and preprocessor.
    
    Returns:
        tuple: (model, preprocess) - The loaded CLIP model and preprocessor
    """
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, preprocess = clip.load("ViT-B/32", device=device)
    return model, preprocess

def load_metadata(json_file_path: str) -> List[Dict[str, Any]]:
    """
    Load and process metadata from JSON file.
    
    Args:
        json_file_path (str): Path to the JSON metadata file
        
    Returns:
        List[Dict[str, Any]]: Processed metadata list
    """
    with open(json_file_path, "r") as file:
        json_data = json.load(file)
    
    logger.info(f"Length of JSON data: {len(json_data)}")
    
    metadata = []
    for item in json_data:
        metadata.append({
            'topic': item.get('topic'),
            'subtopic': item.get('subtopic'),
            'image_url': item.get('image_url'),
            'caption': item.get('caption'),
            'image_id': item.get('image_id')
        })
    
    return metadata

def encode_image_from_url(image_url: str, model: Any, preprocess: Any, device: str) -> torch.Tensor:
    """
    Encode an image from URL using CLIP model.
    
    Args:
        image_url (str): URL of the image to encode
        model: CLIP model instance
        preprocess: CLIP preprocessor
        device (str): Device to run the model on
        
    Returns:
        torch.Tensor: Normalized image embedding
    """
    try:
        response = requests.get(image_url)
        image = Image.open(BytesIO(response.content))
        image = preprocess(image).unsqueeze(0).to(device)
        
        with torch.no_grad():
            image_embedding = model.encode_image(image)
            
        return image_embedding / image_embedding.norm(dim=-1, keepdim=True)
    except Exception as e:
        logger.error(f"Error encoding image from URL {image_url}: {str(e)}")
        raise

def create_and_save_index(image_embeddings: np.ndarray, metadata: List[Dict[str, Any]], 
                         index_path: str, metadata_path: str) -> None:
    """
    Create FAISS index and save it along with metadata.
    
    Args:
        image_embeddings (np.ndarray): Array of image embeddings
        metadata (List[Dict[str, Any]]): List of metadata dictionaries
        index_path (str): Path to save the FAISS index
        metadata_path (str): Path to save the metadata JSON
    """
    index = faiss.IndexFlatL2(image_embeddings.shape[1])
    index.add(image_embeddings)
    
    faiss.write_index(index, index_path)
    
    with open(metadata_path, "w") as f:
        json.dump(metadata, f)
    
    logger.info("Image embeddings and metadata stored successfully!")

def main():
    """Main function to orchestrate the image embedding process."""
    # Setup
    model, preprocess = setup_clip_model()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    # Load metadata
    metadata = load_metadata("preprocess/dataset/image_metadata.json")
    
    # Encode images with progress bar
    image_embeddings = torch.cat([
        encode_image_from_url(item["image_url"], model, preprocess, device) 
        for item in tqdm(metadata, desc="Encoding images")
    ]).cpu().numpy()
    
    os.makedirs("preprocess/clip", exist_ok=True)

    # Create and save index
    create_and_save_index(
        image_embeddings,
        metadata,
        "preprocess/clip/image_embedding/clip_index.faiss",
        "preprocess/clip/image_embedding/clip_metadata.json"
    )

if __name__ == "__main__":
    main()
