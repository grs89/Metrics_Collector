# 🚀 Despliegue en Kubernetes

Esta guía explica cómo desplegar el stack de SonarQube Metrics en un cluster de Kubernetes.

## 📋 Prerequisitos

- Kubernetes cluster (v1.24+)
- kubectl configurado
- kustomize (v4.0+) o kubectl con soporte de kustomize
- Acceso a un registry de imágenes Docker (para el collector)

## 📁 Estructura de Archivos

```
k8s/
├── kustomization.yaml              # Archivo principal de Kustomize
├── namespace.yaml                  # Namespace dedicado
├── configmap.yaml                  # Configuración general
├── secrets.yaml                    # Credenciales (⚠️ modificar antes de aplicar)
├── ingress.yaml                    # Ingress para acceso externo (opcional)
├── postgres/
│   ├── pvc.yaml                    # PersistentVolumeClaim
│   ├── configmap-init.yaml         # Script de inicialización SQL
│   ├── deployment.yaml             # Deployment de PostgreSQL
│   └── service.yaml                # Service de PostgreSQL
├── grafana/
│   ├── pvc.yaml                    # PersistentVolumeClaim
│   ├── configmap-datasource.yaml   # Configuración del datasource
│   ├── configmap-dashboard-provider.yaml  # Provider de dashboards
│   ├── deployment.yaml             # Deployment de Grafana
│   └── service.yaml                # Service de Grafana
├── collector/
│   └── deployment.yaml             # Deployment del Collector
└── dashboards/
    ├── sonarqube-overview.json     # Dashboard por proyecto
    └── sonarqube-all-projects.json # Dashboard general
```

## 🔧 Configuración

### 1. Construir y publicar la imagen del Collector

```bash
# Desde la raíz del proyecto
cd collector

# Construir la imagen
docker build -t tu-registry.com/sonarqube-collector:v1.0.0 .

# Publicar al registry
docker push tu-registry.com/sonarqube-collector:v1.0.0
```

### 2. Configurar Secrets (⚠️ IMPORTANTE)

Edita `k8s/secrets.yaml` con tus credenciales:

```yaml
stringData:
  POSTGRES_USER: "metrics"
  POSTGRES_PASSWORD: "tu_password_seguro"   # ⚠️ CAMBIAR
  GRAFANA_USER: "admin"
  GRAFANA_PASSWORD: "tu_password_grafana"   # ⚠️ CAMBIAR
  SONARQUBE_TOKEN: "squ_tu_token_aqui"      # ⚠️ CAMBIAR
```

> **⚠️ Nota de Seguridad:** En producción, considera usar:
> - Sealed Secrets
> - External Secrets Operator
> - HashiCorp Vault
> - AWS Secrets Manager / Azure Key Vault / GCP Secret Manager

### 3. Configurar ConfigMap

Edita `k8s/configmap.yaml`:

```yaml
data:
  SONARQUBE_URL: "https://tu-sonarqube.empresa.com"  # ⚠️ CAMBIAR
  COLLECTION_INTERVAL: "3600"   # Cada hora
  DATA_RETENTION_DAYS: "365"    # 1 año
```

### 4. Configurar el Deployment del Collector

Edita `k8s/collector/deployment.yaml`:

```yaml
spec:
  template:
    spec:
      containers:
        - name: collector
          image: tu-registry.com/sonarqube-collector:v1.0.0  # ⚠️ CAMBIAR
```

### 5. Configurar Datasource de Grafana (si cambias credenciales de PostgreSQL)

Edita `k8s/grafana/configmap-datasource.yaml`:

```yaml
user: metrics                    # Debe coincidir con POSTGRES_USER
secureJsonData:
  password: tu_password_seguro   # Debe coincidir con POSTGRES_PASSWORD
```

### 6. (Opcional) Configurar Ingress

Si quieres acceso externo, edita `k8s/ingress.yaml`:

```yaml
spec:
  rules:
    - host: sonarqube-metrics.tu-dominio.com  # ⚠️ CAMBIAR
```

Y descomenta la línea en `kustomization.yaml`:

```yaml
resources:
  # ...
  - ingress.yaml  # Descomentar
```

## 🚀 Despliegue

### Opción 1: Usando Kustomize

```bash
# Ver los recursos que se van a crear
kubectl kustomize k8s/

# Aplicar
kubectl apply -k k8s/

# O con kustomize directamente
kustomize build k8s/ | kubectl apply -f -
```

### Opción 2: Usando kubectl apply

