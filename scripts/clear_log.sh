#!/bin/bash

log_dir="./app/logs"

# Change to the log directory
cd "$log_dir" || exit

# Clear all log files except .gitkeep
find . -type f ! -name ".gitkeep" -exec rm -f {} +

echo "Log files cleared successfully."