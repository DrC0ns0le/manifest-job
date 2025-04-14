#!/bin/bash

# Script to deactivate a Python virtual environment

# Print a message with color
print_message() {
    echo -e "\e[32m$1\e[0m"
}

# Check if we're in a virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    print_message "No active virtual environment detected."
    exit 0
fi

# Store the name of the current virtual environment
VENV_NAME=$(basename "$VIRTUAL_ENV")

# Deactivate the virtual environment
print_message "Deactivating virtual environment: $VENV_NAME..."
deactivate

# Check if deactivation was successful
if [ -z "$VIRTUAL_ENV" ]; then
    print_message "Virtual environment deactivated successfully!"
else
    echo "Error: Failed to deactivate virtual environment"
    exit 1
fi

print_message "Returned to system Python: $(which python)"
