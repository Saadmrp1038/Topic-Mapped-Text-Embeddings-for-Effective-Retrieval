"""
BM25 Tokenizer for processing text data with different structure variants.
This module handles text tokenization with and without stopwords for BM25 retrieval.
"""

import json
import os
import pickle
from typing import Dict, List, Optional, Set

import nltk
import pandas as pd
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from tqdm import tqdm

# Download required NLTK data
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('punkt_tab')

# Constants
STOP_WORDS: Set[str] = set(stopwords.words('english'))
JSON_FILE_PATH = "preprocess/dataset/image_metadata.json"
BM25_WITH_STOPWORDS_DIR = "preprocess/bm25/pickle_files/with_stopwords"
BM25_WITHOUT_STOPWORDS_DIR = "preprocess/bm25/pickle_files/without_stopwords"

os.makedirs(BM25_WITH_STOPWORDS_DIR, exist_ok=True)
os.makedirs(BM25_WITHOUT_STOPWORDS_DIR, exist_ok=True)

class BM25Tokenizer:
    """Handles text tokenization for BM25 retrieval with different structure variants."""
    
    def __init__(self, json_data: List[Dict]):
        """
        Initialize the BM25Tokenizer.
        
        Args:
            json_data: List of dictionaries containing the input data
        """
        self.json_data = json_data
        os.makedirs(BM25_WITH_STOPWORDS_DIR, exist_ok=True)
    
    @staticmethod
    def word_tokenize_with_stopwords(text: str) -> List[str]:
        """
        Tokenize text while keeping stopwords.
        
        Args:
            text: Input text to tokenize
            
        Returns:
            List of tokenized words
        """
        return [word.lower() for word in word_tokenize(text) if word.isalnum()]
    
    @staticmethod
    def word_tokenize_without_stopwords(text: str) -> List[str]:
        """
        Tokenize text while removing stopwords.
        
        Args:
            text: Input text to tokenize
            
        Returns:
            List of tokenized words without stopwords
        """
        return [word.lower() for word in word_tokenize(text) 
                if word.lower() not in STOP_WORDS and word.isalnum()]
    
    @staticmethod
    def get_text_for_structure(item: Dict, structure_num: int) -> str:
        """
        Get text based on the structure variant.
        
        Args:
            item: Dictionary containing text fields
            structure_num: Structure variant number (1-5)
            
        Returns:
            Combined text based on the structure
        """
        topic_mapped_image_description = item.get("topic_mapped_image_description", "")
        context_free_description = item.get("context_free_description", "")
        topic_definition = item.get("topic_definition", "")
        subtopic_definition = item.get("subtopic_definition", "")
        
        if not all([topic_mapped_image_description, context_free_description, 
                   topic_definition, subtopic_definition]):
            return ""
            
        structures = {
            1: context_free_description,
            2: topic_mapped_image_description,
            3: f"{topic_definition}, {subtopic_definition}",
            4: f"{topic_definition}, {subtopic_definition}, {context_free_description}",
            5: f"{topic_definition}, {subtopic_definition}, {topic_mapped_image_description}"
        }
        
        return structures.get(structure_num, "")
    
    def _get_metadata(self, item: Dict) -> Dict:
        """Extract metadata from an item."""
        return {
            'topic': item.get('topic'),
            'subtopic': item.get('subtopic'),
            'image_url': item.get('image_url'),
            'caption': item.get('caption'),
            'topic_mapped_image_description': item.get('topic_mapped_image_description', ''),
            'context_free_description': item.get('context_free_description', ''),
            'topic_definition': item.get('topic_definition', ''),
            'subtopic_definition': item.get('subtopic_definition', ''),
        }
    
    def process_structure(self, structure_num: int, with_stopwords: bool = True) -> List[Dict]:
        """
        Process data for a specific structure variant.
        
        Args:
            structure_num: Structure variant number (1-5)
            with_stopwords: Whether to keep stopwords
            
        Returns:
            List of processed documents
        """
        tokenizer = (self.word_tokenize_with_stopwords if with_stopwords 
                    else self.word_tokenize_without_stopwords)
        stopword_status = "with" if with_stopwords else "without"
        
        print(f"\nProcessing BM25 {stopword_status} stopwords for Structure {structure_num}:")
        
        tokenized_data = []
        for item in tqdm(self.json_data):
            text = self.get_text_for_structure(item, structure_num)
            if text.strip():
                tokenized_content = tokenizer(text)
                tokenized_data.append({
                    "page_content": tokenized_content,
                    "metadata": self._get_metadata(item),
                })
        
        print(f"Length of tokenized data for BM25 {stopword_status} stopwords, "
              f"structure {structure_num}: {len(tokenized_data)}")
        
        if tokenized_data:
            if with_stopwords:
                pickle_path = os.path.join(BM25_WITH_STOPWORDS_DIR, 
                                        f"{stopword_status}_stopwords_structure_{structure_num}.pkl")
            else:
                pickle_path = os.path.join(BM25_WITHOUT_STOPWORDS_DIR, 
                                        f"{stopword_status}_stopwords_structure_{structure_num}.pkl")
            with open(pickle_path, "wb") as f:
                pickle.dump(tokenized_data, f)
            print(f"BM25 {stopword_status} stopwords data for structure {structure_num} "
                  f"saved to {pickle_path}")
            
            # Save default structure (1) for backward compatibility
            if structure_num == 1:
                if with_stopwords:
                    default_path = os.path.join(BM25_WITH_STOPWORDS_DIR, f"{stopword_status}_stopwords.pkl")
                else:
                    default_path = os.path.join(BM25_WITHOUT_STOPWORDS_DIR, f"{stopword_status}_stopwords.pkl")
                with open(default_path, "wb") as f:
                    pickle.dump(tokenized_data, f)
                print(f"Default BM25 {stopword_status} stopwords (structure 1) saved")
        else:
            print(f"No data to save for BM25 {stopword_status} stopwords, structure {structure_num}")
        
        return tokenized_data

def main():
    """Main function to process all structure variants."""
    # Load JSON data
    with open(JSON_FILE_PATH, "r") as file:
        json_data = json.load(file)
    print(f"Length of JSON data: {len(json_data)}")
    
    # Initialize tokenizer
    tokenizer = BM25Tokenizer(json_data)
    
    # Process each structure variant
    for structure_num in range(1, 6):
        tokenizer.process_structure(structure_num, with_stopwords=True)
        tokenizer.process_structure(structure_num, with_stopwords=False)

if __name__ == "__main__":
    main()