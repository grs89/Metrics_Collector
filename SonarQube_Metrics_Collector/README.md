# 📊 SonarQube Metrics History - Grafana & PostgreSQL

Sistema completo para recolectar, almacenar y visualizar el historial de métricas de calidad de código de SonarQube.

![Grafana](https://img.shields.io/badge/Grafana-10.2-orange?logo=grafana)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue?logo=postgresql)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)
![Kubernetes](https://img.shields.io/badge/Kubernetes-Ready-326CE5?logo=kubernetes)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python)

## 🎯 Descripción

Este proyecto proporciona una solución lista para usar que permite:

- **Recolectar** métricas de todos tus proyectos de SonarQube automáticamente
- **Almacenar** el historial de métricas en PostgreSQL
- **Visualizar** tendencias y evolución en dashboards de Grafana preconfigurados
- **Monitorear** la calidad del código a lo largo del tiempo

## 🏗️ Arquitectura

```
┌─────────────────┐    ┌──────────────┐    ┌──────────────┐
│   SonarQube     │───▶│   Collector  │───▶│  PostgreSQL  │
│   (existente)   │    │   (Python)   │    │   (metrics)  │
└─────────────────┘    └──────────────┘    └──────┬───────┘
                                                  │
                                                  ▼
                                          ┌──────────────┐
                                          │   Grafana    │
                                          │ (dashboards) │
                                          └──────────────┘
```

## 📈 Métricas Recolectadas

| Categoría | Métricas |
|-----------|----------|
| **Seguridad** | 🔓 Vulnerabilities, 🔥 Security Hotspots, Hotspots Reviewed % |
| **Bugs** | 🐛 Bugs, Reliability Rating |
| **Mantenibilidad** | 🦨 Code Smells, ⏱️ Technical Debt (sqale_index), Maintainability Rating |
| **Cobertura** | ✅ Coverage %, Lines to Cover, Uncovered Lines |
| **Duplicación** | 📋 Duplicated Lines %, Duplicated Blocks, Duplicated Files |
| **Tamaño** | 📏 Lines of Code (ncloc) |

## 🚀 Opciones de Despliegue

Este proyecto incluye dos opciones de despliegue, cada una con su documentación detallada:

### 🐳 Docker Compose (Recomendado para desarrollo y entornos simples)

Ideal para:
- Desarrollo local
- Servidores individuales
- Pruebas y evaluación

```bash
cd SonarQube-docker
cp env.example .env
# Editar .env con tus configuraciones
docker-compose up -d
```

📖 **[Ver documentación completa de Docker →](./SonarQube-docker/README.md)**

### ☸️ Kubernetes (Recomendado para producción)

Ideal para:
- Entornos de producción
- Alta disponibilidad
- Integración con infraestructura cloud

```bash
cd SonarQube-k8s
# Configurar secrets.yaml y configmap.yaml
kubectl apply -k .
```

📖 **[Ver documentación completa de Kubernetes →](./SonarQube-k8s/README.md)**

## ✨ Características

- **📊 Dashboards preconfigurados**: Vista general de todos los proyectos y vista detallada por proyecto
- **⏰ Recolección automática**: Configurable (por defecto cada hora)
- **📅 Retención de datos**: Configurable (por defecto 1 año)
- **🔄 Commits inmediatos**: Los datos aparecen en Grafana al instante
- **🧹 Limpieza automática**: Eliminación de datos antiguos según política de retención
- **📈 Historial de versiones**: Seguimiento de métricas por versión del proyecto

## 📋 Requisitos Previos

- **SonarQube** accesible vía API (v8.x o superior)
- **Token de SonarQube** con permisos de lectura
- **Docker + Docker Compose** (para despliegue con Docker)
- **Kubernetes v1.24+** (para despliegue en K8s)

## 🔐 Generar Token de SonarQube

1. Accede a tu instancia de SonarQube
2. Click en tu avatar → **My Account**
3. Ve a la pestaña **Security**
4. En **Generate Tokens**:
   - Nombre: `grafana-metrics-collector`
   - Type: `User Token`
5. Click en **Generate** y copia el token

## 📁 Estructura del Proyecto

```
.
├── README.md                    # Este archivo
├── SonarQube-docker/            # Despliegue con Docker Compose
│   ├── docker-compose.yml
│   ├── env.example
│   ├── README.md
│   ├── collector/               # Servicio recolector (Python)
│   │   ├── collector.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── grafana/                 # Configuración de Grafana
│   │   ├── dashboards/
│   │   └── provisioning/
│   └── init-db/                 # Scripts de inicialización DB
│       └── 01-schema.sql
└── SonarQube-k8s/               # Despliegue con Kubernetes
    ├── kustomization.yaml
    ├── namespace.yaml
    ├── configmap.yaml
    ├── secrets.yaml
    ├── README.md
    ├── collector/
    ├── grafana/
    ├── postgres/
    └── dashboards/
```

## 🌐 API de SonarQube Utilizada

El collector utiliza las siguientes APIs:

| Endpoint | Descripción |
|----------|-------------|
| `GET /api/projects/search` | Lista de proyectos |
| `GET /api/measures/component` | Métricas del proyecto |
| `GET /api/project_analyses/search` | Información de análisis y versión |

## 🛠️ Solución de Problemas

Consulta la documentación específica de cada tipo de despliegue:

- [Troubleshooting Docker](./SonarQube-docker/README.md#️-solución-de-problemas)
- [Troubleshooting Kubernetes](./SonarQube-k8s/README.md#️-troubleshooting)

## 📝 Licencia

MIT License - Siéntete libre de usar y modificar según tus necesidades.

---

**¿Preguntas o problemas?** Abre un issue en el repositorio.
