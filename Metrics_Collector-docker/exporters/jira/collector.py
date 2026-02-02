#!/usr/bin/env python3
"""
Jira Metrics Collector
Recolecta métricas de Jira (Issues, Cycle Time, Velocity) y las almacena en PostgreSQL.
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
from dateutil import parser

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

class JiraCollector:
    """Clase para recolectar métricas de Jira."""
    
    def __init__(self):
        self.jira_url = os.environ.get('JIRA_URL', 'https://your-domain.atlassian.net').rstrip('/')
        self.jira_user = os.environ.get('JIRA_USER', '')
        self.jira_token = os.environ.get('JIRA_TOKEN', '')
        self.projects = os.environ.get('JIRA_PROJECTS', '').split(',')
        self.db_config = {
            'host': os.environ.get('POSTGRES_HOST', 'localhost'),
            'port': int(os.environ.get('POSTGRES_PORT', 5432)),
            'database': os.environ.get('POSTGRES_DB', 'jira_metrics'),
            'user': os.environ.get('POSTGRES_USER', 'admin'),
            'password': os.environ.get('POSTGRES_PASSWORD', 'admin123')
        }
        self.retention_days = int(os.environ.get('DATA_RETENTION_DAYS', 365))
        
        if not self.jira_token:
            logger.warning("JIRA_TOKEN no está configurado. La conexión puede fallar.")

    def is_available(self) -> bool:
        """Verificar si Jira está disponible."""
        try:
            url = f"{self.jira_url}/rest/api/2/serverInfo"
            # Jira Cloud/Server suelen tener este endpoint público o que devuelve 401 si está vivo
            response = requests.get(url, timeout=10)
            return response.status_code in [200, 401, 403]
        except Exception:
            return False

    def get_db_connection(self):
        """Obtiene conexión a PostgreSQL."""
        return psycopg2.connect(**self.db_config)

    def jira_request(self, endpoint, params=None):
        """Realiza una petición a la API de Jira."""
        url = f"{self.jira_url}/rest/api/2/{endpoint}"
        auth = (self.jira_user, self.jira_token) if self.jira_user else None
        
        try:
            response = requests.get(url, params=params, auth=auth, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error en petición a Jira ({endpoint}): {e}")
            return None

    def upsert_project(self, conn, project_key):
        """Asegura que el proyecto existe en la DB."""
        # Intentar obtener info del proyecto de Jira
        info = self.jira_request(f"project/{project_key}")
        project_name = info.get('name', project_key) if info else project_key
        
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO projects (project_key, project_name, updated_at)
                VALUES (%s, %s, NOW())
                ON CONFLICT (project_key) 
                DO UPDATE SET project_name = EXCLUDED.project_name, updated_at = NOW()
                RETURNING id
            """, (project_key, project_name))
            return cur.fetchone()[0]

    def get_issues(self, project_key):
        """Obtiene issues recientes del proyecto."""
        issues = []
        start_at = 0
        max_results = 50
        
        # JQL para obtener issues actualizados recientemente
        jql = f"project = {project_key} ORDER BY updated DESC"
        
        while True:
            data = self.jira_request('search', {
                'jql': jql,
                'startAt': start_at,
                'maxResults': max_results,
                'expand': 'changelog'
            })
            
            if not data or 'issues' not in data:
                break
                
            issues.extend(data['issues'])
            
            if len(issues) >= data.get('total', 0) or len(issues) >= 200: # Limitar a 200 por ejecución
                break
            start_at += max_results
            
        return issues

    def process_issue(self, conn, project_id, issue_data):
        """Procesa un issue y su historial."""
        fields = issue_data.get('fields', {})
        key = issue_data.get('key')
        
        with conn.cursor() as cur:
            # Upsert Issue
            cur.execute("""
                INSERT INTO issues (
                    project_id, issue_key, issue_type, priority, status, 
                    resolution, assignee_name, reporter_name, summary,
                    created_at, updated_at, story_points
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (issue_key) DO UPDATE SET
                    status = EXCLUDED.status,
                    resolution = EXCLUDED.resolution,
                    assignee_name = EXCLUDED.assignee_name,
                    updated_at = EXCLUDED.updated_at,
                    summary = EXCLUDED.summary,
                    story_points = EXCLUDED.story_points,
                    collected_at = NOW()
            """, (
                project_id, key, 
                fields.get('issuetype', {}).get('name'),
                fields.get('priority', {}).get('name'),
                fields.get('status', {}).get('name'),
                fields.get('resolution', {}).get('name') if fields.get('resolution') else None,
                fields.get('assignee', {}).get('displayName') if fields.get('assignee') else None,
                fields.get('reporter', {}).get('displayName') if fields.get('reporter') else None,
                fields.get('summary'),
                parser.parse(fields.get('created')),
                parser.parse(fields.get('updated')),
                fields.get('customfield_10016') # Story points usualmente en este campo en Cloud
            ))

            # Procesar historial para Cycle Time
            changelog = issue_data.get('changelog', {}).get('histories', [])
            for history in changelog:
                author = history.get('author', {}).get('displayName')
                date = parser.parse(history.get('created'))
                for item in history.get('items', []):
                    if item.get('field') == 'status':
                        cur.execute("""
                            INSERT INTO status_history (issue_key, from_status, to_status, transition_date, author_name)
                            VALUES (%s, %s, %s, %s, %s)
                            ON CONFLICT DO NOTHING
                        """, (key, item.get('fromString'), item.get('toString'), date, author))

    def collect_all_metrics(self):
        """Recolecta métricas de todos los proyectos configurados."""
        if not self.projects or (len(self.projects) == 1 and self.projects[0] == ''):
            logger.warning("No hay proyectos configurados en JIRA_PROJECTS")
            return

        logger.info(f"Iniciando recolección de Jira para proyectos: {self.projects}")
        
        conn = None
        try:
            conn = self.get_db_connection()
            for p_key in self.projects:
                p_key = p_key.strip()
                if not p_key: continue
                
                logger.info(f"Procesando proyecto: {p_key}")
                p_id = self.upsert_project(conn, p_key)
                
                issues = self.get_issues(p_key)
                for issue in issues:
                    self.process_issue(conn, p_id, issue)
                    
                conn.commit()
                logger.info(f"  ✓ {p_key}: {len(issues)} issues procesados/actualizados")
            
            # Limpieza
            with conn.cursor() as cur:
                cur.execute("SELECT cleanup_old_jira_data(%s)", (self.retention_days,))
                logger.info(f"Limpieza de datos antiguos completada (>{self.retention_days} días)")
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error en recolección de Jira: {e}")
            if conn: conn.rollback()
        finally:
            if conn: conn.close()

