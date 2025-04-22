import logging , json, os
from typing import List
from langchain_qdrant import Qdrant  # Correct import for Qdrant
from qdrant_client import QdrantClient  # Required for Qdrant client management
from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain_core.documents import Document
from qdrant_client.http.models import ScoredPoint
from dotenv import load_dotenv  # Import load_dotenv to load environment variables

# Load environment variables from .env file
load_dotenv()

# Define environment variables with default values
LOG_CHATBOT_FILE_PATH = "chatbot.log"
VECTOR_COLLECTION_NAME = "finops_db"
LOG_INGESTOR_FILE_PATH="data_ingestor.log"
OLLAMA_BASE_URL = "http://localhost:11434"
QDRANT_URL = "http://localhost:6333"
QDRANT_API_KEY = ""

# ANSI color codes
GREEN = "\033[92m"
LIGHT_BLUE = "\033[94m"
RESET = "\033[0m"

# Configure logging
# Ensure the directory for the log file exists
log_dir = os.path.dirname(LOG_CHATBOT_FILE_PATH)
if log_dir and not os.path.exists(log_dir):
    os.makedirs(log_dir)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_CHATBOT_FILE_PATH),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def create_prompt(query: str, docs: List[Document]) -> str:
    doc_details = "\n".join(f"- {doc.page_content}" for doc in docs)
    prompt = f"""
You are a FinOps assistant specializing in cloud cost analysis. You help users understand their cloud spending across different dimensions such as cloud providers, organizations, VPs, pillars, applications, and time periods.

User Query: {query}

Relevant Information:
{doc_details}

Based on the above details, provide a precise and relevant response that addresses the user's query. Focus on:
1. Cost figures and trends
2. Comparisons between different dimensions if applicable
3. Highlighting significant spending areas or unusual patterns

Use dollar amounts and percentages where appropriate. If the information provided doesn't directly answer the question, state that clearly without making assumptions or referencing unrelated information.
"""
    return prompt


