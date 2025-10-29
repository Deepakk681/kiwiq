# WEAVIATE CLEANUP
docker-compose -f docker-compose-dev.yml exec weaviate \
  sh -c "find /var/lib/weaviate -type f -name '*.db.tmp' -exec rm -f {} \;"

docker-compose -f docker-compose.prod.yml exec weaviate \
  sh -c "find /var/lib/weaviate -type f -name '*.db.tmp' -exec rm -f {} \;"

## Find weaviate volume correct
docker volume ls

`kiwiq-backend_weaviate_data`

docker run --rm \
  -v weaviate_data:/var/lib/weaviate \
  alpine:3.18 \
  sh -c "find /var/lib/weaviate \
    -type f \
    \\( -name 'segment-*.db' -o -name '*.db.tmp' \\) \
    -exec rm -f {} +"

# SSH / SCP

ec2-user@MACHINE.IP.ADDRESS

ssh -i "~/.ssh/your-key.pem" ec2-user@MACHINE.IP.ADDRESS

scp -i ~/.ssh/your-key.pem -r "/path/to/project/.env.prod" ec2-user@MACHINE.IP.ADDRESS:/home/ec2-user/stealth-backend/
scp -i ~/.ssh/your-key.pem -r "/path/to/project/secrets" ec2-user@MACHINE.IP.ADDRESS:/home/ec2-user/stealth-backend/secrets

## Copy server file
scp -i ~/.ssh/your-key.pem -r ec2-user@MACHINE.IP.ADDRESS:/home/ec2-user/stealth-backend/services/workflow_service/services/scraping/browsers/scrapeless/data/scrapeless_profiles_cache.json .

## Copy to server file
scp -i ~/.ssh/your-key.pem -r "/path/to/project/services/workflow_service/services/scraping/browsers/scrapeless/data/scrapeless_profiles_cache.json.backup" ec2-user@MACHINE.IP.ADDRESS:/home/ec2-user/stealth-backend/services/workflow_service/services/scraping/browsers/scrapeless/data/ && scp -i ~/.ssh/your-key.pem -r "/path/to/project/services/workflow_service/services/scraping/browsers/scrapeless/data/scrapeless_profiles_cache.json" ec2-user@MACHINE.IP.ADDRESS:/home/ec2-user/stealth-backend/services/workflow_service/services/scraping/browsers/scrapeless/data/

# docker compose

## bash / sh exec
docker-compose -f docker-compose.prod.yml exec nginx sh
docker-compose -f docker-compose.prod.yml exec app bash

```bash
docker-compose -f docker-compose.prod.yml exec prefect-agent bash
echo $RAPID_API_HOST
```

### DEV exec
docker-compose -f docker-compose-dev.yml exec prefect-agent bash

## DEV YML
./scripts/graceful_flow_cancel_prefect_agent_dev.sh && docker-compose -f docker-compose-dev.yml up -d --build
./scripts/graceful_flow_cancel_prefect_agent_dev.sh && docker-compose -f docker-compose-dev.yml up -d --build app prefect-agent
./scripts/graceful_flow_cancel_prefect_agent_dev.sh && docker-compose -f docker-compose-dev.yml up -d --build prefect-agent
docker-compose -f docker-compose-dev.yml up -d --build weaviate

./scripts/graceful_flow_cancel_prefect_agent_dev.sh && docker-compose -f docker-compose-dev.yml down

## PROD YML!
./scripts/graceful_flow_cancel_prefect_agent.sh && sudo docker-compose -f docker-compose.prod.yml up -d --build app prefect-agent prefect-server nginx
./scripts/graceful_flow_cancel_prefect_agent.sh && sudo docker-compose -f docker-compose.prod.yml up -d --build prefect-server
sudo docker-compose -f docker-compose.prod.yml up -d --build nginx

./scripts/graceful_flow_cancel_prefect_agent.sh && sudo docker-compose -f docker-compose.prod.yml up -d --build prefect-agent

## NGINX RELOAD (after config changes)
# Reload nginx config without restarting container
sudo docker-compose -f docker-compose.prod.yml exec nginx nginx -s reload
# Or restart nginx container if needed
sudo docker-compose -f docker-compose.prod.yml restart nginx

docker-compose -f docker-compose.prod.yml exec prefect-agent bash


./scripts/graceful_flow_cancel_prefect_agent.sh && sudo docker-compose -f docker-compose.prod.yml up -d --build
### NOTE: when upgrading server, you may have to run below CMD to make nginx sync with app new IP!
docker restart kiwiq_prod_nginx

