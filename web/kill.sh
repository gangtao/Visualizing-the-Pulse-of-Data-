#!/bin/bash

# Check if the process name is provided as an argument
if [ $# -ne 1 ]; then
    echo "Usage: $0 <process_name>"
    exit 1
fi

# Get the process name from the command line argument
process_name=$1

# Use pkill to kill processes matching the specified name
pkill -9 -f "$process_name"

# Check if any processes were killed
if [ $? -eq 0 ]; then
    echo "Processes containing '$process_name' in their name killed successfully."
else
    echo "No processes containing '$process_name' in their name found."
fi
