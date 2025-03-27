#!/bin/bash

# AI-Native ERP System - Ollama Setup Script
# This script sets up Ollama with the required models for the ERP system
# It handles installation, model pulling, and basic configuration

set -e  # Exit on any error

# Color formatting for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Required models for different ERP components
FINANCE_MODEL="llama3:latest"
HR_MODEL="llama3:latest"
SUPPLY_CHAIN_MODEL="mistral:latest"
OPERATIONS_MODEL="orca2:latest"
GENERAL_MODEL="mixtral:latest"  # For general queries and orchestration

# Ollama configuration
OLLAMA_HOST="localhost"
OLLAMA_PORT="11434"

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
    
    # Check for jq (for JSON parsing)
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
}

install_ollama() {
    print_header "Installing Ollama"
    
    # Check if Ollama is already installed
    if command -v ollama &> /dev/null; then
        echo -e "${GREEN}Ollama is already installed. Checking version...${NC}"
        OLLAMA_VERSION=$(ollama --version)
        echo -e "Current version: ${YELLOW}$OLLAMA_VERSION${NC}"
        
        read -p "Do you want to reinstall Ollama? (y/n): " REINSTALL
        if [[ $REINSTALL != "y" && $REINSTALL != "Y" ]]; then
            echo -e "${GREEN}Skipping Ollama installation.${NC}"
            return
        fi
    fi
    
    echo -e "${YELLOW}Installing Ollama...${NC}"
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        curl -fsSL https://ollama.com/install.sh | sh
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # For macOS, download the app
        echo -e "${YELLOW}For macOS, please download Ollama from https://ollama.com/download/mac${NC}"
        echo -e "${YELLOW}After installation, please run this script again.${NC}"
        exit 0
    else
        echo -e "${RED}Unsupported OS. Please install Ollama manually from https://ollama.com${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Ollama installed successfully${NC}"
}

start_ollama_service() {
    print_header "Starting Ollama Service"
    
    # Check if Ollama service is running
    if curl -s http://$OLLAMA_HOST:$OLLAMA_PORT/api/version &> /dev/null; then
        echo -e "${GREEN}✓ Ollama service is already running${NC}"
    else
        echo -e "${YELLOW}Starting Ollama service...${NC}"
        
        # Different ways to start Ollama based on installation method
        if command -v systemctl &> /dev/null && systemctl is-active --quiet ollama.service; then
            sudo systemctl start ollama.service
        elif command -v ollama &> /dev/null; then
            # Start in background
            nohup ollama serve > ollama.log 2>&1 &
            echo $! > ollama.pid
            echo -e "${YELLOW}Waiting for Ollama service to start...${NC}"
            sleep 5  # Give it some time to start
        else
            echo -e "${RED}Could not start Ollama service. Please start it manually.${NC}"
            exit 1
        fi
        
        # Verify that the service has started
        if curl -s http://$OLLAMA_HOST:$OLLAMA_PORT/api/version &> /dev/null; then
            echo -e "${GREEN}✓ Ollama service started successfully${NC}"
        else
            echo -e "${RED}Failed to start Ollama service. Check ollama.log for details.${NC}"
            exit 1
        fi
    fi
}

pull_models() {
    print_header "Pulling Required Models"
    
    # Function to pull a model with progress tracking
    pull_model() {
        MODEL=$1
        PURPOSE=$2
        
        echo -e "${YELLOW}Pulling $MODEL for $PURPOSE...${NC}"
        
        # Check if model is already pulled
        if curl -s http://$OLLAMA_HOST:$OLLAMA_PORT/api/tags | jq -r '.models[].name' | grep -q "^$MODEL$"; then
            echo -e "${GREEN}✓ Model $MODEL already exists${NC}"
        else
            # Pull the model
            ollama pull $MODEL
            
            # Verify model was pulled successfully
            if curl -s http://$OLLAMA_HOST:$OLLAMA_PORT/api/tags | jq -r '.models[].name' | grep -q "^$MODEL$"; then
                echo -e "${GREEN}✓ Successfully pulled $MODEL${NC}"
            else
                echo -e "${RED}Failed to pull $MODEL. Please check your network connection and try again.${NC}"
                exit 1
            fi
        fi
    }
    
    # Pull all required models
    pull_model "$FINANCE_MODEL" "Finance Agents"
    pull_model "$HR_MODEL" "HR Agents"
    pull_model "$SUPPLY_CHAIN_MODEL" "Supply Chain Agents"
    pull_model "$OPERATIONS_MODEL" "Operations Agents"
    pull_model "$GENERAL_MODEL" "General Orchestration"
}