./scripts/graceful_flow_cancel_prefect_agent.sh && docker-compose -f docker-compose.prod.yml down

### Build only APP!
sudo docker-compose -f docker-compose.prod.yml up app --build -d
### Build only worker
./scripts/graceful_flow_cancel_prefect_agent.sh && sudo docker-compose -f docker-compose.prod.yml up prefect-agent --build -d

docker-compose -f docker-compose.prod.yml up -d --force-recreate prefect-server

TEMP_SERVICE_VAR=prefect-agent


# LOGS
docker-compose -f docker-compose.prod.yml logs $TEMP_SERVICE_VAR

docker-compose -f docker-compose.prod.yml logs app -f
docker-compose -f docker-compose.prod.yml logs --since 5m app -f
docker-compose -f docker-compose.prod.yml logs --since 20m app -f
docker-compose -f docker-compose.prod.yml logs --since 20m app
docker-compose -f docker-compose.prod.yml logs --since 20m prefect-agent -f
docker-compose -f docker-compose.prod.yml logs --since 20m prefect-server -f
docker-compose -f docker-compose.prod.yml logs --since 5m nginx -f


## Logs search with `less`
docker-compose -f docker-compose.prod.yml logs --since 10h prefect-agent 2>&1 | less

`As vim fan I prefer to use less and search with / (or ? for backwards search)`
[https://www.cyberciti.biz/faq/find-a-word-in-vim-or-vi-text-editor/](https://www.cyberciti.biz/faq/find-a-word-in-vim-or-vi-text-editor/)


## DEV LOGS
docker-compose -f docker-compose-dev.yml logs --since 20m app

docker-compose -f docker-compose-dev.yml logs --since 5m app -f

docker-compose -f docker-compose-dev.yml logs --since 5m prefect-agent -f

## NOTE: PROD APP LOGS IN FILES

cd ./logs
tail -n 200 kiwiq_backend.log

## COPY LOG FILE:
docker cp $(docker-compose -f docker-compose.prod.yml ps -q app):/app/logs ./logs



-- REMOVE ALL! -> dev docker compose file somehow removes both prod?? --

### RESTART PREFECT_AGENT AFTER CODE CHANGES:
#### DEV
./scripts/graceful_flow_cancel_prefect_agent_dev.sh && docker-compose -f docker-compose-dev.yml restart prefect-agent app
docker-compose -f docker-compose-dev.yml restart app

#### PROD
./scripts/graceful_flow_cancel_prefect_agent.sh && docker-compose -f docker-compose.prod.yml restart prefect-agent
docker-compose -f docker-compose.prod.yml restart nginx
./scripts/graceful_flow_cancel_prefect_agent.sh && docker-compose -f docker-compose.prod.yml restart app prefect-agent

## DEV YML!
docker-compose -f docker-compose-dev.yml exec app postgres

docker-compose -f docker-compose-dev.yml down --rmi all --volumes --remove-orphans

### RESTART PREFECT_AGENT AFTER CODE CHANGES:
./scripts/graceful_flow_cancel_prefect_agent_dev.sh && docker-compose -f docker-compose-dev.yml restart prefect-agent



# migrations

## LOCAL passwords
psql postgresql://postgres_user:postgres_password@localhost:5432/workflow_service

psql postgresql://postgres_user:postgres_password@localhost:5432/postgres

POSTGRES_HOST=postgres
POSTGRES_PORT="5432"
MONGO_HOST=mongo
RABBITMQ_HOST=rabbitmq
REDIS_HOST=redis


postgresql://prod_db_user:Tz8j5pQr2xK9vF7mE3@$localhost:5432/postgres


# Port Forwarding

## Forward a local port to a remote port
# Syntax: ssh -i <key_file> -L <local_port>:<remote_host>:<remote_port> <ssh_host>
# Example: Forward local port 8000 to remote port 8000
ssh -i "~/.ssh/your-key.pem" ec2-user@MACHINE.IP.ADDRESS

ssh -i "~/.ssh/your-key.pem" -L 4200:localhost:4200 ec2-user@MACHINE.IP.ADDRESS

## Forward multiple ports (add multiple -L flags)
# Example: Forward local ports 8000, 5432, and 27017 to corresponding remote ports
ssh -i "~/.ssh/your-key.pem" -L 8000:localhost:8000 -L 5432:localhost:5432 -L 27017:localhost:27017 ec2-user@MACHINE.IP.ADDRESS

## Forward to a specific service in docker-compose
# Example: Forward local port 5432 to postgres container port 5432
ssh -i "~/.ssh/your-key.pem" -L 5432:postgres:5432 ec2-user@MACHINE.IP.ADDRESS

## Background port forwarding (add -N -f flags)
# -N: Do not execute a remote command (useful for port forwarding only)
# -f: Run in background
ssh -i "~/.ssh/your-key.pem" -N -f -L 8000:localhost:8000 ec2-user@MACHINE.IP.ADDRESS

# IP address browsing
https://<SERVER_IP>/docs


# Copy standalone client
yes | cp -rf standalone_test_client/* ../standalone_test_client/


# Disk Utils
```bash
df -h --total
sudo du -xh --max-depth=1 / | sort -rh | head -n20
```

### Totals on 9th Aug 2025:
```bash
[ec2-user@<SERVER_HOSTNAME> stealth-backend]$ df -h --total
Filesystem        Size  Used Avail Use% Mounted on
devtmpfs          4.0M     0  4.0M   0% /dev
tmpfs              16G     0   16G   0% /dev/shm
tmpfs             6.2G  1.6M  6.2G   1% /run
/dev/nvme0n1p1   1000G  143G  858G  15% /
tmpfs              16G     0   16G   0% /tmp
/dev/nvme0n1p128   10M  1.3M  8.7M  13% /boot/efi
tmpfs             3.1G     0  3.1G   0% /run/user/1000
total             1.1T  143G  898G  14% -
```


# DANGER!! --- Docker pruning / cleanup --- DANGER!!

sudo docker-compose -f docker-compose.prod.yml down --volumes
~~ sudo docker-compose -f docker-compose.prod.yml down --volumes --remove-orphans ~~
~~ sudo docker volume prune --all -f~~ 

# **** Start HERE for PROD disk cleanup! ****

## Without stopping docker
docker volume prune -f

### BEST for cleanup!
```bash
docker image prune -f
docker image prune -a -f
docker builder prune -af
```
### AVOID in PROD
```bash
docker volume prune               # removes ALL unused volumes
docker system prune --volumes     # same, nukes unused volumes
docker compose down -v            # removes this project's volumes
```


~~ docker-compose -f docker-compose-dev.yml down --volumes --remove-orphans~~ 

# Docker health checks

docker stats

sudo docker-compose -f docker-compose.prod.yml ps


# RAM USAGE
CONTAINER ID   NAME                               CPU %     MEM USAGE / LIMIT    MEM %     NET I/O           BLOCK I/O         PIDS
6e592ffe7aac   kiwiq_prod_prefect_agent           306.53%   7.317GiB / 9GiB      81.30%    389MB / 258MB     3.73MB / 274kB    1339
7c1c4604e66a   kiwiq_prod_app                     23.12%    706.7MiB / 2GiB      34.51%    236MB / 72.3MB    119kB / 0B        24
2651ec77d57d   kiwiq_prod_prefect_server          2.29%     395.2MiB / 2GiB      19.30%    7.11GB / 3.79GB   164kB / 17.9MB    5
58fda6e7cae0   kiwiq_prod_nginx                   0.00%     19.93MiB / 512MiB    3.89%     8.69GB / 8.49GB   7.62MB / 4.93GB   11
687776f409b8   kiwiq_prod_certbot                 0.00%     21.2MiB / 256MiB     8.28%     693kB / 43kB      21.1MB / 2.02MB   2
561c23e40979   kiwiq_prod_redis                   0.41%     5.742MiB / 512MiB    1.12%     34.8MB / 12.6MB   365kB / 0B        6
94f4ea163856   kiwiq_prod_postgres                64.61%    1.927GiB / 3GiB      64.23%    10.5GB / 10.5GB   1.15GB / 24.8GB   44
07758b8fda5b   c571acd8d2a9_kiwiq_prod_rabbitmq   16.25%    188.1MiB / 2GiB      9.18%     2.04GB / 2.12GB   111kB / 2.12GB    41
94ce69cccca0   kiwiq_prod_mongo                   10.59%    3.321GiB / 4GiB      83.03%    3.16GB / 11.5GB   128MB / 8.59GB    201
c4d4c93a6996   kiwiq_prod_weaviate                0.48%     231.2MiB / 4.75GiB   4.75%     62.9MB / 21.6MB   88.3MB / 255MB    13


