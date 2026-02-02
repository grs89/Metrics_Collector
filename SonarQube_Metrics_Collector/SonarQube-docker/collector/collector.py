#!/usr/bin/env python3
"""
SonarQube Metrics Collector
Recolecta métricas de SonarQube y las almacena en PostgreSQL para visualización en Grafana.
"""

import os
import sys
import time
import logging
import requests
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
import schedule

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Métricas a recolectar de SonarQube
METRICS_TO_COLLECT = [
    'vulnerabilities',
    'bugs',
    'code_smells',
    'security_hotspots',
    'security_hotspots_reviewed',
    'coverage',
    'lines_to_cover',
    'uncovered_lines',
    'duplicated_lines_density',
    'duplicated_blocks',
    'duplicated_files',
    'duplicated_lines',
    'ncloc',
    'sqale_index',
    'reliability_rating',
    'security_rating',
    'sqale_rating'
]


class SonarQubeCollector:
    """Clase para recolectar métricas de SonarQube."""
    
    def __init__(self):
        self.sonarqube_url = os.environ.get('SONARQUBE_URL', 'http://localhost:9000').rstrip('/')
        self.sonarqube_token = os.environ.get('SONARQUBE_TOKEN', '')
        self.db_config = {
            'host': os.environ.get('POSTGRES_HOST', 'localhost'),
            'port': int(os.environ.get('POSTGRES_PORT', 5432)),
            'database': os.environ.get('POSTGRES_DB', 'sonarqube_metrics'),
            'user': os.environ.get('POSTGRES_USER', 'metrics'),
            'password': os.environ.get('POSTGRES_PASSWORD', 'metrics_password')
        }
        self.retention_days = int(os.environ.get('DATA_RETENTION_DAYS', 365))
        
        if not self.sonarqube_token:
            logger.warning("SONARQUBE_TOKEN no está configurado. Algunas APIs pueden no estar disponibles.")
    
    def get_db_connection(self):
        """Obtiene conexión a PostgreSQL."""
        return psycopg2.connect(**self.db_config)
    
    def sonarqube_request(self, endpoint, params=None):
        """Realiza una petición a la API de SonarQube."""
        url = f"{self.sonarqube_url}/api/{endpoint}"
        auth = (self.sonarqube_token, '') if self.sonarqube_token else None
        
        try:
            response = requests.get(url, params=params, auth=auth, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error en petición a SonarQube: {e}")
            return None
    
    def get_projects(self):
        """Obtiene lista de todos los proyectos de SonarQube."""
        projects = []
        page = 1
        page_size = 100
        
        while True:
            data = self.sonarqube_request('projects/search', {
                'p': page,
                'ps': page_size
            })
            
            if not data or 'components' not in data:
                break
            
            projects.extend(data['components'])
            
            # Verificar si hay más páginas
            total = data.get('paging', {}).get('total', 0)
            if page * page_size >= total:
                break
            page += 1
        
        logger.info(f"Encontrados {len(projects)} proyectos en SonarQube")
        return projects
    
    def get_project_metrics(self, project_key):
        """Obtiene las métricas actuales de un proyecto."""
        data = self.sonarqube_request('measures/component', {
            'component': project_key,
            'metricKeys': ','.join(METRICS_TO_COLLECT)
        })
        
        if not data or 'component' not in data:
            return None
        
        metrics = {}
        for measure in data['component'].get('measures', []):
            metric_key = measure['metric']
            value = measure.get('value', measure.get('bestValue', 0))
            metrics[metric_key] = value
        
        return metrics
    
    def get_project_version(self, project_key):
        """Obtiene la versión actual del proyecto."""
        data = self.sonarqube_request('project_analyses/search', {
            'project': project_key,
            'ps': 1
        })
        
        if data and 'analyses' in data and data['analyses']:
            analysis = data['analyses'][0]
            # Buscar evento de versión
            for event in analysis.get('events', []):
                if event.get('category') == 'VERSION':
                    return event.get('name')
            return analysis.get('projectVersion')
        
        return None
    
    def get_analysis_date(self, project_key):
        """Obtiene la fecha del último análisis."""
        data = self.sonarqube_request('project_analyses/search', {
            'project': project_key,
            'ps': 1
        })
        
        if data and 'analyses' in data and data['analyses']:
            date_str = data['analyses'][0].get('date')
            if date_str:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        
        return datetime.now()
    
    def upsert_project(self, conn, project_key, project_name):
        """Inserta o actualiza un proyecto en la base de datos."""
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO projects (project_key, project_name, updated_at)
                VALUES (%s, %s, NOW())
                ON CONFLICT (project_key) 
                DO UPDATE SET project_name = EXCLUDED.project_name, updated_at = NOW()
                RETURNING id
            """, (project_key, project_name))
            return cur.fetchone()[0]
    
    def insert_metrics(self, conn, project_id, version, analysis_date, metrics):
        """Inserta métricas en la base de datos."""
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO metrics_history (
                    project_id, version, analysis_date,
                    vulnerabilities, bugs, code_smells, security_hotspots,
                    hotspots_reviewed_percentage, coverage, lines_to_cover,
                    uncovered_lines, duplicated_lines_density, duplicated_blocks,
                    duplicated_files, duplicated_lines, ncloc, sqale_index,
                    reliability_rating, security_rating, sqale_rating
                ) VALUES (
                    %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s
                )
                ON CONFLICT (project_id, analysis_date) 
                DO UPDATE SET
                    version = EXCLUDED.version,
                    vulnerabilities = EXCLUDED.vulnerabilities,
                    bugs = EXCLUDED.bugs,
                    code_smells = EXCLUDED.code_smells,
                    security_hotspots = EXCLUDED.security_hotspots,
                    hotspots_reviewed_percentage = EXCLUDED.hotspots_reviewed_percentage,
                    coverage = EXCLUDED.coverage,
                    lines_to_cover = EXCLUDED.lines_to_cover,
                    uncovered_lines = EXCLUDED.uncovered_lines,
                    duplicated_lines_density = EXCLUDED.duplicated_lines_density,
                    duplicated_blocks = EXCLUDED.duplicated_blocks,
                    duplicated_files = EXCLUDED.duplicated_files,
                    duplicated_lines = EXCLUDED.duplicated_lines,
                    ncloc = EXCLUDED.ncloc,
                    sqale_index = EXCLUDED.sqale_index,
                    reliability_rating = EXCLUDED.reliability_rating,
                    security_rating = EXCLUDED.security_rating,
                    sqale_rating = EXCLUDED.sqale_rating,
                    collected_at = NOW()
            """, (
                project_id, version, analysis_date,
                int(metrics.get('vulnerabilities', 0)),
                int(metrics.get('bugs', 0)),
                int(metrics.get('code_smells', 0)),
                int(metrics.get('security_hotspots', 0)),
                float(metrics.get('security_hotspots_reviewed', 0)),
                float(metrics.get('coverage', 0)),
                int(metrics.get('lines_to_cover', 0)),
                int(metrics.get('uncovered_lines', 0)),
                float(metrics.get('duplicated_lines_density', 0)),
                int(metrics.get('duplicated_blocks', 0)),
                int(metrics.get('duplicated_files', 0)),
                int(metrics.get('duplicated_lines', 0)),
                int(metrics.get('ncloc', 0)),
                int(metrics.get('sqale_index', 0)),
                self.rating_to_letter(metrics.get('reliability_rating')),
                self.rating_to_letter(metrics.get('security_rating')),
                self.rating_to_letter(metrics.get('sqale_rating'))
            ))
    
    @staticmethod
    def rating_to_letter(rating):
        """Convierte rating numérico a letra (1.0 -> A, 2.0 -> B, etc.)."""
        if rating is None:
            return None
        try:
            rating_num = int(float(rating))
            return chr(ord('A') + rating_num - 1) if 1 <= rating_num <= 5 else None
        except (ValueError, TypeError):
            return None
    
    def cleanup_old_data(self, conn):
        """Elimina datos más antiguos que el período de retención."""
        with conn.cursor() as cur:
            cur.execute("SELECT cleanup_old_metrics(%s)", (self.retention_days,))
            deleted = cur.fetchone()[0]
            if deleted > 0:
                logger.info(f"Eliminados {deleted} registros antiguos (>{self.retention_days} días)")
    
    def collect_all_metrics(self):
        """Recolecta métricas de todos los proyectos."""
        logger.info("Iniciando recolección de métricas...")
        
        projects = self.get_projects()
        if not projects:
            logger.warning("No se encontraron proyectos en SonarQube")
            return
        
        conn = None
        try:
            conn = self.get_db_connection()
            
            for project in projects:
                project_key = project['key']
                project_name = project.get('name', project_key)
                
                logger.info(f"Procesando proyecto: {project_name} ({project_key})")
                
                # Obtener métricas
                metrics = self.get_project_metrics(project_key)
                if not metrics:
                    logger.warning(f"No se pudieron obtener métricas para {project_key}")
                    continue
                
                # Obtener versión y fecha de análisis
                version = self.get_project_version(project_key)
                analysis_date = self.get_analysis_date(project_key)
                
                # Guardar en base de datos
                project_id = self.upsert_project(conn, project_key, project_name)
                self.insert_metrics(conn, project_id, version, analysis_date, metrics)
                conn.commit()  # Commit después de cada proyecto
                
                logger.info(f"  Versión: {version}, Bugs: {metrics.get('bugs', 0)}, "
                           f"Vulnerabilities: {metrics.get('vulnerabilities', 0)}, "
                           f"Coverage: {metrics.get('coverage', 0)}%")
            
            # Limpiar datos antiguos
            self.cleanup_old_data(conn)
            conn.commit()
            logger.info(f"Recolección completada: {len(projects)} proyectos procesados")
            
        except Exception as e:
            logger.error(f"Error durante la recolección: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()


def wait_for_postgres(max_retries=30, delay=2):
    """Espera a que PostgreSQL esté disponible."""
    collector = SonarQubeCollector()
    
    for attempt in range(max_retries):
        try:
            conn = collector.get_db_connection()
            conn.close()
            logger.info("Conexión a PostgreSQL establecida")
            return True
        except psycopg2.OperationalError:
            logger.info(f"Esperando a PostgreSQL... intento {attempt + 1}/{max_retries}")
            time.sleep(delay)
    
    logger.error("No se pudo conectar a PostgreSQL")
    return False


def main():
    """Función principal."""
    logger.info("=== SonarQube Metrics Collector ===")
    
    # Configuración
    collection_interval = int(os.environ.get('COLLECTION_INTERVAL', 3600))
    
    logger.info(f"SonarQube URL: {os.environ.get('SONARQUBE_URL', 'http://localhost:9000')}")
    logger.info(f"Intervalo de recolección: {collection_interval} segundos")
    logger.info(f"Retención de datos: {os.environ.get('DATA_RETENTION_DAYS', 365)} días")
    
    # Esperar a PostgreSQL
    if not wait_for_postgres():
        sys.exit(1)
    
    collector = SonarQubeCollector()
    
    # Ejecutar recolección inicial
    try:
        collector.collect_all_metrics()
    except Exception as e:
        logger.error(f"Error en recolección inicial: {e}")
    
    # Programar recolección periódica
    schedule.every(collection_interval).seconds.do(collector.collect_all_metrics)
    
    logger.info(f"Programada recolección cada {collection_interval} segundos")
    
    # Loop principal
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == '__main__':
    main()

