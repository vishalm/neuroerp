#!/bin/bash

# AI-Native ERP System - Vector Database Setup Script
# This script sets up and configures vector databases for the Neural Data Fabric component
# Supports Weaviate, Pinecone, and Qdrant as vector database options

set -e  # Exit on any error

# Color formatting for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default settings
DEFAULT_VECTOR_DB="weaviate"  # Options: weaviate, pinecone, qdrant
VECTOR_DB_PORT="8080"
DATA_PATH="../data/vector_db"
CONFIG_DIR="../config"

# Vector embedding dimensions for different models
DIMENSIONS=1536  # Default for OpenAI embeddings
CONSISTENCY_LEVEL="QUORUM"
USE_DOCKER=true
INITIALIZE_SCHEMA=true

print_header() {
    echo -e "\n${BLUE}======================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}======================================${NC}\n"
}

check_dependencies() {
    print_header "Checking Dependencies"
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Docker is not installed. Please install Docker first.${NC}"
        echo "Visit https://docs.docker.com/get-docker/ for installation instructions."
        exit 1
    else
        echo -e "${GREEN}✓ Docker is installed${NC}"
    fi
    
    # Check for Docker Compose
    if ! command -v docker compose &> /dev/null; then
        echo -e "${RED}Docker Compose is not installed. Please install Docker Compose first.${NC}"
        echo "Visit https://docs.docker.com/compose/install/ for installation instructions."
        exit 1
    else
        echo -e "${GREEN}✓ Docker Compose is installed${NC}"
    fi
    
    # Check for curl
    if ! command -v curl &> /dev/null; then
        echo -e "${RED}curl is not installed. Installing curl...${NC}"
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            sudo apt-get update && sudo apt-get install -y curl
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            brew install curl
        else
            echo -e "${RED}Unsupported OS. Please install curl manually.${NC}"
            exit 1
        fi
    else
        echo -e "${GREEN}✓ curl is installed${NC}"
    fi
    
    # Check for jq
    if ! command -v jq &> /dev/null; then
        echo -e "${RED}jq is not installed. Installing jq...${NC}"
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            sudo apt-get update && sudo apt-get install -y jq
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            brew install jq
        else
            echo -e "${RED}Unsupported OS. Please install jq manually.${NC}"
            exit 1
        fi
    else
        echo -e "${GREEN}✓ jq is installed${NC}"
    fi
    
    # Check for Python if needed for schema initialization
    if [ "$INITIALIZE_SCHEMA" = true ]; then
        if ! command -v python3 &> /dev/null; then
            echo -e "${RED}Python 3 is not installed. Please install Python 3 first.${NC}"
            exit 1
        else
            echo -e "${GREEN}✓ Python 3 is installed${NC}"
            
            # Check for required Python packages
            python3 -m pip install --quiet weaviate-client pinecone-client qdrant-client
            echo -e "${GREEN}✓ Python vector DB clients installed${NC}"
        fi
    fi
}

parse_arguments() {
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --vector-db)
                VECTOR_DB="$2"
                shift 2
                ;;
            --port)
                VECTOR_DB_PORT="$2"
                shift 2
                ;;
            --dimensions)
                DIMENSIONS="$2"
                shift 2
                ;;
            --no-docker)
                USE_DOCKER=false
                shift
                ;;
            --no-schema)
                INITIALIZE_SCHEMA=false
                shift
                ;;
            --api-key)
                API_KEY="$2"
                shift 2
                ;;
            --help)
                print_usage
                exit 0
                ;;
            *)
                echo -e "${RED}Unknown option: $1${NC}"
                print_usage
                exit 1
                ;;
        esac
    done
    
    # Set default vector DB if not specified
    if [ -z "$VECTOR_DB" ]; then
        VECTOR_DB=$DEFAULT_VECTOR_DB
    fi
    
    # Validate vector DB choice
    if [[ ! "$VECTOR_DB" =~ ^(weaviate|pinecone|qdrant)$ ]]; then
        echo -e "${RED}Unsupported vector database: $VECTOR_DB${NC}"
        echo -e "${YELLOW}Supported options: weaviate, pinecone, qdrant${NC}"
        exit 1
    fi
    
    # Check if API key is required but not provided
    if [[ "$VECTOR_DB" == "pinecone" && -z "$API_KEY" ]]; then
        echo -e "${RED}Pinecone requires an API key. Please provide it with --api-key${NC}"
        exit 1
    fi
}