def wait_for_services(max_retries=30, delay=10):
    """Espera a que Jira y PostgreSQL estén disponibles."""
    collector = JiraCollector()
    logger.info("Esperando a que los servicios estén disponibles...")
    
    for attempt in range(max_retries):
        jira_ready = collector.is_available()
        postgres_ready = False
        try:
            conn = collector.get_db_connection()
            conn.close()
            postgres_ready = True
        except Exception:
            pass
            
        if jira_ready and postgres_ready:
            logger.info("✓ Todos los servicios están disponibles")
            return True
        
        status = f"Jira: {'✓' if jira_ready else '✗'}, PostgreSQL: {'✓' if postgres_ready else '✗'}"
        logger.info(f"Esperando... {status} ({attempt + 1}/{max_retries})")
        time.sleep(delay)
    
    logger.error("Timeout esperando servicios")
    return False

def main():
    logger.info("=== Jira Metrics Collector ===")
    
    # Esperar a los servicios
    if not wait_for_services():
        sys.exit(1)
    
    collector = JiraCollector()
    poll_interval = int(os.environ.get('JIRA_POLL_INTERVAL', 3600))
    
    # Ejecución inicial
    collector.collect_all_metrics()
    
    # Programar
    schedule.every(poll_interval).seconds.do(collector.collect_all_metrics)
    logger.info(f"Programada recolección cada {poll_interval} segundos")
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == '__main__':
    main()
