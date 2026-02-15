#!/bin/sh
set -e

# Install dependencies if node_modules is empty or outdated
if [ ! -d "node_modules/@nordlig" ]; then
  echo "Installing dependencies..."
  npm install
fi

exec "$@"
