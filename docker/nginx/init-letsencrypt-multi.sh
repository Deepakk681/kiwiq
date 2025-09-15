#!/bin/bash
# Multi-domain Let's Encrypt certificate setup
# Usage: ./init-letsencrypt-multi.sh "api.prod.kiwiq.ai,kq-prefect-server.prod.kiwiq.ai" your@email.com

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

# Read domains and email from command-line args, or use defaults from environment
# Priority: Command line args > DOMAINS env var > DOMAIN env var
if [ -n "$1" ]; then
  domains="$1"
elif [ -n "$DOMAINS" ]; then
  domains="$DOMAINS"
elif [ -n "$DOMAIN" ]; then
  domains="$DOMAIN"
else
  domains=""
fi

email=${2:-$EMAIL}

if [ -z "$domains" ]; then
  echo "Error: No domains specified!" >&2
  echo "Please either:" >&2
  echo "1. Set DOMAINS in your .env file (comma-separated): DOMAINS=api.prod.kiwiq.ai,kq-prefect-server.prod.kiwiq.ai" >&2
  echo "2. Set DOMAIN in your .env file (single domain): DOMAIN=api.prod.kiwiq.ai" >&2
  echo "3. Pass domains as argument: ./init-letsencrypt-multi.sh 'api.prod.kiwiq.ai,kq-prefect-server.prod.kiwiq.ai'" >&2
  exit 1
fi

if [ -z "$email" ]; then
  echo "Error: EMAIL is not set. Please provide email as second argument or set EMAIL environment variable." >&2
  exit 1
fi

# Convert comma-separated domains to array
IFS=',' read -ra DOMAIN_ARRAY <<< "$domains"
primary_domain="${DOMAIN_ARRAY[0]}"

# Print configuration for verification
echo "Primary domain: $primary_domain"
echo "All domains: $domains"
echo "Email: $email"

rsa_key_size=4096
BASE_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
data_path="$BASE_DIR/docker/nginx/data/certbot"
compose_file="$BASE_DIR/docker-compose.prod.yml"

echo "Working directory: $(pwd)"
echo "Base directory: $BASE_DIR"
echo "Data path: $data_path"
echo "Compose file: $compose_file"

# Check if certificate already exists for primary domain
if [ -d "$data_path/conf/live/$primary_domain" ]; then
  read -p "Existing certificate found for $primary_domain. Continue and replace existing certificate? (y/N) " decision
  if [ "$decision" != "Y" ] && [ "$decision" != "y" ]; then
    exit
  fi
fi

# Create required directories
mkdir -p "$data_path/conf/live/$primary_domain"
mkdir -p "$data_path/www"

# Download TLS parameters if not exist
if [ ! -e "$data_path/conf/options-ssl-nginx.conf" ] || [ ! -e "$data_path/conf/ssl-dhparams.pem" ]; then
  echo "### Downloading recommended TLS parameters ..."
  curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot-nginx/certbot_nginx/_internal/tls_configs/options-ssl-nginx.conf > "$data_path/conf/options-ssl-nginx.conf"
  curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot/certbot/ssl-dhparams.pem > "$data_path/conf/ssl-dhparams.pem"
  echo
fi

# Create dummy certificates for primary domain
echo "### Creating dummy certificate for $primary_domain ..."
path="/etc/letsencrypt/live/$primary_domain"
docker-compose -f "$compose_file" run --rm --entrypoint "\
  openssl req -x509 -nodes -newkey rsa:$rsa_key_size -days 1\
    -keyout '$path/privkey.pem' \
    -out '$path/fullchain.pem' \
    -subj '/CN=localhost'" certbot
echo

# Update the nginx config to use the correct domains
echo "### Updating Nginx configuration with domains: $domains ..."
nginx_conf_path="$BASE_DIR/docker/nginx/data/nginx/app.conf"

# Update primary domain
sed -i.bak "s/\${DOMAIN}/$primary_domain/g" "$nginx_conf_path"
sed -i.bak "s/\${APP_HOST}/${APP_HOST:-app}/g" "$nginx_conf_path"
sed -i.bak "s/\${APP_PORT}/${APP_PORT:-8000}/g" "$nginx_conf_path"

echo "Nginx configuration updated at $nginx_conf_path"
echo "Note: Make sure both server blocks are properly configured for all domains"

# Start nginx
echo "### Starting nginx ..."
cd "$BASE_DIR"
docker-compose -f "$compose_file" up --force-recreate -d nginx
echo

# Delete dummy certificates
echo "### Deleting dummy certificate for $primary_domain ..."
docker-compose -f "$compose_file" run --rm --entrypoint "\
  rm -Rf /etc/letsencrypt/live/$primary_domain && \
  rm -Rf /etc/letsencrypt/archive/$primary_domain && \
  rm -Rf /etc/letsencrypt/renewal/$primary_domain.conf" certbot
echo

# Build domain arguments for certbot
domain_args=""
for domain in "${DOMAIN_ARRAY[@]}"; do
  domain_args="$domain_args -d $domain"
done

# Request Let's Encrypt certificate for all domains
echo "### Requesting Let's Encrypt certificate for domains: $domains ..."

if [ -z "$email" ]; then
  docker-compose -f "$compose_file" run --rm --entrypoint "\
    certbot certonly --webroot -w /var/www/certbot \
      --register-unsafely-without-email \
      $domain_args \
      --rsa-key-size $rsa_key_size \
      --agree-tos \
      --force-renewal" certbot
else
  docker-compose -f "$compose_file" run --rm --entrypoint "\
    certbot certonly --webroot -w /var/www/certbot \
      --email $email \
      $domain_args \
      --rsa-key-size $rsa_key_size \
      --agree-tos \
      --force-renewal" certbot
fi

echo

# Reload nginx
echo "### Reloading nginx ..."
docker-compose -f "$compose_file" exec nginx nginx -s reload 

echo
echo "### SSL certificate setup complete!"
echo "Your certificate covers the following domains:"
for domain in "${DOMAIN_ARRAY[@]}"; do
  echo "  - $domain"
done
echo
echo "Certificate files are located at:"
echo "  - $data_path/conf/live/$primary_domain/"
echo
echo "Next steps:"
echo "1. Make sure DNS A records point to your server IP:"
for domain in "${DOMAIN_ARRAY[@]}"; do
  echo "   $domain → YOUR_SERVER_IP"
done
echo "2. Test your domains:"
for domain in "${DOMAIN_ARRAY[@]}"; do
  echo "   https://$domain"
done
