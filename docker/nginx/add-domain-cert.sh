#!/bin/bash
# Add a new domain to existing Let's Encrypt certificate
# Usage: ./add-domain-cert.sh kq-prefect-server.prod.kiwiq.ai your@email.com

# Determine the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Load variables from .env file if it exists
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
elif [ -f ../../.env ]; then
  export $(grep -v '^#' ../../.env | xargs)
fi

if ! [ -x "$(command -v docker-compose)" ]; then
  echo 'Error: docker-compose is not installed.' >&2
  exit 1
fi

# Read new domain and email from command-line args, or use .env
new_domain=${1}
email=${2:-$EMAIL}

# Determine primary domain from .env
if [ -n "$DOMAINS" ]; then
  # Extract first domain from DOMAINS list as primary
  primary_domain=$(echo "$DOMAINS" | cut -d',' -f1)
elif [ -n "$DOMAIN" ]; then
  primary_domain="$DOMAIN"
else
  primary_domain="api.prod.kiwiq.ai"  # fallback
fi

if [ -z "$new_domain" ]; then
  echo "Error: New domain not provided!" >&2
  echo "Usage: ./add-domain-cert.sh NEW_DOMAIN [EMAIL]" >&2
  echo "Example: ./add-domain-cert.sh kq-prefect-server.prod.kiwiq.ai" >&2
  echo "" >&2
  echo "Alternatively, add the domain to DOMAINS in your .env file and run init-letsencrypt-multi.sh" >&2
  exit 1
fi

if [ -z "$email" ]; then
  echo "Error: EMAIL is not set. Please provide email as second argument or set EMAIL environment variable." >&2
  exit 1
fi

echo "Primary domain: $primary_domain"
echo "Adding domain: $new_domain"
echo "Email: $email"

BASE_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
data_path="$BASE_DIR/docker/nginx/data/certbot"
compose_file="$BASE_DIR/docker-compose.prod.yml"

# Check if primary certificate exists
if [ ! -d "$data_path/conf/live/$primary_domain" ]; then
  echo "Error: No existing certificate found for primary domain $primary_domain" >&2
  echo "Please run init-letsencrypt-multi.sh first to create the initial certificate." >&2
  exit 1
fi

echo "### Adding $new_domain to existing certificate for $primary_domain ..."

# Get all existing domains from the certificate
existing_domains=$(docker-compose -f "$compose_file" exec certbot openssl x509 -in /etc/letsencrypt/live/$primary_domain/fullchain.pem -noout -text | grep -A1 "Subject Alternative Name" | tail -1 | tr ',' '\n' | sed 's/DNS://g' | tr -d ' ' | tr '\n' ',' | sed 's/,$//')

if [ -z "$existing_domains" ]; then
  # Fallback: just use primary domain
  existing_domains="$primary_domain"
fi

echo "Existing domains in certificate: $existing_domains"

# Create combined domain list
all_domains="$existing_domains,$new_domain"

echo "New combined domain list: $all_domains"

# Convert comma-separated domains to array for certbot arguments
IFS=',' read -ra DOMAIN_ARRAY <<< "$all_domains"

# Build domain arguments for certbot
domain_args=""
for domain in "${DOMAIN_ARRAY[@]}"; do
  if [ ! -z "$domain" ]; then
    domain_args="$domain_args -d $domain"
  fi
done

echo "Domain arguments: $domain_args"

# Request updated Let's Encrypt certificate
echo "### Requesting updated Let's Encrypt certificate..."

docker-compose -f "$compose_file" run --rm --entrypoint "\
  certbot certonly --webroot -w /var/www/certbot \
    --email $email \
    $domain_args \
    --rsa-key-size 4096 \
    --agree-tos \
    --force-renewal" certbot

if [ $? -eq 0 ]; then
  echo
  echo "### Reloading nginx ..."
  docker-compose -f "$compose_file" exec nginx nginx -s reload
  
  echo
  echo "### Domain addition complete!"
  echo "Your certificate now covers:"
  for domain in "${DOMAIN_ARRAY[@]}"; do
    if [ ! -z "$domain" ]; then
      echo "  - $domain"
    fi
  done
  echo
  echo "Make sure DNS A record exists: $new_domain → YOUR_SERVER_IP"
  echo "Test your new domain: https://$new_domain"
else
  echo
  echo "### Certificate renewal failed!"
  echo "Please check:"
  echo "1. DNS A record exists: $new_domain → YOUR_SERVER_IP"
  echo "2. Port 80 is accessible from the internet"
  echo "3. Nginx is properly configured for the new domain"
  exit 1
fi
