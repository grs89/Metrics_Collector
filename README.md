# 📊 Metrics Collector All-in-One

Una solución integral y unificada para la recolección, almacenamiento y visualización de métricas críticas de **Jenkins** y **SonarQube**. Este proyecto optimiza la infraestructura mediante el uso de contenedores compartidos para base de datos y visualización, facilitando el monitoreo de la salud del ciclo de vida de desarrollo de software (SDLC).

---

## 🚀 Características Principales

*   **Centralización Total**: Monitoreo de Jenkins, SonarQube y Jira en un solo ecosistema.
*   **Infraestructura Eficiente**: Uso de una única instancia de PostgreSQL y Grafana para múltiples fuentes de datos.
*   **Inicialización Auto-Suficiente**: Scripts SQL automáticos que crean bases de datos, tablas y permisos al arrancar.
*   **Dashboards "Out-of-the-Box"**: Paneles de Grafana pre-configurados para visualización inmediata.
*   **Gestión de Retención**: Limpieza automática de datos antiguos (configurable en días) para mantener el rendimiento.
*   **Dual-Deployment**: Soporte nativo y optimizado tanto para **Docker Compose** como para **Kubernetes**.

---

## 🛠️ Tech Stack

*   **Backend**: Python 3.11 (Exporters personalizados).
*   **Database**: PostgreSQL 15 (Alpine based).
*   **Visualization**: Grafana 10.
*   **Orchestration**: Docker Compose & Kubernetes (Kustomize ready).

---

## 📂 Estructura del Proyecto

```text
.
├── Metrics_Collector-docker/         # Configuración para Docker Compose
│   ├── .env.example                  # Variables de entorno de referencia
│   ├── docker-compose.yml            # Orquestación de todos los servicios
│   ├── exporters/                    # Fuente de los recolectores (Python 3.11)
│   │   ├── argocd/                   # Recolector de Apps ArgoCD
│   │   ├── argorollouts/             # Recolector de Canary Rollouts
│   │   ├── git/                      # Recolector DORA (GitHub/GitLab)
│   │   ├── jenkins/                  # Recolector de Jobs y Builds
│   │   ├── jira/                     # Recolector de Tickets y Sprints
│   │   └── sonarqube/                # Recolector de Calidad de Código
│   ├── grafana/                      # Visualización y Provisioning
│   │   ├── dashboards/               # Definiciones JSON de dashboards
│   │   └── provisioning/             # Configuración automática de Grafana
│   └── postgres/                     # Persistencia de Datos
│       └── init/                     # Scripts SQL de inicialización (00-07)
├── Metrics_Collector-kubernetes/      # Manifiestos para K8s (Kustomize)
│   ├── base/                         # Infraestructura base (DB, Grafana)
│   └── [collector]/                  # Manifiestos por cada servicio
├── ARCHITECTURE.md                   # Diagramas y flujo de datos
└── README.md                         # Esta guía
```

---

## ⚙️ Instalación y Despliegue

### 🐳 Docker Compose (Recomendado para inicio rápido)

1.  **Configura el entorno**:
    ```bash
    cd Metrics_Collector-docker
    cp .env.example .env
    ```
    *Edita el archivo `.env` con las URLs y Tokens de tus servidores Jenkins y SonarQube.*

2.  **Inicia los servicios**:
    ```bash
    docker-compose up -d --build
    ```

3.  **Acceso**:
    *   **Grafana**: `http://localhost:3000` (Usuario/Pass definidos en `.env`).
    *   **Dashboard Jira**: `http://localhost:3000/d/jira-overview`
    *   **Postgres**: Accesible internamente en el puerto `5432`.

### ☸️ Kubernetes

1.  **Desplegar Infraestructura Base**:
    ```bash
    kubectl apply -f Metrics_Collector-kubernetes/base/
    ```

2.  **Configurar Secretos**:
    Completa los archivos en `Metrics_Collector-kubernetes/jenkins/secrets` y `Metrics_Collector-kubernetes/sonarqube/secrets`.

3.  **Desplegar Colectores**:
    ```bash
    # Desplegar Jenkins Collector
    kubectl apply -k Metrics_Collector-kubernetes/jenkins/
    
    # Desplegar SonarQube Collector
    kubectl apply -k Metrics_Collector-kubernetes/sonarqube/
    
    # Desplegar Jira Collector
    kubectl apply -k Metrics_Collector-kubernetes/jira/
    ```

---

## 🔧 Configuración Avanzada

### Variables de Entorno Clave

| Variable | Descripción | Default |
| :--- | :--- | :--- |
| `JENKINS_POLL_INTERVAL` | Frecuencia de escaneo de Jenkins (segundos) | `60` |
| `SONARQUBE_POLL_INTERVAL`| Frecuencia de escaneo de SonarQube (segundos)| `3600` |
| `DATA_RETENTION_DAYS` | Días que se conservan las métricas históricas | `365` |
| `POSTGRES_DB` | Base de datos principal de configuración | `metrics_main` |

### Monitoreo de Logs
Para verificar la salud de los colectores:
```bash
docker logs jenkins-metrics-collector -f
docker logs sonarqube-metrics-collector -f
docker logs jira-metrics-collector -f
```

---

## 📜 Licencia

Este proyecto está bajo la licencia MIT. Consulta el archivo [LICENSE](LICENSE) para más detalles.
