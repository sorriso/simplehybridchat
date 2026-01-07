#!/bin/bash
# path: scripts/generate-test-certs.sh
# version: 2.0
# Generate test CA, client certificates and server TLS certificate
# Changes in v2.0:
# - Added server TLS certificate generation for *.kube.local wildcard

set -e

CERTS_DIR="./test-certs"
CA_KEY="$CERTS_DIR/ca.key"
CA_CERT="$CERTS_DIR/ca.crt"
CLIENT_KEY="$CERTS_DIR/client.key"
CLIENT_CERT="$CERTS_DIR/client.crt"
CLIENT_P12="$CERTS_DIR/client.p12"
SERVER_KEY="$CERTS_DIR/server.key"
SERVER_CERT="$CERTS_DIR/server.crt"
SERVER_CSR="$CERTS_DIR/server.csr"
SAN_CONFIG="$CERTS_DIR/san.cnf"

echo "🔐 Generating test certificates for fingerprint testing..."
echo ""

# Create certificates directory
mkdir -p "$CERTS_DIR"

# Generate CA private key
echo "📝 Generating CA private key..."
openssl genrsa -out "$CA_KEY" 4096 2>/dev/null

# Generate CA certificate (valid for 10 years)
echo "📝 Generating CA certificate..."
openssl req -new -x509 -days 3650 -key "$CA_KEY" -out "$CA_CERT" \
    -subj "/C=FR/ST=IDF/L=Paris/O=Test/OU=Test/CN=Test CA" 2>/dev/null

# Generate client private key
echo "📝 Generating client private key..."
openssl genrsa -out "$CLIENT_KEY" 4096 2>/dev/null

# Generate client certificate signing request
echo "📝 Generating client CSR..."
openssl req -new -key "$CLIENT_KEY" -out "$CERTS_DIR/client.csr" \
    -subj "/C=FR/ST=IDF/L=Paris/O=Test/OU=Test/CN=test-client" 2>/dev/null

# Sign client certificate with CA (valid for 1 year)
echo "📝 Signing client certificate with CA..."
openssl x509 -req -days 365 -in "$CERTS_DIR/client.csr" \
    -CA "$CA_CERT" -CAkey "$CA_KEY" -set_serial 01 \
    -out "$CLIENT_CERT" 2>/dev/null

# Generate PKCS12 bundle (for browser import)
echo "📝 Generating PKCS12 bundle (password: test)..."
openssl pkcs12 -export -out "$CLIENT_P12" \
    -inkey "$CLIENT_KEY" -in "$CLIENT_CERT" \
    -certfile "$CA_CERT" -passout pass:test 2>/dev/null

# =============================================================================
# SERVER TLS CERTIFICATE (for Ingress HTTPS)
# =============================================================================

echo ""
echo "📝 Generating server TLS certificate for *.kube.local..."
echo ""

# Generate server private key
echo "📝 Generating server private key..."
openssl genrsa -out "$SERVER_KEY" 4096 2>/dev/null

# Create SAN configuration file for wildcard certificate
cat > "$SAN_CONFIG" <<EOF
[req]
default_bits = 4096
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = FR
ST = IDF
L = Paris
O = Test
OU = Test
CN = *.kube.local

[v3_req]
keyUsage = keyEncipherment, dataEncipherment, digitalSignature
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = *.kube.local
DNS.2 = kube.local
EOF

# Generate server certificate signing request with SAN
echo "📝 Generating server CSR with wildcard *.kube.local..."
openssl req -new -key "$SERVER_KEY" -out "$SERVER_CSR" \
    -config "$SAN_CONFIG" 2>/dev/null

# Sign server certificate with CA (valid for 1 year)
echo "📝 Signing server certificate with CA..."
openssl x509 -req -days 365 -in "$SERVER_CSR" \
    -CA "$CA_CERT" -CAkey "$CA_KEY" -set_serial 02 \
    -out "$SERVER_CERT" \
    -extensions v3_req -extfile "$SAN_CONFIG" 2>/dev/null

# Cleanup CSR and config
rm -f "$CERTS_DIR/client.csr" "$SERVER_CSR" "$SAN_CONFIG"

echo ""
echo "✅ Certificates generated successfully!"
echo ""
echo "📂 Files created in $CERTS_DIR/:"
ls -lh "$CERTS_DIR/"
echo ""

# =============================================================================
# CLIENT CERTIFICATE INFO
# =============================================================================

# Calculate and display client certificate fingerprint (SHA1 - used by NGINX)
FINGERPRINT_SHA1=$(openssl x509 -noout -fingerprint -sha1 -in "$CLIENT_CERT" | cut -d'=' -f2 | tr -d ':' | tr '[:upper:]' '[:lower:]')
echo "🔑 Client certificate fingerprint (SHA1 - NGINX format):"
echo "   $FINGERPRINT_SHA1"
echo ""
echo "⚠️  NGINX Ingress v1.14.1 uses SHA1 (not SHA256)"
echo "   This is the fingerprint to whitelist in Caddy"
echo ""

# Display certificate details
echo "📋 Client certificate details:"
openssl x509 -noout -subject -issuer -dates -in "$CLIENT_CERT"
echo ""

# =============================================================================
# SERVER CERTIFICATE INFO
# =============================================================================

echo "🌐 Server TLS certificate details:"
openssl x509 -noout -subject -issuer -dates -in "$SERVER_CERT"
echo ""
echo "📋 Server certificate SAN (Subject Alternative Names):"
openssl x509 -noout -text -in "$SERVER_CERT" | grep -A 1 "Subject Alternative Name"
echo ""

echo "💡 Next steps:"
echo ""
echo "1. Generate k8s YAML files for CA and server TLS:"
echo "   make -f Makefile.test-fingerprint deploy-ca"
echo "   make -f Makefile.test-fingerprint deploy-server-tls"
echo ""
echo "2. Deploy infrastructure (includes generated secrets):"
echo "   make -f Makefile.test-fingerprint deploy-all"
echo ""
echo "3. Run test:"
echo "   make -f Makefile.test-fingerprint test"
echo ""
echo "4. Whitelist client fingerprint in caddy/configmap.yaml"
echo ""
echo "5. Trust server certificate on your machine (to avoid browser warnings):"
echo "   # macOS:"
echo "   sudo security add-trusted-cert -d -r trustRoot \\"
echo "     -k /Library/Keychains/System.keychain \\"
echo "     test-certs/ca.crt"
echo "   # Linux:"
echo "   sudo cp test-certs/ca.crt /usr/local/share/ca-certificates/kube-local-ca.crt"
echo "   sudo update-ca-certificates"
echo ""
echo "ℹ️  To add more clients later:"
echo "   - Generate: ./scripts/generate-additional-client.sh <client-name>"
echo "   - No need to redeploy CA, just whitelist the new fingerprint"
echo ""
echo "ℹ️  Server certificate covers:"
echo "   - *.kube.local (wildcard for all subdomains)"
echo "   - kube.local (base domain)"