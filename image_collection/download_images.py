import requests
import json
import os
import glob
from urllib.parse import urlparse
from pathlib import Path
import imghdr
import multiprocessing
from functools import partial

SUBJECT = "Physics"
VALID_FORMATS = {'jpeg', 'jpg', 'png'}  # Valid image formats
NUM_CORES = 8  # Number of cores to use for parallel processing


# Change this to correct directory structure
def create_directory_structure():
    """Create the base directory structure for the project."""
    base_dir = Path(SUBJECT)
    dirs = {
        'base': str(base_dir),
        'downloaded_data': str(base_dir / "Downloaded Data"),
        'search_results': str(base_dir / "Search Results")
    }
    
    for dir_path in dirs.values():
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    return dirs

def create_topic_subtopic_dirs(dirs, topic, subtopic):
    """Create and return paths for topic/subtopic specific directories."""
    # Sanitize topic and subtopic names for directory creation
    topic_dir = topic.replace('|', '-').replace('/', '-').replace('\\', '-')
    subtopic_dir = subtopic.replace('|', '-').replace('/', '-').replace('\\', '-')
    
    # Create full paths under Downloaded Data using Path
    topic_path = Path(dirs['downloaded_data']) / topic_dir
    subtopic_path = topic_path / subtopic_dir
    
    # Create directories
    topic_path.mkdir(parents=True, exist_ok=True)
    subtopic_path.mkdir(parents=True, exist_ok=True)
    
    return str(subtopic_path)

def create_image_filename(index):
    """Create a structured, readable image filename with just the index.
    Format: index
    Example: 001
    """
    return f"{index:03d}"

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

def download_single_image(image_data, subtopic_path, search_index, dirs):
    """Download a single image with its metadata."""
    if 'imageUrl' not in image_data:
        return None
    
    base_filename = os.path.join(
        subtopic_path,
        create_image_filename(search_index + 1)  # Use search_index for filename
    )
    success, final_path = download_image(image_data['imageUrl'], base_filename)
    
    if success:
        print(f"      Downloaded image at index {search_index + 1}")
        return {
            'file_path': os.path.relpath(final_path, dirs['downloaded_data']),
            'original_url': image_data['imageUrl'],
            'title': image_data.get('title', ''),
            'source': image_data.get('source', ''),
            'search_index': search_index + 1  # Store original search index
        }
    return None

def process_search_results(args):
    """Process a single search results file and download images."""
    search_results_file, dirs = args
    
    with open(search_results_file, 'r') as f:
        data = json.load(f)
    
    topic = data['topic']
    subtopic = data['subtopic']
    
    subtopic_name = os.path.basename(search_results_file).replace('.json', '')
    print(f"\nProcessing subtopic: {subtopic_name}")
    
    # Create topic/subtopic directories and get the path
    subtopic_path = create_topic_subtopic_dirs(dirs, topic, subtopic)
    
    # Prepare metadata for this download session
    metadata = {
        'subject': SUBJECT,
        'topic': topic,
        'subtopic': subtopic,
        'search_results_file': search_results_file,
        'downloaded_images': []
    }
    
    successful_downloads = []
    total_images = len(data['images'])
    
    print(f"  Found {total_images} total images to try for {subtopic}")
    
    # Try to download all images
    for current_idx, image_data in enumerate(data['images']):
        result = download_single_image(image_data, subtopic_path, current_idx, dirs)
        
        if result:
            successful_downloads.append(result)
            print(f"  Progress: Downloaded {len(successful_downloads)} valid images so far")
    
    metadata['downloaded_images'] = successful_downloads
    
    print(f"  Successfully downloaded {len(successful_downloads)} valid images for {subtopic} "
          f"out of {total_images} total images")
    
    # Save metadata in the same subtopic directory
    metadata_file = os.path.join(subtopic_path, "metadata.json")
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    return len(successful_downloads)

def main():
    # Create directory structure
    dirs = create_directory_structure()
    
    # Get all topic directories in Search Results
    search_results_path = Path(dirs['search_results'])
    topic_dirs = [d for d in search_results_path.iterdir() 
                 if d.is_dir()]
    
    if not topic_dirs:
        print("No topic directories found in Search Results. Please run search.py first.")
        return
    
    # Limit to first 7 topics
    topic_dirs.sort()
    topic_dirs = topic_dirs[:7]
    print([d.name for d in topic_dirs])
    print(f"Processing first {len(topic_dirs)} topics")

    # Process each topic directory
    all_subtopic_tasks = []
    
    # Gather all subtopic tasks across all topics
    for topic_dir in topic_dirs:
        print(f"\nGathering subtopics for topic: {topic_dir.name}")
        
        # Get all search results files for this topic
        search_results_files = list(topic_dir.glob("*.json"))
        
        if not search_results_files:
            print(f"  No search results found in {topic_dir.name}")
            continue
        
        print(f"  Found {len(search_results_files)} subtopics")
        
        # Add tasks for this topic
        for search_file in search_results_files:
            all_subtopic_tasks.append((str(search_file), dirs))
    
    # Process subtopics in parallel across all topics
    print(f"\nProcessing {len(all_subtopic_tasks)} subtopics in parallel with {NUM_CORES} workers")
    
    with multiprocessing.Pool(processes=NUM_CORES) as pool:
        results = pool.map(process_search_results, all_subtopic_tasks)
    
    total_downloaded = sum(results)
    print(f"\nDownload completed! {total_downloaded} images saved in {os.path.join(SUBJECT, 'Downloaded Data')} directory.")

if __name__ == "__main__":
    # Required for Windows multiprocessing
    multiprocessing.freeze_support()
    main() 