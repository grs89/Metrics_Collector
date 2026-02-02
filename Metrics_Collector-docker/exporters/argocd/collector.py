#!/usr/bin/env python3
"""
ArgoCD Metrics Collector
Recolecta estado de aplicaciones y sincronizaciones de ArgoCD.
"""

import os
import sys
import time
import logging
import requests
import psycopg2
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

class ArgoCDCollector:
    """Clase para recolectar métricas de ArgoCD."""
    
    def __init__(self):
        self.argocd_url = os.environ.get('ARGOCD_URL', 'https://argocd.example.com').rstrip('/')
        self.argocd_token = os.environ.get('ARGOCD_TOKEN', '')
        self.db_config = {
            'host': os.environ.get('POSTGRES_HOST', 'localhost'),
            'port': int(os.environ.get('POSTGRES_PORT', 5432)),
            'database': os.environ.get('POSTGRES_DB', 'argocd_metrics'),
            'user': os.environ.get('POSTGRES_USER', 'admin'),
            'password': os.environ.get('POSTGRES_PASSWORD', 'admin123')
        }
        # Config para tabla de salud centralizada
        self.main_db_config = self.db_config.copy()
        self.main_db_config['database'] = 'metrics_main'
        
        self.retention_days = int(os.environ.get('DATA_RETENTION_DAYS', 365))
        
        if not self.argocd_token:
            logger.warning("ARGOCD_TOKEN no está configurado. La conexión puede fallar.")

    def update_health(self, status, details=""):
        """Actualiza el estado de salud en la DB centralizada."""
        try:
            conn = psycopg2.connect(**self.main_db_config)
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO collector_status (collector_name, status, details, last_run)
                    VALUES ('argocd', %s, %s, NOW())
                    ON CONFLICT (collector_name) DO UPDATE SET
                        status = EXCLUDED.status,
                        details = EXCLUDED.details,
                        last_run = NOW()
                """, (status, details))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error actualizando salud centralizada: {e}")

    def is_available(self) -> bool:
        """Verificar si ArgoCD está disponible."""
        try:
            url = f"{self.argocd_url}/api/v1/version"
            headers = {"Authorization": f"Bearer {self.argocd_token}"} if self.argocd_token else {}
            response = requests.get(url, headers=headers, timeout=10, verify=False) # verify=False para entornos dev
            return response.status_code in [200, 401, 403]
        except Exception:
            return False

    def get_db_connection(self):
        """Obtiene conexión a PostgreSQL."""
        return psycopg2.connect(**self.db_config)

    def argocd_request(self, endpoint):
        """Petición a la API de ArgoCD."""
        url = f"{self.argocd_url}/api/v1/{endpoint}"
        headers = {"Authorization": f"Bearer {self.argocd_token}"}
        try:
            response = requests.get(url, headers=headers, timeout=30, verify=False)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error en ArgoCD ({endpoint}): {e}")
            return None

    def collect_all_metrics(self):
        """Recolecta métricas de aplicaciones."""
        logger.info("Iniciando recolección de ArgoCD...")
        
        data = self.argocd_request('applications')
        if not data or 'items' not in data:
            logger.error("No se pudieron obtener aplicaciones de ArgoCD")
            self.update_health('ERROR', 'No se pudieron obtener aplicaciones')
            return

        conn = None
        try:
            conn = self.get_db_connection()
            apps = data.get('items', [])
            for app in apps:
                metadata = app.get('metadata', {})
                name = metadata.get('name')
                spec = app.get('spec', {})
                status = app.get('status', {})
                
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO applications (
                            name, project, sync_status, health_status, 
                            repo_url, target_revision, destination_namespace, updated_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (name) DO UPDATE SET
                            sync_status = EXCLUDED.sync_status,
                            health_status = EXCLUDED.health_status,
                            target_revision = EXCLUDED.target_revision,
                            updated_at = EXCLUDED.updated_at,
                            collected_at = NOW()
                    """, (
                        name,
                        spec.get('project'),
                        status.get('sync', {}).get('status'),
                        status.get('health', {}).get('status'),
                        spec.get('source', {}).get('repoURL'),
                        spec.get('source', {}).get('targetRevision'),
                        spec.get('destination', {}).get('namespace'),
                        parser.parse(metadata.get('creationTimestamp'))
                    ))
            
            # Limpieza y Commit
            with conn.cursor() as cur:
                cur.execute("SELECT cleanup_old_argocd_data(%s)", (self.retention_days,))
            conn.commit()
            
            logger.info(f"✓ {len(apps)} aplicaciones procesadas")
            self.update_health('OK', f'{len(apps)} aplicaciones procesadas')
            
        except Exception as e:
            logger.error(f"Error en recolección: {e}")
            self.update_health('ERROR', f'Excepción: {str(e)}')
            if conn: conn.rollback()
        finally:
            if conn: conn.close()

def wait_for_services(max_retries=30, delay=10):
    collector = ArgoCDCollector()
    logger.info("Esperando a que los servicios estén disponibles...")
    for attempt in range(max_retries):
        argocd_ready = collector.is_available()
        postgres_ready = False
        try:
            conn = collector.get_db_connection()
            conn.close()
            postgres_ready = True
        except Exception:
            pass
        if argocd_ready and postgres_ready:
            logger.info("✓ Todos los servicios están disponibles")
            return True
        status = f"ArgoCD: {'✓' if argocd_ready else '✗'}, PostgreSQL: {'✓' if postgres_ready else '✗'}"
        logger.info(f"Esperando... {status} ({attempt+1}/{max_retries})")
        time.sleep(delay)
    return False

def main():
    if not wait_for_services(): sys.exit(1)
    
    collector = ArgoCDCollector()
    interval = int(os.environ.get('ARGOCD_POLL_INTERVAL', 300))
    
    collector.collect_all_metrics()
    schedule.every(interval).seconds.do(collector.collect_all_metrics)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == '__main__':
    main()
