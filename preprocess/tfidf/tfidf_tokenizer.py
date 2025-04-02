from langchain_community.retrievers import TFIDFRetriever
from langchain_core.documents import Document
import os
from dotenv import load_dotenv
from tqdm import tqdm
import json

# Constants
JSON_FILE_PATH = "preprocess/dataset/image_metadata.json"
PICKLE_DIR = "preprocess/tfidf/pickle_files"

def load_json_data(file_path):
    """Load and return JSON data from the specified file."""
    with open(file_path, "r") as file:
        return json.load(file)

def create_document(item, text, structure_num):
    """Create a Document object with the given text and metadata."""
    return Document(
        page_content=text,
        metadata={
            'topic': item.get('topic'),
            'subtopic': item.get('subtopic'),
            'image_url': item.get('image_url'),
            'caption': item.get('caption'),
            'topic_mapped_image_description': item.get('topic_mapped_image_description', ''),
            'context_free_description': item.get('context_free_description', ''),
            'topic_definition': item.get('topic_definition', ''),
            'subtopic_definition': item.get('subtopic_definition', ''),
            'structure': structure_num
        }
    )

def get_text_structure(item, structure_num):
    """Get text based on the specified structure number."""
    topic_mapped_image_description = item.get("topic_mapped_image_description", "")
    context_free_description = item.get("context_free_description", "")
    topic_definition = item.get("topic_definition", "")
    subtopic_definition = item.get("subtopic_definition", "")
    
    if not all([topic_mapped_image_description, context_free_description, 
                topic_definition, subtopic_definition]):
        return None
        
    structures = {
        1: context_free_description,
        2: topic_mapped_image_description,
        3: f"{topic_definition}, {subtopic_definition}",
        4: f"{topic_definition}, {subtopic_definition}, {context_free_description}",
        5: f"{topic_definition}, {subtopic_definition}, {topic_mapped_image_description}"
    }
    
    return structures.get(structure_num, "").strip()

def process_structure(json_data, structure_num):
    """Process documents for a specific structure number."""
    data = []
    for item in tqdm(json_data, desc=f"Processing Structure {structure_num}"):
        text = get_text_structure(item, structure_num)
        if text:
            doc = create_document(item, text, structure_num)
            data.append(doc)
    return data

def save_tfidf_retriever(retriever, structure_num):
    """Save TF-IDF retriever to disk."""
    # Save structure-specific retriever
    tfidf_path = os.path.join(PICKLE_DIR, f"tfidf_structure_{structure_num}.pkl")
    retriever.save_local(tfidf_path)
    print(f"TF-IDF retriever saved to {tfidf_path}")
    
    # If this is structure 1, also save as default
    if structure_num == 1:
        default_path = os.path.join(PICKLE_DIR, "tfidf.pkl")
        retriever.save_local(default_path)
        print(f"Default TF-IDF retriever (structure 1) saved to {default_path}")
    
    return tfidf_path

def main():
    # Load environment variables
    load_dotenv()
    
    # Create directory for storing pickle files
    os.makedirs(PICKLE_DIR, exist_ok=True)
    
    # Load JSON data
    json_data = load_json_data(JSON_FILE_PATH)
    print(f"Length of JSON data: {len(json_data)}")
    
    # Process each structure variant
    for structure_num in range(1, 6):
        print(f"\nProcessing Structure {structure_num}:")
        data = process_structure(json_data, structure_num)
        print(f"Total documents for structure {structure_num}: {len(data)}")
        
        if data:
            tfidf_retriever = TFIDFRetriever.from_documents(data)
            save_tfidf_retriever(tfidf_retriever, structure_num)
        else:
            print(f"No documents to process for structure {structure_num}")

if __name__ == "__main__":
    main()