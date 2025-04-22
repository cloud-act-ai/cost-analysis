# FinOps360 RAG System

This directory contains a Retrieval-Augmented Generation (RAG) implementation for the FinOps360 project, allowing conversational access to cloud cost analysis data.

## Overview

The RAG system uses Langchain, Ollama, and Qdrant to create a knowledge base from the FinOps data and provide an interactive chat interface for querying this data. The system has two main components:

1. **Data Ingestion**: Processes the FinOps data CSV file and stores it in a vector database
2. **Interactive Chat**: Provides a conversational interface to query the FinOps data

## Prerequisites

- Python 3.8+
- [Ollama](https://ollama.ai/) running locally (or remotely with configured base URL)
- [Qdrant](https://qdrant.tech/) vector database running locally (or remotely with configured URL)
- Required Python packages listed in requirements.txt

## Installation

1. Ensure Ollama is running with the required models:
   ```
   ollama pull mistral:7b
   ollama pull nomic-embed-text
   ```

2. Ensure Qdrant is running:
   ```
   docker run -p 6333:6333 qdrant/qdrant
   ```

3. Install required Python packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

### 1. Data Ingestion

Run the data ingestion script to process the FinOps data and load it into the vector database:

```bash
python data_ingestion.py
```

This script:
- Reads the FinOps data from `../data/finops_data.csv`
- Converts each row into a document with metadata
- Embeds the documents and stores them in Qdrant

### 2. Interactive Chat

Once the data is ingested, run the interactive chat script:

```bash
python Interactive_chat.py
```

This provides a command-line interface where you can ask questions about the FinOps data. Example questions:

- "What was the cloud spend for AWS in Q1 2024?"
- "Show me the top applications by cost for the Retail pillar"
- "Which VP had the highest spend in March 2024?"
- "Compare GCP vs Azure costs for the Engineering pillar"

## Configuration

Both scripts use the following environment variables which can be set in a `.env` file:

- `OLLAMA_BASE_URL`: URL for Ollama API (default: http://localhost:11434)
- `QDRANT_URL`: URL for Qdrant API (default: http://localhost:6333)
- `QDRANT_API_KEY`: API key for Qdrant (if needed)
- `VECTOR_COLLECTION_NAME`: Name of the collection in Qdrant (default: finops_db)

## Integration with FinOps360

This RAG system complements the core FinOps360 analysis tools by providing:

1. Natural language querying of cost data
2. Conversational access to insights
3. A user-friendly interface for non-technical stakeholders

The system uses the same underlying data as the main FinOps360 reporting tools, ensuring consistency across different interfaces.