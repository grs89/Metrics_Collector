# Jenkins Metrics Dashboard con Grafana y PostgreSQL

Sistema de monitoreo del historial de builds de Jenkins usando Grafana y PostgreSQL, con retención de datos de 1 año.

## 🏗️ Arquitectura

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Jenkins        │────▶│ Metrics Exporter │────▶│   PostgreSQL    │
│  (existente)    │     │   (Python)       │     │   (Docker)      │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
                                                          ▼
                                                 ┌─────────────────┐
                                                 │    Grafana      │
                                                 │   (Docker)      │
                                                 └─────────────────┘
```

## 📋 Requisitos

- Docker y Docker Compose instalados
- Jenkins existente accesible por red
- Token de API de Jenkins (recomendado)

## 🚀 Inicio Rápido

### 1. Configurar variables de entorno

Copiar el archivo de ejemplo y editarlo con tu configuración:

```bash
cp env.example .env
```

Editar `.env` con los datos de tu Jenkins:

```bash
# URL de tu Jenkins existente
JENKINS_URL=http://tu-jenkins-server:8080

# Usuario de Jenkins
JENKINS_USER=admin

# Token API de Jenkins (ver instrucciones abajo)
JENKINS_TOKEN=tu-api-token

# Intervalo de polling en segundos (opcional, default: 60)
POLL_INTERVAL=60
```

### 2. Obtener Token API de Jenkins

1. Inicia sesión en Jenkins
2. Ve a tu perfil → Configure
3. En la sección "API Token", clic en "Add new Token"
4. Dale un nombre y clic en "Generate"
5. Copia el token y añádelo al archivo `.env`

### 3. Iniciar los servicios

```bash
# Construir e iniciar todos los servicios
docker-compose up -d --build

# Ver logs
docker-compose logs -f
```

### 4. Acceder a Grafana

- **URL:** http://localhost:3000
- **Usuario:** admin
- **Contraseña:** admin123

## 📊 Dashboards Disponibles

### Jenkins - Overview
Vista general de todos los jobs con:
- Total de builds
- Tasa de éxito
- Builds fallidos
- Duración promedio
- Historial temporal de builds
- Distribución de resultados
- Top 10 jobs por builds

### Jenkins - Detalle por Job
Métricas específicas por job con:
- Selector de job
- Estadísticas del job seleccionado
- Historial de builds del job
- Tendencia de duración
- Builds por versión
- Gauge de tasa de éxito
- Tabla detallada de builds

### Jenkins - Historial de Versiones
Seguimiento de versiones deployadas:
- Total de versiones únicas
- Timeline de versiones
- Última versión por job
- Top 15 versiones más deployadas
- Historial completo de versiones

## 🗄️ Base de Datos

### Esquema Principal

```sql
-- Tabla de builds
jenkins_builds (
    job_name,
    build_number,
    version,
    result,
    duration_ms,
    timestamp,
    ...
)

-- Resumen por job
jenkins_job_summary (
    job_name,
    total_builds,
    success_count,
    failure_count,
    avg_duration_ms,
    ...
)

-- Historial de versiones
jenkins_versions (
    job_name,
    version,
    total_builds,
    first_seen,
    last_seen,
    ...
)
```

### Retención de Datos

Los datos se mantienen durante **1 año**. La limpieza automática se ejecuta:
- Al iniciar el exportador
- Diariamente durante la ejecución

Para ejecutar limpieza manual:

```bash
docker-compose exec postgres psql -U jenkins_metrics -d jenkins_metrics -c "SELECT cleanup_old_builds();"
```

### Consultas Útiles

```sql
-- Ver distribución de datos por antigüedad
SELECT * FROM data_age_distribution;

-- Ver tamaño de tablas
SELECT * FROM table_stats;

-- Ejecutar mantenimiento
SELECT * FROM run_maintenance();
```

## 🔧 Configuración Avanzada

### Cambiar credenciales de PostgreSQL

Editar en `docker-compose.yml`:

```yaml
environment:
  - POSTGRES_USER=tu_usuario
  - POSTGRES_PASSWORD=tu_password
  - POSTGRES_DB=jenkins_metrics
```

Y actualizar en el servicio `metrics-exporter` y `grafana/provisioning/datasources/datasources.yml`.

### Cambiar credenciales de Grafana

```yaml
environment:
  - GF_SECURITY_ADMIN_USER=admin
  - GF_SECURITY_ADMIN_PASSWORD=tu_password
```

### Ajustar intervalo de polling

```yaml
# En docker-compose.yml o .env
POLL_INTERVAL=30  # En segundos
```

## 🐛 Troubleshooting

### El exportador no conecta con Jenkins

```bash
# Ver logs del exportador
docker-compose logs -f metrics-exporter

# Verificar conectividad
docker-compose exec metrics-exporter curl -v http://host.docker.internal:8080/api/json
```

### No aparecen datos en Grafana

1. Verificar que el exportador está funcionando:
   ```bash
   docker-compose logs metrics-exporter | tail -50
   ```

2. Verificar datos en PostgreSQL:
   ```bash
   docker-compose exec postgres psql -U jenkins_metrics -d jenkins_metrics -c "SELECT COUNT(*) FROM jenkins_builds;"
   ```

3. Verificar conexión del datasource en Grafana:
   - Configuration → Data Sources → PostgreSQL-Jenkins → Test

### Reiniciar servicios

```bash
# Reiniciar todo
docker-compose restart

# Reiniciar solo el exportador
docker-compose restart metrics-exporter
```

### Ver estado de los servicios

```bash
docker-compose ps
```

## 📁 Estructura del Proyecto

```
.
├── docker-compose.yml          # Orquestación de servicios
├── env.example                 # Plantilla de variables de entorno
├── .env                        # Variables de entorno (crear desde env.example)
├── README.md                   # Este archivo
├── grafana/
│   ├── provisioning/
│   │   ├── datasources/
│   │   │   └── datasources.yml # Configuración de PostgreSQL
│   │   └── dashboards/
│   │       └── dashboards.yml  # Provisión de dashboards
│   └── dashboards/
│       ├── jenkins-overview.json
│       ├── jenkins-job-details.json
│       └── jenkins-versions.json
├── postgres/
│   └── init/
│       ├── 01-schema.sql       # Esquema de base de datos
│       └── 02-cleanup-job.sql  # Funciones de mantenimiento
└── metrics-exporter/
    ├── Dockerfile
    ├── requirements.txt
    └── exporter.py             # Script de exportación
```

## 🛑 Detener Servicios

```bash
# Detener sin eliminar datos
docker-compose down

# Detener y eliminar volúmenes (BORRA TODOS LOS DATOS)
docker-compose down -v
```

## 📝 Licencia

MIT License