setup_weaviate() {
    print_header "Setting Up Weaviate Vector Database"
    
    # Create the Docker Compose file for Weaviate
    mkdir -p $DATA_PATH/weaviate
    
    echo -e "${YELLOW}Creating Docker Compose file for Weaviate...${NC}"
    cat > docker-compose.weaviate.yml << EOF
version: '3.4'
services:
  weaviate:
    image: semitechnologies/weaviate:1.25.5
    restart: unless-stopped
    ports:
      - "${VECTOR_DB_PORT}:8080"
    environment:
      QUERY_DEFAULTS_LIMIT: 25
      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: 'true'
      PERSISTENCE_DATA_PATH: '/var/lib/weaviate'
      DEFAULT_VECTORIZER_MODULE: 'none'
      ENABLE_MODULES: ''
      CLUSTER_HOSTNAME: 'node1'
    volumes:
      - ${DATA_PATH}/weaviate:/var/lib/weaviate
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/v1/.well-known/ready"]
      interval: 10s
      timeout: 5s
      retries: 5
EOF
    
    if [ "$USE_DOCKER" = true ]; then
        echo -e "${YELLOW}Starting Weaviate container...${NC}"
        docker compose -f docker-compose.weaviate.yml up -d
        
        # Wait for Weaviate to be ready
        echo -e "${YELLOW}Waiting for Weaviate to be ready...${NC}"
        until curl -s http://localhost:$VECTOR_DB_PORT/v1/.well-known/ready | grep -q "true"; do
            echo -n "."
            sleep 2
        done
        echo -e "\n${GREEN}✓ Weaviate is running and ready${NC}"
    else
        echo -e "${YELLOW}Docker Compose file created at docker-compose.weaviate.yml${NC}"
        echo -e "${YELLOW}Run 'docker compose -f docker-compose.weaviate.yml up -d' to start Weaviate${NC}"
    fi
}

setup_qdrant() {
    print_header "Setting Up Qdrant Vector Database"
    
    # Create the Docker Compose file for Qdrant
    mkdir -p $DATA_PATH/qdrant
    
    echo -e "${YELLOW}Creating Docker Compose file for Qdrant...${NC}"
    cat > docker-compose.qdrant.yml << EOF
version: '3.4'
services:
  qdrant:
    image: qdrant/qdrant:latest
    restart: unless-stopped
    ports:
      - "${VECTOR_DB_PORT}:6333"
    volumes:
      - ${DATA_PATH}/qdrant:/qdrant/storage
    environment:
      QDRANT__SERVICE__GRPC_PORT: 6334
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/readiness"]
      interval: 10s
      timeout: 5s
      retries: 5
EOF
    
    if [ "$USE_DOCKER" = true ]; then
        echo -e "${YELLOW}Starting Qdrant container...${NC}"
        docker compose -f docker-compose.qdrant.yml up -d
        
        # Wait for Qdrant to be ready
        echo -e "${YELLOW}Waiting for Qdrant to be ready...${NC}"
        until curl -s http://localhost:$VECTOR_DB_PORT/readiness | grep -q "ok"; do
            echo -n "."
            sleep 2
        done
        echo -e "\n${GREEN}✓ Qdrant is running and ready${NC}"
    else
        echo -e "${YELLOW}Docker Compose file created at docker-compose.qdrant.yml${NC}"
        echo -e "${YELLOW}Run 'docker compose -f docker-compose.qdrant.yml up -d' to start Qdrant${NC}"
    fi
}

