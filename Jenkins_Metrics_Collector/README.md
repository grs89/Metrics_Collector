<p align="center">
  <img src="https://www.jenkins.io/images/logos/jenkins/jenkins.svg" alt="Jenkins" width="80" height="80"/>
  &nbsp;&nbsp;&nbsp;&nbsp;
  <img src="https://raw.githubusercontent.com/grafana/grafana/main/public/img/grafana_icon.svg" alt="Grafana" width="80" height="80"/>
</p>

<h1 align="center">🔧 Jenkins Metrics Collector</h1>

<p align="center">
  <strong>Sistema de monitoreo y visualización del historial de builds de Jenkins</strong>
</p>

<p align="center">
  <a href="#-características">Características</a> •
  <a href="#-arquitectura">Arquitectura</a> •
  <a href="#-opciones-de-despliegue">Despliegue</a> •
  <a href="#-dashboards">Dashboards</a> •
  <a href="#-inicio-rápido">Inicio Rápido</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python" alt="Python"/>
  <img src="https://img.shields.io/badge/PostgreSQL-16-blue?style=flat-square&logo=postgresql" alt="PostgreSQL"/>
  <img src="https://img.shields.io/badge/Grafana-10.2-orange?style=flat-square&logo=grafana" alt="Grafana"/>
  <img src="https://img.shields.io/badge/Docker-Compose-blue?style=flat-square&logo=docker" alt="Docker"/>
  <img src="https://img.shields.io/badge/Kubernetes-ready-326CE5?style=flat-square&logo=kubernetes" alt="Kubernetes"/>
</p>

---

## 📋 Descripción

**Jenkins Metrics Collector** es una solución completa para recopilar, almacenar y visualizar métricas del historial de builds de Jenkins. Permite monitorear en tiempo real el rendimiento de tus pipelines CI/CD, analizar tendencias y hacer seguimiento de versiones deployadas.

El sistema se conecta a un Jenkins existente mediante su API REST, exporta los datos a PostgreSQL y los visualiza mediante dashboards interactivos en Grafana.

## ✨ Características

| Característica | Descripción |
|----------------|-------------|
| 📊 **Métricas Completas** | Recopila builds, resultados, duraciones, versiones y más |
| 🔄 **Polling Automático** | Sincronización continua con Jenkins configurable |
| 📈 **Dashboards Preconstruidos** | 3 dashboards Grafana listos para usar |
| 🗂️ **Soporte de Carpetas** | Explora jobs en carpetas y multibranch pipelines |
| 🧹 **Retención Automática** | Limpieza de datos con más de 1 año de antigüedad |
| 🔒 **Autenticación** | Soporte para tokens API de Jenkins |
| 🐳 **Containerizado** | Despliegue sencillo con Docker Compose o Kubernetes |

## 🏗️ Arquitectura

```
                                    ┌─────────────────────────────────────────────────────────┐
                                    │              Jenkins Metrics Collector                   │
                                    └─────────────────────────────────────────────────────────┘
                                                            │
        ┌───────────────────────────────────────────────────┼───────────────────────────────────────────────────┐
        │                                                   │                                                   │
        ▼                                                   ▼                                                   ▼
┌───────────────────┐                             ┌───────────────────┐                             ┌───────────────────┐
│                   │      API REST / JSON        │                   │      SQL                   │                   │
│     Jenkins       │─────────────────────────────│  Metrics Exporter │───────────────────────────│    PostgreSQL     │
│   (existente)     │     Polling periódico       │     (Python)      │     Inserción de datos    │     (Docker)      │
│                   │                             │                   │                           │                   │
└───────────────────┘                             └───────────────────┘                           └─────────┬─────────┘
                                                                                                           │
                                                                                                           │ Consultas SQL
                                                                                                           │
                                                                                                  ┌────────▼────────┐
                                                                                                  │                 │
                                                                                                  │     Grafana     │
                                                                                                  │    Dashboards   │
                                                                                                  │                 │
                                                                                                  └─────────────────┘
```

### Componentes

| Componente | Tecnología | Descripción |
|------------|------------|-------------|
| **Metrics Exporter** | Python 3.11 | Consulta la API de Jenkins y almacena datos en PostgreSQL |
| **Base de Datos** | PostgreSQL 16 | Almacena historial de builds, versiones y estadísticas |
| **Visualización** | Grafana 10.2 | Dashboards interactivos con métricas y gráficos |

## 📦 Opciones de Despliegue

El proyecto soporta múltiples métodos de despliegue para adaptarse a diferentes infraestructuras:

### 🐳 Docker Compose (Recomendado)

Ideal para entornos locales, desarrollo o infraestructura basada en Docker.

```bash
cd Jenkis-Docker
make init       # Crear archivo .env
make build      # Construir imágenes
make up         # Iniciar servicios
```

📖 **[Ver documentación completa de Docker →](./Jenkis-Docker/README.md)**

### ☸️ Kubernetes

Para despliegues en clústeres Kubernetes con alta disponibilidad.

```bash
cd Jenkis-K8S

# Configurar secrets
nano secrets/jenkins-secret.yaml

# Desplegar con Kustomize
kubectl apply -k .
```

📖 **[Ver documentación completa de Kubernetes →](./Jenkis-K8S/README.md)**

## 📊 Dashboards

El sistema incluye **3 dashboards preconstruidos** para Grafana:

