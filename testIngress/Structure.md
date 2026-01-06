# Structure et Emplacement d'Exécution

## 📂 Structure des fichiers

```
testIngress/                           # ⚠️ Répertoire de travail principal
├── Makefile.test-fingerprint          # Exécuter depuis ce répertoire
├── README.md
├── namespace.yaml
├── kustomization.yaml
├── ingress.yaml
├── k8s/                               # Fichiers de patch pour NGINX Ingress
│   ├── nginx-ingress-controller-patch.json
│   └── nginx-ingress-configmap-patch.json
├── scripts/                           # Scripts de test
│   ├── generate-test-certs.sh
│   └── test-fingerprint.sh
├── app/                               # Service public NGINX
│   ├── configmap.yaml
│   ├── deployment.yaml
│   └── service.yaml
├── admin/                             # Service protégé NGINX
│   ├── configmap.yaml
│   ├── deployment.yaml
│   └── service.yaml
└── caddy/                             # Reverse proxy avec filtering
    ├── configmap.yaml
    ├── deployment.yaml
    └── service.yaml
```

## ⚠️ IMPORTANT : Emplacement d'exécution

**Toutes les commandes make doivent être exécutées depuis le répertoire `testIngress/`**

```bash
cd testIngress/
make -f Makefile.test-fingerprint <command>
```

## ✅ Chemins relatifs utilisés

Le Makefile utilise des chemins relatifs au répertoire `testIngress/` :

- `namespace.yaml` (au lieu de `testIngress/namespace.yaml`)
- `kubectl apply -k .` (au lieu de `kubectl apply -k testIngress/`)
- `k8s/nginx-ingress-*.json` (au lieu de `testIngress/k8s/...`)
- `scripts/generate-test-certs.sh` (au lieu de `testIngress/scripts/...`)

## 📝 Fichiers de patch

Les fichiers `nginx-ingress-controller-patch.json` et `nginx-ingress-configmap-patch.json` 
sont dans `testIngress/k8s/` et sont référencés par le Makefile lors de l'installation 
de l'ingress controller.

## 🔧 Modification de configuration

Pour whitelister un fingerprint dans Caddy, éditer :

```bash
caddy/configmap.yaml
```

Puis appliquer :

```bash
kubectl apply -f caddy/configmap.yaml
kubectl delete pod -l app=caddy -n chatbot
```

## 🗑️ Nettoyage

Les certificats générés sont stockés dans :

```
testIngress/test-certs/
├── ca.key
├── ca.crt
├── client.key
├── client.crt
└── client.p12
```

Ils sont supprimés avec :

```bash
make -f Makefile.test-fingerprint clean
```