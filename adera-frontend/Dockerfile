FROM node:20-alpine

WORKDIR /app

# Install reproducible frontend dependencies using committed lockfile
COPY package.json package-lock.json ./
RUN npm ci

# Copy frontend source files
COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
