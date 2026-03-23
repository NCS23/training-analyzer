# ---- Build Stage ----
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
COPY packages/ ./packages/
RUN npm ci

ARG CACHEBUST=1
COPY . .
RUN npm run build

# ---- Production Stage ----
# nginx-brotli adds Brotli compression module (~20-30% smaller than gzip)
FROM fholzer/nginx-brotli:latest

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD wget -q --spider http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]

