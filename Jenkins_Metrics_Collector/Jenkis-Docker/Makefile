.PHONY: help init build up down restart logs ps clean db-shell grafana-reset cleanup

# Variables
COMPOSE = docker-compose

help: ## Mostrar esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

init: ## Crear archivo .env desde plantilla
	@if [ ! -f .env ]; then \
		cp env.example .env; \
		echo "✓ Archivo .env creado. Edítalo con tu configuración de Jenkins."; \
	else \
		echo "⚠ El archivo .env ya existe. No se sobrescribió."; \
	fi

build: ## Construir imágenes
	$(COMPOSE) build

up: ## Iniciar todos los servicios
	$(COMPOSE) up -d

up-logs: ## Iniciar servicios y mostrar logs
	$(COMPOSE) up

down: ## Detener servicios
	$(COMPOSE) down

restart: ## Reiniciar servicios
	$(COMPOSE) restart

logs: ## Ver logs de todos los servicios
	$(COMPOSE) logs -f

logs-exporter: ## Ver logs del exportador
	$(COMPOSE) logs -f metrics-exporter

logs-grafana: ## Ver logs de Grafana
	$(COMPOSE) logs -f grafana

logs-postgres: ## Ver logs de PostgreSQL
	$(COMPOSE) logs -f postgres

ps: ## Ver estado de los servicios
	$(COMPOSE) ps

db-shell: ## Abrir shell de PostgreSQL
	$(COMPOSE) exec postgres psql -U jenkins_metrics -d jenkins_metrics

db-stats: ## Ver estadísticas de la base de datos
	$(COMPOSE) exec postgres psql -U jenkins_metrics -d jenkins_metrics -c "SELECT * FROM table_stats;"

db-age: ## Ver distribución de datos por antigüedad
	$(COMPOSE) exec postgres psql -U jenkins_metrics -d jenkins_metrics -c "SELECT * FROM data_age_distribution;"

db-jobs: ## Ver resumen de jobs
	$(COMPOSE) exec postgres psql -U jenkins_metrics -d jenkins_metrics -c "SELECT job_name, total_builds, success_count, failure_count, last_version FROM jenkins_job_summary ORDER BY total_builds DESC;"

cleanup: ## Ejecutar limpieza de datos antiguos
	$(COMPOSE) exec postgres psql -U jenkins_metrics -d jenkins_metrics -c "SELECT * FROM run_maintenance();"

clean: ## Detener servicios y eliminar volúmenes (BORRA DATOS)
	$(COMPOSE) down -v

grafana-reset: ## Reiniciar Grafana (útil si hay problemas con dashboards)
	$(COMPOSE) restart grafana