setup_pinecone() {
    print_header "Setting Up Pinecone Integration"
    
    # Pinecone is a cloud service, so we just create a configuration file
    echo -e "${YELLOW}Setting up Pinecone configuration...${NC}"
    
    mkdir -p $CONFIG_DIR
    
    # Create a configuration file for Pinecone
    cat > $CONFIG_DIR/pinecone_config.json << EOF
{
    "api_key": "${API_KEY}",
    "environment": "gcp-starter",
    "dimensions": ${DIMENSIONS},
    "metric": "cosine",
    "pods": 1,
    "replicas": 1,
    "pod_type": "starter"
}
EOF
    
    echo -e "${GREEN}✓ Pinecone configuration created at $CONFIG_DIR/pinecone_config.json${NC}"
    echo -e "${YELLOW}Note: Pinecone is a cloud service. You need to create indexes via API calls.${NC}"
}

initialize_schemas() {
    if [ "$INITIALIZE_SCHEMA" = true ]; then
        print_header "Initializing Vector Database Schemas"
        
        # Create a Python script to initialize the schema based on the selected vector DB
        echo -e "${YELLOW}Creating schema initialization script...${NC}"
        
        mkdir -p scripts
        
        cat > scripts/initialize_vector_db.py << EOF
#!/usr/bin/env python3

import sys
import json
import time
import os

# ERP vector database schema initialization
print("Initializing vector database schema for AI-Native ERP system...")

# Common schema definitions for ERP system
class_definitions = {
    "Document": {
        "description": "A business document in the ERP system",
        "properties": [
            {"name": "title", "dataType": ["text"]},
            {"name": "content", "dataType": ["text"]},
            {"name": "documentType", "dataType": ["text"]},
            {"name": "department", "dataType": ["text"]},
            {"name": "createdAt", "dataType": ["date"]},
            {"name": "metadata", "dataType": ["text"]}
        ]
    },
    "Employee": {
        "description": "Employee information in the ERP system",
        "properties": [
            {"name": "employeeId", "dataType": ["text"]},
            {"name": "name", "dataType": ["text"]},
            {"name": "position", "dataType": ["text"]},
            {"name": "department", "dataType": ["text"]},
            {"name": "skills", "dataType": ["text[]"]},
            {"name": "hireDate", "dataType": ["date"]},
            {"name": "metadata", "dataType": ["text"]}
        ]
    },
    "Product": {
        "description": "Product information in the ERP system",
        "properties": [
            {"name": "productId", "dataType": ["text"]},
            {"name": "name", "dataType": ["text"]},
            {"name": "description", "dataType": ["text"]},
            {"name": "category", "dataType": ["text"]},
            {"name": "price", "dataType": ["number"]},
            {"name": "features", "dataType": ["text[]"]},
            {"name": "metadata", "dataType": ["text"]}
        ]
    },
    "Customer": {
        "description": "Customer information in the ERP system",
        "properties": [
            {"name": "customerId", "dataType": ["text"]},
            {"name": "name", "dataType": ["text"]},
            {"name": "industry", "dataType": ["text"]},
            {"name": "location", "dataType": ["text"]},
            {"name": "contactInfo", "dataType": ["text"]},
            {"name": "metadata", "dataType": ["text"]}
        ]
    },
    "Transaction": {
        "description": "Business transaction in the ERP system",
        "properties": [
            {"name": "transactionId", "dataType": ["text"]},
            {"name": "description", "dataType": ["text"]},
            {"name": "amount", "dataType": ["number"]},
            {"name": "currency", "dataType": ["text"]},
            {"name": "date", "dataType": ["date"]},
            {"name": "parties", "dataType": ["text[]"]},
            {"name": "category", "dataType": ["text"]},
            {"name": "metadata", "dataType": ["text"]}
        ]
    }
}

# Get vector DB type from argument or environment
vector_db = "${VECTOR_DB}"
port = ${VECTOR_DB_PORT}
dimensions = ${DIMENSIONS}

if vector_db == "weaviate":
    import weaviate
    
    # Connect to Weaviate
    print(f"Connecting to Weaviate on port {port}...")
    client = weaviate.Client(f"http://localhost:{port}")
    
    # Check if Weaviate is ready
    if not client.is_ready():
        print("Weaviate is not ready. Please check your installation.")
        sys.exit(1)
    
    # Create schema classes
    print("Creating schema classes...")
    for class_name, class_def in class_definitions.items():
        try:
            # Check if class already exists
            try:
                client.schema.get(class_name)
                print(f"Class '{class_name}' already exists, skipping...")
                continue
            except:
                pass
            
            # Create the class
            class_obj = {
                "class": class_name,
                "description": class_def["description"],
                "vectorizer": "none",  # Using external vectorizer
                "properties": class_def["properties"],
                "vectorIndexConfig": {
                    "distance": "cosine"
                }
            }
            
            client.schema.create_class(class_obj)
            print(f"Created class '{class_name}'")
        except Exception as e:
            print(f"Error creating class '{class_name}': {e}")
            
elif vector_db == "qdrant":
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
    
    # Connect to Qdrant
    print(f"Connecting to Qdrant on port {port}...")
    client = QdrantClient(host="localhost", port=port)
    
    # Create collections for each class
    print("Creating collections...")
    for class_name, class_def in class_definitions.items():
        try:
            # Convert properties to payload schema (Qdrant doesn't enforce schema but we'll document it)
            payload_schema = {}
            for prop in class_def["properties"]:
                payload_schema[prop["name"]] = prop["dataType"][0]
            
            # Create collection
            client.create_collection(
                collection_name=class_name.lower(),
                vectors_config=models.VectorParams(
                    size=dimensions,
                    distance=models.Distance.COSINE
                )
            )
            print(f"Created collection '{class_name.lower()}'")
            
            # Document the schema in collection metadata
            client.update_collection(
                collection_name=class_name.lower(),
                metadata={
                    "description": class_def["description"],
                    "schema": payload_schema
                }
            )
            
        except Exception as e:
            if "already exists" in str(e):
                print(f"Collection '{class_name.lower()}' already exists, skipping...")
            else:
                print(f"Error creating collection '{class_name.lower()}': {e}")
    
elif vector_db == "pinecone":
    import pinecone
    
    # Read config for API key
    with open("${CONFIG_DIR}/pinecone_config.json", "r") as f:
        config = json.load(f)
    
    # Initialize Pinecone
    print("Initializing Pinecone...")
    pinecone.init(api_key=config["api_key"], environment=config["environment"])
    
    # Create index for ERP data if it doesn't exist
    index_name = "erp-data"
    
    # Check if index exists
    if index_name not in pinecone.list_indexes():
        print(f"Creating Pinecone index '{index_name}'...")
        pinecone.create_index(
            name=index_name,
            dimension=dimensions,
            metric="cosine",
            pods=config.get("pods", 1),
            replicas=config.get("replicas", 1),
            pod_type=config.get("pod_type", "starter")
        )
        print(f"Created Pinecone index '{index_name}'")
        
        # Wait for index to be ready
        print("Waiting for index to initialize...")
        time.sleep(20)
    else:
        print(f"Pinecone index '{index_name}' already exists, skipping...")
    
    # Document the schema in a local file for reference
    with open("${CONFIG_DIR}/pinecone_schema.json", "w") as f:
        json.dump(class_definitions, f, indent=2)
    print(f"Saved schema reference to ${CONFIG_DIR}/pinecone_schema.json")

print("Vector database schema initialization complete!")
EOF
        
        # Make the script executable
        chmod +x scripts/initialize_vector_db.py
        
        # Run the initialization script
        echo -e "${YELLOW}Running schema initialization script...${NC}"
        python3 scripts/initialize_vector_db.py
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ Vector database schema initialized successfully${NC}"
        else
            echo -e "${RED}Schema initialization failed. Please check the error messages above.${NC}"
        fi
    else
        echo -e "${YELLOW}Skipping schema initialization as requested.${NC}"
    fi
}

