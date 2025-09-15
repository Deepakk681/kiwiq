# Nginx with Let's Encrypt - Multi-Domain Setup

This directory contains a setup for Nginx with automatic SSL certificate management using Let's Encrypt, supporting multiple subdomains. Based on [this article](https://pentacent.medium.com/nginx-and-lets-encrypt-with-docker-in-less-than-5-minutes-b4b8a60d3a71).

## Current Setup

Our production setup handles multiple services via subdomains:
- **Main API**: `api.prod.kiwiq.ai` → FastAPI application
- **Prefect Server**: `kq-prefect-server.prod.kiwiq.ai` → Prefect orchestration UI/API

## Prerequisites

### 0. EC2 Security Group Rules

⚠️ **CRITICAL**: Open both ports 80 and 443 in your security group:
- **Port 80**: Required for Let's Encrypt domain verification
- **Port 443**: Required for HTTPS traffic

### 1. DNS Configuration

Create DNS A records pointing to your EC2 instance IP:
```
api.prod.kiwiq.ai              → YOUR_EC2_IP
kq-prefect-server.prod.kiwiq.ai → YOUR_EC2_IP  (same IP)
```

### 2. Environment Configuration

Update your `.env` file with the new multi-domain format:

```bash
# Multi-domain setup (recommended)
DOMAINS=api.prod.kiwiq.ai,kq-prefect-server.prod.kiwiq.ai
EMAIL=your@email.com
APP_HOST=app
APP_PORT=8000

# Optional: Legacy single domain (still supported)
# DOMAIN=api.prod.kiwiq.ai
```

**Key Changes:**
- **NEW**: `DOMAINS` - Comma-separated list of all domains for SSL certificate
- **EXISTING**: `DOMAIN` - Still works for single domain (backwards compatible)
- **REQUIRED**: `EMAIL` - Your email for Let's Encrypt registration

## SSL Certificate Setup

### Option A: Simple Setup from .env (Recommended)

The easiest way - uses domains from your `.env` file:

```bash
cd docker/nginx

# Make script executable (first time only)
chmod +x init-ssl.sh

# Setup SSL certificates for all domains in .env
./init-ssl.sh

# Or pass email if not in .env
./init-ssl.sh your@email.com
```

### Option B: Manual Multi-Domain Setup

For advanced usage or manual control:

```bash
cd docker/nginx

# Setup certificates for specific domains
./init-letsencrypt-multi.sh "api.prod.kiwiq.ai,kq-prefect-server.prod.kiwiq.ai" your@email.com

# Or let script read from .env
./init-letsencrypt-multi.sh
```

### Option C: Add Single Domain to Existing Certificate

If you already have certificates and want to add one more domain:

```bash
cd docker/nginx

# Add new domain to existing certificate
./add-domain-cert.sh kq-prefect-server.prod.kiwiq.ai

# Or pass email if not in .env
./add-domain-cert.sh kq-prefect-server.prod.kiwiq.ai your@email.com
```

## How It Works

### Virtual Host Routing

Nginx differentiates traffic using the `Host` header:
- Same IP address and ports (80/443)
- Different `server_name` directives in nginx config
- Automatic routing based on the domain in the request

### Certificate Management

- **Single Certificate**: Covers multiple subdomains (SAN certificate)
- **Automatic Renewal**: Certbot renews all domains in the certificate
- **Shared Storage**: All certificates stored in `./data/certbot/conf/`

## Configuration Files

### Important Note About Config Files

⚠️ **CRITICAL**: The production nginx uses `app.conf`, not `nginx.conf`:

- **Development**: `nginx.conf` (not used in production)
- **Production**: `data/nginx/app.conf` (actual config file used)

Make sure to update `app.conf` with your server blocks for all domains.

## Step-by-Step Production Deployment

### 1. Setup DNS Records

Create A records in your DNS provider:
```
api.prod.kiwiq.ai              A    YOUR_EC2_IP
kq-prefect-server.prod.kiwiq.ai A    YOUR_EC2_IP
```

### 2. Update Nginx Configuration

Copy the updated nginx config with both server blocks:
```bash
# Make sure app.conf has server blocks for both domains
# - api.prod.kiwiq.ai (main API)
# - kq-prefect-server.prod.kiwiq.ai (Prefect server)
```

### 3. Setup SSL Certificates

**Recommended - Simple .env approach:**
```bash
cd docker/nginx

# Make scripts executable (first time only)
chmod +x init-ssl.sh init-letsencrypt-multi.sh add-domain-cert.sh

# Setup SSL certificates for all domains in .env
./init-ssl.sh
```

**Alternative - Manual approach:**
```bash
cd docker/nginx
./init-letsencrypt-multi.sh "api.prod.kiwiq.ai,kq-prefect-server.prod.kiwiq.ai" your@email.com
```

