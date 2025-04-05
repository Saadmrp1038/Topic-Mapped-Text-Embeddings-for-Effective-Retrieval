# Topic Mapped Text Embeddings for Effective Retrieval

A comparative analysis system for different text-to-image retrieval methods with specialized topic mapping capabilities.

## Overview

This project implements and evaluates multiple approaches to text-to-image retrieval:

- BGE Embeddings (BERT-based)
- CLIP (Contrastive Language-Image Pre-training)
- TF-IDF (Term Frequency-Inverse Document Frequency)
- BM25 (with and without stopwords)

The system allows for querying an image collection using natural language and comparing the effectiveness of different retrieval methods side by side.

## Features

- Multiple retrieval methods for text-to-image search
- Backend API for image retrieval with FastAPI
- Frontend visualization using Svelte
- Streamlit interface for evaluation
- Automatic evaluation metrics collection
- Comparative analysis of retrieval methods

## Project Structure

- `backend/`: FastAPI server for image retrieval
- `frontend/`: Svelte-based UI for visualization
- `retreivers/`: Different retrieval method implementations
- `evaluation_dataset/`: Test dataset for retrieval evaluation
- `evaluation_results/`: Storage for evaluation metrics
- `image_collection/`: Code for image link collection, download and also image selection ui
- `preprocess/`: Scripts for data preprocessing

## Requirements

- Python 3.9+
- Node.js/npm for frontend
- Various Python libraries (see `requirements.txt`)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/topic-mapped-text-embeddings.git
   cd topic-mapped-text-embeddings
   ```

2. Set up a Python virtual environment:
   ```
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up the frontend:
   ```
   cd frontend
   npm install  # or pnpm install
   ```

5. Configure environment variables:
   - Copy `.env.example` to `.env`
   - Update the variables as needed

## Usage

### Running the Backend API

```
cd backend
uvicorn main:app --reload
```

The API will be available at http://localhost:8000

### Running the Frontend

```
cd frontend
npm run dev  # or pnpm dev
```

The frontend will be available at http://localhost:5173

### Running the Streamlit Evaluation App

```
streamlit run image_collection/image_picker_streamlit_ui.py
```

The Streamlit app will be available at http://localhost:8501

## License

[Specify the license here]

## Contributors

[List contributors here]
