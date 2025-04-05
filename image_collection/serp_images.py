import requests
import json
import os
from dotenv import load_dotenv
import time
from urllib.parse import urlparse
from pathlib import Path
import imghdr
from datetime import datetime

load_dotenv()

SERPER_API_KEY = os.getenv('SERPER_API_KEY')
SEARCH_URL = "https://google.serper.dev/images"
DOWNLOAD_IMAGES = True  # Flag to control image downloading
REQUIRED_IMAGES = 10  # Number of images we want per subtopic
VALID_FORMATS = {'jpeg', 'jpg', 'png'}  # Valid image formats
SUBJECT = "Physics"  # Current subject being processed

def create_directory_structure():
    """Create the base directory structure for the project."""
    base_dir = SUBJECT
    dirs = {
        'raw_data': os.path.join(base_dir, "Raw Data"),
        'images': os.path.join(base_dir, "Images"),
        'metadata': os.path.join(base_dir, "Metadata")
    }
    
    for dir_path in dirs.values():
        os.makedirs(dir_path, exist_ok=True)
    
    return dirs

def create_image_filename(chapter, subtopic, index):
    """Create a structured, readable image filename that's easily parseable.
    Format: chapter|subtopic|index
    Example: Vector|Scalar and Vector Quantities|001
    """
    # Replace any '|' in chapter or subtopic with '-' to maintain parsing integrity
    chapter_name = chapter.replace('|', '-').replace('/', '-').replace('\\', '-')
    subtopic_name = subtopic.replace('|', '-').replace('/', '-').replace('\\', '-')
    return f"{chapter_name}|{subtopic_name}|{index:03d}"

def parse_image_filename(filename):
    """Parse an image filename to extract chapter, subtopic and index.
    Example: 'Vector|Scalar and Vector Quantities|001.jpg' ->
    ('Vector', 'Scalar and Vector Quantities', 1)
    """
    # Remove extension and split by delimiter
    base_name = os.path.splitext(filename)[0]
    parts = base_name.split('|')
    if len(parts) == 3:
        chapter, subtopic, index = parts
        return chapter, subtopic, int(index)
    return None

def is_valid_image(file_path):
    """Check if the downloaded file is a valid jpg or png image."""
    try:
        image_type = imghdr.what(file_path)
        return image_type in VALID_FORMATS
    except Exception:
        return False

def download_image(url, save_path):
    """Download an image from URL and save it to the specified path."""
    temp_path = None  # Initialize temp_path to None
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Get file extension from URL or default to .jpg
        parsed_url = urlparse(url)
        extension = os.path.splitext(parsed_url.path)[1].lower()
        if not extension or extension[1:] not in VALID_FORMATS:
            extension = '.jpg'
        
        temp_path = f"{save_path}_temp{extension}"
        final_path = f"{save_path}{extension}"
        
        # Save to temporary file first
        with open(temp_path, 'wb') as f:
            f.write(response.content)
        
        # Verify if it's a valid image
        if is_valid_image(temp_path):
            os.rename(temp_path, final_path)
            return True, final_path
        else:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return False, None
            
    except Exception as e:
        print(f"Error downloading image {url}: {str(e)}")
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        return False, None

def search_educational_images(topic, subtopic, num_images=20):
    """Search for educational illustrations for a given subtopic."""
    query = f"educational illustration diagram {subtopic} {topic} physics learning"
    
    payload = json.dumps({
        "q": query,
        "num": num_images  # Request more images than needed to account for failures
    })
    
    headers = {
        'X-API-KEY': SERPER_API_KEY,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.request("POST", SEARCH_URL, headers=headers, data=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error searching for {subtopic}: {str(e)}")
        return None

def save_results(chapter, subtopic, results, dirs):
    """Save search results to a JSON file and optionally download images."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save raw search results
    raw_data_file = os.path.join(
        dirs['raw_data'], 
        f"{chapter} - {subtopic} - Raw Data ({timestamp}).json"
    )
    with open(raw_data_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Prepare metadata for this search
    metadata = {
        'subject': SUBJECT,
        'chapter': chapter,
        'subtopic': subtopic,
        'timestamp': timestamp,
        'search_query': f"educational illustration diagram {subtopic} {chapter} physics learning",
        'downloaded_images': []
    }
    
    # Download images if flag is set
    if DOWNLOAD_IMAGES and 'images' in results:
        successful_downloads = 0
        idx = 0
        
        while successful_downloads < REQUIRED_IMAGES and idx < len(results['images']):
            if 'imageUrl' in results['images'][idx]:
                base_filename = os.path.join(
                    dirs['images'],
                    create_image_filename(chapter, subtopic, successful_downloads + 1)
                )
                success, final_path = download_image(results['images'][idx]['imageUrl'], base_filename)
                
                if success:
                    print(f"      Downloaded image {successful_downloads + 1}/{REQUIRED_IMAGES}")
                    # Add image metadata
                    metadata['downloaded_images'].append({
                        'file_path': os.path.relpath(final_path, dirs['images']),
                        'original_url': results['images'][idx]['imageUrl'],
                        'title': results['images'][idx].get('title', ''),
                        'source': results['images'][idx].get('source', ''),
                        'chapter': chapter,
                        'subtopic': subtopic,
                        'index': successful_downloads + 1
                    })
                    successful_downloads += 1
                    
                time.sleep(0.5)  # Small delay between downloads
            idx += 1
            
        if successful_downloads < REQUIRED_IMAGES:
            print(f"      Warning: Only able to download {successful_downloads} valid images for {subtopic}")
    
    # Save metadata
    metadata_file = os.path.join(
        dirs['metadata'],
        f"{chapter} - {subtopic} - Metadata ({timestamp}).json"
    )
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    return successful_downloads

def main():
    # Create directory structure
    dirs = create_directory_structure()
    
    # Read topics from JSON file
    with open('Topics_1.json', 'r') as f:
        topics = json.load(f)
    
    # Process each topic and subtopic
    for topic in topics:
        chapter = topic['chapter']
        print(f"\nProcessing chapter: {chapter}")
        
        for subtopic in topic['subtopics']:
            print(f"  Searching for: {subtopic}")
            results = search_educational_images(chapter, subtopic)
            
            if results:
                num_downloaded = save_results(chapter, subtopic, results, dirs)
                print(f"    Saved results for {subtopic} ({num_downloaded} images)")
                
                # If we didn't get enough images, try another search with remaining count
                if num_downloaded < REQUIRED_IMAGES:
                    remaining = REQUIRED_IMAGES - num_downloaded
                    print(f"    Searching for {remaining} more images...")
                    additional_results = search_educational_images(chapter, subtopic, num_images=remaining * 2)
                    if additional_results:
                        save_results(chapter, subtopic, additional_results, dirs)
            
    
    print("\nSearch completed! Results saved in the Physics directory.")

if __name__ == "__main__":
    main()
