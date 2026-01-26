# path: frontend/Dockerfile
# version: 3.1
#
# Changes in v3.1:
# - Added USER root for build stage to allow Next.js to write files
# - Switched back to nonroot after build completes
# Stage 1: Install dependencies
FROM cgr.dev/chainguard/node:latest-dev AS deps
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Stage 2: Build the Next.js application
FROM cgr.dev/chainguard/node:latest-dev AS builder

# Switch to root for build operations (Next.js needs write permissions)
USER root
WORKDIR /app

# Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules

# Copy source code
COPY . .

# Set environment variables for build
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production

# Build the application
RUN npm run build

# Stage 3: Production image
FROM cgr.dev/chainguard/node:latest AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Copy necessary files from builder (Chainguard uses nonroot user by default)
COPY --from=builder --chown=nonroot:nonroot /app/public ./public
COPY --from=builder --chown=nonroot:nonroot /app/.next/standalone ./
COPY --from=builder --chown=nonroot:nonroot /app/.next/static ./.next/static

# Expose port 3000
EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Start the application (already running as nonroot user)
CMD ["server.js"]