#!/bin/bash
# DOMAIN=$(grep DOMAIN .env | cut -d '=' -f2) EMAIL=$(grep EMAIL .env | cut -d '=' -f2) ./docker/nginx/init-letsencrypt.sh

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

# Read domain and email from command-line args, or use defaults from environment
domain=${1:-$DOMAIN}
email=${2:-$EMAIL}

if [ -z "$domain" ]; then
  echo "Error: DOMAIN is not set. Please provide domain as first argument or set DOMAIN environment variable." >&2
  exit 1
fi

if [ -z "$email" ]; then
  echo "Error: EMAIL is not set. Please provide email as second argument or set EMAIL environment variable." >&2
  exit 1
fi

# Print configuration for verification
echo "Domain: $domain"
echo "Email: $email"

rsa_key_size=4096
BASE_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
data_path="$BASE_DIR/docker/nginx/data/certbot"
compose_file="$BASE_DIR/docker-compose.prod.yml"

echo "Working directory: $(pwd)"
echo "Base directory: $BASE_DIR"
echo "Data path: $data_path"
echo "Compose file: $compose_file"

if [ -d "$data_path/conf/live/$domain" ]; then
  read -p "Existing data found for $domain. Continue and replace existing certificate? (y/N) " decision
  if [ "$decision" != "Y" ] && [ "$decision" != "y" ]; then
    exit
  fi
fi

# Create required directories
mkdir -p "$data_path/conf/live/$domain"
mkdir -p "$data_path/www"

if [ ! -e "$data_path/conf/options-ssl-nginx.conf" ] || [ ! -e "$data_path/conf/ssl-dhparams.pem" ]; then
  echo "### Downloading recommended TLS parameters ..."
  curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot-nginx/certbot_nginx/_internal/tls_configs/options-ssl-nginx.conf > "$data_path/conf/options-ssl-nginx.conf"
  curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot/certbot/ssl-dhparams.pem > "$data_path/conf/ssl-dhparams.pem"
  echo
fi

# Create dummy certificates
echo "### Creating dummy certificate for $domain ..."
path="/etc/letsencrypt/live/$domain"
docker-compose -f "$compose_file" run --rm --entrypoint "\
  openssl req -x509 -nodes -newkey rsa:$rsa_key_size -days 1\
    -keyout '$path/privkey.pem' \
    -out '$path/fullchain.pem' \
    -subj '/CN=localhost'" certbot
echo

# Update the nginx config to use the correct domain
echo "### Updating Nginx configuration with domain: $domain ..."
nginx_conf_path="$BASE_DIR/docker/nginx/data/nginx/app.conf"
sed -i.bak "s/\${DOMAIN}/$domain/g" "$nginx_conf_path"
sed -i.bak "s/\${APP_HOST}/${APP_HOST:-app}/g" "$nginx_conf_path"
sed -i.bak "s/\${APP_PORT}/${APP_PORT:-8000}/g" "$nginx_conf_path"
echo "Nginx configuration updated at $nginx_conf_path"

# Start nginx
echo "### Starting nginx ..."
cd "$BASE_DIR"
docker-compose -f "$compose_file" up --force-recreate -d nginx
echo

# Delete dummy certificates
echo "### Deleting dummy certificate for $domain ..."
docker-compose -f "$compose_file" run --rm --entrypoint "\
  rm -Rf /etc/letsencrypt/live/$domain && \
  rm -Rf /etc/letsencrypt/archive/$domain && \
  rm -Rf /etc/letsencrypt/renewal/$domain.conf" certbot
echo

# Request Let's Encrypt certificate
echo "### Requesting Let's Encrypt certificate for $domain ..."

# Use direct email flag without variable substitution in the command string
if [ -z "$email" ]; then
  docker-compose -f "$compose_file" run --rm --entrypoint "\
    certbot certonly --webroot -w /var/www/certbot \
      --register-unsafely-without-email \
      -d $domain \
      --rsa-key-size $rsa_key_size \
      --agree-tos \
      --force-renewal" certbot
else
  docker-compose -f "$compose_file" run --rm --entrypoint "\
    certbot certonly --webroot -w /var/www/certbot \
      --email $email \
      -d $domain \
      --rsa-key-size $rsa_key_size \
      --agree-tos \
      --force-renewal" certbot
fi

echo

# Reload nginx
echo "### Reloading nginx ..."
docker-compose -f "$compose_file" exec nginx nginx -s reload 
