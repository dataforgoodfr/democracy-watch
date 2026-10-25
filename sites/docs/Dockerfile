# Image de production de la documentation : site statique Zudoku servi par nginx.
# Construite depuis la racine du dépôt (contexte = monorepo) :
#   docker build -f sites/docs/Dockerfile -t democracy-watch-docs .

FROM node:22-slim AS build
WORKDIR /repo
RUN corepack enable
# Pas de hooks git dans l'image (ni dépôt git ni binaire `git`) : lefthook les ignore si CI est défini.
ENV CI=true
COPY . .
RUN pnpm install --frozen-lockfile --filter "@democracy-watch/docs..." \
  && pnpm --filter @democracy-watch/docs build

FROM nginx:1.27-alpine
COPY sites/docs/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /repo/sites/docs/dist /usr/share/nginx/html
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD wget -qO- http://127.0.0.1/ >/dev/null || exit 1
