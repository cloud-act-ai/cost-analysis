#!/bin/bash

# Script to run the FinOps RAG application
# Usage: ./run.sh [ingest|chat]

# Create and activate virtual environment if it doesn't exist
if [ ! -d "../finops_env" ]; then
    echo "Creating virtual environment..."
    cd ..
    python -m venv finops_env
    cd sample_llm_rag
fi

# Activate the virtual environment
source ../finops_env/bin/activate

# Install dependencies if needed
if ! pip show langchain-ollama > /dev/null 2>&1; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Handle command-line arguments
if [ "$1" == "ingest" ]; then
    echo "Running data ingestion..."
    python data_ingestion.py
elif [ "$1" == "chat" ]; then
    echo "Starting interactive chat..."
    python Interactive_chat.py
else
    echo "FinOps360 RAG System"
    echo "-------------------"
    echo "Usage: ./run.sh [ingest|chat]"
    echo ""
    echo "Commands:"
    echo "  ingest - Process the FinOps data CSV and load it into the vector database"
    echo "  chat   - Start the interactive chat interface to query FinOps data"
    echo ""
    echo "Make sure Ollama and Qdrant are running before using these commands."
fi

# Deactivate the virtual environment
deactivate