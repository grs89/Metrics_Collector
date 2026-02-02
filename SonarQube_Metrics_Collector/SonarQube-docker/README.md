# 📊 SonarQube Metrics History con Grafana

Sistema completo para recolectar, almacenar y visualizar el historial de métricas de SonarQube usando Docker.

![Dashboard Preview](https://img.shields.io/badge/Grafana-Dashboard-orange?logo=grafana)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue?logo=postgresql)
![Docker](https://img.shields.io/badge/Docker-Compose-blue?logo=docker)

## 🎯 Características

- **Métricas recolectadas:**
  - 🔓 Vulnerabilities
  - 🐛 Bugs
  - 🦨 Code Smells
  - 🔥 Security Hotspots / Hotspots Reviewed
  - ✅ Coverage
  - 📋 Duplications (líneas duplicadas)
  - 📏 Lines of Code (ncloc)
  - ⏱️ Technical Debt (sqale_index)

- **Retención de datos:** 1 año (configurable)
- **Recolección automática:** Cada hora (configurable)
- **Dashboards preconfigurados:** Vista por proyecto y vista general
- **Commits inmediatos:** Los datos aparecen en Grafana al instante

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

## 🚀 Instalación Rápida

### 1. Configurar variables de entorno

```bash
# Copiar el archivo de configuración
cp env.example .env

# Editar con tus valores
nano .env
```

Configura el archivo `.env`:

```env
# URL de tu SonarQube (sin slash al final)
SONARQUBE_URL=https://tu-sonarqube.empresa.com

# Token de SonarQube (generar en: My Account > Security > Generate Tokens)
SONARQUBE_TOKEN=squ_tu_token_aqui

# Credenciales de PostgreSQL
POSTGRES_USER=metrics
POSTGRES_PASSWORD=metrics

# Credenciales de Grafana
GRAFANA_USER=admin
GRAFANA_PASSWORD=admin

# Intervalo de recolección (segundos) - default: 1 hora
COLLECTION_INTERVAL=3600

# Retención de datos (días) - default: 1 año
DATA_RETENTION_DAYS=365
```

### 2. Configurar credenciales de PostgreSQL en Grafana

⚠️ **Importante:** Si cambias las credenciales de PostgreSQL, también debes actualizar el archivo de datasource de Grafana:

```bash
nano grafana/provisioning/datasources/datasource.yml
```

Actualiza `user` y `password` con los mismos valores del `.env`:

```yaml
user: metrics
secureJsonData:
  password: metrics
```

### 3. Iniciar servicios

```bash
docker-compose up -d
```

### 4. Verificar que todo funcione

```bash
# Ver logs del collector
docker-compose logs -f collector

# Verificar que hay datos en la base de datos
docker-compose exec postgres psql -U metrics -d sonarqube_metrics -c "SELECT COUNT(*) FROM projects;"
```

### 5. Acceder a Grafana

- **URL:** http://localhost:3000
- **Usuario:** `admin`
- **Password:** `admin`

Los dashboards estarán en: **Dashboards → SonarQube**

## 📈 Dashboards Incluidos

### 1. SonarQube All Projects Overview
Vista general de todos los proyectos:
- 📁 Total de proyectos
- 🔓 Total de vulnerabilities
- 🐛 Total de bugs
- ✅ Coverage promedio
- 📊 Tabla comparativa con indicadores de color
- 🥧 Gráficos de distribución por proyecto

### 2. SonarQube Project Metrics
Vista detallada por proyecto individual:
- Métricas actuales (stats cards)
- 📈 Historial de Vulnerabilities, Bugs, Code Smells
- 📈 Historial de Coverage
- 📈 Historial de Duplications
- 📈 Historial de Hotspots Reviewed
- 📋 Tabla con métricas por versión

## 🔧 Configuración Avanzada

### Cambiar intervalo de recolección

```env
# Cada 30 minutos
COLLECTION_INTERVAL=1800

# Cada 2 horas
COLLECTION_INTERVAL=7200

# Cada 6 horas
COLLECTION_INTERVAL=21600
```

### Cambiar retención de datos

```env
# 6 meses
DATA_RETENTION_DAYS=180

# 2 años
DATA_RETENTION_DAYS=730
```

### Ejecutar recolección manual

```bash
# Reiniciar el collector para ejecutar inmediatamente
docker-compose restart collector

# Ver logs en tiempo real
docker-compose logs -f collector
```

### Limpiar y reiniciar desde cero

```bash
# Detener y eliminar contenedores y datos
docker-compose down -v
rm -rf postgres_data grafana_data

# Iniciar de nuevo
docker-compose up -d
```

## 📁 Estructura del Proyecto

```
.
├── docker-compose.yml          # Orquestación de servicios
├── .env                        # Variables de entorno (crear desde env.example)
├── env.example                 # Plantilla de variables de entorno
├── README.md                   # Este archivo
├── collector/
│   ├── Dockerfile              # Imagen del collector
│   ├── collector.py            # Script de recolección
│   └── requirements.txt        # Dependencias Python
├── grafana/
│   ├── provisioning/
│   │   ├── datasources/
│   │   │   └── datasource.yml  # Configuración de PostgreSQL
│   │   └── dashboards/
│   │       └── dashboard.yml   # Provisioning de dashboards
│   └── dashboards/
│       ├── sonarqube-overview.json      # Dashboard por proyecto
│       └── sonarqube-all-projects.json  # Dashboard general
├── init-db/
│   └── 01-schema.sql           # Esquema de base de datos
├── postgres_data/              # Datos de PostgreSQL (generado)
└── grafana_data/               # Datos de Grafana (generado)
```

## 🔍 Consultas SQL Útiles

Acceder a la base de datos:
```bash
docker-compose exec postgres psql -U metrics -d sonarqube_metrics
```

### Ver todas las métricas del último análisis por proyecto

```sql
SELECT project_name, version, vulnerabilities, bugs, code_smells, coverage
FROM v_metrics_with_project 
WHERE (project_key, analysis_date) IN (
  SELECT project_key, MAX(analysis_date) 
  FROM v_metrics_with_project 
  GROUP BY project_key
)
ORDER BY vulnerabilities DESC;
```

### Ver historial de un proyecto específico

```sql
SELECT version, analysis_date, vulnerabilities, bugs, coverage 
FROM v_metrics_with_project 
WHERE project_key = 'tu-proyecto' 
ORDER BY analysis_date DESC;
```

### Ver proyectos con más bugs

```sql
SELECT project_name, bugs, code_smells, vulnerabilities
FROM v_metrics_with_project v1
WHERE analysis_date = (
  SELECT MAX(analysis_date) FROM v_metrics_with_project v2 
  WHERE v2.project_key = v1.project_key
)
ORDER BY bugs DESC
LIMIT 20;
```

### Estadísticas generales

```sql
SELECT 
  COUNT(DISTINCT project_key) as total_projects,
  SUM(vulnerabilities) as total_vulnerabilities,
  SUM(bugs) as total_bugs,
  ROUND(AVG(coverage)::numeric, 2) as avg_coverage
FROM v_metrics_with_project v1
WHERE analysis_date = (
  SELECT MAX(analysis_date) FROM v_metrics_with_project v2 
  WHERE v2.project_key = v1.project_key
);
```

### Limpiar datos antiguos manualmente

```sql
SELECT cleanup_old_metrics(365); -- Elimina datos > 365 días
```

## 🛠️ Solución de Problemas

### El collector no conecta a SonarQube

1. **Verifica la URL:** Asegúrate que sea accesible desde Docker
2. **Verifica el token:** Debe tener permisos de lectura
3. **Si SonarQube es interno/VPN:** El container puede no resolver el DNS
   - Conéctate a VPN antes de iniciar Docker
   - O usa la IP directa en lugar del dominio

```bash
# Ver logs del collector
docker-compose logs collector | grep -i error
```

### Grafana muestra "No data"

1. **Verifica que el collector haya terminado:**
```bash
docker-compose logs collector | tail -20
```

2. **Verifica que hay datos en PostgreSQL:**
```bash
docker-compose exec postgres psql -U metrics -d sonarqube_metrics -c "SELECT COUNT(*) FROM metrics_history;"
```

3. **Verifica las credenciales del datasource:**
   - El archivo `grafana/provisioning/datasources/datasource.yml` debe tener las mismas credenciales que el `.env`

4. **Reinicia Grafana después de cambiar el datasource:**
```bash
docker-compose restart grafana
```

### Error de autenticación en PostgreSQL

Si ves `password authentication failed`, los datos de PostgreSQL fueron creados con credenciales diferentes:

```bash
# Limpiar y reiniciar
docker-compose down -v
rm -rf postgres_data grafana_data
docker-compose up -d
```

### Ver estado de los servicios

```bash
docker-compose ps
```

### Ver uso de recursos

```bash
docker stats
```

## 📊 API de SonarQube Utilizada

El collector utiliza las siguientes APIs de SonarQube:

| Endpoint | Descripción |
|----------|-------------|
| `GET /api/projects/search` | Lista de proyectos |
| `GET /api/measures/component` | Métricas del proyecto |
| `GET /api/project_analyses/search` | Información de análisis y versión |

## 🔐 Generar Token de SonarQube

1. Accede a tu instancia de SonarQube
2. Click en tu avatar → **My Account**
3. Ve a la pestaña **Security**
4. En **Generate Tokens**:
   - Nombre: `grafana-metrics-collector`
   - Type: `User Token`
5. Click en **Generate**
6. ⚠️ **Copia el token inmediatamente** (no se mostrará de nuevo)
7. Pega el token en tu archivo `.env`

## 🐳 Puertos Utilizados

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| Grafana | 3000 | Dashboard web |
| PostgreSQL | 5432 | Base de datos |

Si necesitas cambiar los puertos, edita el `docker-compose.yml`.

## 📝 Licencia

MIT License - Siéntete libre de usar y modificar según tus necesidades.

---

**¿Problemas?** Revisa los logs con `docker-compose logs -f` o abre un issue.
