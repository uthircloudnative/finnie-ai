# ==========================================
# Stage 1: Build the React Application
# ==========================================
FROM node:18-alpine AS builder

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json* ./
RUN npm install

# Setup dynamic routing via Build Arguments. 
# This is how Azure injects the live backend URL into your React build.
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

# Copy source and build the optimized production package
COPY . .
RUN npm run build

# ==========================================
# Stage 2: Serve with NGINX (Static Server)
# ==========================================
FROM nginx:alpine

# Remove default Nginx page
RUN rm -rf /usr/share/nginx/html/*

# Copy the optimized React build from Stage 1 into the NGINX web root
COPY --from=builder /app/dist /usr/share/nginx/html

# Optional: You can copy a custom nginx.conf here if React routing (React Router) requires it
# COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

# Keep NGINX running in the foreground so the container stays alive
CMD ["nginx", "-g", "daemon off;"]
