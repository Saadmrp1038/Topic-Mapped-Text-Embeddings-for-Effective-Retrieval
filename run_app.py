"""Run the Streamlit app for retriever evaluation."""
import os
import sys
import streamlit.web.bootstrap

# Make sure the ui directory exists
os.makedirs("ui/results", exist_ok=True)

# Add the current directory to Python path
sys.path.insert(0, os.path.abspath("."))

# Run the Streamlit app
if __name__ == "__main__":
    streamlit.web.bootstrap.run("ui/app.py", "", [], []) 