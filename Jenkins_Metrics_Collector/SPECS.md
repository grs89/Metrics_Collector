# 📋 Specification Coding - Jenkins Metrics Collector

## Document Information

| Campo | Valor |
|-------|-------|
| **Proyecto** | Jenkins Metrics Collector |
| **Versión** | 1.0.0 |
| **Fecha** | Diciembre 2024 |
| **Estado** | Production Ready |

---

## 1. Descripción General

### 1.1 Propósito
Sistema de recopilación, almacenamiento y visualización de métricas del historial de builds de Jenkins. Permite monitorear pipelines CI/CD, analizar tendencias de rendimiento y hacer seguimiento de versiones deployadas.

### 1.2 Alcance
- Recolección automática de datos de Jenkins vía API REST
- Almacenamiento persistente en PostgreSQL con retención de 1 año
- Visualización mediante dashboards Grafana preconstruidos
- Soporte para despliegue en Docker Compose y Kubernetes

### 1.3 Stakeholders
- Equipos de DevOps
- Desarrolladores
- QA Engineers
- Administradores de sistemas

---

## 2. Arquitectura del Sistema

### 2.1 Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           JENKINS METRICS COLLECTOR                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐                                                           │
│  │   Jenkins    │◄──────────────────────────────────────────────┐           │
│  │   Server     │                                               │           │
│  │  (External)  │                                               │           │
│  └──────┬───────┘                                               │           │
│         │                                                       │           │
│         │ HTTP/HTTPS (API REST)                                 │           │
│         │ Polling: configurable (default 60s)                   │           │
│         ▼                                                       │           │
│  ┌──────────────────────────────────────────────┐               │           │
│  │           METRICS EXPORTER                    │               │           │
│  │  ┌─────────────────────────────────────────┐ │               │           │
│  │  │  JenkinsClient                          │ │               │           │
│  │  │  - GET /api/json (jobs list)            │ │               │           │
│  │  │  - GET /job/{name}/api/json (builds)    │ │               │           │
│  │  │  - Recursive folder scanning            │ │               │           │
│  │  │  - Version extraction (regex)           │ │               │           │
│  │  └─────────────────────────────────────────┘ │               │           │
│  │  ┌─────────────────────────────────────────┐ │               │           │
│  │  │  PostgresExporter                       │ │               │           │
│  │  │  - Batch insert with ON CONFLICT       │ │               │           │
│  │  │  - Job summary updates                  │ │               │           │
│  │  │  - Automatic cleanup                    │ │               │           │
│  │  └─────────────────────────────────────────┘ │               │           │
│  └──────────────────┬───────────────────────────┘               │           │
│                     │                                           │           │
│                     │ SQL (psycopg2)                            │           │
│                     │ Port: 5432                                │           │
│                     ▼                                           │           │
│  ┌──────────────────────────────────────────────┐               │           │
│  │              POSTGRESQL 16                    │               │           │
│  │  ┌─────────────────────────────────────────┐ │               │           │
│  │  │  Tables:                                │ │               │           │
│  │  │  - jenkins_builds (main)                │ │               │           │
│  │  │  - jenkins_job_summary (aggregated)     │ │               │           │
│  │  │  - jenkins_versions (version tracking)  │ │               │           │
│  │  └─────────────────────────────────────────┘ │               │           │
│  │  ┌─────────────────────────────────────────┐ │               │           │
│  │  │  Functions:                             │ │               │           │
│  │  │  - cleanup_old_builds()                 │ │               │           │
│  │  │  - update_job_summary()                 │ │               │           │
│  │  │  - run_maintenance()                    │ │               │           │
│  │  └─────────────────────────────────────────┘ │               │           │
│  │  ┌─────────────────────────────────────────┐ │               │           │
│  │  │  Triggers:                              │ │               │           │
│  │  │  - trigger_update_version_stats         │ │               │           │
│  │  └─────────────────────────────────────────┘ │               │           │
│  └──────────────────┬───────────────────────────┘               │           │
│                     │                                           │           │
│                     │ SQL Queries                               │           │
│                     │ Port: 5432                                │           │
│                     ▼                                           │           │
│  ┌──────────────────────────────────────────────┐               │           │
│  │              GRAFANA 10.2                     │               │           │
│  │  ┌─────────────────────────────────────────┐ │               │           │
│  │  │  Datasource: PostgreSQL-Jenkins         │ │               │           │
│  │  │  - UID: postgres-jenkins                │ │               │           │
│  │  │  - Auto-provisioned                     │ │               │           │
│  │  └─────────────────────────────────────────┘ │               │           │
│  │  ┌─────────────────────────────────────────┐ │  ┌─────────┐ │           │
│  │  │  Dashboards:                            │ │  │ Plugins │ │           │
│  │  │  - jenkins-overview                     │ │  │ - clock │ │           │
│  │  │  - jenkins-job-details                  │ │  │ - pie   │ │           │
│  │  │  - jenkins-versions                     │ │  └─────────┘ │           │
│  │  └─────────────────────────────────────────┘ │               │           │
│  └──────────────────┬───────────────────────────┘               │           │
│                     │                                           │           │
│                     │ HTTP                                      │           │
│                     │ Port: 3000                                │           │
│                     ▼                                           │           │
│              ┌──────────────┐                                   │           │
│              │    Users     │                                   │           │
│              │  (Browser)   │                                   │           │
│              └──────────────┘                                   │           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Componentes

