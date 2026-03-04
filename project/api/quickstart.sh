#!/bin/bash

# KOISK FastAPI Quick Start Script
# ================================
# This script sets up and runs the KOISK FastAPI backend

set -e

echo "========================================="
echo "KOISK FastAPI Backend - Quick Start"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python installation
echo "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is not installed. Please install Python 3.8 or higher.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python 3 found: $(python3 --version)${NC}"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${YELLOW}! Virtual environment already exists${NC}"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel > /dev/null 2>&1
echo -e "${GREEN}✓ pip upgraded${NC}"
echo ""

# Install dependencies
echo "Installing dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    echo -e "${RED}requirements.txt not found!${NC}"
    exit 1
fi
echo ""

# Create .env file if it doesn't exist
echo "Setting up environment configuration..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${GREEN}✓ Created .env from .env.example${NC}"
    echo -e "${YELLOW}! Please update .env with your configuration${NC}"
else
    echo -e "${YELLOW}! .env already exists, skipping creation${NC}"
fi
echo ""

# Create logs directory
mkdir -p logs
echo -e "${GREEN}✓ Logs directory created${NC}"
echo ""

# Display startup information
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Update .env file with your configuration:"
echo "   - Database URL"
echo "   - Payment gateway credentials"
echo "   - CORS origins for your frontend"
echo ""
echo "2. Start the API:"
echo "   Option A - Development (with auto-reload):"
echo "   ${GREEN}python koisk_api.py${NC}"
echo ""
echo "   Option B - Using uvicorn directly:"
echo "   ${GREEN}uvicorn koisk_api:app --reload --host 0.0.0.0 --port 8000${NC}"
echo ""
echo "   Option C - Using Docker:"
echo "   ${GREEN}docker-compose up${NC}"
echo ""
echo "3. Access the API documentation:"
echo "   ${GREEN}http://localhost:8000/docs${NC}"
echo ""
echo "4. Test the API:"
echo "   ${GREEN}curl http://localhost:8000/health${NC}"
echo ""
echo "========================================="
echo ""

# Ask if user wants to start the server
read -p "Would you like to start the API server now? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Starting KOISK FastAPI Backend..."
    echo "Press Ctrl+C to stop"
    echo ""
    python koisk_api.py
else
    echo "To start the server later, run:"
    echo "  python koisk_api.py"
    echo ""
    echo "Remember to activate the virtual environment first:"
    echo "  source venv/bin/activate"
fi
