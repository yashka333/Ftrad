# One image runs the API and serves the game page (server/public, built by `npm run client`).
FROM node:22-alpine
WORKDIR /app
ENV NODE_ENV=production
COPY package.json package-lock.json ./
COPY shared/package.json shared/
COPY server/package.json server/
RUN npm ci
COPY shared shared
COPY server server
EXPOSE 8787
CMD ["npm", "run", "start"]
