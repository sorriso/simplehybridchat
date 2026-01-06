# Test SSL Client Fingerprint - NGINX Ingress + Caddy

Système d'authentification par certificat client (mTLS) pour protéger des services backend.

## 🎯 Ce qui fonctionne

✅ NGINX Ingress capture le fingerprint SHA1 du certificat client  
✅ Transmission via header `X-Client-Cert-Fingerprint` à Caddy  
✅ Caddy filtre l'accès basé sur une whitelist de fingerprints  
✅ Format : SHA1 lowercase sans deux-points (40 caractères hex)  
✅ Accès depuis navigateur (Safari, Chrome, Firefox) avec certificat installé

## 📦 Installation rapide

### Workflow automatisé (recommandé)

```bash
cd /workspace/testIngress

# 1. Installer NGINX Ingress Controller
make -f Makefile.test-fingerprint install-ingress

# 2. Générer CA et certificat client
make -f Makefile.test-fingerprint generate-certs

# 3. Déployer le CA dans Kubernetes (secret pour l'ingress)
make -f Makefile.test-fingerprint deploy-ca

# 4. Déployer les services (app, admin, caddy, ingress)
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

**Avantage** : Complètement automatisé, aucune édition manuelle nécessaire !

### Installation manuelle (si besoin)

Si vous préférez contrôler chaque étape manuellement, suivez les sections ci-dessous.

### Installation manuelle (si besoin)

Si vous préférez contrôler chaque étape manuellement :

#### Whitelister manuellement le fingerprint

```bash
# Calculer le fingerprint
openssl x509 -noout -fingerprint -sha1 -in test-certs/client.crt | \
  cut -d'=' -f2 | tr -d ':' | tr '[:upper:]' '[:lower:]'

# Éditer caddy/configmap.yaml ligne ~73
nano caddy/configmap.yaml

# Remplacer :
header X-Client-Cert-Fingerprint "YOUR_FINGERPRINT_HERE"
# Par le fingerprint calculé ci-dessus

# Appliquer
kubectl apply -f caddy/configmap.yaml
kubectl delete pod -l app=caddy -n chatbot
```

## 🌐 Accès depuis navigateur

### Configuration machine locale

#### 1. Installer le certificat

**macOS** :
```bash
# Régénérer .p12 avec format compatible
openssl pkcs12 -export \
  -out test-certs/client.p12 \
  -inkey test-certs/client.key \
  -in test-certs/client.crt \
  -certfile test-certs/ca.crt \
  -passout pass:test \
  -keypbe PBE-SHA1-3DES \
  -certpbe PBE-SHA1-3DES \
  -macalg sha1

# Importer
security import test-certs/client.p12 \
  -k ~/Library/Keychains/login.keychain-db \
  -P test \
  -T /Applications/Safari.app

# Marquer CA comme fiable
sudo security add-trusted-cert \
  -d -r trustRoot \
  -k ~/Library/Keychains/login.keychain-db \
  test-certs/ca.crt
```

**Windows** : Double-cliquer sur `client.p12` → Importer (mot de passe: `test`)

**Linux Firefox** : `about:preferences#privacy` → Certificats → Importer `client.p12`

#### 2. Configuration DNS

```bash
# macOS/Linux
echo "127.0.0.1 app.kube.local admin.kube.local" | sudo tee -a /etc/hosts

# Windows (C:\Windows\System32\drivers\etc\hosts)
127.0.0.1 app.kube.local admin.kube.local
```

#### 3. Trouver le port NodePort

```bash
kubectl get svc -n ingress-nginx ingress-nginx-controller | grep 443
# Exemple : 443:30731/TCP → utiliser 30731
```

#### 4. Accéder via navigateur

```
Public : https://app.kube.local:30731/
Admin  : https://admin.kube.local:30731/
```

**Premier accès** :
1. Accepter le certificat serveur auto-signé
2. Sélectionner certificat client "test-client"
3. Page admin s'affiche ✅

## 🔧 Architecture