configure_ollama() {
    print_header "Configuring Ollama for ERP System"
    
    # Create the Ollama config directory if it doesn't exist
    mkdir -p "${HOME}/.ollama"
    
    # Create or update Ollama configuration
    echo -e "${YELLOW}Setting up Ollama configuration...${NC}"
    
    # Create configuration file for our ERP system
    CONFIG_DIR="../config"
    mkdir -p $CONFIG_DIR
    
    cat > $CONFIG_DIR/ollama_config.yaml << EOF
# Ollama Configuration for AI-Native ERP System
ollama:
  host: ${OLLAMA_HOST}
  port: ${OLLAMA_PORT}
  models:
    finance: ${FINANCE_MODEL}
    hr: ${HR_MODEL}
    supply_chain: ${SUPPLY_CHAIN_MODEL}
    operations: ${OPERATIONS_MODEL}
    general: ${GENERAL_MODEL}
  parameters:
    default:
      num_ctx: 4096
      num_gpu: 1
      num_thread: 4
    finance:
      num_ctx: 8192
      temperature: 0.1
    hr:
      temperature: 0.7
    supply_chain:
      temperature: 0.2
    operations:
      temperature: 0.3
EOF
    
    echo -e "${GREEN}✓ Ollama configuration created at $CONFIG_DIR/ollama_config.yaml${NC}"
}

create_modelfiles() {
    print_header "Creating Specialized Modelfiles"
    
    # Create modelfile directory
    MODELFILE_DIR="modelfiles"
    mkdir -p $MODELFILE_DIR
    
    # Create Finance Agent Modelfile with specialized system prompt
    cat > $MODELFILE_DIR/finance.modelfile << EOF
FROM ${FINANCE_MODEL}

# System prompt for Finance agent
SYSTEM """
You are a specialized financial analysis AI for an Enterprise Resource Planning system.
Your role is to:
1. Analyze financial data and provide insights
2. Detect anomalies in financial transactions
3. Forecast financial trends based on historical data
4. Optimize financial resource allocation
5. Ensure compliance with accounting standards and regulations

Always provide concise, accurate financial analysis with appropriate justification.
"""

# Parameter adjustments for financial precision
PARAMETER temperature 0.1
PARAMETER num_ctx 8192
EOF
    
    # Create HR Agent Modelfile
    cat > $MODELFILE_DIR/hr.modelfile << EOF
FROM ${HR_MODEL}

# System prompt for HR agent
SYSTEM """
You are a specialized Human Resources AI for an Enterprise Resource Planning system.
Your role is to:
1. Analyze employee data to identify patterns and trends
2. Assist with recruitment by evaluating candidate profiles
3. Identify skill gaps and suggest training opportunities
4. Monitor employee satisfaction and engagement
5. Ensure compliance with labor laws and regulations

Always maintain employee privacy and confidentiality while providing helpful insights.
"""

# Parameter adjustments for HR tasks
PARAMETER temperature 0.7
PARAMETER num_ctx 4096
EOF
    
    echo -e "${GREEN}✓ Created specialized modelfiles in $MODELFILE_DIR/${NC}"
    
    # Option to create the specialized models
    read -p "Do you want to create the specialized models now? This may take some time. (y/n): " CREATE_MODELS
    if [[ $CREATE_MODELS == "y" || $CREATE_MODELS == "Y" ]]; then
        echo -e "${YELLOW}Creating finance model...${NC}"
        ollama create finance -f $MODELFILE_DIR/finance.modelfile
        
        echo -e "${YELLOW}Creating HR model...${NC}"
        ollama create hr -f $MODELFILE_DIR/hr.modelfile
        
        echo -e "${GREEN}✓ Specialized models created successfully${NC}"
    else
        echo -e "${YELLOW}Skipping model creation. You can create them later with:${NC}"
        echo -e "  ollama create finance -f $MODELFILE_DIR/finance.modelfile"
        echo -e "  ollama create hr -f $MODELFILE_DIR/hr.modelfile"
    fi
}