| Componente | Tecnología | Versión | Función |
|------------|------------|---------|---------|
| Metrics Exporter | Python | 3.11+ | Recolección de datos de Jenkins |
| Base de Datos | PostgreSQL | 16-alpine | Almacenamiento persistente |
| Visualización | Grafana | 10.2.0 | Dashboards y alertas |

### 2.3 Patrones de Diseño

- **Polling Pattern**: Consulta periódica a Jenkins API
- **Batch Processing**: Inserción masiva de registros
- **Upsert Pattern**: ON CONFLICT para evitar duplicados
- **Provisioning Pattern**: Auto-configuración de Grafana

---

## 3. Especificaciones de Componentes

### 3.1 Metrics Exporter

#### 3.1.1 Descripción
Script Python que actúa como puente entre Jenkins y PostgreSQL, extrayendo métricas de builds y almacenándolas para análisis.

#### 3.1.2 Clases Principales

```python
class JenkinsClient:
    """
    Cliente para interactuar con la API de Jenkins
    
    Métodos:
    - __init__(url: str, user: str, token: str)
    - _get(endpoint: str, params: dict) -> dict
    - get_all_jobs() -> List[Dict]
    - _get_jobs_recursive(path: str, jobs: List)
    - get_job_builds(job_path: str, limit: int) -> List[Dict]
    - is_available() -> bool
    """

class PostgresExporter:
    """
    Exportador de métricas a PostgreSQL
    
    Métodos:
    - __init__(host, port, database, user, password)
    - connect() -> bool
    - close()
    - get_existing_builds(job_name: str) -> set
    - insert_builds(builds: List[Dict]) -> int
    - update_job_summary(job_name: str)
    - run_cleanup()
    """
```

#### 3.1.3 Funciones Auxiliares

```python
def extract_version(build: Dict) -> str:
    """
    Extrae versión del build usando patrones regex
    
    Patrones soportados:
    - v?(\d+\.\d+\.\d+(?:-[\w.]+)?)  # v1.2.3, 1.2.3-beta
    - version[:\s]+(\S+)             # version: xxx
    - release[:\s]+(\S+)             # release: xxx
    - tag[:\s]+(\S+)                 # tag: xxx
    - \[(\d+\.\d+(?:\.\d+)?)\]       # [1.2.3]
    
    Returns: Versión encontrada o 'N/A'
    """

def wait_for_services(jenkins_url: str, pg_params: dict, max_retries: int) -> bool:
    """
    Espera a que Jenkins y PostgreSQL estén disponibles
    
    - Timeout por servicio: 5s
    - Intervalo entre reintentos: 10s
    - Máximo reintentos: 30 (default)
    """

def export_metrics(jenkins: JenkinsClient, postgres: PostgresExporter):
    """
    Función principal de exportación
    
    Flujo:
    1. Obtener todos los jobs de Jenkins
    2. Para cada job:
       a. Obtener builds existentes en BD
       b. Obtener builds desde Jenkins API
       c. Filtrar builds nuevos
       d. Insertar en PostgreSQL
       e. Actualizar resumen del job
    """
```