### 1️⃣ Jenkins - Overview
Vista general de todos los jobs con:
- Total de builds y tasa de éxito
- Historial temporal de builds
- Distribución de resultados (SUCCESS, FAILURE, UNSTABLE, ABORTED)
- Top 10 jobs más activos
- Duración promedio de builds

### 2️⃣ Jenkins - Detalle por Job
Métricas específicas por job:
- Selector interactivo de jobs
- Historial de builds del job seleccionado
- Tendencia de duración en el tiempo
- Gauge de tasa de éxito
- Tabla detallada con todos los builds

### 3️⃣ Jenkins - Historial de Versiones
Seguimiento de versiones deployadas:
- Timeline de versiones por job
- Top versiones más deployadas
- Primera y última aparición de cada versión
- Historial completo con filtros

## 🚀 Inicio Rápido

### Requisitos Previos

- Docker y Docker Compose instalados
- Jenkins existente accesible por red
- Token de API de Jenkins (recomendado)

### Pasos de Instalación

```bash
# 1. Clonar o navegar al repositorio
cd Jenkis-Docker

# 2. Crear archivo de configuración
cp env.example .env

# 3. Editar configuración con datos de tu Jenkins
nano .env    # o tu editor preferido
```

**Configuración mínima requerida en `.env`:**

```env
JENKINS_URL=http://tu-servidor-jenkins:8080
JENKINS_USER=tu-usuario
JENKINS_TOKEN=tu-api-token
```

```bash
# 4. Iniciar los servicios
docker-compose up -d --build

# 5. Verificar que todo funciona
docker-compose ps
docker-compose logs -f metrics-exporter
```

### Acceder a Grafana

| Campo | Valor |
|-------|-------|
| **URL** | http://localhost:3000 |
| **Usuario** | admin |
| **Contraseña** | admin123 |

## 🗄️ Modelo de Datos

### Tablas Principales

```sql
-- Historial de todos los builds
jenkins_builds (
    job_name, build_number, version, result,
    duration_ms, timestamp, description
)

-- Estadísticas agregadas por job  
jenkins_job_summary (
    job_name, total_builds, success_count,
    failure_count, avg_duration_ms, last_version
)

-- Historial de versiones deployadas
jenkins_versions (
    job_name, version, total_builds,
    first_seen, last_seen
)
```

### Retención de Datos

- **Período**: 1 año
- **Limpieza**: Automática (diaria) y manual disponible
- **Vistas**: Métricas diarias, historial de versiones, últimas versiones

## 🔧 Comandos Útiles

El proyecto incluye un `Makefile` con comandos útiles:

```bash
make help          # Ver todos los comandos disponibles
make up            # Iniciar servicios
make down          # Detener servicios
make logs          # Ver logs de todos los servicios
make logs-exporter # Ver logs del exportador
make db-shell      # Abrir shell de PostgreSQL
make db-stats      # Ver estadísticas de la base de datos
make db-jobs       # Ver resumen de todos los jobs
make cleanup       # Ejecutar limpieza de datos antiguos
make clean         # Detener y eliminar volúmenes (⚠️ BORRA DATOS)
```

## 🐛 Troubleshooting

### El exportador no conecta con Jenkins

```bash
# Ver logs del exportador
docker-compose logs -f metrics-exporter

# Verificar conectividad desde el contenedor
docker-compose exec metrics-exporter curl -v $JENKINS_URL/api/json
```

### No aparecen datos en Grafana

1. Verificar que el exportador está funcionando correctamente
2. Revisar que hay datos en PostgreSQL:
   ```bash
   make db-shell
   SELECT COUNT(*) FROM jenkins_builds;
   ```
3. Verificar la conexión del datasource en Grafana

### Reiniciar servicios

```bash
docker-compose restart              # Reiniciar todo
docker-compose restart metrics-exporter  # Solo el exportador
```

## 📁 Estructura del Proyecto

```
Jenkis/
├── README.md                    # Este archivo
├── Jenkis-Docker/               # Implementación con Docker Compose
│   ├── docker-compose.yml       # Orquestación de servicios
│   ├── env.example              # Plantilla de configuración
│   ├── Makefile                 # Comandos útiles
│   ├── README.md                # Documentación detallada Docker
│   ├── grafana/                 # Configuración de Grafana
│   │   ├── dashboards/          # Dashboards JSON
│   │   └── provisioning/        # Auto-provisioning
│   ├── metrics-exporter/        # Exportador Python
│   │   ├── Dockerfile
│   │   ├── exporter.py
│   │   └── requirements.txt
│   └── postgres/
│       └── init/                # Scripts de inicialización SQL
└── Jenkis-K8S/                  # Implementación Kubernetes
    ├── kustomization.yaml       # Kustomize para despliegue unificado
    ├── namespace.yaml           # Namespace dedicado
    ├── README.md                # Documentación detallada K8S
    ├── configmaps/              # ConfigMaps (SQL, Grafana, dashboards)
    ├── deployments/             # Deployments (Postgres, Grafana, Exporter)
    ├── docker/                  # Dockerfile del exportador
    ├── ingress/                 # Ingress para acceso externo
    ├── secrets/                 # Secrets (credenciales)
    ├── services/                # Services (ClusterIP, NodePort)
    └── storage/                 # PersistentVolumeClaims
```

## 🤝 Contribuir

¿Encontraste un bug o tienes una sugerencia? ¡Las contribuciones son bienvenidas!

1. Fork del repositorio
2. Crear rama de feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit de cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo [LICENSE](LICENSE) para más detalles.

---


