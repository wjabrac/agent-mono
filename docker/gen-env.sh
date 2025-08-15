#!/usr/bin/env bash
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"
cat > .env <<EOT
GRAFANA_ADMIN_PASSWORD=$(openssl rand -hex 32)
N8N_USER=admin
N8N_PASS=$(openssl rand -hex 32)
MEILI_MASTER_KEY=$(openssl rand -hex 32)
QDRANT_API_KEY=$(openssl rand -hex 32)
NEXTAUTH_SECRET=$(openssl rand -hex 32)
LANGFUSE_SALT=$(openssl rand -hex 32)
WORDPRESS_JWT_AUTH_SECRET_KEY=$(openssl rand -hex 32)
EOT
echo ".env generated with random credentials."
