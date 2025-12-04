FROM node:20

# Solución para el problema de WebSocket en Windows + Docker
# Esto le dice al servidor de desarrollo de React que no use WebSockets.
ENV WDS_SOCKET_HOST=0.0.0.0

WORKDIR /frontend

# Copiamos package.json y (si existe) package-lock.json desde ESTA carpeta
COPY package.json package-lock.json* /frontend/

RUN npm install

# Copiamos el resto del código React
COPY . /frontend

CMD ["npm", "start"]