```bash
# Crear namespace primero
kubectl apply -f k8s/namespace.yaml

# Aplicar todo
kubectl apply -k k8s/
```

## ✅ Verificar Despliegue

```bash
# Ver todos los recursos
kubectl -n sonarqube-metrics get all

# Ver pods
kubectl -n sonarqube-metrics get pods -w

# Ver logs del collector
kubectl -n sonarqube-metrics logs -f deployment/collector

# Ver logs de PostgreSQL
kubectl -n sonarqube-metrics logs -f deployment/postgres

# Ver logs de Grafana
kubectl -n sonarqube-metrics logs -f deployment/grafana
```

## 🌐 Acceder a Grafana

### Opción 1: Port Forward (desarrollo/pruebas)

```bash
kubectl -n sonarqube-metrics port-forward svc/grafana 3000:3000
```

Acceder a: http://localhost:3000

### Opción 2: NodePort

Cambia el Service de Grafana a NodePort:

```yaml
spec:
  type: NodePort
  ports:
    - port: 3000
      targetPort: 3000
      nodePort: 30300  # Puerto externo
```

### Opción 3: LoadBalancer (Cloud)

```yaml
spec:
  type: LoadBalancer
```

### Opción 4: Ingress

Usa el archivo `ingress.yaml` configurado.

## 🔄 Actualizar

### Actualizar configuración

```bash
kubectl apply -k k8s/
```

### Actualizar imagen del collector

```bash
# Construir nueva imagen
docker build -t tu-registry.com/sonarqube-collector:v1.0.1 ./collector
docker push tu-registry.com/sonarqube-collector:v1.0.1

# Actualizar deployment
kubectl -n sonarqube-metrics set image deployment/collector \
  collector=tu-registry.com/sonarqube-collector:v1.0.1
```

### Reiniciar collector

```bash
kubectl -n sonarqube-metrics rollout restart deployment/collector
```

## 🗑️ Desinstalar

```bash
# Eliminar todos los recursos (mantiene PVCs)
kubectl delete -k k8s/

# Eliminar incluyendo datos persistentes
kubectl delete namespace sonarqube-metrics
```

## 🛠️ Troubleshooting

### Collector no conecta a PostgreSQL

```bash
# Verificar que PostgreSQL está listo
kubectl -n sonarqube-metrics get pods -l app.kubernetes.io/name=postgres

# Ver logs de PostgreSQL
kubectl -n sonarqube-metrics logs deployment/postgres

# Probar conexión
kubectl -n sonarqube-metrics exec -it deployment/postgres -- \
  psql -U metrics -d sonarqube_metrics -c "SELECT 1"
```

### Collector no conecta a SonarQube

```bash
# Ver logs del collector
kubectl -n sonarqube-metrics logs deployment/collector

# Verificar DNS
kubectl -n sonarqube-metrics exec -it deployment/collector -- \
  nslookup tu-sonarqube.empresa.com
```

### Grafana no muestra datos

```bash
# Verificar que hay datos en PostgreSQL
kubectl -n sonarqube-metrics exec -it deployment/postgres -- \
  psql -U metrics -d sonarqube_metrics -c "SELECT COUNT(*) FROM projects"

# Reiniciar Grafana para recargar provisioning
kubectl -n sonarqube-metrics rollout restart deployment/grafana
```

### Ver eventos del namespace

```bash
kubectl -n sonarqube-metrics get events --sort-by='.lastTimestamp'
```

## 📊 Monitoreo

### Métricas de recursos

```bash
# CPU y memoria de los pods
kubectl -n sonarqube-metrics top pods
```

### Espacio en disco de PostgreSQL

```bash
kubectl -n sonarqube-metrics exec -it deployment/postgres -- \
  psql -U metrics -d sonarqube_metrics -c "SELECT pg_size_pretty(pg_database_size('sonarqube_metrics'))"
```

## 🔐 Seguridad en Producción

1. **Usa Secrets externos** (Vault, External Secrets, etc.)
2. **Habilita TLS** en el Ingress
3. **Configura NetworkPolicies** para restringir tráfico
4. **Usa RBAC** para limitar acceso al namespace
5. **Configura PodSecurityPolicies** o Pod Security Standards
6. **Habilita audit logging** en el cluster

## 📝 Notas

- El collector espera a que PostgreSQL esté listo antes de comenzar
- Los dashboards se provisionan automáticamente al iniciar Grafana
- Los datos se persisten en PVCs, sobreviven a reinicios de pods
- La retención de datos se maneja automáticamente (default: 1 año)