create_config_file() {
    print_header "Creating Configuration File"
    
    # Create a configuration file for the vector database
    mkdir -p $CONFIG_DIR
    
    echo -e "${YELLOW}Creating vector database configuration file...${NC}"
    
    cat > $CONFIG_DIR/vector_db_config.yaml << EOF
# Vector Database Configuration for AI-Native ERP System
vector_db:
  type: ${VECTOR_DB}
  host: localhost
  port: ${VECTOR_DB_PORT}
  dimensions: ${DIMENSIONS}
  classes:
    - Document
    - Employee
    - Product
    - Customer
    - Transaction
EOF
    
    # Add specific configuration based on vector DB type
    if [ "$VECTOR_DB" == "weaviate" ]; then
        cat >> $CONFIG_DIR/vector_db_config.yaml << EOF
  weaviate:
    batch_size: 100
    consistency_level: ${CONSISTENCY_LEVEL}
EOF
    elif [ "$VECTOR_DB" == "qdrant" ]; then
        cat >> $CONFIG_DIR/vector_db_config.yaml << EOF
  qdrant:
    batch_size: 100
    optimization_ttl: 300
EOF
    elif [ "$VECTOR_DB" == "pinecone" ]; then
        cat >> $CONFIG_DIR/vector_db_config.yaml << EOF
  pinecone:
    environment: gcp-starter
    index_name: erp-data
    batch_size: 100
EOF
    fi
    
    echo -e "${GREEN}✓ Vector database configuration created at $CONFIG_DIR/vector_db_config.yaml${NC}"
}

