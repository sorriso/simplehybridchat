#!/bin/bash
# path: scripts/generate-test-certs.sh
# version: 1.0
# Generate test CA and client certificates for fingerprint testing

set -e

CERTS_DIR="./test-certs"
CA_KEY="$CERTS_DIR/ca.key"
CA_CERT="$CERTS_DIR/ca.crt"
CLIENT_KEY="$CERTS_DIR/client.key"
CLIENT_CERT="$CERTS_DIR/client.crt"
CLIENT_P12="$CERTS_DIR/client.p12"

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

# Cleanup CSR
rm -f "$CERTS_DIR/client.csr"

echo ""
echo "✅ Certificates generated successfully!"
echo ""
echo "📂 Files created in $CERTS_DIR/:"
ls -lh "$CERTS_DIR/"
echo ""

# Calculate and display client certificate fingerprint
FINGERPRINT=$(openssl x509 -noout -fingerprint -sha256 -in "$CLIENT_CERT" | cut -d'=' -f2)
echo "🔑 Client certificate fingerprint (SHA256):"
echo "   $FINGERPRINT"
echo ""

# Display certificate details
echo "📋 Client certificate details:"
openssl x509 -noout -subject -issuer -dates -in "$CLIENT_CERT"
echo ""

echo "💡 Next steps:"
echo "   1. Deploy CA to k8s: make deploy-test-ca-kube"
echo "   2. Deploy test ingress: make deploy-test-ingress-kube"
echo "   3. Update /etc/hosts: 127.0.0.1 test.kube.local"
echo "   4. Run test: make test-fingerprint"