#### 3.1.4 Variables de Entorno

| Variable | Tipo | Default | Descripción |
|----------|------|---------|-------------|
| `JENKINS_URL` | string | `http://localhost:8080` | URL del servidor Jenkins |
| `JENKINS_USER` | string | `admin` | Usuario de Jenkins |
| `JENKINS_TOKEN` | string | `""` | Token API de Jenkins |
| `POSTGRES_HOST` | string | `postgres` | Host de PostgreSQL |
| `POSTGRES_PORT` | int | `5432` | Puerto de PostgreSQL |
| `POSTGRES_DB` | string | `jenkins_metrics` | Nombre de la base de datos |
| `POSTGRES_USER` | string | `jenkins_metrics` | Usuario de PostgreSQL |
| `POSTGRES_PASSWORD` | string | `jenkins_metrics_password` | Contraseña de PostgreSQL |
| `POLL_INTERVAL` | int | `60` | Intervalo de polling en segundos |

#### 3.1.5 Dependencias Python

```
requests>=2.31.0      # HTTP client para Jenkins API
psycopg2-binary>=2.9.9  # Driver PostgreSQL
python-dateutil>=2.8.2  # Manejo de fechas
```

---

### 3.2 PostgreSQL

#### 3.2.1 Esquema de Base de Datos

##### Tabla: jenkins_builds

```sql
CREATE TABLE jenkins_builds (
    id SERIAL PRIMARY KEY,
    job_name VARCHAR(500) NOT NULL,
    build_number INTEGER NOT NULL,
    version VARCHAR(255),
    display_name VARCHAR(500),
    result VARCHAR(50),
    duration_ms BIGINT DEFAULT 0,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_job_build UNIQUE (job_name, build_number)
);
```

| Columna | Tipo | Nullable | Descripción |
|---------|------|----------|-------------|
| id | SERIAL | NO | Identificador único auto-incremental |
| job_name | VARCHAR(500) | NO | Nombre completo del job (incluye ruta) |
| build_number | INTEGER | NO | Número de build |
| version | VARCHAR(255) | YES | Versión extraída del build |
| display_name | VARCHAR(500) | YES | Nombre visible del build |
| result | VARCHAR(50) | YES | Resultado: SUCCESS, FAILURE, UNSTABLE, ABORTED |
| duration_ms | BIGINT | NO | Duración en milisegundos |
| timestamp | TIMESTAMPTZ | NO | Fecha/hora del build |
| description | TEXT | YES | Descripción del build |
| created_at | TIMESTAMPTZ | NO | Fecha de inserción en BD |

**Índices:**
```sql
CREATE INDEX idx_builds_job_name ON jenkins_builds(job_name);
CREATE INDEX idx_builds_timestamp ON jenkins_builds(timestamp DESC);
CREATE INDEX idx_builds_result ON jenkins_builds(result);
CREATE INDEX idx_builds_version ON jenkins_builds(version);
CREATE INDEX idx_builds_job_timestamp ON jenkins_builds(job_name, timestamp DESC);
```

##### Tabla: jenkins_job_summary

