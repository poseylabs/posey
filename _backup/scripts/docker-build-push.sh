#!/bin/bash
# Direct Docker build and push script (NX-independent fallback)
set -e

# Configuration
REGISTRY="registry.digitalocean.com/posey"
TAG="${1:-latest}"  # Use provided tag or default to 'latest'
SERVICES_DIR="services"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
  echo -e "${RED}Error: Docker is not running.${NC}"
  exit 1
fi

# Check if logged into DigitalOcean registry
echo -e "${YELLOW}Ensuring DigitalOcean registry login...${NC}"
doctl registry login

# Get list of services by scanning the services directory
if [ ! -d "$SERVICES_DIR" ]; then
  echo -e "${RED}Error: Services directory '$SERVICES_DIR' not found.${NC}"
  exit 1
fi

SERVICES=()
for dir in "$SERVICES_DIR"/*; do
  if [ -d "$dir" ] && [ -f "$dir/Dockerfile" ]; then
    service_name=$(basename "$dir")
    SERVICES+=("$service_name")
  fi
done

if [ ${#SERVICES[@]} -eq 0 ]; then
  echo -e "${RED}Error: No services with Dockerfiles found in '$SERVICES_DIR'.${NC}"
  exit 1
fi

echo -e "${GREEN}Found ${#SERVICES[@]} services: ${SERVICES[*]}${NC}"
echo ""

# Process each service
SUCCESSFUL=()
FAILED=()

for service in "${SERVICES[@]}"; do
  image_name="posey-$service"
  full_image_name="$REGISTRY/$image_name:$TAG"
  
  echo -e "${YELLOW}=== Processing $service ===${NC}"
  echo -e "Building image: ${GREEN}$full_image_name${NC}"
  
  # Navigate to service directory
  cd "$SERVICES_DIR/$service"
  
  # Build the Docker image
  if docker build -t "$full_image_name" .; then
    echo -e "✅ ${GREEN}Successfully built $image_name${NC}"
    
    # Push to registry
    echo -e "Pushing to registry: ${GREEN}$full_image_name${NC}"
    if docker push "$full_image_name"; then
      echo -e "✅ ${GREEN}Successfully pushed $image_name${NC}"
      SUCCESSFUL+=("$service")
    else
      echo -e "❌ ${RED}Failed to push $image_name${NC}"
      FAILED+=("$service (push failed)")
    fi
  else
    echo -e "❌ ${RED}Failed to build $image_name${NC}"
    FAILED+=("$service (build failed)")
  fi
  
  # Return to root directory
  cd - > /dev/null
  echo ""
done

# Summary
echo -e "${YELLOW}=== Build and Push Summary ===${NC}"
echo -e "${GREEN}Successfully processed (${#SUCCESSFUL[@]}): ${SUCCESSFUL[*]}${NC}"
if [ ${#FAILED[@]} -gt 0 ]; then
  echo -e "${RED}Failed (${#FAILED[@]}): ${FAILED[*]}${NC}"
  exit 1
fi

echo -e "\n${GREEN}All services built and pushed successfully!${NC}"
echo -e "You can now deploy them with: ${YELLOW}yarn helm:debug${NC}"
echo -e "And access them with: ${YELLOW}yarn helmport${NC}" 