def create_interactive_chatbot(vectorstore, llm):
    def interactive_retriever(query: str) -> str:
        print(f"{LIGHT_BLUE}Original User Query: {query}{RESET}")

        try:
            decision_prompt = f"""
            You are a smart assistant interacting with a structured database. The database contains both metadata and full-text content about cloud cost (FinOps) data, with the following metadata fields:
            - date
            - week
            - quarter
            - month
            - fiscal_year
            - product
            - organization
            - org_contact
            - vp
            - pillar
            - application
            - cloud
            - environment
            - cost

            Given the user's query: "{query}", decide whether to:
            1. Use a filter based on one of the metadata fields if you can clearly identify a specific value to filter on.
            2. Perform a general similarity search in the database using the query text.

            Only use filter if you are 100% confident of both the field name AND a specific value to filter on. 
            If filter_key is provided, filter_value MUST NOT be null or empty.

            Respond in JSON format:
            {{
              "use_filter": true/false,
              "filter_key": "metadata_field_name (only if you have a specific value)",
              "filter_value": "specific value to filter on (required if use_filter is true)",
              "similarity_query": "query text for similarity search"
            }}
            """
            decision_response = llm.generate([decision_prompt])
            decision_json = decision_response.generations[0][0].text.strip()
            logger.info(f"Decision JSON: {decision_json}")

            try:
                decision = json.loads(decision_json)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse decision JSON: {e}")
                return "Sorry, I couldn't process your query. Could you clarify or rephrase it?"

            use_filter = decision.get("use_filter", False)
            filter_key = decision.get("filter_key")
            filter_value = decision.get("filter_value")
            similarity_query = decision.get("similarity_query", query)
            
            # Validate filter: if use_filter is True but filter_value is None or empty, default to similarity search
            if use_filter and (filter_value is None or filter_value == ""):
                logger.warning("Filter value is null or empty. Defaulting to similarity search.")
                use_filter = False

            docs = []

            if use_filter and filter_key and filter_value:
                try:
                    if filter_key in ["cost", "fiscal_year"]:
                        try:
                            filter_value = float(filter_value)
                        except ValueError:
                            filter_value = str(filter_value)

                    vector_size = 768
                    logger.info(f"Using vector size: {vector_size}")

                    qdrant_filter = {
                        "must": [
                            {
                                "key": f"metadata.{filter_key}",
                                "match": {"value": filter_value}
                            }
                        ]
                    }
                    logger.info(f"Prepared Qdrant filter: {qdrant_filter}")

                    logger.info("Sending filtered search request to Qdrant...")
                    results = vectorstore.client.search(
                        collection_name=VECTOR_COLLECTION_NAME,
                        query_vector=[0.0] * vector_size,
                        query_filter=qdrant_filter,
                        limit=5,
                    )
                    logger.info(f"Qdrant Filtered Search Results: {results}")

                    for result in results:
                        if isinstance(result, ScoredPoint):
                            payload = result.payload
                            page_content = payload.get("page_content", "")
                            metadata = payload.get("metadata", {})
                            docs.append(Document(page_content=page_content, metadata=metadata))

                    if not docs:
                        logger.warning("No results found using the filter. Switching to semantic search.")
                        use_filter = False

                except Exception as e:
                    logger.error(f"Error during filtered search: {e}")
                    use_filter = False

            if not use_filter:
                logger.info("Performing general similarity search.")
                logger.info(f"Qdrant Similarity Search Query: {similarity_query}")
                try:
                    docs = vectorstore.similarity_search(query=similarity_query, k=5)
                    if not docs:
                        return "No relevant results were found. Could you refine your query?"
                    logger.info(f"Qdrant Similarity Search Response: {docs}")
                except Exception as e:
                    logger.error(f"Error during similarity search: {e}")
                    return "Sorry, something went wrong while processing your query."

            if docs:
                print(f"{LIGHT_BLUE}Vector DB Results (Top 5):{RESET}")
                for i, doc in enumerate(docs, 1):
                    print(f"{LIGHT_BLUE}Result {i}: {doc.page_content}{RESET}")
                    print(f"{LIGHT_BLUE}Metadata {i}: {doc.metadata}{RESET}")

                prompt = create_prompt(query, docs)
                logger.info(f"Generated Prompt for AI: {prompt}")

                response = llm.generate([prompt])
                if response and response.generations:
                    return response.generations[0][0].text
                else:
                    return "Sorry, I couldn't generate a response. Please try again."
            else:
                return "No results found for your query. Please try a different query."

        except Exception as e:
            logger.error(f"Error in interactive_retriever: {e}")
            return "Sorry, something went wrong while processing your query."

    return interactive_retriever


def main():
    try:
        llm = OllamaLLM(base_url=OLLAMA_BASE_URL, model="mistral:7b")
        embeddings = OllamaEmbeddings(base_url=OLLAMA_BASE_URL, model="nomic-embed-text")

        if not embeddings:
            logger.error("Embeddings are not initialized properly.")
            raise ValueError("Embeddings are required but not initialized.")
        logger.info("Embeddings initialized successfully.")

        qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

        if not qdrant_client:
            logger.error("Qdrant client is not initialized.")
            raise ValueError("Qdrant client connection failed.")
        logger.info("Qdrant client initialized successfully.")

        vectorstore = Qdrant(
            client=qdrant_client,
            collection_name=VECTOR_COLLECTION_NAME,
            embeddings=embeddings
        )

        if not vectorstore:
            logger.error("Vectorstore initialization failed.")
            raise ValueError("Vectorstore could not be initialized.")
        logger.info("Connected to Qdrant vector store.")

        chatbot = create_interactive_chatbot(vectorstore, llm)

        while True:
            query = input(f"{GREEN}User: {RESET}")
            if query.lower() in ('exit', 'quit'):
                print(f"{GREEN}Goodbye! FinOps360 Cost Analysis Assistant{RESET}")
                break
            response = chatbot(query)
            print(f"{GREEN}Chatbot: {response}{RESET}")

    except Exception as e:
        logger.error(f"Error in main execution: {e}")


if __name__ == "__main__":
    main()
