# syntax=docker/dockerfile:1
FROM node:20-alpine AS deps
WORKDIR /app

# Need build tools for some npm packages
RUN apk add --no-cache libc6-compat

# pnpm via corepack
RUN corepack enable && corepack prepare pnpm@9.15.0 --activate

# .npmrc has the @thomasbrunner-spec scope. Token is supplied as build secret.
COPY .npmrc package.json pnpm-lock.yaml ./

RUN --mount=type=secret,id=npm_token \
    echo "//npm.pkg.github.com/:_authToken=$(cat /run/secrets/npm_token)" >> .npmrc && \
    pnpm install --frozen-lockfile && \
    rm -f .npmrc

# Build
FROM node:20-alpine AS builder
WORKDIR /app
RUN corepack enable && corepack prepare pnpm@9.15.0 --activate
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN pnpm run build

# Runner
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME=0.0.0.0

RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs
EXPOSE 3000

CMD ["node", "server.js"]
