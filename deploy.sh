#!/bin/bash

# Google ADK Teams Bot Deployment Script
# This script deploys the weather bot to Google Cloud Run

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting Google ADK Teams Bot Deployment${NC}"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI is not installed. Please install it first.${NC}"
    echo "Visit: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${YELLOW}⚠️  You are not authenticated with gcloud.${NC}"
    echo "Running: gcloud auth login"
    gcloud auth login
fi

# Get current project
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ No Google Cloud project is set.${NC}"
    echo "Run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo -e "${GREEN}📋 Using Google Cloud Project: ${PROJECT_ID}${NC}"

# Enable required APIs
echo -e "${YELLOW}🔧 Enabling required Google Cloud APIs...${NC}"
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

echo -e "${GREEN}✅ APIs enabled successfully${NC}"

# Build and deploy using Cloud Build
echo -e "${YELLOW}🏗️  Building and deploying with Cloud Build...${NC}"
gcloud builds submit --config cloudbuild.yaml .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Deployment successful!${NC}"
    
    # Get the service URL
    SERVICE_URL=$(gcloud run services describe weather-bot --region=us-central1 --format="value(status.url)")
    
    echo -e "${GREEN}🌐 Your bot is deployed at: ${SERVICE_URL}${NC}"
    echo -e "${GREEN}🏥 Health check: ${SERVICE_URL}/health${NC}"
    echo -e "${GREEN}🤖 Webhook endpoint: ${SERVICE_URL}/api/teams/webhook${NC}"
    
    echo ""
    echo -e "${YELLOW}📝 Next steps:${NC}"
    echo "1. Update your Teams app manifest.json with the webhook URL"
    echo "2. Package your Teams app: python package_app.py"
    echo "3. Upload the app package to Microsoft Teams"
    echo "4. Test the bot by sending a message"
    
    echo ""
    echo -e "${GREEN}🎉 Deployment complete!${NC}"
else
    echo -e "${RED}❌ Deployment failed. Check the logs above for details.${NC}"
    exit 1
fi