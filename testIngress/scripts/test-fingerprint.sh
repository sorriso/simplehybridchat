#!/bin/bash
# path: scripts/test-fingerprint.sh
# version: 2.0
# Test script to verify ssl_client_fingerprint capture
# Changes in v2.0:
# - Uses openssl s_client instead of curl (curl doesn't present client cert with optional mTLS)
# - Uses node IP and NodePort (192.168.65.3:30731) instead of localhost
# - Works with SHA1 fingerprint format (lowercase, no colons)

set -e

CERTS_DIR="./test-certs"
CLIENT_KEY="$CERTS_DIR/client.key"
CLIENT_CERT="$CERTS_DIR/client.crt"
CA_CERT="$CERTS_DIR/ca.crt"

# Get node IP
NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')

# Get HTTPS NodePort
HTTPS_PORT=$(kubectl get svc -n ingress-nginx ingress-nginx-controller -o jsonpath='{.spec.ports[?(@.name=="https")].nodePort}')

APP_URL="https://$NODE_IP:$HTTPS_PORT/debug"
ADMIN_URL="https://$NODE_IP:$HTTPS_PORT/debug"

echo "🧪 Testing ssl_client_fingerprint capture"
echo "=========================================="
echo ""
echo "Node IP: $NODE_IP"
echo "HTTPS Port: $HTTPS_PORT"
echo ""

# Check if certificates exist
if [ ! -f "$CLIENT_CERT" ] || [ ! -f "$CLIENT_KEY" ]; then
    echo "❌ Error: Test certificates not found!"
    echo "   Run 'make -f Makefile.test-fingerprint generate-certs' first"
    exit 1
fi

# Get expected fingerprint (SHA1 - lowercase without colons)
EXPECTED_FINGERPRINT=$(openssl x509 -noout -fingerprint -sha1 -in "$CLIENT_CERT" | cut -d'=' -f2 | tr -d ':' | tr '[:upper:]' '[:lower:]')
echo "🔑 Expected client certificate fingerprint (SHA1):"
echo "   $EXPECTED_FINGERPRINT"
echo ""

# Test 1: Request to app.kube.local WITHOUT client certificate
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📡 Test 1: app.kube.local WITHOUT client certificate"
echo "   → Fingerprint should be empty"
echo ""
echo -e "GET /debug HTTP/1.1\r\nHost: app.kube.local\r\nConnection: close\r\n\r\n" | \
  openssl s_client -connect $NODE_IP:$HTTPS_PORT -servername app.kube.local -quiet 2>/dev/null || true
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Test 2: Request to app.kube.local WITH client certificate
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📡 Test 2: app.kube.local WITH client certificate"
echo "   → Fingerprint should be: $EXPECTED_FINGERPRINT"
echo ""
RESPONSE_WITH_CERT=$(echo -e "GET /debug HTTP/1.1\r\nHost: app.kube.local\r\nConnection: close\r\n\r\n" | \
  openssl s_client -connect $NODE_IP:$HTTPS_PORT \
  -servername app.kube.local \
  -cert "$CLIENT_CERT" \
  -key "$CLIENT_KEY" \
  -quiet 2>/dev/null)
echo "$RESPONSE_WITH_CERT"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Test 3: Request to admin.kube.local WITHOUT client certificate
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📡 Test 3: admin.kube.local WITHOUT client certificate"
echo "   → Should receive 403 Forbidden (no fingerprint)"
echo ""
echo -e "GET /debug HTTP/1.1\r\nHost: admin.kube.local\r\nConnection: close\r\n\r\n" | \
  openssl s_client -connect $NODE_IP:$HTTPS_PORT -servername admin.kube.local -quiet 2>/dev/null || true
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Test 4: Request to admin.kube.local WITH client certificate
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📡 Test 4: admin.kube.local WITH client certificate"
echo "   → Should receive 403 Forbidden (fingerprint not whitelisted)"
echo ""
echo -e "GET /debug HTTP/1.1\r\nHost: admin.kube.local\r\nConnection: close\r\n\r\n" | \
  openssl s_client -connect $NODE_IP:$HTTPS_PORT \
  -servername admin.kube.local \
  -cert "$CLIENT_CERT" \
  -key "$CLIENT_KEY" \
  -quiet 2>/dev/null || true
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Extract fingerprint from test 2
echo "🔍 Validating fingerprint capture..."
CAPTURED_FINGERPRINT=$(echo "$RESPONSE_WITH_CERT" | grep "Client Cert Fingerprint:" | cut -d':' -f2- | xargs)

echo ""
if [ -z "$CAPTURED_FINGERPRINT" ]; then
    echo "❌ FAILED: No fingerprint captured!"
    echo "   Check that:"
    echo "   - NGINX Ingress Controller has snippets enabled"
    echo "   - Test ingress is deployed with auth-tls-verify-client: optional_no_ca"
    echo "   - CA secret is deployed"
    echo "   - Caddy is running and responding"
    exit 1
elif [ "$CAPTURED_FINGERPRINT" == "$EXPECTED_FINGERPRINT" ]; then
    echo "✅ SUCCESS: Fingerprint correctly captured!"
    echo "   Expected: $EXPECTED_FINGERPRINT"
    echo "   Captured: $CAPTURED_FINGERPRINT"
else
    echo "⚠️  WARNING: Fingerprint mismatch!"
    echo "   Expected: $EXPECTED_FINGERPRINT"
    echo "   Captured: $CAPTURED_FINGERPRINT"
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💡 To enable access to admin.kube.local:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. Update caddy/configmap.yaml"
echo "   Replace: header X-Client-Cert-Fingerprint \"YOUR_FINGERPRINT_HERE\""
echo "   With:    header X-Client-Cert-Fingerprint \"$EXPECTED_FINGERPRINT\""
echo ""
echo "2. Apply the change:"
echo "   kubectl apply -f caddy/configmap.yaml"
echo "   kubectl delete pod -l app=caddy -n chatbot"
echo ""
echo "3. Test admin access:"
echo "   echo -e 'GET / HTTP/1.1\\r\\nHost: admin.kube.local\\r\\nConnection: close\\r\\n\\r\\n' | \\"
echo "     openssl s_client -connect $NODE_IP:$HTTPS_PORT \\"
echo "     -servername admin.kube.local \\"
echo "     -cert test-certs/client.crt \\"
echo "     -key test-certs/client.key \\"
echo "     -quiet 2>/dev/null"
echo ""