# syntax=docker/dockerfile:1
FROM node:20-alpine AS deps
WORKDIR /app

# Need build tools for some npm packages
RUN apk add --no-cache libc6-compat

# pnpm via corepack
RUN corepack enable && corepack prepare pnpm@9.15.0 --activate

# .npmrc has the @thomasbrunner-spec scope. Token is supplied as a build arg.
# (Coolify can't bind-mount file-based compose secrets, so we accept the token
# as a build arg here. It is only present in this RUN layer and removed
# afterwards; the runner stage doesn't carry it.)
ARG GITHUB_PACKAGES_TOKEN
COPY .npmrc package.json pnpm-lock.yaml ./

RUN echo "//npm.pkg.github.com/:_authToken=${GITHUB_PACKAGES_TOKEN}" >> .npmrc && \
    pnpm install --frozen-lockfile && \
    rm -f .npmrc

# Build
FROM node:20-alpine AS builder
WORKDIR /app
RUN corepack enable && corepack prepare pnpm@9.15.0 --activate
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Next.js inlines NEXT_PUBLIC_* at build time (prerender / static export),
# so the Supabase config must be passed as build args, not just runtime env.
ARG NEXT_PUBLIC_SUPABASE_URL
ARG NEXT_PUBLIC_SUPABASE_ANON_KEY
ENV NEXT_PUBLIC_SUPABASE_URL=$NEXT_PUBLIC_SUPABASE_URL \
    NEXT_PUBLIC_SUPABASE_ANON_KEY=$NEXT_PUBLIC_SUPABASE_ANON_KEY

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
