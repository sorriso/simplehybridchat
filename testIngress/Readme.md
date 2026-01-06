# Test SSL Client Fingerprint - Documentation Finale

## 🎯 Ce qui fonctionne

✅ **Capture du fingerprint client** : NGINX Ingress capture le fingerprint SHA1 du certificat client  
✅ **Transmission à Caddy** : Le fingerprint est passé via le header `X-Client-Cert-Fingerprint`  
✅ **Format** : SHA1 lowercase sans deux-points (40 caractères hex)  
✅ **Exemple** : `7214738db7c8dd74ba12aadd3ec47b1da0c96418`

## 🏗️ Architecture validée

```
Client (openssl s_client)
    ↓
NGINX Ingress (192.168.65.3:30731 NodePort)
    ├─ Capture $ssl_client_fingerprint (SHA1)
    ├─ Header: X-Client-Cert-Fingerprint
    ↓
Caddy (:3000 HTTP)
    ├─ Matcher: @allowed_fingerprints
    ├─ Vérifie le header
    ↓
app-service:80 (public) ou admin-service:80 (protected)
```

## ⚡ Procédure complète

### 1. Installer NGINX Ingress Controller

```bash
cd testIngress/
make -f Makefile.test-fingerprint install-ingress
```

### 2. Déployer l'infrastructure

```bash
make -f Makefile.test-fingerprint deploy-all
```

### 3. Générer les certificats de test

```bash
make -f Makefile.test-fingerprint generate-certs
```

Notez le fingerprint affiché (SHA1, 40 caractères hex).

### 4. Déployer le CA

```bash
make -f Makefile.test-fingerprint deploy-ca
```

### 5. Lancer les tests

```bash
make -f Makefile.test-fingerprint test
```

**Résultat attendu** :
```
✅ SUCCESS: Fingerprint correctly captured!
   Expected: 7214738db7c8dd74ba12aadd3ec47b1da0c96418
   Captured: 7214738db7c8dd74ba12aadd3ec47b1da0c96418
```

## 🔓 Activer l'accès admin

Une fois le test réussi, whitelistez le fingerprint dans Caddy :

### 1. Éditer `caddy/configmap.yaml`

```yaml
@allowed_fingerprints {
    header X-Client-Cert-Fingerprint "7214738db7c8dd74ba12aadd3ec47b1da0c96418"
}
```

### 2. Appliquer

```bash
kubectl apply -f caddy/configmap.yaml
kubectl delete pod -l app=caddy -n chatbot
```

### 3. Tester l'accès admin

```bash
# Récupérer l'IP du node et le port
NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')
HTTPS_PORT=$(kubectl get svc -n ingress-nginx ingress-nginx-controller -o jsonpath='{.spec.ports[?(@.name=="https")].nodePort}')

# Tester l'accès admin avec le certificat
echo -e "GET / HTTP/1.1\r\nHost: admin.kube.local\r\nConnection: close\r\n\r\n" | \
  openssl s_client -connect $NODE_IP:$HTTPS_PORT \
  -servername admin.kube.local \
  -cert test-certs/client.crt \
  -key test-certs/client.key \
  -quiet 2>/dev/null
```

**Résultat attendu** : Page HTML admin au lieu de 403 Forbidden.

## 🔍 Points importants

### Pourquoi openssl et pas curl ?

Curl ne présente pas le certificat client avec `ssl_verify_client optional`. OpenSSL fonctionne correctement.

### Pourquoi SHA1 et pas SHA256 ?

NGINX Ingress Controller v1.14.1 n'a pas la variable `$ssl_client_fingerprint_sha256`. Seulement SHA1 disponible.

### Pourquoi 192.168.65.3:30731 ?

Avec Rancher Desktop, le LoadBalancer n'expose pas réellement localhost:443. Il faut utiliser l'IP du node avec le NodePort.

### Format du fingerprint

- **NGINX envoie** : SHA1 lowercase sans deux-points → `7214738db7c8dd74ba12aadd3ec47b1da0c96418`
- **Caddy vérifie** : Même format dans le header `X-Client-Cert-Fingerprint`
- **Ne pas utiliser** : Format avec deux-points → `72:14:73:8D:B7:C8:...`

## 📋 Commandes utiles

```bash
# Vérifier l'IP du node
kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}'

# Vérifier le port HTTPS NodePort
kubectl get svc -n ingress-nginx ingress-nginx-controller -o jsonpath='{.spec.ports[?(@.name=="https")].nodePort}'

# Calculer le fingerprint SHA1 d'un certificat
openssl x509 -noout -fingerprint -sha1 -in test-certs/client.crt | cut -d'=' -f2 | tr -d ':' | tr '[:upper:]' '[:lower:]'

# Voir les logs NGINX Ingress
kubectl logs -n ingress-nginx -l app.kubernetes.io/component=controller --tail=50

# Voir les logs Caddy
kubectl logs -n chatbot -l app=caddy --tail=20
```

## 🧹 Nettoyage

```bash
# Supprimer les certificats
make -f Makefile.test-fingerprint clean

# Supprimer l'infrastructure
make -f Makefile.test-fingerprint undeploy-all

# Désinstaller l'ingress controller
make -f Makefile.test-fingerprint uninstall-ingress
```

## 📚 Fichiers importants

- `caddy/configmap.yaml` : Configuration Caddy avec whitelist fingerprint
- `ingress.yaml` : Ingress avec mTLS optional et snippet
- `scripts/test-fingerprint.sh` : Script de test automatisé
- `k8s/nginx-ingress-*.json` : Patches pour activer les snippets

## ⚠️ Troubleshooting

Voir `TROUBLESHOOTING.md` pour les problèmes courants et leurs solutions.