### 4. Start Services

```bash
# Start all services
docker-compose -f docker-compose.prod.yml up -d

# Check nginx is running and routing correctly
docker-compose -f docker-compose.prod.yml logs nginx
```

### 5. Test Your Setup

Test both domains:
```bash
# Test main API
curl -k https://api.prod.kiwiq.ai/health

# Test Prefect server
curl -k https://kq-prefect-server.prod.kiwiq.ai/api/health
```

## Configuration Details

### Server Blocks Required in app.conf

Your `app.conf` needs these server blocks:

1. **HTTP redirect for main domain**
2. **HTTPS for main domain** → FastAPI app
3. **HTTP redirect for Prefect domain**
4. **HTTPS for Prefect domain** → Prefect server

### Certificate Structure

The multi-domain setup creates a **single certificate** covering both domains:
```
Certificate: /etc/letsencrypt/live/api.prod.kiwiq.ai/
├── fullchain.pem    # Used by both server blocks
├── privkey.pem      # Used by both server blocks
└── ...
```

### CORS Configuration

Update CORS origins in your nginx config to include all subdomains:
```nginx
map $http_origin $cors_origin {
    default "";
    "http://localhost:3000"                       $http_origin;
    "https://beta.kiwiq.ai"                       $http_origin;
    "https://kiwiq-frontend.vercel.app"           $http_origin;
    "https://api.prod.kiwiq.ai"                   $http_origin;
    "https://kq-prefect-server.prod.kiwiq.ai"     $http_origin;
}
```

**Remember**: Update both `nginx.conf` (development) and `data/nginx/app.conf` (production)

## Maintenance

### Certificate Renewal

Certificates auto-renew via the certbot container. Manual renewal:
```bash
docker-compose -f docker-compose.prod.yml exec certbot certbot renew
docker-compose -f docker-compose.prod.yml exec nginx nginx -s reload
```

### Adding New Domains

**Option 1 - Update .env and regenerate (Recommended):**
```bash
# 1. Add domain to .env file:
DOMAINS=api.prod.kiwiq.ai,kq-prefect-server.prod.kiwiq.ai,new-subdomain.prod.kiwiq.ai

# 2. Regenerate certificate
cd docker/nginx
./init-ssl.sh
```

**Option 2 - Add single domain to existing certificate:**
```bash
cd docker/nginx
./add-domain-cert.sh new-subdomain.prod.kiwiq.ai
```

### Available Scripts

- **`init-ssl.sh`** - Simple setup using domains from .env (recommended)
- **`init-letsencrypt-multi.sh`** - Advanced multi-domain setup
- **`add-domain-cert.sh`** - Add single domain to existing certificate  
- **`init-letsencrypt.sh`** - Legacy single domain setup

### 3. Start the services

Start Nginx and Certbot services:

```bash
# Using the main docker-compose.prod.yml
docker-compose -f ../../docker-compose.prod.yml up -d
```

## Features

- Automatic redirection from HTTP to HTTPS
- Automatic SSL certificate renewal every 12 hours (if needed)
- Nginx configuration reloaded every 6 hours to pick up new certificates
- Secure SSL configuration with recommended parameters

## Troubleshooting

### Let's Encrypt Verification Failures

If you see errors like:
```
Certbot failed to authenticate some domains (authenticator: webroot). The Certificate Authority reported these problems:
  Domain: yourdomain.com
  Type:   connection
  Detail: Timeout during connect (likely firewall problem)
```

Check the following:

1. **DNS Configuration**: Make sure your domain correctly points to your server's IP address. You can check with:
   ```bash
   host yourdomain.com
   ```

2. **Firewall Settings**: Ensure port 80 is open in your firewall/security group.
   - For AWS EC2 instances, check the security group settings
   - For other cloud providers, check their firewall settings
   - For local firewalls (iptables, ufw), make sure port 80 is allowed

3. **Network Configuration**: If you're behind a load balancer or proxy, ensure it correctly forwards traffic to your Nginx container.

4. **Port Conflicts**: Make sure no other service is using port 80 on your host machine.

The improved script will automatically check most of these for you and offer a fallback option to use self-signed certificates if Let's Encrypt verification fails.

### Manual Certificate Renewal

If automatic renewal isn't working, you can manually renew certificates with:

```bash
docker-compose -f docker-compose.prod.yml exec certbot certbot renew
```

### Viewing Logs

Check Let's Encrypt logs:
```bash
docker-compose -f docker-compose.prod.yml exec certbot cat /var/log/letsencrypt/letsencrypt.log
```

Check Nginx logs:
```bash
docker-compose -f docker-compose.prod.yml logs nginx
```
