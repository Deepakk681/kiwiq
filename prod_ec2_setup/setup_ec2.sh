#!/bin/bash
# setup_ec2.sh
# Revised script to install prerequisites for Docker Compose deployment
# on Amazon Linux 2023, using native Docker and standalone Docker Compose.
# Run this once after launching and SSHing into the EC2 instance.

# Exit immediately if a command exits with a non-zero status.
set -e

echo "--- [1/7] Updating system packages ---"
sudo dnf update -y

echo "--- [2/7] Installing Git ---"
sudo dnf install git -y

echo "--- [3/7] Installing Docker Engine (from AL2023 repo) ---"
sudo dnf install docker -y

echo "--- [4/7] Starting and Enabling Docker Service ---"
sudo systemctl start docker
sudo systemctl enable docker # Ensures Docker starts on boot
echo "Docker service started and enabled."

echo "--- [5/7] Adding ec2-user to the 'docker' group ---"
# This allows running docker commands without sudo after re-login
sudo usermod -aG docker ec2-user
echo "'ec2-user' added to the docker group."

echo "--- [6/7] Installing Docker Compose (Standalone Binary) ---"
# Find latest stable version
COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)
if [ -z "$COMPOSE_VERSION" ]; then
    echo "Could not automatically determine latest Docker Compose version. Exiting."
    exit 1
fi
# Define installation path
DESTINATION=/usr/local/bin/docker-compose

echo "Downloading Docker Compose version ${COMPOSE_VERSION} to ${DESTINATION}..."
# Download the binary for Linux x86_64
sudo curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-linux-x86_64" -o $DESTINATION

echo "Applying executable permissions to Docker Compose..."
sudo chmod +x $DESTINATION
echo "Docker Compose installed successfully to ${DESTINATION}"

echo "--- [7/7] Verifying installations ---"
docker --version
# Note: Running 'docker-compose' might require re-login first to work without sudo
docker-compose --version || echo "Docker Compose check might require re-login to run without sudo."

echo "--- (Optional Steps) ---"
echo "Consider installing AWS CLI if needed: sudo dnf install awscli -y"

echo ""
echo "--------------------- SETUP SCRIPT COMPLETE ---------------------"
echo ""
echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
echo " CRITICAL: You MUST log out and log back in now                 "
echo "           for Docker group permissions to apply to your user!  "
echo "           Run 'exit', then reconnect via SSH.                  "
echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
echo ""
echo "After logging back in, proceed with cloning your repository,"
echo "creating your .env.prod file, and running 'docker-compose up'."
echo ""
