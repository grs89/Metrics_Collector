#!/usr/bin/env python3
"""
Argo Rollouts Metrics Collector
Recolecta estado de estrategias Canary y Blue-Green de Argo Rollouts via ArgoCD API.
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

class RolloutsCollector:
    def __init__(self):
        self.argocd_url = os.environ.get('ARGOCD_URL', 'https://argocd.example.com').rstrip('/')
        self.argocd_token = os.environ.get('ARGOCD_TOKEN', '')
        self.db_config = {
            'host': os.environ.get('POSTGRES_HOST', 'localhost'),
            'port': int(os.environ.get('POSTGRES_PORT', 5432)),
            'database': os.environ.get('POSTGRES_DB', 'argorollouts_metrics'),
            'user': os.environ.get('POSTGRES_USER', 'admin'),
            'password': os.environ.get('POSTGRES_PASSWORD', 'admin123')
        }
        self.main_db_config = self.db_config.copy()
        self.main_db_config['database'] = 'metrics_main'
        self.retention_days = int(os.environ.get('DATA_RETENTION_DAYS', 365))

    def update_health(self, status, details=""):
        try:
            conn = psycopg2.connect(**self.main_db_config)
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO collector_status (collector_name, status, details, last_run)
                    VALUES ('argorollouts', %s, %s, NOW())
                    ON CONFLICT (collector_name) DO UPDATE SET
                        status = EXCLUDED.status, details = EXCLUDED.details, last_run = NOW()
                """, (status, details))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error actualizando salud: {e}")

    def get_db_connection(self):
        return psycopg2.connect(**self.db_config)

    def argocd_request(self, endpoint):
        url = f"{self.argocd_url}/api/v1/{endpoint}"
        headers = {"Authorization": f"Bearer {self.argocd_token}"}
        try:
            response = requests.get(url, headers=headers, timeout=30, verify=False)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error API ArgoCD ({endpoint}): {e}")
            return None

    def collect_rollouts(self):
        logger.info("Iniciando recolección de Argo Rollouts...")
        
        # Nota: ArgoCD expone Rollouts como recursos. 
        # Dependiendo de la versión, se consultan via generic resources o el plugin de Rollouts.
        # Usaremos el endpoint de applications para filtrar recursos de tipo Rollout.
        apps_data = self.argocd_request('applications')
        if not apps_data:
            self.update_health('ERROR', 'No se pudo conectar con ArgoCD')
            return

        conn = None
        count = 0
        try:
            conn = self.get_db_connection()
            for app in apps_data.get('items', []):
                resources = app.get('status', {}).get('resources', [])
                for res in resources:
                    if res.get('kind') == 'Rollout':
                        name = res.get('name')
                        namespace = res.get('namespace')
                        health = res.get('health', {}).get('status')
                        
                        with conn.cursor() as cur:
                            cur.execute("""
                                INSERT INTO rollouts (name, namespace, status, updated_at)
                                VALUES (%s, %s, %s, NOW())
                                ON CONFLICT (name, namespace) DO UPDATE SET
                                    status = EXCLUDED.status, updated_at = NOW(), collected_at = NOW()
                            """, (name, namespace, health))
                            count += 1

            conn.commit()
            logger.info(f"✓ {count} rollouts procesados")
            self.update_health('OK', f'{count} rollouts monitoreados')
        except Exception as e:
            logger.error(f"Error recolección: {e}")
            self.update_health('ERROR', str(e))
        finally:
            if conn: conn.close()

def main():
    collector = RolloutsCollector()
    interval = int(os.environ.get('ROLLOUTS_POLL_INTERVAL', 300))
    collector.collect_rollouts()
    schedule.every(interval).seconds.do(collector.collect_rollouts)
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == '__main__':
    main()
