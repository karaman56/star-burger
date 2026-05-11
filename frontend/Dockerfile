# Этап 1: сборка бандлов через Parcel
FROM node:18-alpine as builder

WORKDIR /app
COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

# Этап 2: сервер nginx для отдачи статики
FROM nginx:alpine
COPY --from=builder /app/bundles /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