test_ollama() {
    print_header "Testing Ollama Setup"
    
    # Test connection to Ollama API
    echo -e "${YELLOW}Testing connection to Ollama API...${NC}"
    if RESPONSE=$(curl -s http://$OLLAMA_HOST:$OLLAMA_PORT/api/version); then
        VERSION=$(echo $RESPONSE | jq -r '.version')
        echo -e "${GREEN}✓ Connected to Ollama API (Version: $VERSION)${NC}"
    else
        echo -e "${RED}Failed to connect to Ollama API${NC}"
        exit 1
    fi
    
    # Test model generation
    echo -e "${YELLOW}Testing model generation...${NC}"
    TEST_MODEL=$GENERAL_MODEL
    TEST_PROMPT="Briefly explain what an ERP system is."
    
    echo -e "${YELLOW}Sending test prompt to $TEST_MODEL...${NC}"
    if RESPONSE=$(curl -s -X POST http://$OLLAMA_HOST:$OLLAMA_PORT/api/generate -d "{\"model\": \"$TEST_MODEL\", \"prompt\": \"$TEST_PROMPT\", \"stream\": false}"); then
        if echo $RESPONSE | jq -e '.response' > /dev/null; then
            echo -e "${GREEN}✓ Model generation successful${NC}"
            echo -e "${BLUE}Model response:${NC}"
            echo $RESPONSE | jq -r '.response' | head -n 5
            echo "..."
        else
            echo -e "${RED}Failed to generate response:${NC}"
            echo $RESPONSE | jq -r '.error'
            exit 1
        fi
    else
        echo -e "${RED}Failed to connect to Ollama API for generation${NC}"
        exit 1
    fi
}

cleanup() {
    print_header "Cleaning Up"
    
    # Clean up any temporary files
    if [ -f ollama.pid ]; then
        echo -e "${YELLOW}Note: Ollama is running as a background process.${NC}"
        echo -e "${YELLOW}To stop it, run: kill $(cat ollama.pid)${NC}"
    fi
    
    echo -e "${GREEN}✓ Setup completed successfully${NC}"
}

print_usage() {
    echo -e "${YELLOW}AI-Native ERP System - Ollama Setup Script${NC}"
    echo -e "Usage: $0 [OPTIONS]"
    echo -e "\nOptions:"
    echo -e "  --help        Display this help message"
    echo -e "  --no-install  Skip Ollama installation, use existing installation"
    echo -e "  --models-only Pull models only, skip other steps"
}

# Main execution
main() {
    # Check if help is requested
    if [[ "$1" == "--help" ]]; then
        print_usage
        exit 0
    fi
    
    print_header "AI-Native ERP System - Ollama Setup"
    echo -e "${YELLOW}This script will set up Ollama with the required models for the ERP system.${NC}"
    
    # Check if only models should be pulled
    if [[ "$1" == "--models-only" ]]; then
        start_ollama_service
        pull_models
        echo -e "${GREEN}✓ Models setup completed successfully${NC}"
        exit 0
    fi
    
    # Check if installation should be skipped
    if [[ "$1" != "--no-install" ]]; then
        check_dependencies
        install_ollama
    else
        echo -e "${YELLOW}Skipping Ollama installation as requested.${NC}"
    fi
    
    start_ollama_service
    pull_models
    configure_ollama
    create_modelfiles
    test_ollama
    cleanup
    
    echo -e "\n${GREEN}======================================${NC}"
    echo -e "${GREEN}Ollama is now set up and ready for use with the AI-Native ERP System!${NC}"
    echo -e "${GREEN}======================================${NC}"
}

# Run the main function with all arguments
main "$@"