# 🐳 Deploying Finnie AI to Azure

This document provides exactly how to take your Dockerized Finnie AI platform and push it safely to Azure App Services.

---

## 🏗️ 1. Test the Build Locally

Before provisioning expensive cloud hardware, verify your newly constructed completely isolated Nginx and Uvicorn Linux containers function sequentially on your MacBook.

```bash
# This will build both images and bind them locally to Port 3000 (UI) and Port 8000 (API)
docker-compose up --build
```
Navigate to `http://localhost:3000` to verify the frontend can successfully communicate with the `8000` API route.

---

## ☁️ 2. Deploy to Azure

Assuming you have the **Azure CLI** installed and are authenticated (`az login`):

### 2a. Containerize & Upload to ACR
Create a secure Azure Container Registry to house your explicit image builds.

```bash
# Set your preferred Resource Group & Registry Name
export RG="finnie-rg"
export ACR="finnieacr"

# Create Registry
az acr create --resource-group $RG --name $ACR --sku Basic

# Build and Push Backend Image natively using Azure's Cloud builder
az acr build --registry $ACR --image finnie-backend:latest ./backend/

# Build and Push Frontend Image
# Note: You MUST pass the --build-arg so Vite bakes the correct backend API URL into static HTML!
az acr build --registry $ACR \
    --image finnie-frontend:latest \
    --build-arg VITE_API_URL="https://YOUR-FINAL-BACKEND-AZURE-URL.azurewebsites.net" \
    ./frontend/
```

### 2b. Provision Persistent Web Apps

Now, spin the containers up utilizing Azure App Service (Web Apps for Containers), strictly ensuring `WEBSITES_ENABLE_APP_SERVICE_STORAGE` is flagged to `True` so your SQLite file survives!

```bash
# Create the App Service Plan (The underlying server hardware tier)
az appservice plan create --name finnie-plan --resource-group $RG --sku B1 --is-linux

# Deploy the Backend Container
az webapp create --resource-group $RG --plan finnie-plan --name finnie-api \
    --deployment-container-image-name $ACR.azurecr.io/finnie-backend:latest

# Define the DB_PATH to explicitly use Azure's perpetual home mounted pathway
az webapp config appsettings set --resource-group $RG --name finnie-api \
    --settings \
        DB_PATH="/home/finnie.db" \
        WEBSITES_ENABLE_APP_SERVICE_STORAGE="true"

# Next, Deploy the Frontend NGINX Container
az webapp create --resource-group $RG --plan finnie-plan --name finnie-web \
    --deployment-container-image-name $ACR.azurecr.io/finnie-frontend:latest
```

## Maintenance & Updates
Whenever you modify local Python code, execute:
```bash
az acr build --registry $ACR --image finnie-backend:latest ./backend/
az webapp restart --name finnie-api --resource-group $RG
```
