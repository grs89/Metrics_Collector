#!/usr/bin/env python3
"""
Notifier Service (Alert Manager)
Monitorea la salud de los colectores y métricas críticas para enviar alertas.
"""

import os
import sys
import time
import logging
import requests
import psycopg2
from datetime import datetime
import schedule

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AlertManager:
    def __init__(self):
        self.discord_webhook = os.environ.get('DISCORD_WEBHOOK_URL', '')
        self.slack_webhook = os.environ.get('SLACK_WEBHOOK_URL', '')
        self.db_host = os.environ.get('POSTGRES_HOST', 'localhost')
        self.db_port = int(os.environ.get('POSTGRES_PORT', 5432))
        self.db_user = os.environ.get('POSTGRES_USER', 'admin')
        self.db_password = os.environ.get('POSTGRES_PASSWORD', 'admin123')
        
        self.failure_threshold = float(os.environ.get('FAILED_BUILD_THRESHOLD', 20.0))
        self.last_alerts = {} # Para evitar spam

    def send_notification(self, message):
        logger.info(f"Enviando alerta: {message}")
        
        # Discord
        if self.discord_webhook:
            try:
                requests.post(self.discord_webhook, json={"content": f"🚨 **ALERT**: {message}"}, timeout=10)
            except Exception as e:
                logger.error(f"Error Discord: {e}")
        
        # Slack
        if self.slack_webhook:
            try:
                requests.post(self.slack_webhook, json={"text": f"🚨 *ALERT*: {message}"}, timeout=10)
            except Exception as e:
                logger.error(f"Error Slack: {e}")

    def check_collector_health(self):
        logger.info("Revisando salud de colectores...")
        try:
            conn = psycopg2.connect(host=self.db_host, port=self.db_port, database='metrics_main', user=self.db_user, password=self.db_password)
            with conn.cursor() as cur:
                cur.execute("SELECT collector_name, status, details FROM collector_status WHERE status = 'ERROR'")
                errors = cur.fetchall()
                for name, status, details in errors:
                    alert_key = f"health_{name}"
                    if alert_key not in self.last_alerts:
                        self.send_notification(f"Colector '{name}' reportó ERROR: {details}")
                        self.last_alerts[alert_key] = datetime.now()
                
                # Limpiar alertas viejas de la memoria si el estado ya no es ERROR
                cur.execute("SELECT collector_name FROM collector_status WHERE status = 'OK'")
                ok_collectors = [r[0] for r in cur.fetchall()]
                for name in ok_collectors:
                    self.last_alerts.pop(f"health_{name}", None)
            conn.close()
        except Exception as e:
            logger.error(f"Error checking health: {e}")

    def check_jenkins_failures(self):
        logger.info("Revisando tasa de fallos en Jenkins...")
        try:
            conn = psycopg2.connect(host=self.db_host, port=self.db_port, database='jenkins_metrics', user=self.db_user, password=self.db_password)
            with conn.cursor() as cur:
                # Ver últimos 100 builds
                cur.execute("""
                    WITH stats AS (
                        SELECT result, count(*) as cnt 
                        FROM builds 
                        WHERE timestamp > NOW() - INTERVAL '24 hours'
                        GROUP BY result
                    )
                    SELECT 
                        COALESCE(SUM(CASE WHEN result IN ('FAILURE', 'ABORTED') THEN cnt ELSE 0 END), 0) * 100.0 / 
                        NULLIF(SUM(cnt), 0) as failure_rate
                    FROM stats
                """)
                res = cur.fetchone()
                if res and res[0] and res[0] > self.failure_threshold:
                    alert_key = "jenkins_failure_rate"
                    if alert_key not in self.last_alerts:
                        self.send_notification(f"Tasa de fallos en Jenkins elevada: {res[0]:.1f}% (Umbral: {self.failure_threshold}%)")
                        self.last_alerts[alert_key] = datetime.now()
                else:
                    self.last_alerts.pop("jenkins_failure_rate", None)
            conn.close()
        except Exception as e:
            logger.error(f"Error checking Jenkins: {e}")

    def update_self_health(self):
        try:
            conn = psycopg2.connect(host=self.db_host, port=self.db_port, database='metrics_main', user=self.db_user, password=self.db_password)
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO collector_status (collector_name, status, details, last_run)
                    VALUES ('notifier', 'OK', 'Monitoreando alertas activo', NOW())
                    ON CONFLICT (collector_name) DO UPDATE SET
                        status = EXCLUDED.status, details = EXCLUDED.details, last_run = NOW()
                """)
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error auto-salud: {e}")

    def run(self):
        logger.info("==== Notifier Service Started ====")
        self.check_collector_health()
        self.check_jenkins_failures()
        self.update_self_health()
        
        schedule.every(5).minutes.do(self.check_collector_health)
        schedule.every(15).minutes.do(self.check_jenkins_failures)
        schedule.every(5).minutes.do(self.update_self_health)
        
        while True:
            schedule.run_pending()
            time.sleep(60)

if __name__ == '__main__':
    manager = AlertManager()
    manager.run()