create_python_client() {
    print_header "Creating Python Client Utilities"
    
    # Create a Python directory for client utilities
    mkdir -p ../neural_data_fabric
    
    echo -e "${YELLOW}Creating Python client utilities...${NC}"
    
    # Create a base vector store client
    cat > ../neural_data_fabric/vector_store.py << EOF
"""
AI-Native ERP System - Vector Store Client

This module provides a unified interface to interact with different vector databases
(Weaviate, Pinecone, Qdrant) used in the Neural Data Fabric component.
"""

import os
import yaml
import logging
from typing import Dict, List, Any, Optional, Union, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vector_store")

class VectorStore:
    """Unified interface for vector database operations."""
    
    def __init__(self, config_path: str = "../config/vector_db_config.yaml"):
        """Initialize the vector store client.
        
        Args:
            config_path: Path to the vector database configuration file
        """
        self.client = None
        self.config = self._load_config(config_path)
        self.db_type = self.config["vector_db"]["type"]
        self._connect()
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            logger.error(f"Failed to load config from {config_path}: {e}")
            raise
    
    def _connect(self):
        """Connect to the vector database based on configuration."""
        db_type = self.db_type
        host = self.config["vector_db"]["host"]
        port = self.config["vector_db"]["port"]
        
        try:
            if db_type == "weaviate":
                self._connect_weaviate(host, port)
            elif db_type == "qdrant":
                self._connect_qdrant(host, port)
            elif db_type == "pinecone":
                self._connect_pinecone()
            else:
                raise ValueError(f"Unsupported vector database type: {db_type}")
            
            logger.info(f"Connected to {db_type} successfully")
        except Exception as e:
            logger.error(f"Failed to connect to {db_type}: {e}")
            raise
    
    def _connect_weaviate(self, host: str, port: int):
        """Connect to Weaviate."""
        import weaviate
        self.client = weaviate.Client(f"http://{host}:{port}")
        
        # Verify connection
        if not self.client.is_ready():
            raise ConnectionError("Weaviate is not ready")
    
    def _connect_qdrant(self, host: str, port: int):
        """Connect to Qdrant."""
        from qdrant_client import QdrantClient
        self.client = QdrantClient(host=host, port=port)
        
        # Verify connection by listing collections
        self.client.get_collections()
    
    def _connect_pinecone(self):
        """Connect to Pinecone."""
        import pinecone
        
        # Get API key from config
        pinecone_config_path = "../config/pinecone_config.json"
        if not os.path.exists(pinecone_config_path):
            raise FileNotFoundError(f"Pinecone config file not found: {pinecone_config_path}")
        
        import json
        with open(pinecone_config_path, 'r') as f:
            pinecone_config = json.load(f)
        
        # Initialize Pinecone
        pinecone.init(
            api_key=pinecone_config["api_key"],
            environment=pinecone_config["environment"]
        )
        
        # Connect to the index
        index_name = self.config["vector_db"]["pinecone"]["index_name"]
        self.client = pinecone.Index(index_name)
    
    def add_document(self, class_name: str, document: Dict[str, Any], vector: List[float], 
                     id: Optional[str] = None) -> str:
        """Add a document to the vector store.
        
        Args:
            class_name: The class/collection name
            document: The document properties/metadata
            vector: The embedding vector
            id: Optional ID for the document
            
        Returns:
            The ID of the added document
        """
        db_type = self.db_type
        
        try:
            if db_type == "weaviate":
                return self._add_document_weaviate(class_name, document, vector, id)
            elif db_type == "qdrant":
                return self._add_document_qdrant(class_name, document, vector, id)
            elif db_type == "pinecone":
                return self._add_document_pinecone(class_name, document, vector, id)
        except Exception as e:
            logger.error(f"Failed to add document to {db_type}: {e}")
            raise
    
    def _add_document_weaviate(self, class_name: str, document: Dict[str, Any], 
                               vector: List[float], id: Optional[str] = None) -> str:
        """Add a document to Weaviate."""
        import uuid
        
        # Generate UUID if not provided
        if id is None:
            id = str(uuid.uuid4())
        
        # Add the object with the vector
        self.client.data_object.create(
            class_name=class_name,
            data_object=document,
            uuid=id,
            vector=vector
        )
        
        return id
    
    def _add_document_qdrant(self, class_name: str, document: Dict[str, Any],
                            vector: List[float], id: Optional[str] = None) -> str:
        """Add a document to Qdrant."""
        from qdrant_client.http import models
        import uuid
        
        # Generate UUID if not provided
        if id is None:
            id = str(uuid.uuid4())
        else:
            # Ensure ID is properly formatted for Qdrant
            try:
                id = str(uuid.UUID(id))
            except ValueError:
                id = str(uuid.uuid5(uuid.NAMESPACE_DNS, id))
        
        # Add the point
        self.client.upsert(
            collection_name=class_name.lower(),
            points=[
                models.PointStruct(
                    id=id,
                    vector=vector,
                    payload=document
                )
            ]
        )
        
        return id
    
    def _add_document_pinecone(self, class_name: str, document: Dict[str, Any],
                              vector: List[float], id: Optional[str] = None) -> str:
        """Add a document to Pinecone."""
        import uuid
        
        # Generate UUID if not provided
        if id is None:
            id = str(uuid.uuid4())
        
        # Add metadata about the class
        document["_class"] = class_name
        
        # Upsert the vector
        self.client.upsert(
            vectors=[(id, vector, document)]
        )
        
        return id
    
    def search(self, class_name: str, query_vector: List[float], limit: int = 10) -> List[Dict[str, Any]]:
        """Search for similar documents using vector similarity.
        
        Args:
            class_name: The class/collection to search in
            query_vector: The query embedding vector
            limit: Maximum number of results to return
            
        Returns:
            List of matching documents with their metadata
        """
        db_type = self.db_type
        
        try:
            if db_type == "weaviate":
                return self._search_weaviate(class_name, query_vector, limit)
            elif db_type == "qdrant":
                return self._search_qdrant(class_name, query_vector, limit)
            elif db_type == "pinecone":
                return self._search_pinecone(class_name, query_vector, limit)
        except Exception as e:
            logger.error(f"Failed to search in {db_type}: {e}")
            raise
    
    def _search_weaviate(self, class_name: str, query_vector: List[float], limit: int) -> List[Dict[str, Any]]:
        """Search in Weaviate."""
        result = (
            self.client.query
            .get(class_name, ["id"])
            .with_near_vector({
                "vector": query_vector
            })
            .with_limit(limit)
            .with_additional(["id", "vector", "distance"])
            .do()
        )
        
        # Extract and format results
        items = result["data"]["Get"][class_name]
        return [
            {
                "id": item["_additional"]["id"],
                "distance": item["_additional"]["distance"],
                "metadata": {k: v for k, v in item.items() if k not in ["_additional"]}
            }
            for item in items
        ]
    
    def _search_qdrant(self, class_name: str, query_vector: List[float], limit: int) -> List[Dict[str, Any]]:
        """Search in Qdrant."""
        from qdrant_client.http import models
        
        result = self.client.search(
            collection_name=class_name.lower(),
            query_vector=query_vector,
            limit=limit
        )
        
        # Format results
        return [
            {
                "id": str(item.id),
                "distance": item.score,
                "metadata": item.payload
            }
            for item in result
        ]
    
    def _search_pinecone(self, class_name: str, query_vector: List[float], limit: int) -> List[Dict[str, Any]]:
        """Search in Pinecone."""
        # Include class filter if specified
        filter = {"_class": {"$eq": class_name}} if class_name else None
        
        result = self.client.query(
            vector=query_vector,
            top_k=limit,
            include_metadata=True,
            filter=filter
        )
        
        # Format results
        return [
            {
                "id": match.id,
                "distance": match.score,
                "metadata": match.metadata
            }
            for match in result.matches
        ]
    
    def delete(self, class_name: str, id: str) -> bool:
        """Delete a document from the vector store.
        
        Args:
            class_name: The class/collection name
            id: The ID of the document to delete
            
        Returns:
            True if successful, False otherwise
        """
        db_type = self.db_type
        
        try:
            if db_type == "weaviate":
                return self._delete_weaviate(class_name, id)
            elif db_type == "qdrant":
                return self._delete_qdrant(class_name, id)
            elif db_type == "pinecone":
                return self._delete_pinecone(id)
        except Exception as e:
            logger.error(f"Failed to delete document from {db_type}: {e}")
            return False
    
    def _delete_weaviate(self, class_name: str, id: str) -> bool:
        """Delete a document from Weaviate."""
        try:
            self.client.data_object.delete(
                class_name=class_name,
                uuid=id
            )
            return True
        except Exception as e:
            logger.error(f"Failed to delete document from Weaviate: {e}")
            return False
    
    def _delete_qdrant(self, class_name: str, id: str) -> bool:
        """Delete a document from Qdrant."""
        try:
            self.client.delete(
                collection_name=class_name.lower(),
                points_selector=[id]
            )
            return True
        except Exception as e:
            logger.error(f"Failed to delete document from Qdrant: {e}")
            return False
    
    def _delete_pinecone(self, id: str) -> bool:
        """Delete a document from Pinecone."""
        try:
            self.client.delete(ids=[id])
            return True
        except Exception as e:
            logger.error(f"Failed to delete document from Pinecone: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get the status of the vector database.
        
        Returns:
            Status information about the vector database
        """
        db_type = self.db_type
        
        try:
            if db_type == "weaviate":
                return self._get_status_weaviate()
            elif db_type == "qdrant":
                return self._get_status_qdrant()
            elif db_type == "pinecone":
                return self._get_status_pinecone()
        except Exception as e:
            logger.error(f"Failed to get status from {db_type}: {e}")
            return {"status": "error", "error": str(e)}
    
    def _get_status_weaviate(self) -> Dict[str, Any]:
        """Get status from Weaviate."""
        try:
            meta = self.client.get_meta()
            schema = self.client.schema.get()
            
            return {
                "status": "ok",
                "type": "weaviate",
                "version": meta["version"],
                "classes": [c["class"] for c in schema["classes"]],
                "class_count": len(schema["classes"]),
                "objects_count": sum(
                    self.client.query.aggregate(c["class"])
                    .with_meta_count()
                    .do()["data"]["Aggregate"][c["class"]][0]["meta"]["count"]
                    for c in schema["classes"]
                )
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _get_status_qdrant(self) -> Dict[str, Any]:
        """Get status from Qdrant."""
        try:
            collections = self.client.get_collections().collections
            collection_info = []
            
            for collection in collections:
                info = self.client.get_collection(collection.name)
                collection_info.append({
                    "name": collection.name,
                    "vectors_count": info.vectors_count,
                    "dimension": info.config.params.vectors.size,
                })
            
            return {
                "status": "ok",
                "type": "qdrant",
                "collections": [c.name for c in collections],
                "collection_count": len(collections),
                "collection_info": collection_info
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _get_status_pinecone(self) -> Dict[str, Any]:
        """Get status from Pinecone."""
        try:
            import pinecone
            
            # Get index stats
            stats = self.client.describe_index_stats()
            
            return {
                "status": "ok",
                "type": "pinecone",
                "namespace_count": len(stats.namespaces),
                "dimensions": self.config["vector_db"]["dimensions"],
                "total_vector_count": stats.total_vector_count,
                "namespaces": [
                    {"name": name, "vector_count": ns.vector_count}
                    for name, ns in stats.namespaces.items()
                ]
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
EOF
    
    echo -e "${GREEN}✓ Vector store client created at ../neural_data_fabric/vector_store.py${NC}"
}

print_usage() {
    echo -e "${YELLOW}AI-Native ERP System - Vector Database Setup Script${NC}"
    echo -e "Usage: $0 [OPTIONS]"
    echo -e "\nOptions:"
    echo -e "  --vector-db TYPE   Specify vector database type (weaviate, pinecone, qdrant)"
    echo -e "  --port PORT        Specify port number for the vector database"
    echo -e "  --dimensions DIM   Specify vector dimensions (default: 1536)"
    echo -e "  --no-docker        Skip Docker container setup"
    echo -e "  --no-schema        Skip schema initialization"
    echo -e "  --api-key KEY      API key for cloud services (required for Pinecone)"
    echo -e "  --help             Display this help message"
}

main() {
    # Parse command line arguments
    parse_arguments "$@"
    
    print_header "AI-Native ERP System - Vector Database Setup"
    echo -e "${YELLOW}Setting up ${VECTOR_DB} vector database for the Neural Data Fabric component.${NC}"
    
    # Check dependencies
    check_dependencies
    
    # Setup the selected vector database
    if [ "$VECTOR_DB" == "weaviate" ]; then
        setup_weaviate
    elif [ "$VECTOR_DB" == "qdrant" ]; then
        setup_qdrant
    elif [ "$VECTOR_DB" == "pinecone" ]; then
        setup_pinecone
    fi
    
    # Initialize schemas
    initialize_schemas
    
    # Create configuration file
    create_config_file
    
    # Create Python client utilities
    create_python_client
    
    echo -e "\n${GREEN}======================================${NC}"
    echo -e "${GREEN}Vector Database Setup Complete!${NC}"
    echo -e "${GREEN}======================================${NC}"
    echo -e "${YELLOW}Vector database type: ${VECTOR_DB}${NC}"
    
    if [ "$VECTOR_DB" == "weaviate" ] || [ "$VECTOR_DB" == "qdrant" ]; then
        echo -e "${YELLOW}Vector database port: ${VECTOR_DB_PORT}${NC}"
    fi
    
    echo -e "${YELLOW}Configuration: ${CONFIG_DIR}/vector_db_config.yaml${NC}"
    echo -e "${YELLOW}Python client: ../neural_data_fabric/vector_store.py${NC}"
    
    echo -e "\n${BLUE}Next steps:${NC}"
    echo -e "1. Import the VectorStore class in your application:"
    echo -e "   ${GREEN}from neural_data_fabric.vector_store import VectorStore${NC}"
    echo -e "2. Create a vector store client:"
    echo -e "   ${GREEN}vector_store = VectorStore()${NC}"
    echo -e "3. Add documents with embeddings to the vector database:"
    echo -e "   ${GREEN}vector_store.add_document('Document', {'title': 'Example'}, [0.1, 0.2, ...])${NC}"
}

# Run the main function with all arguments
main "$@"