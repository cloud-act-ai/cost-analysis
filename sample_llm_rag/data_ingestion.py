import pandas as pd
import hashlib
import os
import logging
from langchain_ollama import OllamaEmbeddings
from langchain_core.documents import Document
from langchain_qdrant import Qdrant
from typing import List
from dotenv import load_dotenv
import sys

# Add parent directory to path to import finops modules if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from .env file
load_dotenv()

# Constants from environment variables
LOCAL_CSV_PATH="../data/finops_data.csv"
HASH_FILE="last_csv_hash.txt"
PULL_POLICY="IfNotPresent"
VECTOR_COLLECTION_NAME = "finops_db"
LOG_INGESTOR_FILE_PATH="data_ingestor.log"
OLLAMA_BASE_URL = "http://localhost:11434"
QDRANT_URL = "http://localhost:6333"
QDRANT_API_KEY = ""

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_INGESTOR_FILE_PATH),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def compute_sha256(file_path: str) -> str:
    """Compute the SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def has_csv_changed(local_file_path: str) -> bool:
    """Check if the local CSV content has changed by comparing its SHA256 hash."""
    if os.path.exists(local_file_path):
        local_hash = compute_sha256(local_file_path)
        logger.info(f"Computed local CSV hash: {local_hash}")

        if os.path.exists(HASH_FILE):
            with open(HASH_FILE, "r") as f:
                last_known_hash = f.read().strip()
            logger.info(f"Last known CSV hash: {last_known_hash}")

            if local_hash != last_known_hash:
                logger.info("Local CSV file has been manually changed. Proceeding with re-ingestion.")
                return True

    return False


def download_csv(csv_url: str, local_file_path: str) -> None:
    """Download the CSV file from the given URL."""
    df = pd.read_csv(csv_url)
    df.to_csv(local_file_path, index=False)
    logger.info("CSV file downloaded and saved locally.")


def update_hash_file(local_file_path: str) -> None:
    """Update the hash file with the current hash of the CSV."""
    current_hash = compute_sha256(local_file_path)
    with open(HASH_FILE, "w") as f:
        f.write(current_hash)
    logger.info(f"Updated hash file with hash: {current_hash}")


def check_and_update_hash(local_file_path: str) -> bool:
    """Check if the CSV content has changed and update the hash file."""
    current_hash = compute_sha256(local_file_path)
    logger.info(f"Computed current CSV hash: {current_hash}")

    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, "r") as f:
            last_known_hash = f.read().strip()
        logger.info(f"Last known CSV hash: {last_known_hash}")

        if current_hash == last_known_hash:
            logger.info("No changes detected in CSV content. Skipping re-ingestion.")
            return False

    update_hash_file(local_file_path)
    logger.info("CSV content has changed. Proceeding with re-ingestion.")
    return True


def load_finops_documents(file_path: str) -> List[Document]:
    """Load FinOps CSV data into LangChain Document objects."""
    try:
        df = pd.read_csv(file_path)
        logger.info(f"Loaded CSV with {len(df)} rows.")

        documents = []
        for _, row in df.iterrows():
            metadata = {
                "date": str(row['DATE']),
                "week": str(row['WM_WEEK']),
                "quarter": str(row['QTR']),
                "month": str(row['Month']),
                "fiscal_year": str(row['FY']),
                "product": str(row['TR_PRODUCT']),
                "organization": str(row['ORG']),
                "org_contact": str(row['Org_AD']),
                "vp": str(row['VP']),
                "pillar": str(row['PILLAR']),
                "application": str(row['Application_Name']),
                "cloud": str(row['Cloud']),
                "environment": str(row['Env']),
                "cost": float(row['Cost'])
            }
            documents.append(
                Document(
                    page_content=(
                        f"Date: {row['DATE']}\n"
                        f"Week: {row['WM_WEEK']}\n"
                        f"Quarter: {row['QTR']}\n"
                        f"Month: {row['Month']}\n"
                        f"Fiscal Year: {row['FY']}\n"
                        f"Product: {row['TR_PRODUCT']}\n"
                        f"Organization: {row['ORG']}\n"
                        f"Organization Contact: {row['Org_AD']}\n"
                        f"VP: {row['VP']}\n"
                        f"Pillar: {row['PILLAR']}\n"
                        f"Application: {row['Application_Name']}\n"
                        f"Cloud: {row['Cloud']}\n"
                        f"Environment: {row['Env']}\n"
                        f"Cost: ${row['Cost']:.2f}"
                    ),
                    metadata=metadata
                )
            )
        logger.info(f"Created {len(documents)} document objects with metadata.")
        return documents
    except Exception as e:
        logger.error(f"Error loading documents: {e}")
        raise


def setup_vector_store(documents: List[Document], ollama_base_url: str, qdrant_url: str, qdrant_api_key: str):
    """Initialize vector store with documents and embeddings."""
    try:
        embeddings = OllamaEmbeddings(base_url=ollama_base_url, model="nomic-embed-text")
        vectorstore = Qdrant.from_documents(
            documents, embeddings, url=qdrant_url, collection_name=VECTOR_COLLECTION_NAME, api_key=qdrant_api_key
        )
        logger.info("Vector store initialized.")
        return vectorstore
    except Exception as e:
        logger.error(f"Error setting up vector store: {e}")
        raise


def main():
    """Main function for inserting data into the vector store."""
    # Check if the local file exists
    if not os.path.exists(LOCAL_CSV_PATH):
        logger.error(f"CSV file not found at {LOCAL_CSV_PATH}")
        raise FileNotFoundError(f"CSV file not found at {LOCAL_CSV_PATH}")

    # Check if the CSV content has changed and proceed with ingestion if necessary
    if check_and_update_hash(LOCAL_CSV_PATH):
        documents = load_finops_documents(LOCAL_CSV_PATH)
        setup_vector_store(documents, OLLAMA_BASE_URL, QDRANT_URL, QDRANT_API_KEY)

if __name__ == "__main__":
    main()