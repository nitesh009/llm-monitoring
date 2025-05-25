import os
import logging
from dotenv import load_dotenv
import openai
from phoenix.otel import register
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from opentelemetry import trace

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_environment():
    """Load environment variables and validate required keys."""
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    phoenix_endpoint = os.getenv("PHOENIX_COLLECTOR_ENDPOINT", "http://localhost:6006/v1/traces")
    qdrant_host = os.getenv("QDRANT_HOST", "localhost")
    qdrant_port = os.getenv("QDRANT_PORT", "6333")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in .env file")
    logger.info(f"Phoenix endpoint: {phoenix_endpoint}")
    logger.info(f"Qdrant host: {qdrant_host}:{qdrant_port}")
    return api_key, phoenix_endpoint, qdrant_host, qdrant_port

def configure_phoenix(endpoint):
    """Configure Phoenix OpenTelemetry tracer."""
    logger.info("Configuring Phoenix tracer...")
    try:
        tracer_provider = register(
            project_name="sample-llm-app",
            endpoint=endpoint,
            auto_instrument=True
        )
        logger.info("Phoenix tracer configured successfully")
        return tracer_provider
    except Exception as e:
        logger.error(f"Failed to configure Phoenix tracer: {str(e)}")
        raise

def setup_qdrant(host, port):
    """Initialize Qdrant client and create collection if it doesn't exist."""
    logger.info("Setting up Qdrant client...")
    try:
        client = QdrantClient(host=host, port=port)
        collections = client.get_collections().collections
        collection_name = "haikus"
        if collection_name not in [c.name for c in collections]:
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
            )
            logger.info(f"Created Qdrant collection: {collection_name}")
        else:
            logger.info(f"Qdrant collection {collection_name} already exists")
        return client, collection_name
    except Exception as e:
        logger.error(f"Failed to set up Qdrant: {str(e)}")
        raise

def generate_haiku(client):
    """Generate a haiku about the ocean using OpenAI API."""
    logger.info("Generating haiku...")
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Write a haiku about the ocean."}]
        )
        haiku = response.choices[0].message.content
        logger.info("Haiku generated successfully")
        return haiku
    except Exception as e:
        logger.error(f"Error generating haiku: {str(e)}")
        raise

def generate_embedding(client, text):
    """Generate embedding for text using OpenAI API."""
    logger.info(f"Generating embedding for text: {text[:50]}...")
    try:
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        embedding = response.data[0].embedding
        logger.info("Embedding generated successfully")
        return embedding
    except Exception as e:
        logger.error(f"Error generating embedding: {str(e)}")
        raise

def store_in_qdrant(qdrant_client, collection_name, haiku, embedding, point_id):
    """Store haiku and its embedding in Qdrant."""
    logger.info(f"Storing haiku in Qdrant: {haiku[:50]}...")
    try:
        qdrant_client.upsert(
            collection_name=collection_name,
            points=[
                PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={"haiku": haiku}
                )
            ]
        )
        logger.info("Haiku stored in Qdrant")
    except Exception as e:
        logger.error(f"Error storing in Qdrant: {str(e)}")
        raise

def search_similar_haikus(qdrant_client, collection_name, embedding, limit=2):
    """Search for similar haikus in Qdrant."""
    logger.info("Searching for similar haikus...")
    try:
        search_result = qdrant_client.search(
            collection_name=collection_name,
            query_vector=embedding,
            limit=limit
        )
        logger.info(f"Found {len(search_result)} similar haikus")
        return [(hit.payload["haiku"], hit.score) for hit in search_result]
    except Exception as e:
        logger.error(f"Error searching Qdrant: {str(e)}")
        raise

def main():
    """Main function to set up and run the haiku generator with Qdrant."""
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("main"):
        # Setup environment and services
        api_key, phoenix_endpoint, qdrant_host, qdrant_port = setup_environment()
        configure_phoenix(phoenix_endpoint)
        qdrant_client, collection_name = setup_qdrant(qdrant_host, qdrant_port)
        openai_client = openai.OpenAI(api_key=api_key)

        # Generate and store haiku
        with tracer.start_as_current_span("generate-and-store"):
            haiku = generate_haiku(openai_client)
            print("Generated Haiku:")
            print(haiku)

            embedding = generate_embedding(openai_client, haiku)
            store_in_qdrant(qdrant_client, collection_name, haiku, embedding, point_id=1)

        # Search for similar haikus
        with tracer.start_as_current_span("search-similar"):
            similar_haikus = search_similar_haikus(qdrant_client, collection_name, embedding)
            print("\nSimilar Haikus:")
            for haiku, score in similar_haikus:
                print(f"Score: {score:.4f}\n{haiku}\n")

if __name__ == "__main__":
    main()
