# Build stage
FROM node:20-alpine AS build

WORKDIR /app

# Copy package files for better caching
COPY package.json package-lock.json ./
RUN npm ci

# Copy source code and build
COPY . .
RUN npm run build

# Serve stage using Nginx
FROM nginx:alpine

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy our custom nginx config
COPY nginx.conf /etc/nginx/conf.d/

# Copy built assets
COPY --from=build /app/dist /usr/share/nginx/html

# Expose port (Cloud Run uses 8080 by default)
EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
