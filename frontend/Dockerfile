FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
COPY packages/ ./packages/
RUN npm install

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]
