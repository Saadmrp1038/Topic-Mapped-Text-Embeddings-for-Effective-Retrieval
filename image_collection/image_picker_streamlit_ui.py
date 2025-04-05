import streamlit as st
import os
import json
import glob
from PIL import Image
import io
import base64
import shutil

# Constants
SUBJECT = "Physics"

# Change this to the path of the downloaded data
DATA_DIR = os.path.join("", SUBJECT, "Downloaded Data")

# Change this to the path of the selected images
SELECTIONS_FILE = os.path.join("", "selected_images.json")

# Set page configuration
st.set_page_config(
    page_title=f"{SUBJECT} Image Selector",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS for better styling
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .image-container {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 10px;
        margin: 5px;
        transition: all 0.3s;
        height: 100%;
        display: flex;
        flex-direction: column;
    }
    .image-container:hover {
        box-shadow: 0 0 10px rgba(0,0,0,0.2);
        transform: translateY(-2px);
    }
    .selected {
        border: 3px solid #4CAF50 !important;
        box-shadow: 0 0 10px rgba(76, 175, 80, 0.5) !important;
    }
    .selected-label {
        background-color: #4CAF50;
        color: white;
        text-align: center;
        padding: 5px;
        border-radius: 5px;
        margin-top: 5px;
        font-weight: 500;
    }
    .progress-container {
        margin-top: 20px;
        padding: 15px;
        background-color: #f8f9fa;
        border-radius: 8px;
    }
    .header {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .stButton > button {
        width: 100%;
        border-radius: 5px;
        font-weight: 500;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .topic-card {
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        transition: all 0.3s;
        background-color: white;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .topic-card:hover {
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        transform: translateY(-2px);
    }
    .nav-button {
        background-color: #f0f2f6;
        padding: 5px 15px;
        border-radius: 5px;
        font-weight: 500;
        margin: 5px;
        text-align: center;
    }
    .nav-button:hover {
        background-color: #e0e2e6;
    }
    .sidebar-header {
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    .image-caption {
        margin-top: 5px;
        font-size: 0.9em;
        text-align: center;
        color: #555;
        overflow: hidden;
        text-overflow: ellipsis;
        max-height: 40px;
    }
    /* Make the sidebar look better */
    [data-testid="stSidebar"] {
        background-color: #f9fafb;
        border-right: 1px solid #eaecef;
    }
    /* Make the buttons more modern */
    .stButton > button {
        background-color: #f0f2f6;
        border: none;
        color: #444;
    }
    .stButton > button:active {
        background-color: #e0e2e6;
    }
    /* Special buttons */
    .primary-button > button {
        background-color: #4CAF50;
        color: white;
    }
    .primary-button > button:hover {
        background-color: #45a049;
    }
</style>
""", unsafe_allow_html=True)

def load_selected_images():
    """Load previously selected images from JSON file."""
    if os.path.exists(SELECTIONS_FILE):
        with open(SELECTIONS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_selected_images(selections):
    """Save selected images to JSON file."""
    with open(SELECTIONS_FILE, 'w') as f:
        json.dump(selections, f, indent=2)

def load_topics():
    """Load all topics from the downloaded data directory."""
    if not os.path.exists(DATA_DIR):
        st.error(f"Data directory {DATA_DIR} not found. Please download images first.")
        st.stop()
        
    topics = [d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))]
    return sorted(topics)

def load_subtopics(topic):
    """Load all subtopics for a given topic."""
    topic_dir = os.path.join(DATA_DIR, topic)
    subtopics = [d for d in os.listdir(topic_dir) if os.path.isdir(os.path.join(topic_dir, d))]
    return sorted(subtopics)

def load_images(topic, subtopic):
    """Load all images for a given subtopic."""
    subtopic_dir = os.path.join(DATA_DIR, topic, subtopic)
    image_files = []
    
    # Get all image files
    for ext in ['jpg', 'jpeg', 'png']:
        image_files.extend(glob.glob(os.path.join(subtopic_dir, f"*.{ext}")))
    
    # Try to load metadata
    metadata_file = os.path.join(subtopic_dir, "metadata.json")
    metadata = {}
    if os.path.exists(metadata_file):
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
    
    return sorted(image_files), metadata

def get_image_caption(image_path, metadata):
    """Get caption for an image based on metadata if available."""
    filename = os.path.basename(image_path)
    base_name = os.path.splitext(filename)[0]
    
    # Try to find image metadata
    if 'downloaded_images' in metadata:
        for img_data in metadata['downloaded_images']:
            if img_data['file_path'].endswith(filename):
                return img_data.get('title', '')
    
    return base_name

def display_image_selection(topic, subtopic, selected_images):
    """Display images for selection and handle user choice."""
    subtopic_key = f"{topic}/{subtopic}"
    image_files, metadata = load_images(topic, subtopic)
    
    if not image_files:
        st.warning(f"No images found for {subtopic} in {topic}")
        return

    st.subheader(f"Select an image for: {subtopic}")
    
    # Check if there's already a selection for this subtopic
    current_selection = selected_images.get(subtopic_key, None)
    
    # Create columns for images
    cols = st.columns(min(4, len(image_files)))  # Reduced to 4 for better sizing
    
    # Display images
    for i, img_path in enumerate(image_files):
        col_idx = i % len(cols)
        with cols[col_idx]:
            try:
                img = Image.open(img_path)
                caption = get_image_caption(img_path, metadata)
                
                # Check if this is the currently selected image
                is_selected = os.path.basename(img_path) == os.path.basename(current_selection) if current_selection else False
                
                # Add CSS class based on selection status
                container_class = "image-container selected" if is_selected else "image-container"
                
                # Display the image with a button to select it
                st.markdown(f'<div class="{container_class}">', unsafe_allow_html=True)
                
                # Display the image
                st.image(img, use_container_width=True)
                st.markdown(f'<div class="image-caption">{caption}</div>', unsafe_allow_html=True)
                
                # Show select button only if not already selected
                if not is_selected:
                    with st.container():
                        st.markdown('<div class="primary-button">', unsafe_allow_html=True)
                        if st.button("Select", key=f"btn_{topic}_{subtopic}_{i}"):
                            selected_images[subtopic_key] = img_path
                            save_selected_images(selected_images)
                            
                            # Auto-navigate based on preference
                            advance_to_next_subtopic_or_image(topic, subtopic)
                        st.markdown('</div>', unsafe_allow_html=True)
                else:
                    # Show selected status
                    st.markdown('<div class="selected-label">✓ Selected</div>', unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error loading image {img_path}: {str(e)}")

def advance_to_next_subtopic_or_image(topic, subtopic):
    """Helper function to advance to the next subtopic or image based on auto-advance setting"""
    # Check if we need to auto-advance to next subtopic
    if st.session_state.get('auto_advance', True):  # Default to True if not set
        subtopics = load_subtopics(topic)
        current_idx = subtopics.index(subtopic)
        if current_idx < len(subtopics) - 1:
            st.session_state.selected_subtopic = subtopics[current_idx + 1]
            st.rerun()
    else:
        st.rerun()

def navigate_subtopics(topic, selected_images):
    """Navigate through subtopics for a topic."""
    subtopics = load_subtopics(topic)
    
    # Create a sidebar for navigation
    st.sidebar.markdown('<div class="sidebar-header">', unsafe_allow_html=True)
    st.sidebar.header("Subtopics")
    st.sidebar.markdown('</div>', unsafe_allow_html=True)
    
    # Initialize auto-advance option with default to True
    if 'auto_advance' not in st.session_state:
        st.session_state.auto_advance = True
    
    # Add auto-advance option with default to true - don't update session state directly after
    st.sidebar.checkbox("Auto-advance to next subtopic", 
                         key="auto_advance",
                         value=True,  # Default to true for better UX
                         help="Automatically move to the next subtopic after selecting an image")
    
    # Track completion
    completed_subtopics = [st for st in subtopics if f"{topic}/{st}" in selected_images]
    incomplete_subtopics = [st for st in subtopics if f"{topic}/{st}" not in selected_images]
    completion_percentage = int(len(completed_subtopics) / len(subtopics) * 100) if subtopics else 0
    
    # Progress bar
    st.sidebar.progress(completion_percentage/100)
    st.sidebar.markdown(f"**Progress:** {len(completed_subtopics)}/{len(subtopics)} subtopics ({completion_percentage}%)")
    
    # Initialize selected_subtopic if not in session state
    if 'selected_subtopic' not in st.session_state or st.session_state.selected_subtopic not in subtopics:
        st.session_state.selected_subtopic = subtopics[0] if subtopics else None
        
    # Get selected subtopic
    current_subtopic = st.session_state.selected_subtopic
    selected_index = subtopics.index(current_subtopic) if current_subtopic in subtopics else 0
    
    # Create a selection widget for subtopics
    subtopic_statuses = [f"✅ {st}" if f"{topic}/{st}" in selected_images else f"⬜ {st}" for st in subtopics]
    new_selected_index = st.sidebar.selectbox("Jump to subtopic:", 
                                         range(len(subtopic_statuses)),
                                         index=selected_index,
                                         format_func=lambda i: subtopic_statuses[i])
    
    # If user changes the dropdown selection, update the selected subtopic
    if new_selected_index != selected_index:
        st.session_state.selected_subtopic = subtopics[new_selected_index]
        st.rerun()
    
    # Show current subtopic and navigation buttons
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if selected_index > 0:
            prev_subtopic = subtopics[selected_index - 1]
            if st.button("⬅️ Previous", key="prev_btn"):
                st.session_state.selected_subtopic = prev_subtopic
                st.rerun()
    
    with col2:
        st.markdown(f"<h3 style='text-align: center;'>{current_subtopic}</h3>", unsafe_allow_html=True)
    
    with col3:
        if selected_index < len(subtopics) - 1:
            next_subtopic = subtopics[selected_index + 1]
            if st.button("Next ➡️", key="next_btn"):
                st.session_state.selected_subtopic = next_subtopic
                st.rerun()
    
    # Display selected subtopic's images
    display_image_selection(topic, current_subtopic, selected_images)
    
    # Navigation buttons in sidebar
    if incomplete_subtopics:
        st.sidebar.markdown("---")
        
        # "Jump to First Incomplete" button
        with st.sidebar.container():
            st.markdown('<div class="primary-button">', unsafe_allow_html=True)
            if st.button("Jump to First Incomplete", key="first_incomplete_btn"):
                # Find the first incomplete subtopic
                first_incomplete = incomplete_subtopics[0]
                st.session_state.selected_subtopic = first_incomplete
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        
        # "Jump to Next New" button - Find first incomplete after the last completed one
        with st.sidebar.container():
            st.markdown('<div class="primary-button" style="margin-top: 10px;">', unsafe_allow_html=True)
            
            # Find the next new incomplete subtopic
            if completed_subtopics:
                # Get the index of the last completed subtopic
                completed_indices = [subtopics.index(st) for st in completed_subtopics]
                last_completed_idx = max(completed_indices)
                
                # Find the first incomplete subtopic after the last completed one
                next_new_subtopics = [st for st in incomplete_subtopics if subtopics.index(st) > last_completed_idx]
                
                if next_new_subtopics:
                    next_new = next_new_subtopics[0]
                    btn_label = f"Jump to Next New ({next_new})"
                    btn_disabled = False
                else:
                    btn_label = "No New Subtopics Ahead"
                    btn_disabled = True
                    next_new = None
            else:
                # If no subtopics completed yet, use the first incomplete
                next_new = incomplete_subtopics[0] if incomplete_subtopics else None
                btn_label = f"Jump to First Subtopic ({next_new})"
                btn_disabled = False
            
            if st.button(btn_label, key="next_new_btn", disabled=btn_disabled) and next_new:
                st.session_state.selected_subtopic = next_new
                st.rerun()
                
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Add guidance text
    if incomplete_subtopics:
        st.sidebar.markdown("""
        <div style="margin-top: 10px; font-size: 0.85em; color: #777;">
        <b>Navigation Help:</b>
        <ul style="padding-left: 15px;">
            <li><b>First Incomplete</b>: Goes to the first subtopic you haven't completed yet</li>
            <li><b>Next New</b>: Skips to the first incomplete subtopic that comes <i>after</i> your last completed one</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)

def main():
    # Header
    st.markdown("<div class='header'>", unsafe_allow_html=True)
    st.title(f"{SUBJECT} Image Selector")
    st.markdown("Select one image for each subtopic")
    st.markdown("</div>", unsafe_allow_html=True)
    
    try:
        # Load previously selected images
        selected_images = load_selected_images()
        
        # Initialize session state
        if 'selected_topic' not in st.session_state:
            st.session_state.selected_topic = None
        
        # Get all topics
        topics = load_topics()
        
        if not topics:
            st.error("No topics found. Please make sure you've downloaded images first.")
            return
        
        # Main content based on navigation state
        if st.session_state.selected_topic is None:
            # Show topic selection
            st.header("Select a Topic")
            
            # Create a grid of topic cards
            cols = st.columns(3)
            for i, topic in enumerate(topics):
                with cols[i % 3]:
                    # Count selected images for this topic
                    topic_subtopics = load_subtopics(topic)
                    completed = sum(1 for st in topic_subtopics if f"{topic}/{st}" in selected_images)
                    total = len(topic_subtopics)
                    progress = int(completed / total * 100) if total > 0 else 0
                    
                    # Create a card-like button
                    with st.container():
                        st.markdown(f"""
                        <div class="topic-card">
                            <h3>{topic}</h3>
                            <div style="margin-bottom:10px;">Progress: {completed}/{total} ({progress}%)</div>
                            <div style="background-color:#e0e0e0; height:10px; border-radius:5px;">
                                <div style="background-color:#4CAF50; width:{progress}%; height:10px; border-radius:5px;"></div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        with st.container():
                            st.markdown('<div class="primary-button">', unsafe_allow_html=True)
                            if st.button(f"Select Topic", key=f"topic_{i}"):
                                st.session_state.selected_topic = topic
                                # Reset the selected subtopic when selecting a new topic
                                st.session_state.selected_subtopic = None 
                                st.rerun()
                            st.markdown('</div>', unsafe_allow_html=True)
        else:
            # Show navigation breadcrumb
            col1, col2 = st.columns([1, 5])
            with col1:
                if st.button("← Back to Topics", key="back_to_topics"):
                    st.session_state.selected_topic = None
                    st.session_state.selected_subtopic = None
                    st.rerun()
            with col2:
                st.markdown(f"<h2>{st.session_state.selected_topic}</h2>", unsafe_allow_html=True)
            
            # Show subtopic navigation and image selection
            navigate_subtopics(st.session_state.selected_topic, selected_images)
        
        # Show overall progress
        total_subtopics = sum(len(load_subtopics(topic)) for topic in topics)
        total_selected = len(selected_images)
        overall_progress = int(total_selected / total_subtopics * 100) if total_subtopics > 0 else 0
        
        st.sidebar.markdown("---")
        st.sidebar.markdown('<div class="sidebar-header">', unsafe_allow_html=True)
        st.sidebar.header("Overall Progress")
        st.sidebar.markdown('</div>', unsafe_allow_html=True)
        st.sidebar.progress(overall_progress/100)
        st.sidebar.markdown(f"**{total_selected}/{total_subtopics}** subtopics completed ({overall_progress}%)")
        
        # Export button
        st.sidebar.markdown("---")
        with st.sidebar.container():
            st.markdown('<div class="primary-button">', unsafe_allow_html=True)
            if st.button("Export Selections", key="export_btn"):
                export_selections(selected_images)
            st.markdown('</div>', unsafe_allow_html=True)
            
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.info("If you're seeing directory errors, make sure you've downloaded images first using the download.py script.")

def export_selections(selected_images):
    """Export selected images to a new consolidated JSON file and copy the images to a new folder structure."""
    # First create JSON export data
    export_data = {
        "subject": SUBJECT,
        "selections": {}
    }
    
    # Create a base directory for selected images
    selected_images_dir = os.path.join("", f"{SUBJECT}_Selected_Images")
    
    # Show a spinner while exporting
    with st.spinner("Exporting selected images..."):
        try:
            # Create the base directory if it doesn't exist
            if not os.path.exists(selected_images_dir):
                os.makedirs(selected_images_dir, exist_ok=True)
            
            # Create an array for topics and subtopics
            topics_array = []
            
            for key, img_path in selected_images.items():
                try:
                    topic, subtopic = key.split('/', 1)
                    
                    # Add to topics_array
                    topic_exists = False
                    for topic_obj in topics_array:
                        if topic_obj["topic"] == topic:
                            if subtopic not in topic_obj["subtopics"]:
                                topic_obj["subtopics"].append(subtopic)
                            topic_exists = True
                            break
                    
                    if not topic_exists:
                        topics_array.append({
                            "topic": topic,
                            "subtopics": [subtopic]
                        })
                    
                    if topic not in export_data["selections"]:
                        export_data["selections"][topic] = {}
                    
                    # Get image metadata
                    img_dir = os.path.dirname(img_path)
                    metadata_file = os.path.join(img_dir, "metadata.json")
                    img_filename = os.path.basename(img_path)
                    
                    img_data = {
                        "file_path": img_path,
                        "relative_path": os.path.join(topic, subtopic, img_filename)
                    }
                    
                    # Add metadata if available
                    if os.path.exists(metadata_file):
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                            
                            for img_metadata in metadata.get('downloaded_images', []):
                                if img_metadata['file_path'].endswith(img_filename):
                                    img_data.update({
                                        "title": img_metadata.get('title', ''),
                                        "source": img_metadata.get('source', ''),
                                        "original_url": img_metadata.get('original_url', '')
                                    })
                                    break
                    
                    export_data["selections"][topic][subtopic] = img_data
                    
                    # Create topic directory if it doesn't exist
                    topic_dir = os.path.join(selected_images_dir, topic)
                    if not os.path.exists(topic_dir):
                        os.makedirs(topic_dir, exist_ok=True)
                    
                    # Copy the image file to the new location
                    destination_file = os.path.join(topic_dir, f"{subtopic}.{img_filename.split('.')[-1]}")
                    
                    try:
                        # Copy the image with shutil
                        shutil.copy2(img_path, destination_file)
                        
                        # Add the new destination path to the export data
                        export_data["selections"][topic][subtopic]["exported_path"] = destination_file
                    except Exception as e:
                        st.error(f"Error copying image {img_path}: {str(e)}")
                        continue
                        
                except Exception as e:
                    st.error(f"Error processing {key}: {str(e)}")
                    continue
            
            # Save export data
            export_file = os.path.join("", f"{SUBJECT}_selected_images.json")
            with open(export_file, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            # Save topics and subtopics data
            topics_subtopics_file = os.path.join("", f"{SUBJECT}_topics_subtopics.json")
            with open(topics_subtopics_file, 'w') as f:
                json.dump(topics_array, f, indent=2)
            
            # If export was successful, show success message with folder path and count
            total_exported = len(selected_images)
            st.sidebar.success(f"✅ Exported {total_exported} images to {selected_images_dir}")
            
            # Calculate total subtopics
            total_subtopics = sum(len(topic_obj["subtopics"]) for topic_obj in topics_array)
            
            # Create subtopics count HTML
            subtopics_html = "<ul style='padding-left: 15px;'>"
            for topic_obj in topics_array:
                subtopics_html += f"<li><b>{topic_obj['topic']}:</b> {len(topic_obj['subtopics'])} subtopics</li>"
            subtopics_html += f"<li><b>Total:</b> {total_subtopics} subtopics</li></ul>"
            
            # Add some helpful information
            st.sidebar.markdown(f"""
            <div style="margin-top: 10px; padding: 10px; background-color: #f0f2f6; border-radius: 5px;">
                <b>Export Info:</b>
                <ul style="padding-left: 15px;">
                    <li>Images saved to: <code>{selected_images_dir}</code></li>
                    <li>JSON metadata saved to: <code>{export_file}</code></li>
                    <li>Topics and subtopics saved to: <code>{topics_subtopics_file}</code></li>
                    <li>Total images exported: {total_exported}</li>
                </ul>
                <b>Subtopics Count:</b>
                {subtopics_html}
            </div>
            """, unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"An error occurred during export: {str(e)}")
            st.info("Please try exporting again. If the error persists, you may need to restart the Streamlit app.")

if __name__ == "__main__":
    main() 