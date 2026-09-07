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

### Phase 1: Create the Cloud Registry & Build the Backend

You must first create the underlying Resource Group and upload the Python Backend to the cloud.

```bash
# Set your preferred Resource Group & Registry Name
export RG="finnie-rg"
export ACR="finnieacr"

# 1. Create the foundational Resource Group
az group create --name $RG --location eastus

# 2. Create the Docker Container Vault (ACR)
az acr create --resource-group $RG --name $ACR --sku Basic

# 3. Build and Push Backend Image natively using Azure's Cloud builder
az acr build --registry $ACR --image finnie-backend:latest ./backend/
```

### Phase 2: Deploy the Backend Server

> [!WARNING]
> **Quota = 0 Error on Basic VMs?**
> If you are on an Azure Free Trial or Student account, your limit for "Basic A Family vCPUs" might be hard-locked to 0. If Step 1 fails, go to the **Azure Portal -> Quotas**, request an increase to `1` for the Basic tier, wait 30 minutes for the servers to sync, and try again!

```bash
# 1. Create the App Service Plan (The underlying Linux hardware)
az appservice plan create --name finnie-plan --resource-group $RG --sku B1 --is-linux

# 2. Deploy the Backend Container
# IMPORTANT: Pick a GLOBALLY UNIQUE NAME (like finnie-api-YOURNAME2026).
export BACKEND_NAME="finnie-api-unique123"

az webapp create --resource-group $RG --plan finnie-plan --name $BACKEND_NAME \
    --deployment-container-image-name $ACR.azurecr.io/finnie-backend:latest

# 3. Define deployment settings for database persistence, CORS, and Gunicorn workers
az webapp config appsettings set --resource-group $RG --name $BACKEND_NAME \
    --settings \
        DB_PATH="/home/finnie.db" \
        WEBSITES_ENABLE_APP_SERVICE_STORAGE="true" \
        ALLOWED_ORIGINS="https://$FRONTEND_NAME.azurestaticapps.net,https://$FRONTEND_NAME.azurewebsites.net" \
        WORKERS="2"
```

### Phase 3: Build & Deploy the React Frontend

Because the React app is a *compiled static builder*, you cannot build it until you know exactly what your API URL is from Phase 2! Now that we know your backend URL is `https://$BACKEND_NAME.azurewebsites.net`, we can officially build the frontend container!

```bash
export FRONTEND_NAME="finnie-web-unique123"

# 1. Build and Push Frontend Image, baking the Backend URL permanently into the JavaScript
az acr build --registry $ACR \
    --image finnie-frontend:latest \
    --build-arg VITE_API_URL="https://$BACKEND_NAME.azurewebsites.net" \
    ./frontend/

# 2. Deploy the Frontend NGINX Container
az webapp create --resource-group $RG --plan finnie-plan --name $FRONTEND_NAME \
    --deployment-container-image-name $ACR.azurecr.io/finnie-frontend:latest
```

---

## Maintenance & Updates
Whenever you modify local Python code, execute:
```bash
az acr build --registry $ACR --image finnie-backend:latest ./backend/
az webapp restart --name $BACKEND_NAME --resource-group $RG
```
