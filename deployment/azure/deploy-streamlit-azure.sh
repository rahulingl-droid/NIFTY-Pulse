#!/usr/bin/env bash
# ==============================================================================
# Automated Azure Deployment Script for NIFTY-Pulse Streamlit Dashboard
# Builds Streamlit container, pushes to Azure Container Registry (ACR), and deploys to ACA.
# ==============================================================================

set -euo pipefail

# Configuration
RESOURCE_GROUP="${AZURE_RESOURCE_GROUP:-rg-nifty-pulse-prod}"
LOCATION="${AZURE_LOCATION:-centralindia}"
ACR_NAME="${AZURE_ACR_NAME:-acrniftypulse}"
IMAGE_NAME="nifty-pulse-streamlit"
TAG="${IMAGE_TAG:-latest}"

echo "=========================================================="
echo "🚀 Deploying NIFTY-Pulse Streamlit to Microsoft Azure (${LOCATION})"
echo "=========================================================="

# 1. Ensure Resource Group exists
echo "1. Checking Resource Group: ${RESOURCE_GROUP}..."
az group create --name "${RESOURCE_GROUP}" --location "${LOCATION}" --output table

# 2. Ensure ACR exists
echo "2. Checking Azure Container Registry: ${ACR_NAME}..."
if ! az acr show --name "${ACR_NAME}" --resource-group "${RESOURCE_GROUP}" > /dev/null 2>&1; then
    echo "Creating ACR: ${ACR_NAME}..."
    az acr create --resource-group "${RESOURCE_GROUP}" --name "${ACR_NAME}" --sku Basic --admin-enabled true --output table
fi

# 3. Build container using ACR Cloud Build
echo "3. Building Streamlit container image in Azure ACR..."
az acr build --registry "${ACR_NAME}" --image "${IMAGE_NAME}:${TAG}" -f deployment/docker/Dockerfile.streamlit .

# 4. Deploy Bicep template
echo "4. Deploying Bicep infrastructure..."
LOGIN_SERVER=$(az acr show --name "${ACR_NAME}" --query loginServer -o tsv)
FULL_IMAGE="${LOGIN_SERVER}/${IMAGE_NAME}:${TAG}"

az deployment group create \
    --resource-group "${RESOURCE_GROUP}" \
    --template-file deployment/azure/main-streamlit.bicep \
    --parameters location="${LOCATION}" containerImage="${FULL_IMAGE}" \
    --output table

echo ""
echo "=========================================================="
echo "✅ Streamlit Deployment Successful!"
echo "Check Container App FQDN in Azure Portal to view live Streamlit dashboard."
echo "=========================================================="