```
Navigateur/Client
    ↓ (HTTPS + certificat client)
NGINX Ingress (NodePort :30731)
    ├─ Capture: $ssl_client_fingerprint (SHA1)
    ├─ Header: X-Client-Cert-Fingerprint: 7214738db7c8dd74ba12aadd3ec47b1da0c96418
    ↓ (HTTP non chiffré)
Caddy (:3000)
    ├─ Vérifie header vs whitelist
    ├─ Match → accès autorisé
    ├─ Pas de match → 403 Forbidden
    ↓
Services NGINX (app:80 public, admin:80 protégé)
```

## 🧪 Tests de validation

| Test | URL | Résultat attendu |
|------|-----|------------------|
| Public sans cert | `https://app.kube.local:30731/` | Page gradient violet |
| Admin sans cert | `https://admin.kube.local:30731/` | 403 Forbidden |
| Admin avec cert | `https://admin.kube.local:30731/` | Page gradient rose + RESTRICTED |
| Debug | `https://admin.kube.local:30731/debug` | Fingerprint affiché |

## 🔄 Ajouter une machine

**La CA existe déjà**, générez simplement un nouveau certificat client :

```bash
# 1. Générer certificat pour la nouvelle machine
./scripts/generate-additional-client.sh machine2

# 2. Whitelister automatiquement
./scripts/whitelist-fingerprint.sh test-certs/machine2.crt

# 3. Appliquer
make -f Makefile.test-fingerprint apply-caddy
```

**Avantage** : Entièrement automatisé, pas besoin d'éditer manuellement le configmap !

## ⚠️ Problèmes fréquents

### ❌ Import .p12 échoue (macOS)
**Solution** : Utiliser le format legacy avec `-keypbe PBE-SHA1-3DES` (voir commande ci-dessus)

### ❌ "403 Forbidden" avec certificat
**Cause** : Fingerprint pas dans la whitelist ou Caddy pas redémarré  
**Solution** :
```bash
# Vérifier le fingerprint capturé dans la page 403
# Comparer avec caddy/configmap.yaml
# Redémarrer Caddy
kubectl delete pod -l app=caddy -n chatbot
```

### ❌ Navigateur ne demande pas le certificat
**Solution** : Vérifier l'import `security find-identity -v | grep test`, redémarrer le navigateur

### ❌ "Connection refused" sur port 30731
**Solution** : Vérifier le port exact : `kubectl get svc -n ingress-nginx ingress-nginx-controller`

## 📋 Points importants

- **Format fingerprint** : SHA1 lowercase, 40 caractères hex, sans deux-points
- **Exemple** : `7214738db7c8dd74ba12aadd3ec47b1da0c96418`
- **Pas SHA256** : Non supporté par NGINX Ingress v1.14.1
- **NodePort** : Utiliser le port NodePort (ex: 30731) pas 443
- **Caddy restart** : Toujours redémarrer après modification du ConfigMap
- **Tests CLI** : Utilisent `openssl s_client`, pas `curl`

## 🧹 Nettoyage

```bash
make -f Makefile.test-fingerprint clean           # Supprimer certificats
make -f Makefile.test-fingerprint undeploy-all    # Supprimer infrastructure
make -f Makefile.test-fingerprint uninstall-ingress  # Désinstaller ingress
```

## 📂 Structure

```
testIngress/
├── Makefile.test-fingerprint         # Commandes automatisées
├── README.md                         # Ce fichier
├── ingress.yaml                      # Ingress avec mTLS optional
├── caddy/configmap.yaml              # Configuration Caddy avec whitelist
├── scripts/
│   ├── generate-test-certs.sh        # Génération CA + premier client
│   ├── generate-additional-client.sh # Génération clients supplémentaires
│   ├── whitelist-fingerprint.sh      # Whitelist automatique dans Caddy
│   └── test-fingerprint.sh           # Tests automatisés
├── app/                              # Service public
├── admin/                            # Service protégé
└── k8s/                              # Patches NGINX Ingress
```

## 🔒 Production

⚠️ Certificats de test uniquement !

Pour la production :
- Utiliser une vraie CA (Let's Encrypt, DigiCert, etc.)
- Certificats avec durée de vie courte
- Rotation automatique des certificats
- Logging des accès
- HTTPS pour le serveur ingress (pas certificat fake)