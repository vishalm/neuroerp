#!/bin/bash

# Define the base directory
BASE_DIR="ai-native-erp"

# Define the folder structure
DIRECTORIES=(
    "$BASE_DIR/core"
    "$BASE_DIR/agents/finance"
    "$BASE_DIR/agents/hr"
    "$BASE_DIR/agents/supply_chain"
    "$BASE_DIR/data/connectors"
    "$BASE_DIR/orchestration/workflow_templates"
    "$BASE_DIR/interfaces/api"
    "$BASE_DIR/interfaces/chat"
    "$BASE_DIR/interfaces/web/static"
    "$BASE_DIR/interfaces/web/templates"
    "$BASE_DIR/security"
    "$BASE_DIR/models/prompts"
    "$BASE_DIR/infrastructure"
    "$BASE_DIR/tests/unit"
    "$BASE_DIR/tests/integration"
    "$BASE_DIR/examples"
)

# Define the files to be created
FILES=(
    "$BASE_DIR/docker-compose.yml"
    "$BASE_DIR/.env"
    "$BASE_DIR/README.md"
    "$BASE_DIR/ollama.json"
    "$BASE_DIR/.gitignore"
    "$BASE_DIR/core/__init__.py"
    "$BASE_DIR/core/config.py"
    "$BASE_DIR/core/ai_engine.py"
    "$BASE_DIR/core/neural_fabric.py"
    "$BASE_DIR/core/event_bus.py"
    "$BASE_DIR/agents/__init__.py"
    "$BASE_DIR/agents/base_agent.py"
    "$BASE_DIR/agents/finance/__init__.py"
    "$BASE_DIR/agents/finance/accounting_agent.py"
    "$BASE_DIR/agents/finance/forecasting_agent.py"
    "$BASE_DIR/agents/hr/__init__.py"
    "$BASE_DIR/agents/hr/recruitment_agent.py"
    "$BASE_DIR/agents/hr/employee_agent.py"
    "$BASE_DIR/agents/supply_chain/__init__.py"
    "$BASE_DIR/agents/supply_chain/inventory_agent.py"
    "$BASE_DIR/agents/supply_chain/logistics_agent.py"
    "$BASE_DIR/data/__init__.py"
    "$BASE_DIR/data/vector_store.py"
    "$BASE_DIR/data/knowledge_graph.py"
    "$BASE_DIR/data/connectors/__init__.py"
    "$BASE_DIR/data/connectors/sql_connector.py"
    "$BASE_DIR/data/connectors/api_connector.py"
    "$BASE_DIR/orchestration/__init__.py"
    "$BASE_DIR/orchestration/workflow_engine.py"
    "$BASE_DIR/orchestration/task_scheduler.py"
    "$BASE_DIR/orchestration/workflow_templates/__init__.py"
    "$BASE_DIR/orchestration/workflow_templates/procurement.py"
    "$BASE_DIR/orchestration/workflow_templates/onboarding.py"
    "$BASE_DIR/interfaces/__init__.py"
    "$BASE_DIR/interfaces/api/__init__.py"
    "$BASE_DIR/interfaces/api/routes.py"
    "$BASE_DIR/interfaces/api/middleware.py"
    "$BASE_DIR/interfaces/chat/__init__.py"
    "$BASE_DIR/interfaces/chat/chat_engine.py"
    "$BASE_DIR/interfaces/chat/prompt_templates.py"
    "$BASE_DIR/interfaces/web/app.py"
    "$BASE_DIR/security/__init__.py"
    "$BASE_DIR/security/auth.py"
    "$BASE_DIR/security/identity.py"
    "$BASE_DIR/security/compliance.py"
    "$BASE_DIR/models/Modelfile.finance"
    "$BASE_DIR/models/Modelfile.hr"
    "$BASE_DIR/models/Modelfile.supply_chain"
    "$BASE_DIR/models/prompts/system_prompts.py"
    "$BASE_DIR/models/prompts/few_shot_examples.py"
    "$BASE_DIR/infrastructure/ollama_setup.sh"
    "$BASE_DIR/infrastructure/vector_db_setup.sh"
    "$BASE_DIR/infrastructure/monitoring.py"
    "$BASE_DIR/tests/unit/test_agents.py"
    "$BASE_DIR/tests/unit/test_neural_fabric.py"
    "$BASE_DIR/tests/integration/test_workflows.py"
    "$BASE_DIR/tests/integration/test_ai_processing.py"
    "$BASE_DIR/examples/finance_workflow.py"
    "$BASE_DIR/examples/hr_onboarding.py"
    "$BASE_DIR/examples/supply_chain_optimization.py"
)

# Create directories
for dir in "${DIRECTORIES[@]}"; do
    mkdir -p "$dir"
    echo "Created directory: $dir"
done

# Create files
for file in "${FILES[@]}"; do
    touch "$file"
    echo "Created file: $file"
done

echo "Folder structure created successfully."

