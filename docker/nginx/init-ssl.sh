#!/bin/bash
# Simple SSL certificate setup using domains from .env file
# Usage: ./init-ssl.sh [EMAIL]

# Determine the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Load variables from .env file if it exists
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
elif [ -f ../../.env ]; then
  export $(grep -v '^#' ../../.env | xargs)
fi

# Use email from argument or .env
email=${1:-$EMAIL}

if [ -z "$email" ]; then
  echo "Error: EMAIL is not set!" >&2
  echo "Please either:" >&2
  echo "1. Set EMAIL in your .env file: EMAIL=your@email.com" >&2
  echo "2. Pass email as argument: ./init-ssl.sh your@email.com" >&2
  exit 1
fi

# Check if we have domains configured
if [ -n "$DOMAINS" ]; then
  echo "🔧 Setting up SSL certificates for domains from .env: $DOMAINS"
  ./init-letsencrypt-multi.sh "$DOMAINS" "$email"
elif [ -n "$DOMAIN" ]; then
  echo "🔧 Setting up SSL certificate for domain from .env: $DOMAIN"
  ./init-letsencrypt-multi.sh "$DOMAIN" "$email"
else
  echo "❌ Error: No domains configured in .env file!" >&2
  echo "" >&2
  echo "Please add one of these to your .env file:" >&2
  echo "" >&2
  echo "Option 1 - Multiple domains (recommended):" >&2
  echo "DOMAINS=api.prod.kiwiq.ai,kq-prefect-server.prod.kiwiq.ai" >&2
  echo "" >&2
  echo "Option 2 - Single domain:" >&2
  echo "DOMAIN=api.prod.kiwiq.ai" >&2
  echo "" >&2
  exit 1
fi
