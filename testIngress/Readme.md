# Test SSL Client Fingerprint - NGINX Ingress + Caddy

Système d'authentification par certificat client (mTLS) pour protéger des services backend.

## 📑 Table des matières

- [Installation rapide](#-installation-rapide)
- [Architecture](#-architecture)
- [Génération des certificats](#-génération-des-certificats)
- [Secrets Kubernetes](#-secrets-kubernetes)
- [Configuration Caddy](#-configuration-caddy)
- [Accès navigateur](#-accès-depuis-navigateur)
- [Ajouter une machine](#-ajouter-une-machine)
- [Troubleshooting](#-troubleshooting)
- [Structure du projet](#-structure)

---

## 🎯 Ce qui fonctionne

✅ NGINX Ingress capture le fingerprint SHA1 du certificat client  
✅ Transmission via header `X-Client-Cert-Fingerprint` à Caddy  
✅ Caddy filtre l'accès basé sur une whitelist de fingerprints  
✅ Format : SHA1 lowercase sans deux-points (40 caractères hex)  
✅ Accès depuis navigateur (Safari, Chrome, Firefox) avec certificat installé  
✅ Certificat serveur TLS wildcard pour *.kube.local  
✅ Génération automatique de fichiers YAML pour les secrets

---

## 📦 Installation rapide

### Workflow complet

```bash
cd /workspace/testIngress

# 1. Installer NGINX Ingress Controller
make -f Makefile.test-fingerprint install-ingress

# 2. Générer CA + certificats client + certificat serveur TLS
make -f Makefile.test-fingerprint generate-certs

# 3. Générer les fichiers YAML des secrets
make -f Makefile.test-fingerprint deploy-ca
make -f Makefile.test-fingerprint deploy-server-tls

# 4. Déployer les services (app, admin, caddy, ingress, secrets)
make -f Makefile.test-fingerprint deploy-all

# 5. Whitelister automatiquement le certificat client
make -f Makefile.test-fingerprint whitelist
make -f Makefile.test-fingerprint apply-caddy

# 6. Tester la capture
make -f Makefile.test-fingerprint test
```

**Résultat attendu** :
```
✅ SUCCESS: Fingerprint correctly captured!
   Expected: 7214738db7c8dd74ba12aadd3ec47b1da0c96418
   Captured: 7214738db7c8dd74ba12aadd3ec47b1da0c96418
```

---

## 🔧 Architecture

```
Navigateur/Client
    ↓ (HTTPS + certificat client)
NGINX Ingress (NodePort :30731)
    ├─ Mode: auth-tls-verify-client: optional_no_ca
    ├─ Capture: $ssl_client_fingerprint (SHA1)
    ├─ Header: X-Client-Cert-Fingerprint: 7214738db7c8dd74ba12aadd3ec47b1da0c96418
    ├─ ⚠️ Le CA n'est PAS vérifié (n'importe quel certificat accepté)
    ↓ (HTTP non chiffré)
Caddy (:3000)
    ├─ Vérifie header vs whitelist
    ├─ Match → accès autorisé
    ├─ Pas de match → 403 Forbidden
    ↓
Services NGINX (app:80 public, admin:80 protégé)
```

**Note sur la sécurité** : 
- Le mode `optional_no_ca` accepte n'importe quel certificat client (même auto-signé)
- Seul le fingerprint est vérifié par Caddy
- Le CA généré sert uniquement à créer vos certificats clients de test
- Vous pouvez whitelister n'importe quel certificat existant (pas besoin qu'il soit signé par votre CA)

---

## 🔐 Génération des certificats

### Certificats générés

Le script génère 3 types de certificats signés par une même CA :

```
test-certs/
├── ca.crt + ca.key          # CA racine (validité : 10 ans)
├── client.crt + client.key  # Certificat client pour mTLS (validité : 1 an)
├── client.p12               # Bundle PKCS12 pour navigateur (password: test)
└── server.crt + server.key  # Certificat serveur TLS wildcard *.kube.local (validité : 1 an)
```

### Certificat serveur TLS

**CN** : `*.kube.local`  
**SAN** : `*.kube.local`, `kube.local`

**Couverture** :
- ✅ chat.kube.local
- ✅ minio.kube.local
- ✅ n8n.kube.local
- ✅ arango.kube.local
- ✅ Tout autre *.kube.local

### Commande

```bash
make -f Makefile.test-fingerprint generate-certs
```

Le script affiche :
- Le fingerprint SHA1 du certificat client (pour whitelist Caddy)
- Les instructions de déploiement
- Les détails des certificats générés

---

## 🗂️ Secrets Kubernetes

### Principe

Les commandes `deploy-ca` et `deploy-server-tls` **génèrent des fichiers YAML** avec `stringData` (texte clair) au lieu de créer directement les secrets.

**Avantages** :
- ✅ Lisible (certificats en PEM, pas en base64)
- ✅ Éditable manuellement si nécessaire
- ✅ Diff Git lisibles
- ✅ GitOps-friendly
- ✅ Déploiement unifié avec `kubectl apply -k .`

Kubernetes convertit automatiquement `stringData` en `data` base64 lors du déploiement.

### Fichiers générés

#### ingress/ingress-client-ca-secret.yaml

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: client-ca-secret
type: Opaque
stringData:
  ca.crt: |
    -----BEGIN CERTIFICATE-----
    [CA CERTIFICATE EN PEM]
    -----END CERTIFICATE-----
```

**Usage** : Référencé dans l'ingress avec `auth-tls-secret` (si mode `optional` au lieu de `optional_no_ca`)

#### ingress/ingress-tls-secret.yaml

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: server-tls-secret
type: kubernetes.io/tls
stringData:
  tls.crt: |
    -----BEGIN CERTIFICATE-----
    [SERVER CERTIFICATE EN PEM]
    -----END CERTIFICATE-----
  tls.key: |
    -----BEGIN PRIVATE KEY-----
    [SERVER PRIVATE KEY EN PEM - SENSIBLE]
    -----END PRIVATE KEY-----
```

**Usage** : Référencé dans l'ingress avec `spec.tls[].secretName: kube-local-tls`

### Commandes

```bash
# Générer les fichiers YAML
make -f Makefile.test-fingerprint deploy-ca
make -f Makefile.test-fingerprint deploy-server-tls

# Les secrets seront déployés avec :
make -f Makefile.test-fingerprint deploy-all
# Ou :
kubectl apply -k .
```

### ⚠️ Sécurité

**Fichiers sensibles** :
- `ingress/ingress-tls-secret.yaml` contient la **clé privée du serveur en clair**
- Ne pas commiter en clair en production

**.gitignore recommandé** :
```gitignore
# Certificates
test-certs/
*.key
*.crt
*.p12

# Generated secrets (contiennent clé privée)
ingress/ingress-client-ca-secret.yaml
ingress/ingress-tls-secret.yaml

# Keep examples
!ingress/*.example
```

---

## 🎨 Configuration Caddy

### Whitelist des fingerprints

Éditer `caddy/configmap.yaml` :

```caddyfile
http://admin.kube.local:3000 {
    @allowed_fingerprints {
        # Format : SHA1 lowercase, sans deux-points
        header X-Client-Cert-Fingerprint "7214738db7c8dd74ba12aadd3ec47b1da0c96418"
        header X-Client-Cert-Fingerprint "abc123def456..."  # Machine 2
    }

    handle @allowed_fingerprints {
        reverse_proxy admin-service:80
    }

    handle {
        respond "403 Forbidden - Machine not authorized
Fingerprint: {http.request.header.X-Client-Cert-Fingerprint}" 403
    }
}
```

### Automatiser le whitelist

```bash
# Whitelister automatiquement un certificat
./scripts/whitelist-fingerprint.sh test-certs/client.crt

# Appliquer
make -f Makefile.test-fingerprint apply-caddy
```

---

## 🌐 Accès depuis navigateur

### 1. Configuration DNS

Ajouter dans `/etc/hosts` (macOS/Linux) ou `C:\Windows\System32\drivers\etc\hosts` (Windows) :

```
127.0.0.1 app.kube.local admin.kube.local
```

### 2. Trouver le port NodePort

```bash
HTTPS_PORT=$(kubectl get svc -n ingress-nginx ingress-nginx-controller -o jsonpath='{.spec.ports[?(@.name=="https")].nodePort}')
echo "Port HTTPS: $HTTPS_PORT"
```

### 3. Installer le certificat client

#### macOS

```bash
# Générer PKCS12 format compatible macOS
cd testIngress
openssl pkcs12 -export \
  -out test-certs/client.p12 \
  -inkey test-certs/client.key \
  -in test-certs/client.crt \
  -certfile test-certs/ca.crt \
  -passout pass:test \
  -keypbe PBE-SHA1-3DES \
  -certpbe PBE-SHA1-3DES \
  -macalg sha1

# Importer dans le trousseau
security import test-certs/client.p12 \
  -k ~/Library/Keychains/login.keychain-db \
  -P test

# Marquer le CA comme fiable
sudo security add-trusted-cert \
  -d -r trustRoot \
  -k /Library/Keychains/System.keychain \
  test-certs/ca.crt
```

#### Windows

1. Double-cliquer sur `client.p12`
2. Importer dans **Personnel**
3. Double-cliquer sur `ca.crt`
4. Installer dans **Autorités de certification racines de confiance**

#### Linux

```bash
# Firefox
about:preferences#privacy → Certificats → Importer

# Chrome
chrome://settings/certificates → Importer
```

### 4. Accéder aux services

```
Public (sans certificat) :
https://app.kube.local:30731/

Protégé (certificat requis) :
https://admin.kube.local:30731/
```

**Premier accès** : Le navigateur demandera quel certificat utiliser → Sélectionner `test-client`

---

## 🔄 Ajouter une machine

### Avec certificat généré

```bash
# 1. Générer certificat pour la nouvelle machine
./scripts/generate-additional-client.sh machine2

# 2. Whitelister automatiquement
./scripts/whitelist-fingerprint.sh test-certs/machine2.crt

# 3. Appliquer
make -f Makefile.test-fingerprint apply-caddy
```

### Avec certificat existant

Vous pouvez whitelister **n'importe quel certificat existant** (personnel, entreprise, auto-signé) :

```bash
# 1. Whitelister directement
./scripts/whitelist-fingerprint.sh /path/to/certificat-existant.crt

# 2. Appliquer
make -f Makefile.test-fingerprint apply-caddy
```

---

## 🐛 Troubleshooting

### Problème : 403 Forbidden même avec certificat

**Vérifications** :

```bash
# 1. Vérifier que le certificat est installé
# macOS :
security find-identity -v | grep test

# 2. Vérifier le fingerprint du certificat
openssl x509 -noout -fingerprint -sha1 -in test-certs/client.crt | \
  cut -d'=' -f2 | tr -d ':' | tr '[:upper:]' '[:lower:]'

# 3. Vérifier dans les logs Caddy
kubectl logs -n chatbot -l app=caddy --tail=50

# 4. Vérifier la whitelist dans Caddy
kubectl get configmap caddy-config -n chatbot -o yaml | grep -A 5 "allowed_fingerprints"
```

**Solutions** :
- Le fingerprint dans la whitelist doit correspondre exactement
- Format requis : SHA1, lowercase, sans deux-points
- Redémarrer Caddy après modification : `kubectl delete pod -l app=caddy -n chatbot`

### Problème : NGINX n'envoie pas le header

```bash
# Vérifier les logs NGINX
kubectl logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx

# Vérifier les annotations de l'ingress
kubectl get ingress chatbot-ingress-test-fingerprint -n chatbot -o yaml
```

**Solutions** :
- Vérifier `configuration-snippet` dans l'ingress
- Le header doit être : `proxy_set_header X-Client-Cert-Fingerprint $ssl_client_fingerprint;`

### Problème : Certificat non reconnu par le navigateur

**macOS** : Format PKCS12 legacy requis
```bash
openssl pkcs12 -export \
  -keypbe PBE-SHA1-3DES \
  -certpbe PBE-SHA1-3DES \
  -macalg sha1 \
  ...
```

**Tous OS** : Vérifier que le CA est marqué comme fiable dans le système

### Problème : Avertissement HTTPS dans le navigateur

**Cause** : Certificat serveur auto-signé

**Solution 1** : Faire confiance au CA
```bash
# macOS
sudo security add-trusted-cert -d -r trustRoot \
  -k /Library/Keychains/System.keychain \
  test-certs/ca.crt

# Linux
sudo cp test-certs/ca.crt /usr/local/share/ca-certificates/kube-local-ca.crt
sudo update-ca-certificates
```

**Solution 2** : Utiliser le certificat serveur généré
- Déployer : `make -f Makefile.test-fingerprint deploy-server-tls`
- Référencer dans l'ingress : `secretName: kube-local-tls`

### Problème : Port 443 inaccessible

**Cause** : Rancher Desktop utilise des NodePorts, pas le port 443 standard

**Solution** :
```bash
# Trouver le port HTTPS
kubectl get svc -n ingress-nginx ingress-nginx-controller

# Utiliser le NodePort dans l'URL
https://app.kube.local:30731/
```

### Commandes utiles

```bash
# Calculer un fingerprint SHA1
openssl x509 -noout -fingerprint -sha1 -in cert.crt | \
  cut -d'=' -f2 | tr -d ':' | tr '[:upper:]' '[:lower:]'

# Vérifier certificat
openssl x509 -in cert.crt -text -noout

# Vérifier que certificat est signé par CA
openssl verify -CAfile test-certs/ca.crt test-certs/client.crt

# Redémarrer Caddy
kubectl delete pod -l app=caddy -n chatbot

# Logs temps réel
kubectl logs -n chatbot -l app=caddy -f
```

---

## 📂 Structure

```
testIngress/
├── Makefile.test-fingerprint         # Commandes automatisées
├── README.md                         # Cette documentation
├── .gitignore.example                # Exemple pour ne pas versionner les secrets
│
├── scripts/
│   ├── generate-test-certs.sh        # Génération CA + client + serveur
│   ├── generate-additional-client.sh # Génération clients supplémentaires
│   ├── whitelist-fingerprint.sh      # Whitelist automatique dans Caddy
│   └── test-fingerprint.sh           # Tests automatisés
│
├── ingress/
│   ├── ingress-client-ca-secret.yaml       # Secret CA (généré)
│   └── ingress-tls-secret.yaml             # Secret TLS serveur (généré)
│
├── caddy/
│   └── configmap.yaml                # Configuration Caddy avec whitelist
│
├── ingress.yaml                      # Ingress avec mTLS
├── ingress-with-tls.yaml             # Exemple avec certificat serveur
│
├── app/                              # Service public
│   ├── deployment.yaml
│   ├── service.yaml
│   └── configmap.yaml
│
├── admin/                            # Service protégé
│   ├── deployment.yaml
│   ├── service.yaml
│   └── configmap.yaml
│
└── test-certs/                       # Certificats générés (gitignore)
    ├── ca.crt + ca.key
    ├── client.crt + client.key + client.p12
    └── server.crt + server.key
```

---

## 🎯 Commandes Make disponibles

```bash
# Installation
make -f Makefile.test-fingerprint install-ingress    # Installer NGINX Ingress
make -f Makefile.test-fingerprint uninstall-ingress  # Désinstaller NGINX Ingress

# Certificats
make -f Makefile.test-fingerprint generate-certs     # Générer CA + client + serveur
make -f Makefile.test-fingerprint deploy-ca          # Générer ingress/ingress-client-ca-secret.yaml
make -f Makefile.test-fingerprint deploy-server-tls  # Générer ingress/ingress-tls-secret.yaml

# Déploiement
make -f Makefile.test-fingerprint deploy-all         # Déployer tout (services + secrets)
make -f Makefile.test-fingerprint undeploy-all       # Tout supprimer

# Configuration
make -f Makefile.test-fingerprint whitelist          # Whitelister client.crt automatiquement
make -f Makefile.test-fingerprint apply-caddy        # Appliquer config Caddy et redémarrer

# Tests
make -f Makefile.test-fingerprint test               # Tester capture fingerprint

# Nettoyage
make -f Makefile.test-fingerprint clean              # Supprimer certificats et secrets
```

---

## 🔑 Points clés

### Mode `optional_no_ca`

- ✅ N'importe quel certificat client accepté par NGINX
- ✅ Pas de validation de chaîne de certificats
- ✅ Seul le fingerprint est vérifié par Caddy
- ✅ Vous pouvez whitelister n'importe quel certificat existant

### CA unique

- Le même CA signe les certificats clients (mTLS) ET le certificat serveur (HTTPS)
- Faire confiance au CA = confiance à tous les certificats générés
- Pas besoin de faire confiance à chaque certificat individuellement

### Format fingerprint

- **SHA1** (40 caractères hexadécimaux)
- **Lowercase** (minuscules)
- **Sans deux-points**
- Exemple : `7214738db7c8dd74ba12aadd3ec47b1da0c96418`

### Secrets Kubernetes

- Format `stringData` (texte clair) pour lisibilité
- Kubernetes convertit automatiquement en base64
- GitOps-friendly mais attention aux clés privées

---

## 📚 Ressources

- **Documentation NGINX Ingress** : https://kubernetes.github.io/ingress-nginx/
- **Documentation Caddy** : https://caddyserver.com/docs/
- **OpenSSL** : https://www.openssl.org/docs/

---

## ✅ Checklist complète

- [ ] NGINX Ingress Controller installé
- [ ] Certificats générés (CA + client + serveur)
- [ ] Fichiers secrets YAML générés
- [ ] Services déployés
- [ ] Fingerprint whitelisté dans Caddy
- [ ] Configuration Caddy appliquée
- [ ] DNS configuré dans /etc/hosts
- [ ] Certificat client installé sur la machine locale
- [ ] CA marqué comme fiable
- [ ] Test curl réussi (capture fingerprint)
- [ ] Test navigateur réussi (accès admin avec certificat)

**Système complet et fonctionnel !** 🎉