# ☸️ Jenkins Metrics Collector - Kubernetes

Despliegue de Jenkins Metrics Collector en Kubernetes usando manifiestos nativos y Kustomize.

## 📋 Requisitos Previos

- Kubernetes 1.24+
- kubectl configurado
- Acceso a un registro de contenedores (para la imagen del exporter)
- Jenkins existente accesible desde el clúster
- StorageClass disponible para PersistentVolumes

## 🏗️ Arquitectura en Kubernetes

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Namespace: jenkins-metrics                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────┐    ┌─────────────────┐    ┌─────────────────────┐ │
│  │   Ingress   │───▶│ Grafana Service │───▶│  Grafana Deployment │ │
│  │  (opcional) │    │    ClusterIP    │    │    (1 replica)      │ │
│  └─────────────┘    └─────────────────┘    └──────────┬──────────┘ │
│                                                        │            │
│                                                        ▼            │
│                                             ┌─────────────────────┐ │
│                                             │     Grafana PVC     │ │
│                                             │        2Gi          │ │
│                                             └─────────────────────┘ │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                                                                  ││
│  │  ┌─────────────────┐    ┌──────────────────────────────────┐   ││
│  │  │ Postgres Service│───▶│     PostgreSQL Deployment        │   ││
│  │  │    ClusterIP    │    │         (1 replica)              │   ││
│  │  └────────┬────────┘    └────────────────┬─────────────────┘   ││
│  │           │                              │                      ││
│  │           │                              ▼                      ││
│  │           │                    ┌─────────────────────┐          ││
│  │           │                    │    Postgres PVC     │          ││
│  │           │                    │        10Gi         │          ││
│  │           │                    └─────────────────────┘          ││
│  │           │                                                      ││
│  │           │              ┌──────────────────────────────────┐   ││
│  │           └─────────────▶│    Metrics Exporter Deployment   │   ││
│  │                          │         (1 replica)              │   ││
│  │                          └──────────────────────────────────┘   ││
│  │                                           │                      ││
│  └───────────────────────────────────────────┼──────────────────────┘│
│                                              │                       │
│                                              ▼                       │
│                                     ┌───────────────┐                │
│                                     │    Jenkins    │                │
│                                     │  (externo)    │                │
│                                     └───────────────┘                │
└──────────────────────────────────────────────────────────────────────┘
```

## 📁 Estructura de Directorios

```
Jenkis-K8S/
├── kustomization.yaml              # Kustomize para despliegue unificado
├── namespace.yaml                  # Namespace dedicado
├── README.md                       # Esta documentación
├── configmaps/
│   ├── exporter-configmap.yaml     # Configuración del exportador
│   ├── grafana-dashboards-configmap.yaml  # Dashboards JSON
│   ├── grafana-provisioning-configmap.yaml # Datasources y provisioning
│   └── postgres-init-configmap.yaml # Scripts SQL de inicialización
├── deployments/
│   ├── grafana-deployment.yaml     # Deployment de Grafana
│   ├── metrics-exporter-deployment.yaml # Deployment del exportador
│   └── postgres-deployment.yaml    # Deployment de PostgreSQL
├── docker/
│   ├── Dockerfile                  # Imagen del exportador
│   ├── exporter.py                 # Script Python
│   └── requirements.txt            # Dependencias Python
├── ingress/
│   └── grafana-ingress.yaml        # Ingress para acceso externo
├── secrets/
│   ├── grafana-secret.yaml         # Credenciales de Grafana
│   ├── jenkins-secret.yaml         # Credenciales de Jenkins
│   └── postgres-secret.yaml        # Credenciales de PostgreSQL
├── services/
│   ├── grafana-service.yaml        # Service ClusterIP y NodePort
│   └── postgres-service.yaml       # Service ClusterIP
└── storage/
    ├── grafana-pvc.yaml            # PVC para Grafana
    └── postgres-pvc.yaml           # PVC para PostgreSQL
```

## 🚀 Despliegue

### 1. Construir la imagen del exportador

```bash
cd docker

# Construir imagen
docker build -t jenkins-metrics-exporter:latest .

# Etiquetar para tu registro
docker tag jenkins-metrics-exporter:latest tu-registro.com/jenkins-metrics-exporter:latest

# Subir al registro
docker push tu-registro.com/jenkins-metrics-exporter:latest
```

### 2. Configurar Secrets

Edita los archivos de secrets con tus credenciales reales:

```bash
# Editar credenciales de Jenkins
nano secrets/jenkins-secret.yaml
```

```yaml
stringData:
  JENKINS_URL: "http://tu-jenkins:8080"
  JENKINS_USER: "tu-usuario"
  JENKINS_TOKEN: "tu-api-token"
```

```bash
# Editar credenciales de PostgreSQL (opcional)
nano secrets/postgres-secret.yaml

# Editar credenciales de Grafana (opcional)
nano secrets/grafana-secret.yaml
```

### 3. Ajustar la imagen del exportador

Edita `kustomization.yaml` para usar tu registro:

```yaml
images:
  - name: jenkins-metrics-exporter
    newName: tu-registro.com/jenkins-metrics-exporter
    newTag: latest
