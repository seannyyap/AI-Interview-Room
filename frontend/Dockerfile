# --- Build Stage ---
FROM node:20-alpine as builder

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

# --- Production Stage ---
FROM nginx:alpine

# Copy built app
COPY --from=builder /app/dist/frontend/browser /usr/share/nginx/html

# Copy nginx config (if any, else use default)
# COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
