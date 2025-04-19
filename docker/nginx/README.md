# Nginx with Let's Encrypt

This directory contains a simplified setup for Nginx with automatic SSL certificate management using Let's Encrypt, based on the approach described in [this article](https://pentacent.medium.com/nginx-and-lets-encrypt-with-docker-in-less-than-5-minutes-b4b8a60d3a71).

## How to use

### NOTE: `nginx.conf` needs to copied + renamed after modification to `nginx/data/nginx/app.conf`

### 0. EC2 incoming traffix rules:

NOTE: you will have to open both ports 80 and 443 since lets encrypt will visit the http endpoint to verify your domain!

### 1. Create a `.env` file

Copy the sample environment file and adjust the values:
```bash
cp .env.sample .env
```

First, ensure your `.env` file is set up properly with the following variables:
```
DOMAIN=yourdomain.com
EMAIL=your@email.com
APP_HOST=app
APP_PORT=8000
```

### 2. Initialize SSL certificates

Run the initialization script (it will load the `.env` file automatically):

```bash
# Run from the project root
# ./docker/nginx/init-letsencrypt.sh

# Or run from the nginx directory
# Prefer this!
cd docker/nginx
./init-letsencrypt.sh

# You can also pass domain and email directly as arguments
# Option 2: Load from .env file
set -a; source .env; set +a; ./init-letsencrypt.sh

# Option 3: Pass domain and email as arguments
./init-letsencrypt.sh api.prod.kiwiq.ai admin@example.com
```

This script will:
1. Create dummy SSL certificates
2. Start Nginx
3. Remove the dummy certificates
4. Obtain real certificates from Let's Encrypt
5. Reload Nginx to use the real certificates

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
