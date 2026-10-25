# Image de production de l'application Next.js.
# Construite depuis la racine du dépôt (contexte = monorepo) :
#   docker build -f sites/web/Dockerfile -t democracy-watch-web .

FROM node:22-slim AS build
WORKDIR /repo
RUN corepack enable
# Pas de hooks git dans l'image (ni dépôt git ni binaire `git`) : lefthook les ignore si CI est défini.
ENV CI=true
ENV NEXT_TELEMETRY_DISABLED=1
# URL publique (balises de partage, metadataBase). Fournie par Coolify au build.
ARG SITE_URL
ENV SITE_URL=${SITE_URL}
COPY . .
# N'installe que l'application et les packages dont elle dépend.
RUN pnpm install --frozen-lockfile --filter "@democracy-watch/web..." \
  && pnpm --filter @democracy-watch/web build

FROM node:22-slim
WORKDIR /app
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 PORT=3000 HOSTNAME=0.0.0.0
# Sortie « standalone » de Next.js : serveur + dépendances strictement nécessaires.
COPY --from=build /repo/sites/web/.next/standalone ./
COPY --from=build /repo/sites/web/.next/static ./sites/web/.next/static
COPY --from=build /repo/sites/web/public ./sites/web/public
USER node
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD node -e "fetch('http://127.0.0.1:3000/connexion').then(r => process.exit(r.ok ? 0 : 1)).catch(() => process.exit(1))"
CMD ["node", "sites/web/server.js"]
