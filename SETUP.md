# NeuroERP Setup Guide

## 🖥️ Prerequisites

### System Requirements
- Operating System: Linux (Ubuntu 20.04+), macOS (Catalina+), Windows 10/11
- Python 3.8 or higher
- Minimum 16GB RAM (32GB recommended)
- CUDA-compatible GPU (optional but recommended)
- 50GB free disk space

### Software Dependencies
- Python 3.8+
- pip (Python package manager)
- Ollama
- Docker (optional)
- Git

## 🔧 Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/vishalm/neuroerp.git
cd neuroerp
```

### 2. Set Up Virtual Environment

```bash
# Create virtual environment
python3 -m venv neuroerp_env

# Activate virtual environment
# On Unix/macOS:
source neuroerp_env/bin/activate
# On Windows:
neuroerp_env\Scripts\activate
```

### 3. Install Ollama

#### Linux/macOS
```bash
curl https://ollama.ai/install.sh | sh
```

#### Windows
- Download and run the Ollama installer from the official website
- Follow the installation wizard

### 4. Pull Recommended Ollama Models

```bash
ollama pull llama2:13b
ollama pull mistral:7b
ollama pull openhermes:7b
```

### 5. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 6. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# .env file
OLLAMA_API_BASE=http://localhost:11434
DEFAULT_MODEL=llama2:13b
LOG_LEVEL=INFO
```

### 7. Initialize Database and Migrations

```bash
# Run database migrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser
```

### 8. Start the Development Server

```bash
# Run the main application
python manage.py runserver

# Or with Ollama integration
python run_neuroerp.py
```

## 🐳 Docker Deployment (Optional)

### Build Docker Image
```bash
docker build -t neuroerp .
```

### Run Docker Container
```bash
docker run -p 8000:8000 \
  -e OLLAMA_API_BASE=http://host.docker.internal:11434 \
  neuroerp
```

## 🔬 Troubleshooting

### Common Issues
- **Model Loading Failures**: Ensure Ollama is running and models are pulled
- **Dependency Conflicts**: Use the exact versions in `requirements.txt`
- **Performance Issues**: Verify GPU drivers and CUDA compatibility

### Logging
Check application logs for detailed error information:
```bash
tail -f logs/neuroerp.log
```

## 🛠️ Advanced Configuration

### Custom Model Configuration
Edit `config/model_settings.yaml` to customize model parameters:

```yaml
default_model: 
  name: llama2:13b
  max_tokens: 4096
  temperature: 0.7
  
alternative_models:
  - mistral:7b
  - openhermes:7b
```

## 🔒 Security Recommendations

- Keep `.env` file secure and out of version control
- Use strong, unique passwords
- Regularly update dependencies
- Enable two-factor authentication for admin access

## 🤝 Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## 📄 License

This project is licensed under the MIT License. See [LICENSE.md](LICENSE.md) for details.