#!/bin/bash

# OpenCode Chat - Setup and Run Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
VENV_DIR="$PROJECT_DIR/.venv"

echo "========================================"
echo "  OpenCode Chat - Setup & Run"
echo "========================================"

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

create_venv() {
    echo -e "\n${YELLOW}[1/3] Creating virtual environment...${NC}"
    
    if [ -d "$VENV_DIR" ]; then
        echo "Virtual environment already exists"
    else
        python3 -m venv "$VENV_DIR"
        echo "Virtual environment created at: $VENV_DIR"
    fi
}

install_deps() {
    echo -e "\n${YELLOW}[2/3] Installing dependencies...${NC}"
    
    source "$VENV_DIR/bin/activate"
    
    # Fix for corporate proxy/TLS issues
    unset HTTPS_PROXY
    unset HTTP_PROXY
    
    pip install --upgrade pip --trusted-host pypi.org --trusted-host files.pythonhosted.org -q 2>/dev/null || true
    pip install httpx --trusted-host pypi.org --trusted-host files.pythonhosted.org -q 2>/dev/null || true
    
    echo "Dependencies installed"
}

run_chat() {
    echo -e "\n${YELLOW}[3/3] Starting OpenCode Chat...${NC}"
    echo -e "${GREEN}========================================${NC}\n"
    
    source "$VENV_DIR/bin/activate"
    
    cd "$PROJECT_DIR"
    python src/main.py
}

# Parse arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [options]"
        echo ""
        echo "Options:"
        echo "  --help     Show this help message"
        echo "  --recreate Recreate virtual environment"
        echo "  --no-setup Run without recreating venv"
        echo ""
        echo "Examples:"
        echo "  $0              # Setup and run"
        echo "  $0 --recreate    # Recreate venv and run"
        echo "  $0 --no-setup    # Run without setup"
        exit 0
        ;;
    --recreate)
        echo "Recreating virtual environment..."
        rm -rf "$VENV_DIR"
        create_venv
        install_deps
        run_chat
        ;;
    --no-setup)
        echo "Skipping setup, running chat..."
        run_chat
        ;;
    *)
        if [ ! -d "$VENV_DIR" ]; then
            create_venv
        fi
        install_deps
        run_chat
        ;;
esac
