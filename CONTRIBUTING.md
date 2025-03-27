# Contributing to NeuroERP

## Welcome Contributors! 🚀

NeuroERP is an open-source, AI-native Enterprise Resource Planning system. We welcome contributions from the community!

## 🤝 How to Contribute

### 1. Reporting Issues
- Use GitHub Issues
- Provide detailed description
- Include steps to reproduce
- Mention your environment details

### 2. Feature Requests
- Open a GitHub Issue
- Describe the feature
- Explain the use case
- Provide potential implementation suggestions

## 🛠 Development Setup

### Prerequisites
- Python 3.8+
- Ollama
- Docker (optional)

### Setup Steps
```bash
# Clone the repository
git clone https://github.com/vishalm/neuroerp.git
cd neuroerp

# Create virtual environment
python3 -m venv neuroerp_env
source neuroerp_env/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python manage.py migrate

# Run development server
python run_neuroerp.py
```

## 🧪 Testing

### Running Tests
```bash
# Run all tests
pytest

# Run specific app tests
pytest neuroerp/ai_agents
```

## 📝 Coding Guidelines

### Python Style
- Follow PEP 8
- Use type hints
- Write docstrings
- Use Black for formatting

### Commit Message Convention
- Use conventional commits
- Format: `<type>(<scope>): <description>`
- Types: 
  - `feat`: New feature
  - `fix`: Bug fix
  - `docs`: Documentation
  - `style`: Code formatting
  - `refactor`: Code refactoring
  - `test`: Adding tests
  - `chore`: Maintenance tasks

## 🤖 AI Agent Development

### Creating New Agents
1. Create a new service in `neuroerp/ai_agents/services/`
2. Implement agent logic using `OllamaService`
3. Add views and URLs
4. Write comprehensive tests

## 🔒 Security

- Never commit sensitive information
- Use environment variables
- Follow principle of least privilege

## 🏆 Code of Conduct

- Be respectful
- Collaborate constructively
- Welcome diverse perspectives

## 📄 License

By contributing, you agree to license your changes under the MIT License.

## 🙌 Recognition

All contributors will be recognized in our CONTRIBUTORS.md file!