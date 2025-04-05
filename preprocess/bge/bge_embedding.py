import json
import numpy as np
import faiss
import os
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

# Load the BGE embedding model
model = SentenceTransformer('BAAI/bge-small-en-v1.5')

def embed_text(text):
    """Embed text using BGE-small-en-v1.5 model"""
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding

def process_item_structures(item):
    """Process a single item for embedding with five different structures."""
    topic_mapped_image_description = item.get("topic_mapped_image_description", "")
    context_free_description = item.get("context_free_description", "")
    topic_definition = item.get("topic_definition", "")
    subtopic_definition = item.get("subtopic_definition", "")

    print(subtopic_definition)
    # Structure 1: context_free_image_description
    structure1 = context_free_description
    
    # Structure 2: topic_mapped_image_description
    structure2 = topic_mapped_image_description
    
    # Structure 3: topic_definition, subtopic_definition
    structure3 = f"{topic_definition}, {subtopic_definition}"
    
    # Structure 4: topic_definition, subtopic_definition, image_description
    structure4 = f"{topic_definition}, {subtopic_definition}, {context_free_description}"
    
    # Structure 5: topic_definition, subtopic_definition, context_free_image_description
    structure5 = f"{topic_definition}, {subtopic_definition}, {topic_mapped_image_description}"
    
    results = []
    
    # Process each structure
    for idx, text in enumerate([structure1, structure2, structure3, structure4, structure5]):
        if text.strip():
            try:
                embedding = embed_text(text)
                results.append({
                    "structure": idx + 1,
                    "embedding": embedding,
                    "text": text,
                    "metadata": {
                        "image_url": item.get("image_url"),
                        "topic_mapped_image_description": topic_mapped_image_description,
                        "context_free_description": context_free_description,
                        "topic_definition": topic_definition,
                        "subtopic_definition": subtopic_definition
                    },
                    "status": "success"
                })
            except Exception as e:
                print(f"Error embedding text for structure {idx + 1}: {e}")
                results.append({
                    "structure": idx + 1,
                    "text": text,
                    "metadata": {
                        "topic_mapped_image_description": topic_mapped_image_description,
                        "context_free_description": context_free_description,
                        "topic_definition": topic_definition,
                        "subtopic_definition": subtopic_definition
                    },
                    "status": "embedding_error",
                    "error": str(e)
                })
    
    return results

# Directories setup
text_embedding_dir = "preprocess/bge/text_embedding"
os.makedirs(text_embedding_dir, exist_ok=True)

# File paths
index_file_paths = [
    os.path.join(text_embedding_dir, f"text_index_structure_{i}.faiss")
    for i in range(1, 6)
]
metadata_file_paths = [
    os.path.join(text_embedding_dir, f"text_metadata_structure_{i}.json")
    for i in range(1, 6)
]
error_log_path = os.path.join(text_embedding_dir, "embedding_errors.json")

# Load JSON data
json_file_path = "preprocess/dataset/image_metadata.json"
try:
    with open(json_file_path, "r") as file:
        json_data = json.load(file)
    if isinstance(json_data, str):
        json_data = json.loads(json_data)
except Exception as e:
    print(f"Error loading JSON data: {e}")
    exit(1)

print(f"Total items in JSON data: {len(json_data)}")

# Process items for each structure
print("Processing items for each structure...")
all_results = {i: [] for i in range(1, 6)}
error_log = {i: {"no_text_content": [], "embedding_errors": []} for i in range(1, 6)}

for item in tqdm(json_data):
    results = process_item_structures(item)
    for result in results:
        structure_num = result["structure"]
        if result["status"] == "success":
            all_results[structure_num].append(result)
        elif result["status"] == "embedding_error":
            error_log[structure_num]["embedding_errors"].append(result)
        else:
            error_log[structure_num]["no_text_content"].append(result)

# Save error log
with open(error_log_path, "w") as file:
    json.dump(error_log, file, indent=2)

print(f"Error log saved to {error_log_path}")

# Process each structure separately
for structure_num in range(1, 6):
    results = all_results[structure_num]
    print(f"\nProcessing Structure {structure_num}:")
    print(f"Total items: {len(results)}")
    
    if results:
        # Extract embeddings and metadata
        embeddings = np.array([item["embedding"] for item in results], dtype=np.float32)
        metadata = [item["metadata"] for item in results]
        
        # Create FAISS Index
        dimension = embeddings.shape[1]
        length = embeddings.shape[0]
        
        print(f"Length of embeddings: {length}")
        print(f"Dimension of embeddings: {dimension}")
        
        index = faiss.IndexFlatL2(dimension)
        index.add(embeddings)
        
        # Save the index and metadata
        faiss.write_index(index, index_file_paths[structure_num - 1])
        with open(metadata_file_paths[structure_num - 1], "w") as file:
            json.dump(metadata, file)
        
        print(f"FAISS index saved to {index_file_paths[structure_num - 1]}")
        print(f"Metadata saved to {metadata_file_paths[structure_num - 1]}")
    else:
        print(f"No successful embeddings for structure {structure_num}") 