# Google ADK Teams Bot - Deployment Guide

This guide provides comprehensive instructions for deploying the Google ADK Teams bot to production environments, with a focus on Google Cloud Run deployment.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Configuration](#environment-configuration)
3. [Local Development Setup](#local-development-setup)
4. [Google Cloud Run Deployment](#google-cloud-run-deployment)
5. [Alternative Deployment Options](#alternative-deployment-options)
6. [Teams App Configuration](#teams-app-configuration)
7. [Post-Deployment Verification](#post-deployment-verification)
8. [Monitoring and Logging](#monitoring-and-logging)
9. [Troubleshooting](#troubleshooting)
10. [Maintenance and Updates](#maintenance-and-updates)

## Prerequisites

### Required Accounts and Services
- **Google Cloud Platform account** with billing enabled
- **Microsoft Teams** account (personal or organizational)
- **Git** installed locally
- **Docker** installed locally (optional, for local container testing)

### Required Tools
```bash
# Install Google Cloud CLI
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Install Python 3.11+
python --version  # Should be 3.11 or higher

# Install required Python packages
pip install -r requirements.txt
```

### System Requirements
- **Python**: 3.11 or higher
- **Memory**: Minimum 512MB for Cloud Run deployment
- **Network**: HTTPS endpoint required for Teams webhook
- **Storage**: Minimal (application logs only)

## Environment Configuration

### 1. Google Cloud Project Setup

```bash
# Set your project ID
export PROJECT_ID="your-project-id-here"
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

### 2. Environment Variables

Create environment-specific configuration files:

**For Local Development (`.env.local`):**
```bash
# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT_ID=your-project-id-here
GOOGLE_CLOUD_REGION=us-central1

# Google ADK API Configuration
GOOGLE_ADK_API_KEY=your-adk-api-key-here
GOOGLE_ADK_CLIENT_ID=your-client-id-here
GOOGLE_ADK_CLIENT_SECRET=your-client-secret-here

# Authentication
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account-key.json

# Development Settings
DEBUG=true
LOG_LEVEL=debug
ENVIRONMENT=development

# Teams Configuration (for local testing)
TEAMS_APP_ID=your-teams-app-id
WEBHOOK_SECRET=your-webhook-secret-here
```

**For Production (`.env.prod`):**
```bash
# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT_ID=your-project-id-here
GOOGLE_CLOUD_REGION=us-central1

# Google ADK API Configuration
GOOGLE_ADK_API_KEY=your-adk-api-key-here
GOOGLE_ADK_CLIENT_ID=your-client-id-here
GOOGLE_ADK_CLIENT_SECRET=your-client-secret-here

# Production Settings
DEBUG=false
LOG_LEVEL=INFO
ENVIRONMENT=production

# Teams Configuration
TEAMS_APP_ID=your-teams-app-id
WEBHOOK_SECRET=your-webhook-secret-here
```

### 3. Service Account Setup

```bash
# Create a service account for the application
gcloud iam service-accounts create weather-bot-sa \
    --display-name="Weather Bot Service Account"

# Grant necessary permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:weather-bot-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/run.invoker"

# Create and download service account key
gcloud iam service-accounts keys create service-account-key.json \
    --iam-account=weather-bot-sa@$PROJECT_ID.iam.gserviceaccount.com
```

## Local Development Setup

### 1. Install Dependencies

```bash
# Clone the repository
git clone <repository-url>
cd learn-google-adk

# Install Python dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env.local
# Edit .env.local with your configuration
```

### 2. Run Locally with ngrok

```bash
# Start the FastAPI application
uvicorn app:app --reload --host 0.0.0.0 --port 8000

# In another terminal, expose with ngrok
ngrok http 8000
```

**ngrok will provide a public URL like:** `https://abc123.ngrok.io`

### 3. Update Teams Manifest for Local Testing

Update `manifest.json` with your ngrok URL:
```json
{
  "bots": [{
    "botId": "your-bot-id",
    "messagingEndpoints": [{
      "url": "https://abc123.ngrok.io/api/teams/webhook"
    }]
  }]
}
```

## Google Cloud Run Deployment

### 1. Automated Deployment

The project includes an automated deployment script:

```bash
# Make the script executable
chmod +x deploy.sh

# Run the deployment
./deploy.sh
```

### 2. Manual Deployment Steps

If you prefer manual deployment:

```bash
# 1. Build the Docker image
docker build -t gcr.io/$PROJECT_ID/weather-bot:latest .

# 2. Push to Google Container Registry
docker push gcr.io/$PROJECT_ID/weather-bot:latest

# 3. Deploy to Cloud Run
gcloud run deploy weather-bot \
    --image gcr.io/$PROJECT_ID/weather-bot:latest \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --port 8080 \
    --memory 512Mi \
    --cpu 1 \
    --max-instances 10 \
    --min-instances 0 \
    --timeout 60s \
    --set-env-vars "GOOGLE_CLOUD_PROJECT_ID=$PROJECT_ID,LOG_LEVEL=INFO,ENVIRONMENT=production"
```

### 3. Cloud Build Deployment

Use the included `cloudbuild.yaml` for CI/CD:

```bash
# Deploy using Cloud Build
gcloud builds submit --config cloudbuild.yaml .
```

### 4. Environment Variables in Cloud Run

Set sensitive environment variables through Cloud Run console:

```bash
# Set environment variables securely
gcloud run services update weather-bot \
    --region us-central1 \
    --set-env-vars "GOOGLE_ADK_API_KEY=your-api-key" \
    --set-env-vars "TEAMS_APP_ID=your-teams-app-id" \
    --set-env-vars "WEBHOOK_SECRET=your-webhook-secret"
```

## Alternative Deployment Options

### Heroku Deployment

Create a `Procfile`:
```
web: uvicorn app:app --host 0.0.0.0 --port $PORT
```

Deploy to Heroku:
```bash
# Install Heroku CLI and login
heroku create your-app-name
heroku config:set GOOGLE_ADK_API_KEY=your-api-key
heroku config:set TEAMS_APP_ID=your-teams-app-id
git push heroku main
```

### AWS ECS Deployment

1. Create ECR repository
2. Build and push Docker image
3. Create ECS task definition
4. Deploy as ECS service

### Docker Compose (Local/Development)

Create `docker-compose.yml`:
```yaml
version: '3.8'
services:
  weather-bot:
    build: .
    ports:
      - "8000:8080"
    environment:
      - GOOGLE_CLOUD_PROJECT_ID=your-project-id
      - LOG_LEVEL=INFO
    volumes:
      - ./logs:/app/logs
```

Run with:
```bash
docker-compose up -d
```

## Teams App Configuration

### 1. Prepare App Manifest

Update `manifest.json` with your deployment URL:
```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/teams/v1.16/MicrosoftTeams.schema.json",
  "manifestVersion": "1.16",
  "version": "1.0.0",
  "id": "your-unique-uuid-here",
  "name": {
    "short": "Weather Bot",
    "full": "AI Weather Assistant Bot"
  },
  "description": {
    "short": "Get weather, time, and traffic info",
    "full": "An AI-powered bot that provides weather, time, and traffic information for any city"
  },
  "bots": [{
    "botId": "your-bot-id-here",
    "scopes": ["personal"],
    "messagingEndpoints": [{
      "url": "https://your-cloud-run-url.com/api/teams/webhook"
    }]
  }],
  "validDomains": ["your-cloud-run-domain.com"]
}
```

### 2. Package Teams App

```bash
# Run the packaging script
python package_app.py

# This creates weather-bot.zip ready for upload
```

### 3. Upload to Microsoft Teams

1. Open Microsoft Teams
2. Go to **Apps** → **Manage your apps**
3. Click **Upload an app** → **Upload a custom app**
4. Select `weather-bot.zip`
5. Click **Add** to install for personal use

### 4. Test the Bot

Send a test message to the bot:
- "What's the weather in New York?"
- "What time is it in London?"
- "Traffic status in San Francisco"

## Post-Deployment Verification

### 1. Health Check

```bash
# Get your Cloud Run service URL
SERVICE_URL=$(gcloud run services describe weather-bot --region=us-central1 --format="value(status.url)")

# Test health endpoint
curl $SERVICE_URL/health

# Expected response:
# {"status": "healthy", "timestamp": "2024-01-XX", "version": "1.0.0"}
```

### 2. Webhook Endpoint Test

```bash
# Test webhook endpoint (will return 401 without proper Teams signature)
curl -X POST $SERVICE_URL/api/teams/webhook \
     -H "Content-Type: application/json" \
     -d '{"test": "data"}'

# Expected response:
# {"error": "Invalid request signature"}
```

### 3. Teams Integration Test

1. Send a message to your bot in Teams
2. Verify response is received
3. Check logs for any errors
4. Test different message types (weather, time, traffic)

## Monitoring and Logging

### 1. View Cloud Run Logs

```bash
# View recent logs
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=weather-bot" --limit 50

# Follow logs in real-time
gcloud logs tail "resource.type=cloud_run_revision AND resource.labels.service_name=weather-bot"
```

### 2. Application Logs

Application logs are written to `/app/logs/` in the container and forwarded to Cloud Logging:

- `app.log` - General application logs
- `error.log` - Error-specific logs
- `access.log` - Request/response logs

### 3. Monitoring Metrics

Key metrics to monitor:
- **Request Count** - Number of webhook requests
- **Response Time** - Webhook processing latency
- **Error Rate** - Failed requests percentage
- **Memory Usage** - Container memory consumption
- **CPU Utilization** - Processing load

### 4. Set Up Alerts

```bash
# Create alerting policy for high error rate
gcloud alpha monitoring policies create --policy-from-file=alerting-policy.yaml
```

Example `alerting-policy.yaml`:
```yaml
displayName: "High Error Rate - Weather Bot"
conditions:
  - displayName: "Error rate > 10%"
    conditionThreshold:
      filter: 'resource.type="cloud_run_revision" resource.label.service_name="weather-bot"'
      comparison: COMPARISON_GREATER_THAN
      thresholdValue: 0.1
notificationChannels:
  - "projects/YOUR_PROJECT/notificationChannels/YOUR_CHANNEL_ID"
```

## Troubleshooting

### Common Issues

#### 1. Deployment Failures

**Error**: `Permission denied`
```bash
# Solution: Ensure proper IAM permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="user:your-email@domain.com" \
    --role="roles/run.admin"
```

**Error**: `Cloud Build API not enabled`
```bash
# Solution: Enable the API
gcloud services enable cloudbuild.googleapis.com
```

#### 2. Teams Integration Issues

**Error**: `Bot not responding`
- Check webhook URL in manifest.json
- Verify Cloud Run service is running
- Check logs for authentication errors

**Error**: `Invalid request signature`
- Verify WEBHOOK_SECRET environment variable
- Check Teams app configuration

#### 3. Runtime Errors

**Error**: `Google ADK authentication failed`
```bash
# Solution: Check service account configuration
gcloud auth application-default print-access-token
```

**Error**: `Memory limit exceeded`
```bash
# Solution: Increase memory allocation
gcloud run services update weather-bot \
    --region us-central1 \
    --memory 1Gi
```

### Debugging Steps

1. **Check service status**:
   ```bash
   gcloud run services describe weather-bot --region=us-central1
   ```

2. **Review logs**:
   ```bash
   gcloud logs read "resource.type=cloud_run_revision" --limit 100
   ```

3. **Test endpoints locally**:
   ```bash
   # Run locally and test
   uvicorn app:app --reload
   curl http://localhost:8000/health
   ```

4. **Validate environment variables**:
   ```bash
   gcloud run services describe weather-bot --format="value(spec.template.spec.template.spec.containers.env)"
   ```

## Maintenance and Updates

### 1. Update Application Code

```bash
# 1. Make your code changes
git add .
git commit -m "Update: your changes description"

# 2. Redeploy
./deploy.sh

# 3. Verify deployment
curl $SERVICE_URL/health
```

### 2. Update Teams App

When changing bot functionality:

1. Update `manifest.json` if needed
2. Run `python package_app.py`
3. Re-upload `weather-bot.zip` to Teams
4. Test new functionality

### 3. Scaling Configuration

```bash
# Adjust scaling parameters
gcloud run services update weather-bot \
    --region us-central1 \
    --max-instances 50 \
    --min-instances 1 \
    --cpu 2 \
    --memory 1Gi
```

### 4. Rollback Procedures

```bash
# List previous revisions
gcloud run revisions list --service=weather-bot --region=us-central1

# Rollback to previous revision
gcloud run services update-traffic weather-bot \
    --region us-central1 \
    --to-revisions REVISION-NAME=100
```

### 5. Database Migration (Future)

When adding database functionality:

1. Create Cloud SQL instance
2. Update connection settings
3. Run migration scripts
4. Update service configuration

### 6. Security Updates

Regular maintenance tasks:
- Update Python dependencies: `pip install -r requirements.txt --upgrade`
- Update base Docker image
- Rotate API keys and secrets
- Review IAM permissions

### 7. Backup and Recovery

```bash
# Backup configuration
gcloud run services describe weather-bot --region=us-central1 \
    --format="export" > weather-bot-backup.yaml

# Restore from backup
gcloud run services replace weather-bot-backup.yaml --region=us-central1
```

## Cost Optimization

### Cloud Run Pricing Tips

1. **Use minimum instances sparingly** - Only set min-instances > 0 for high-traffic applications
2. **Right-size resources** - Start with 512Mi memory and 1 CPU, adjust based on usage
3. **Implement request caching** - Cache API responses to reduce processing
4. **Use appropriate timeout values** - Set reasonable timeouts to avoid unnecessary charges

### Monitoring Costs

```bash
# View current month's usage
gcloud billing budgets list

# Set up budget alerts
gcloud billing budgets create \
    --billing-account=BILLING_ACCOUNT_ID \
    --display-name="Weather Bot Budget" \
    --budget-amount=50USD
```

---

## Quick Reference

### Essential Commands

```bash
# Deploy to production
./deploy.sh

# View logs
gcloud logs tail "resource.type=cloud_run_revision AND resource.labels.service_name=weather-bot"

# Update environment variables
gcloud run services update weather-bot --region=us-central1 --set-env-vars "KEY=value"

# Check service status
gcloud run services describe weather-bot --region=us-central1

# Package Teams app
python package_app.py
```

### Important URLs

- **Health Check**: `https://your-service-url/health`
- **Webhook Endpoint**: `https://your-service-url/api/teams/webhook`
- **Cloud Run Console**: `https://console.cloud.google.com/run`
- **Teams App Upload**: `https://teams.microsoft.com/l/app-upload`

---

**Last Updated**: 2024-01-XX  
**Version**: 1.0.0