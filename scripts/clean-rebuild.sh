#!/bin/bash

# Script to clean everything and rebuild the Posey platform from scratch
# This will:
# 1. Clean all Docker containers, images, and volumes
# 2. Clean up Kubernetes resources
# 3. Build and deploy data services
# 4. Build and deploy application services
# 5. Set up ingress and port forwarding

# Set the root directory
ROOT_DIR="$(dirname "$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)")"
DATA_DIR="${ROOT_DIR}/data"
SERVICES_DIR="${ROOT_DIR}/services"

# Color codes for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================================${NC}"
echo -e "${BLUE}🚀 Posey Platform Complete Rebuild 🚀${NC}"
echo -e "${BLUE}=================================================${NC}"

# Confirm before proceeding
read -p "⚠️  This will delete ALL Docker containers, images, volumes, and Kubernetes resources. Are you sure? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}Operation canceled.${NC}"
    exit 1
fi

echo -e "\n${YELLOW}Step 1: Cleaning Kubernetes resources...${NC}"
kubectl delete all --all -n posey
kubectl delete namespace posey --ignore-not-found
kubectl delete pvc --all -n posey
kubectl delete pv --all

echo -e "\n${YELLOW}Step 2: Stopping and removing all Docker containers...${NC}"
docker stop $(docker ps -aq) 2>/dev/null || true
docker rm $(docker ps -aq) 2>/dev/null || true

echo -e "\n${YELLOW}Step 3: Removing all Docker images...${NC}"
docker rmi $(docker images -q) 2>/dev/null || true

echo -e "\n${YELLOW}Step 4: Removing all Docker volumes...${NC}"
docker volume prune -f

echo -e "\n${YELLOW}Step 5: Removing all Docker networks...${NC}"
docker network prune -f

echo -e "\n${GREEN}Clean-up completed. Now rebuilding from scratch...${NC}"

echo -e "\n${YELLOW}Step 6: Building and deploying data services...${NC}"
cd "${DATA_DIR}"
yarn build:local
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Data services build failed. Exiting.${NC}"
    exit 1
fi

yarn deploy:local
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Data services deployment failed. Exiting.${NC}"
    exit 1
fi

echo -e "\n${YELLOW}Step 7: Building and deploying application services...${NC}"
cd "${SERVICES_DIR}"
yarn build:local
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Application services build failed. Exiting.${NC}"
    exit 1
fi

yarn deploy:local
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Application services deployment failed. Exiting.${NC}"
    exit 1
fi

echo -e "\n${YELLOW}Step 8: Setting up ingress...${NC}"
cd "${ROOT_DIR}"
bash "${ROOT_DIR}/scripts/update-ingress.sh"

echo -e "\n${GREEN}✅ Rebuild completed successfully!${NC}"
echo -e "\n${YELLOW}Checking Kubernetes resources:${NC}"

echo -e "\n${BLUE}Kubernetes Pods:${NC}"
kubectl get pods -n posey

echo -e "\n${BLUE}Kubernetes Services:${NC}"
kubectl get services -n posey

echo -e "\n${BLUE}Kubernetes Ingresses:${NC}"
kubectl get ingress -n posey

echo -e "\n${GREEN}To access services, run:${NC}"
echo -e "  ${ROOT_DIR}/port-forward.sh"

echo -e "\n${BLUE}Next steps for production deployment:${NC}"
echo "1. Commit and push all changes"
echo "2. Run deployment to Digital Ocean"
echo "3. Configure DNS settings"
echo "4. Verify services access" 