```sql
CREATE TABLE jenkins_job_summary (
    id SERIAL PRIMARY KEY,
    job_name VARCHAR(500) NOT NULL UNIQUE,
    total_builds INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    unstable_count INTEGER DEFAULT 0,
    aborted_count INTEGER DEFAULT 0,
    avg_duration_ms BIGINT DEFAULT 0,
    last_build_number INTEGER,
    last_build_result VARCHAR(50),
    last_build_timestamp TIMESTAMP WITH TIME ZONE,
    last_version VARCHAR(255),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

| Columna | Tipo | Descripción |
|---------|------|-------------|
| job_name | VARCHAR(500) | Nombre único del job |
| total_builds | INTEGER | Total de builds registrados |
| success_count | INTEGER | Builds exitosos |
| failure_count | INTEGER | Builds fallidos |
| unstable_count | INTEGER | Builds inestables |
| aborted_count | INTEGER | Builds abortados |
| avg_duration_ms | BIGINT | Duración promedio |
| last_build_number | INTEGER | Último número de build |
| last_build_result | VARCHAR(50) | Resultado del último build |
| last_build_timestamp | TIMESTAMPTZ | Fecha del último build |
| last_version | VARCHAR(255) | Última versión deployada |
| updated_at | TIMESTAMPTZ | Última actualización |

##### Tabla: jenkins_versions

```sql
CREATE TABLE jenkins_versions (
    id SERIAL PRIMARY KEY,
    job_name VARCHAR(500) NOT NULL,
    version VARCHAR(255) NOT NULL,
    first_build_number INTEGER,
    last_build_number INTEGER,
    total_builds INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    first_seen TIMESTAMP WITH TIME ZONE,
    last_seen TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT unique_job_version UNIQUE (job_name, version)
);
```

| Columna | Tipo | Descripción |
|---------|------|-------------|
| job_name | VARCHAR(500) | Nombre del job |
| version | VARCHAR(255) | Versión del artefacto |
| first_build_number | INTEGER | Primer build con esta versión |
| last_build_number | INTEGER | Último build con esta versión |
| total_builds | INTEGER | Total de builds con esta versión |
| success_count | INTEGER | Builds exitosos |
| failure_count | INTEGER | Builds fallidos |
| first_seen | TIMESTAMPTZ | Primera aparición |
| last_seen | TIMESTAMPTZ | Última aparición |

#### 3.2.2 Funciones Almacenadas

```sql
-- Limpieza de datos antiguos (retención 1 año)
CREATE OR REPLACE FUNCTION cleanup_old_builds() RETURNS void;

-- Actualizar resumen de job
CREATE OR REPLACE FUNCTION update_job_summary(p_job_name VARCHAR) RETURNS void;

-- Mantenimiento completo con reporte
CREATE OR REPLACE FUNCTION run_maintenance() RETURNS TABLE (
    builds_deleted INTEGER,
    versions_deleted INTEGER,
    message TEXT
);
```

#### 3.2.3 Triggers

```sql
-- Actualiza automáticamente jenkins_versions al insertar builds
CREATE TRIGGER trigger_update_version_stats
    AFTER INSERT ON jenkins_builds
    FOR EACH ROW
    EXECUTE FUNCTION update_version_stats();
```

#### 3.2.4 Vistas

```sql
-- Métricas diarias por job
CREATE VIEW daily_build_metrics AS ...;

-- Historial de versiones (solo versiones válidas)
CREATE VIEW version_history AS ...;

-- Última versión por job
CREATE VIEW latest_versions AS ...;

-- Estadísticas de tablas
CREATE VIEW table_stats AS ...;

-- Distribución de datos por antigüedad
CREATE VIEW data_age_distribution AS ...;
```

---

### 3.3 Grafana

#### 3.3.1 Datasource

```yaml
name: PostgreSQL-Jenkins
uid: postgres-jenkins
type: postgres
url: postgres-service:5432
database: jenkins_metrics
user: jenkins_metrics
jsonData:
  sslmode: disable
  maxOpenConns: 10
  maxIdleConns: 10
  connMaxLifetime: 14400
  postgresVersion: 1600
