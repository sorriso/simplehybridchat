#!/bin/bash
# path: scripts/whitelist-fingerprint.sh
# version: 1.0
# Whitelist a client certificate fingerprint in Caddy configuration

set -e

if [ -z "$1" ]; then
    echo "❌ Error: Certificate file required"
    echo "Usage: $0 <certificate-file>"
    echo "Example: $0 test-certs/client.crt"
    exit 1
fi

CERT_FILE="$1"
CONFIGMAP_FILE="caddy/configmap.yaml"

# Check if certificate exists
if [ ! -f "$CERT_FILE" ]; then
    echo "❌ Error: Certificate not found: $CERT_FILE"
    exit 1
fi

# Check if configmap exists
if [ ! -f "$CONFIGMAP_FILE" ]; then
    echo "❌ Error: ConfigMap not found: $CONFIGMAP_FILE"
    exit 1
fi

# Calculate fingerprint
FINGERPRINT=$(openssl x509 -noout -fingerprint -sha1 -in "$CERT_FILE" | cut -d'=' -f2 | tr -d ':' | tr '[:upper:]' '[:lower:]')

echo "🔑 Fingerprint: $FINGERPRINT"
echo ""

# Check if fingerprint already exists in configmap
if grep -q "$FINGERPRINT" "$CONFIGMAP_FILE"; then
    echo "✅ Fingerprint already whitelisted in $CONFIGMAP_FILE"
    exit 0
fi

# Create backup
cp "$CONFIGMAP_FILE" "${CONFIGMAP_FILE}.bak"
echo "💾 Backup created: ${CONFIGMAP_FILE}.bak"

# Replace YOUR_FINGERPRINT_HERE or add to existing list
if grep -q "YOUR_FINGERPRINT_HERE" "$CONFIGMAP_FILE"; then
    # Replace placeholder
    sed -i.tmp "s/YOUR_FINGERPRINT_HERE/$FINGERPRINT/" "$CONFIGMAP_FILE"
    rm -f "${CONFIGMAP_FILE}.tmp"
    echo "✏️  Replaced placeholder with fingerprint"
else
    # Add to existing @allowed_fingerprints block
    # Find the line with the first fingerprint and add after it
    awk -v fp="$FINGERPRINT" '
        /@allowed_fingerprints \{/ { in_block=1 }
        in_block && /header X-Client-Cert-Fingerprint/ && !added {
            print
            print "            header X-Client-Cert-Fingerprint \"" fp "\"  # Added by script"
            added=1
            next
        }
        { print }
    ' "$CONFIGMAP_FILE" > "${CONFIGMAP_FILE}.tmp"
    mv "${CONFIGMAP_FILE}.tmp" "$CONFIGMAP_FILE"
    echo "✏️  Added fingerprint to whitelist"
fi

echo ""
echo "✅ ConfigMap updated: $CONFIGMAP_FILE"
echo ""
echo "📋 Current whitelist:"
grep -A 5 "@allowed_fingerprints" "$CONFIGMAP_FILE" | grep "header X-Client-Cert-Fingerprint" || echo "   (empty)"
echo ""
echo "💡 Next steps:"
echo "   1. Apply changes: kubectl apply -f $CONFIGMAP_FILE"
echo "   2. Restart Caddy: kubectl delete pod -l app=caddy -n chatbot"
echo ""
echo "Or run: make -f Makefile.test-fingerprint apply-caddy"
echo ""