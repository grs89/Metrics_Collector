# Metrics Collector All-in-One

Este proyecto consolida los colectores de métricas de **Jenkins** y **SonarQube** en una única solución unificada, optimizando recursos mediante el uso compartido de infraestructura (Postgres y Grafana).

## Estructura del Proyecto

- `docker/`: Configuración unificada para despliegues con Docker Compose.
- `kubernetes/`: Manifiestos organizados para despliegues en Kubernetes (Base, Jenkins, SonarQube).
- `exporters/`: Código fuente de los colectores (Python).

## Despliegue con Docker

1. Navega al directorio `docker`:
   ```bash
   cd docker
   ```
2. Copia el archivo de ejemplo de variables de entorno y configuralo:
   ```bash
   cp .env.example .env
   # Edita .env con tus credenciales
   ```
3. Inicia los servicios:
   ```bash
   docker-compose up -d
   ```

## Despliegue con Kubernetes

Los manifiestos están divididos en:
- `base/`: Infraestructura compartida (Namespace, Postgres, Grafana).
- `jenkins/`: Despliegue específico del colector de Jenkins.
- `sonarqube/`: Despliegue específico del colector de SonarQube.

Para desplegar:
1. Crea los secretos necesarios.
2. Aplica la configuración base:
   ```bash
   kubectl apply -f kubernetes/base/
   ```
3. Aplica los colectores:
   ```bash
   kubectl apply -f kubernetes/jenkins/
   ```
4. Repite para SonarQube.

## Dashboards

Grafana viene pre-configurado con dashboards para ambos servicios en el puerto `3000`.
- **Jenkins Overview**: Métricas generales de jobs.
- **SonarQube Projects**: Estado de calidad de código.
