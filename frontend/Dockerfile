# Front Democracy Watch (Nuxt, rendu serveur), déployé sur Coolify avec Base Directory /frontend.
# Variables à fournir : API_KEY, SITE_PASSWORD (et NUXT_API_BASE si l'API n'est pas
# https://dw-api.services.d4g.fr).
FROM node:24-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:24-alpine
WORKDIR /app
COPY --from=build /app/.output ./.output
ENV HOST=0.0.0.0 PORT=3000
EXPOSE 3000
# Fichier statique (hors mot de passe) : le front reste joignable même si l'API est en panne.
# 127.0.0.1 et non localhost, qui vise ::1 sous Alpine alors que Nuxt n'écoute qu'en IPv4.
HEALTHCHECK CMD wget -qO- http://127.0.0.1:3000/icons/logo.svg >/dev/null || exit 1
CMD ["node", ".output/server/index.mjs"]
