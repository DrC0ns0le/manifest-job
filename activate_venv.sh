#!/bin/bash

# Script to create and activate a Python virtual environment

# Configuration
VENV_NAME="venv"
PROJECT_DIR="$(pwd)"
VENV_PATH="${PROJECT_DIR}/${VENV_NAME}"

# Print a message with color
print_message() {
    echo -e "\e[32m$1\e[0m"
}

# Check if virtualenv is already installed
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed or not in PATH"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_PATH" ]; then
    print_message "Creating virtual environment at ${VENV_PATH}..."
    python3 -m venv "$VENV_PATH"
    
    if [ $? -ne 0 ]; then
        echo "Error: Failed to create virtual environment"
        exit 1
    fi
    
    print_message "Virtual environment created successfully!"
else
    print_message "Virtual environment already exists at ${VENV_PATH}"
fi

# Activate the virtual environment
print_message "Activating virtual environment..."
source "${VENV_PATH}/bin/activate"

# Check if activation was successful
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Error: Failed to activate virtual environment"
    exit 1
fi

print_message "Virtual environment activated successfully!"
print_message "Python version: $(python --version)"
print_message "Python interpreter: $(which python)"
print_message "To install dependencies, use: pip install -r requirements.txt (if available)"
print_message "When finished working, run: ./deactivate_venv.sh or simply type 'deactivate'"

# Show the prompt to indicate that the virtual environment is activated
PS1="($VENV_NAME) $PS1"
