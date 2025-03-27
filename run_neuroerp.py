#!/usr/bin/env python
"""
NeuroERP Startup Script

This script provides multiple ways to run the NeuroERP application
with additional configuration and AI agent initialization.
"""

import os
import sys
import subprocess
import argparse
import multiprocessing
from dotenv import load_dotenv

# Ensure the project root is in Python path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

def check_dependencies():
    """
    Check and verify system dependencies
    """
    dependencies = [
        'django', 'ollama', 'torch', 'requests', 
        'transformers', 'python-dotenv'
    ]
    missing_deps = []
    
    for dep in dependencies:
        try:
            __import__(dep)
        except ImportError:
            missing_deps.append(dep)
    
    if missing_deps:
        print("Missing dependencies:")
        for dep in missing_deps:
            print(f" - {dep}")
        print("\nPlease install requirements: pip install -r requirements.txt")
        sys.exit(1)
    
    # Check Ollama installation
    try:
        subprocess.run(['ollama', '--version'], 
                       capture_output=True, 
                       text=True, 
                       check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Ollama is not installed. Please install from https://ollama.ai")
        sys.exit(1)

def initialize_ollama_models():
    """
    Pre-pull and initialize recommended Ollama models
    """
    recommended_models = ['llama2:13b', 'mistral:7b', 'openhermes:7b']
    
    for model in recommended_models:
        try:
            print(f"Pulling Ollama model: {model}")
            result = subprocess.run(
                ['ollama', 'pull', model], 
                capture_output=True, 
                text=True
            )
            if result.returncode == 0:
                print(f"Successfully pulled {model}")
            else:
                print(f"Warning: Could not pull {model}")
                print(result.stderr)
        except Exception as e:
            print(f"Error pulling {model}: {e}")

def run_django_server(host='127.0.0.1', port=8000, debug=False):
    """
    Run Django development server
    """
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neuroerp.settings')
    
    # Set debug mode in environment
    if debug:
        os.environ['DEBUG'] = 'True'
    
    from django.core.management import execute_from_command_line
    
    # Construct Django management command
    sys.argv = [
        'manage.py', 
        'runserver', 
        f'{host}:{port}',
        *(['--insecure'] if debug else [])
    ]
    
    print(f"🌐 Starting NeuroERP Django Server on {host}:{port}")
    if debug:
        print("⚠️  Running in DEBUG mode")
    
    execute_from_command_line(sys.argv)

def run_ai_service():
    """
    Start dedicated AI service for background processing
    """
    from neuroerp.ai_agents.services.ollama_service import OllamaService
    
    print("🤖 Starting NeuroERP AI Service")
    print("Available AI Models:")
    service = OllamaService()
    models = service.list_models()
    
    if not models:
        print("No Ollama models found. Please pull models first.")
        return
    
    for model in models:
        print(f" - {model}")
    
    # Here you could add more sophisticated background processing
    # such as periodic model training, data preprocessing, etc.
    try:
        while True:
            # Keep the service running
            import time
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\n🛑 AI Service Stopped")

def migrate_database():
    """
    Run database migrations
    """
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neuroerp.settings')
    
    from django.core.management import execute_from_command_line
    
    print("🗄️ Running Database Migrations")
    sys.argv = ['manage.py', 'migrate']
    execute_from_command_line(sys.argv)

def create_superuser():
    """
    Create a superuser for admin access
    """
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neuroerp.settings')
    
    from django.core.management import execute_from_command_line
    
    print("👤 Creating Superuser")
    sys.argv = ['manage.py', 'createsuperuser']
    execute_from_command_line(sys.argv)

def main():
    """
    Main entry point for NeuroERP
    """
    # Load environment variables
    load_dotenv()
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='NeuroERP Startup Script')
    parser.add_argument(
        '--mode', 
        choices=['server', 'ai-service', 'all', 'migrate', 'superuser'], 
        default='all', 
        help='Run specific NeuroERP components'
    )
    parser.add_argument(
        '--host', 
        default='127.0.0.1', 
        help='Host for Django server'
    )
    parser.add_argument(
        '--port', 
        type=int, 
        default=8000, 
        help='Port for Django server'
    )
    parser.add_argument(
        '--debug', 
        action='store_true', 
        help='Run in debug mode'
    )
    
    args = parser.parse_args()
    
    # Dependency and environment checks
    check_dependencies()
    
    # Initialize Ollama models
    initialize_ollama_models()
    
    # Multiprocessing for different modes
    if args.mode == 'migrate':
        migrate_database()
        return
    
    if args.mode == 'superuser':
        create_superuser()
        return
    
    # Processes to run based on mode
    processes = []
    
    if args.mode in ['server', 'all']:
        # Django server process
        server_process = multiprocessing.Process(
            target=run_django_server, 
            kwargs={
                'host': args.host, 
                'port': args.port, 
                'debug': args.debug
            }
        )
        processes.append(server_process)
    
    if args.mode in ['ai-service', 'all']:
        # AI service process
        ai_service_process = multiprocessing.Process(
            target=run_ai_service
        )
        processes.append(ai_service_process)
    
    # Start all processes
    for p in processes:
        p.start()
    
    # Wait for all processes
    for p in processes:
        p.join()

if __name__ == '__main__':
    main()