```

#### 3.3.2 Dashboards

##### Dashboard: Jenkins - Overview
- **UID**: `jenkins-overview`
- **Refresh**: 30s
- **Time Range**: Last 7 days

| Panel | Tipo | Query |
|-------|------|-------|
| Total Builds | stat | `SELECT COUNT(*) FROM jenkins_builds WHERE $__timeFilter(timestamp)` |
| Tasa de Éxito | stat | `SELECT ROUND(100.0 * SUM(CASE WHEN result = 'SUCCESS' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2)` |
| Builds Fallidos | stat | `SELECT COUNT(*) WHERE result = 'FAILURE'` |
| Duración Promedio | stat | `SELECT ROUND(AVG(duration_ms) / 1000, 2)` |
| Historial por Resultado | timeseries | Agrupado por timestamp y result |
| Distribución de Resultados | piechart | Agrupado por result |
| Top 10 Jobs | piechart | Ordenado por count DESC |
| Últimos 50 Builds | table | ORDER BY timestamp DESC LIMIT 50 |

##### Dashboard: Jenkins - Detalle por Job
- **UID**: `jenkins-job-details`
- **Refresh**: 30s
- **Time Range**: Last 30 days
- **Variables**: `$job_name` (selector de job)

| Panel | Tipo | Filtro |
|-------|------|--------|
| Total Builds | stat | WHERE job_name = '$job_name' |
| Exitosos | stat | WHERE result = 'SUCCESS' |
| Fallidos | stat | WHERE result = 'FAILURE' |
| Duración Promedio | stat | AVG(duration_ms) |
| Tasa de Éxito | gauge | Porcentaje con thresholds |
| Última Versión | stat | ORDER BY timestamp DESC LIMIT 1 |
| Historial de Builds | timeseries | Agrupado por result |
| Historial Completo | table | Todos los campos |

##### Dashboard: Jenkins - Historial de Versiones
- **UID**: `jenkins-versions`
- **Refresh**: 30s
- **Time Range**: Last 90 days

| Panel | Tipo | Query |
|-------|------|-------|
| Total Versiones Únicas | stat | COUNT(DISTINCT version) |
| Total Jobs | stat | COUNT(DISTINCT job_name) |
| Versiones Nuevas (7d) | stat | WHERE timestamp >= NOW() - INTERVAL '7 days' |
| Timeline de Versiones | timeseries | Agrupado por version |
| Última Versión por Job | table | DISTINCT ON (job_name) |
| Top 15 Versiones | piechart | ORDER BY count DESC LIMIT 15 |
| Historial Completo | table | ORDER BY timestamp DESC LIMIT 100 |

#### 3.3.3 Plugins Instalados

| Plugin | Versión | Uso |
|--------|---------|-----|
| grafana-clock-panel | latest | Widget de reloj |
| grafana-piechart-panel | latest | Gráficos de torta |

---

## 4. API de Jenkins

### 4.1 Endpoints Utilizados

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/json` | GET | Lista de jobs raíz |
| `/job/{folder}/api/json` | GET | Jobs dentro de carpeta |
| `/job/{name}/api/json` | GET | Detalles y builds de job |

### 4.2 Parámetros de Query

```
tree=jobs[name,url,color,_class]
tree=builds[number,url,result,timestamp,duration,displayName,description]{0,100}
```

### 4.3 Autenticación

- **Tipo**: HTTP Basic Auth
- **Usuario**: Jenkins username
- **Password**: API Token (no password)

### 4.4 Respuestas Esperadas

#### Lista de Jobs
```json
{
  "jobs": [
    {
      "name": "job-name",
      "url": "http://jenkins/job/job-name/",
      "color": "blue",
      "_class": "hudson.model.FreeStyleProject"
    }
  ]
}
```

#### Builds de Job
```json
{
  "builds": [
    {
      "number": 123,
      "url": "http://jenkins/job/job-name/123/",
      "result": "SUCCESS",
      "timestamp": 1701234567890,
      "duration": 60000,
      "displayName": "#123",
      "description": "Version 1.2.3"
    }
  ]
}
```

---

## 5. Configuración de Despliegue

### 5.1 Docker Compose

#### 5.1.1 Servicios

```yaml
services:
  postgres:
    image: postgres:16-alpine
    ports: ["5432:5432"]
    volumes:
      - ./postgres_data:/var/lib/postgresql/data
      - ./postgres/init:/docker-entrypoint-initdb.d:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U jenkins_metrics"]
      interval: 10s
      timeout: 5s
      retries: 5

  grafana:
    image: grafana/grafana:10.2.0
    ports: ["3000:3000"]
    depends_on:
      postgres:
        condition: service_healthy

  metrics-exporter:
    build: ./metrics-exporter
    depends_on:
      postgres:
        condition: service_healthy
    extra_hosts:
      - "host.docker.internal:host-gateway"
```

#### 5.1.2 Redes

```yaml
networks:
  jenkins-metrics:
    driver: bridge
```

### 5.2 Kubernetes

#### 5.2.1 Recursos

| Tipo | Nombre | Descripción |
|------|--------|-------------|
| Namespace | jenkins-metrics | Aislamiento de recursos |
| Secret | postgres-secret | Credenciales PostgreSQL |
| Secret | jenkins-secret | Credenciales Jenkins |
| Secret | grafana-secret | Credenciales Grafana |
| ConfigMap | postgres-init-scripts | Scripts SQL |
| ConfigMap | grafana-provisioning | Datasources y dashboards |
| ConfigMap | grafana-dashboards | JSON de dashboards |
| ConfigMap | exporter-config | Configuración exportador |
| PVC | postgres-pvc | 10Gi para PostgreSQL |
| PVC | grafana-pvc | 2Gi para Grafana |
| Deployment | postgres | 1 réplica |
| Deployment | grafana | 1 réplica |
| Deployment | metrics-exporter | 1 réplica |
| Service | postgres-service | ClusterIP:5432 |
| Service | grafana-service | ClusterIP:3000 |
| Service | grafana-nodeport | NodePort:30300 |
| Ingress | grafana-ingress | Acceso externo (opcional) |

#### 5.2.2 Recursos de Compute

| Componente | Requests | Limits |
|------------|----------|--------|
| PostgreSQL | 256Mi/250m | 512Mi/500m |
| Grafana | 256Mi/250m | 512Mi/500m |
| Exporter | 128Mi/100m | 256Mi/250m |

#### 5.2.3 Health Checks

```yaml
# PostgreSQL
livenessProbe:
  exec:
    command: ["pg_isready", "-U", "jenkins_metrics"]
  initialDelaySeconds: 30
  periodSeconds: 10

# Grafana
livenessProbe:
  httpGet:
    path: /api/health
    port: 3000
  initialDelaySeconds: 60
  periodSeconds: 10

# Exporter: No health check (proceso continuo)
```

---

## 6. Flujos de Datos

### 6.1 Flujo de Recolección

```
┌─────────────────────────────────────────────────────────────────┐
│                     FLUJO DE RECOLECCIÓN                         │
└─────────────────────────────────────────────────────────────────┘

1. INICIO
   │
   ▼
2. Esperar servicios (Jenkins + PostgreSQL)
   │
   ▼
3. Conectar a PostgreSQL
   │
   ▼
4. ┌─────────────────────────────┐
   │ LOOP (cada POLL_INTERVAL)  │
   └──────────────┬──────────────┘
                  │
                  ▼
   5. GET /api/json → Lista de jobs
      │
      ▼
   6. Para cada job:
      │
      ├─► GET /job/{name}/api/json → Builds
      │
      ├─► Filtrar builds no existentes en BD
      │
      ├─► extract_version() para cada build
      │
      ├─► INSERT INTO jenkins_builds (batch)
      │
      └─► UPDATE jenkins_job_summary
      │
      ▼
   7. Cleanup diario (si counter >= 1440)
      │
      ▼
   8. Sleep(POLL_INTERVAL)
      │
      └──────────► Volver a paso 4
```

### 6.2 Flujo de Visualización

```
┌─────────────────────────────────────────────────────────────────┐
│                     FLUJO DE VISUALIZACIÓN                       │
└─────────────────────────────────────────────────────────────────┘

1. Usuario accede a Grafana (http://localhost:3000)
   │
   ▼
2. Selecciona dashboard
   │
   ▼
3. Grafana ejecuta queries SQL
   │
   ├─► SELECT COUNT(*) FROM jenkins_builds
   ├─► SELECT ... GROUP BY result
   ├─► SELECT ... FROM jenkins_job_summary
   └─► SELECT ... FROM jenkins_versions
   │
   ▼
4. PostgreSQL retorna datos
   │
   ▼
5. Grafana renderiza paneles
   │
   ▼
6. Auto-refresh cada 30s
```

---

## 7. Seguridad

### 7.1 Autenticación

| Componente | Método | Credenciales |
|------------|--------|--------------|
| Jenkins API | HTTP Basic | Usuario + API Token |
| PostgreSQL | Password | Usuario + Password |
| Grafana | Form Login | Usuario + Password |

### 7.2 Secretos

#### Docker Compose
- Archivo `.env` (gitignored)
- Variables de entorno en runtime

#### Kubernetes
- Kubernetes Secrets (base64)
- Montados como variables de entorno

### 7.3 Red

| Puerto | Componente | Exposición |
|--------|------------|------------|
| 5432 | PostgreSQL | Interna (ClusterIP) |
| 3000 | Grafana | Externa (NodePort/Ingress) |

### 7.4 Recomendaciones de Producción

- [ ] Cambiar credenciales por defecto
- [ ] Habilitar TLS en Ingress
- [ ] Usar External Secrets Operator en K8s
- [ ] Configurar Network Policies
- [ ] Habilitar SSL en PostgreSQL
- [ ] Configurar RBAC en Grafana

---

## 8. Mantenimiento

### 8.1 Retención de Datos

| Política | Valor |
|----------|-------|
| Retención | 1 año |
| Limpieza automática | Diaria |
| Limpieza manual | `SELECT * FROM run_maintenance()` |

### 8.2 Backups

```bash
# PostgreSQL backup
kubectl exec -n jenkins-metrics deployment/postgres -- \
  pg_dump -U jenkins_metrics jenkins_metrics > backup.sql

# Restore
kubectl exec -i -n jenkins-metrics deployment/postgres -- \
  psql -U jenkins_metrics jenkins_metrics < backup.sql
```

### 8.3 Monitoreo

| Métrica | Query |
|---------|-------|
| Total registros | `SELECT COUNT(*) FROM jenkins_builds` |
| Tamaño tablas | `SELECT * FROM table_stats` |
| Distribución edad | `SELECT * FROM data_age_distribution` |

### 8.4 Actualización de Dashboards

1. Editar JSON en ConfigMap
2. Aplicar cambios: `kubectl apply -f configmaps/`
3. Reiniciar Grafana: `kubectl rollout restart deployment/grafana`

---

## 9. Limitaciones Conocidas

| Limitación | Descripción | Workaround |
|------------|-------------|------------|
| Single replica | No HA para PostgreSQL | Usar PostgreSQL operator |
| Polling | No tiempo real | Reducir POLL_INTERVAL |
| Extracción versión | Basada en patrones regex | Personalizar patterns |
| Sin alertas | Dashboards solo visualización | Configurar en Grafana |

---

## 10. Roadmap

### v1.1 (Planificado)
- [ ] Soporte para Jenkins Webhooks
- [ ] Alertas Grafana preconfiguradas
- [ ] Métricas de pipeline stages

### v1.2 (Futuro)
- [ ] Alta disponibilidad PostgreSQL
- [ ] Exportación a Prometheus
- [ ] Dashboard de SLO/SLI

---

## Apéndice A: Comandos de Referencia

### Docker Compose

```bash
make init       # Crear .env
make build      # Construir imágenes
make up         # Iniciar servicios
make down       # Detener servicios
make logs       # Ver logs
make db-shell   # Shell PostgreSQL
make db-stats   # Ver estadísticas
make cleanup    # Ejecutar limpieza
```

### Kubernetes

```bash
kubectl apply -k .                              # Desplegar todo
kubectl get all -n jenkins-metrics              # Ver recursos
kubectl logs -f deployment/metrics-exporter -n jenkins-metrics  # Logs
kubectl port-forward svc/grafana-service 3000:3000 -n jenkins-metrics  # Acceso
kubectl delete -k .                             # Eliminar todo
```

---

## Apéndice B: Troubleshooting

| Problema | Causa | Solución |
|----------|-------|----------|
| Exporter no conecta | Jenkins no accesible | Verificar URL y firewall |
| No hay datos en Grafana | Datasource mal configurado | Verificar conexión en Grafana |
| Builds duplicados | -- | Constraint UNIQUE previene duplicados |
| Alto uso de disco | Datos no purgados | Ejecutar run_maintenance() |
| Grafana no inicia | Plugins fallidos | Verificar conectividad a internet |

---

*Documento generado para Jenkins Metrics Collector v1.0.0*