```

### 4. Desplegar con Kustomize

```bash
# Vista previa de lo que se desplegará
kubectl kustomize .

# Aplicar todos los recursos
kubectl apply -k .
```

### 5. Despliegue manual (sin Kustomize)

```bash
# Crear namespace
kubectl apply -f namespace.yaml

# Aplicar secrets
kubectl apply -f secrets/

# Aplicar configmaps
kubectl apply -f configmaps/

# Aplicar storage
kubectl apply -f storage/

# Aplicar deployments
kubectl apply -f deployments/

# Aplicar services
kubectl apply -f services/

# (Opcional) Aplicar ingress
kubectl apply -f ingress/
```

## 🔍 Verificar Despliegue

```bash
# Ver todos los recursos en el namespace
kubectl get all -n jenkins-metrics

# Ver pods
kubectl get pods -n jenkins-metrics

# Ver logs del exportador
kubectl logs -f deployment/metrics-exporter -n jenkins-metrics

# Ver logs de PostgreSQL
kubectl logs -f deployment/postgres -n jenkins-metrics

# Ver logs de Grafana
kubectl logs -f deployment/grafana -n jenkins-metrics
```

## 🌐 Acceder a Grafana

### Opción 1: Port-Forward (desarrollo)

```bash
kubectl port-forward svc/grafana-service 3000:3000 -n jenkins-metrics
```

Acceder a: http://localhost:3000

### Opción 2: NodePort

El servicio NodePort está configurado en el puerto `30300`:

```bash
# Obtener IP del nodo
kubectl get nodes -o wide

# Acceder a: http://<NODE_IP>:30300
```

### Opción 3: Ingress

Edita `ingress/grafana-ingress.yaml` con tu dominio:

```yaml
spec:
  rules:
    - host: jenkins-metrics.tu-dominio.com
```

```bash
kubectl apply -f ingress/grafana-ingress.yaml
```

### Credenciales por defecto

| Campo | Valor |
|-------|-------|
| **Usuario** | admin |
| **Contraseña** | admin123 |

## 🔧 Configuración Avanzada

### Ajustar StorageClass

Si necesitas una StorageClass específica, edita los PVC:

```yaml
spec:
  storageClassName: tu-storage-class
```

### Ajustar Recursos

Edita los límites de recursos en cada deployment:

```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

### Configurar TLS en Ingress

```yaml
spec:
  tls:
    - hosts:
        - jenkins-metrics.tu-dominio.com
      secretName: grafana-tls
```

### Cambiar intervalo de polling

Edita `configmaps/exporter-configmap.yaml`:

```yaml
data:
  POLL_INTERVAL: "30"  # En segundos
```

## 🐛 Troubleshooting

### El exportador no conecta con Jenkins

```bash
# Ver logs detallados
kubectl logs -f deployment/metrics-exporter -n jenkins-metrics

# Verificar conectividad desde el pod
kubectl exec -it deployment/metrics-exporter -n jenkins-metrics -- curl -v http://tu-jenkins:8080/api/json
```

### PostgreSQL no arranca

```bash
# Ver eventos del pod
kubectl describe pod -l app.kubernetes.io/name=postgres -n jenkins-metrics

# Ver logs
kubectl logs -f deployment/postgres -n jenkins-metrics
```

### Grafana no muestra datos

```bash
# Verificar conexión con PostgreSQL
kubectl exec -it deployment/grafana -n jenkins-metrics -- nc -zv postgres-service 5432

# Verificar datos en la base de datos
kubectl exec -it deployment/postgres -n jenkins-metrics -- psql -U jenkins_metrics -d jenkins_metrics -c "SELECT COUNT(*) FROM jenkins_builds;"
```

### Reiniciar deployments

```bash
# Reiniciar un deployment específico
kubectl rollout restart deployment/metrics-exporter -n jenkins-metrics

# Reiniciar todos
kubectl rollout restart deployment -n jenkins-metrics
```

## 🗑️ Limpieza

```bash
# Eliminar todos los recursos
kubectl delete -k .

# O manualmente
kubectl delete namespace jenkins-metrics
```

## 📊 Dashboards Incluidos

1. **Jenkins - Overview**: Vista general con estadísticas globales
2. **Jenkins - Detalle por Job**: Métricas específicas por job con selector
3. **Jenkins - Historial de Versiones**: Seguimiento de versiones deployadas

## 🔄 Actualizaciones

### Actualizar imagen del exportador

```bash
# Construir nueva versión
docker build -t tu-registro.com/jenkins-metrics-exporter:v2 ./docker/
docker push tu-registro.com/jenkins-metrics-exporter:v2

# Actualizar deployment
kubectl set image deployment/metrics-exporter \
  metrics-exporter=tu-registro.com/jenkins-metrics-exporter:v2 \
  -n jenkins-metrics
```

### Actualizar dashboards

Edita `configmaps/grafana-dashboards-configmap.yaml` y aplica:

```bash
kubectl apply -f configmaps/grafana-dashboards-configmap.yaml
kubectl rollout restart deployment/grafana -n jenkins-metrics
```

---

📖 **[Volver a la documentación principal →](../README.md)**



