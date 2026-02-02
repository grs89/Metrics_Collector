#!/usr/bin/env python3
"""
Git Events Metrics Collector
Recolecta métricas de PRs/MRs de GitHub y GitLab para KPIs DORA.
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

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GitCollector:
    def __init__(self):
        self.provider = os.environ.get('GIT_PROVIDER', 'github').lower() # github o gitlab
        self.token = os.environ.get('GIT_TOKEN', '')
        self.repos = os.environ.get('GIT_REPOS', '').split(',') # owner/repo o project_id
        self.api_url = os.environ.get('GIT_API_URL', 'https://api.github.com' if self.provider == 'github' else 'https://gitlab.com/api/v4')
        
        self.db_config = {
            'host': os.environ.get('POSTGRES_HOST', 'localhost'),
            'port': int(os.environ.get('POSTGRES_PORT', 5432)),
            'database': os.environ.get('POSTGRES_DB', 'git_metrics'),
            'user': os.environ.get('POSTGRES_USER', 'admin'),
            'password': os.environ.get('POSTGRES_PASSWORD', 'admin123')
        }
        self.main_db_config = self.db_config.copy()
        self.main_db_config['database'] = 'metrics_main'

    def update_health(self, status, details=""):
        try:
            conn = psycopg2.connect(**self.main_db_config)
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO collector_status (collector_name, status, details, last_run)
                    VALUES ('git', %s, %s, NOW())
                    ON CONFLICT (collector_name) DO UPDATE SET
                        status = EXCLUDED.status, details = EXCLUDED.details, last_run = NOW()
                """, (status, details))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error salud: {e}")

    def collect_github(self, conn, repo_id, full_name):
        url = f"{self.api_url}/repos/{full_name}/pulls?state=all&sort=updated&direction=desc&per_page=50"
        headers = {"Authorization": f"token {self.token}"} if self.token else {}
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        prs = resp.json()
        
        for pr in prs:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO pull_requests (repo_id, pr_number, title, state, author, created_at, updated_at, closed_at, merged_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (repo_id, pr_number) DO UPDATE SET
                        state = EXCLUDED.state, updated_at = EXCLUDED.updated_at, 
                        closed_at = EXCLUDED.closed_at, merged_at = EXCLUDED.merged_at
                """, (
                    repo_id, pr['number'], pr['title'], pr['state'], pr['user']['login'],
                    parser.parse(pr['created_at']), parser.parse(pr['updated_at']),
                    parser.parse(pr['closed_at']) if pr['closed_at'] else None,
                    parser.parse(pr['merged_at']) if pr['merged_at'] else None
                ))

    def collect_all(self):
        logger.info(f"Iniciando recolección Git ({self.provider})...")
        if not self.repos or not self.repos[0]:
            logger.warning("No hay repositorios configurados")
            return

        conn = None
        try:
            conn = psycopg2.connect(**self.db_config)
            for repo_name in self.repos:
                repo_name = repo_name.strip()
                with conn.cursor() as cur:
                    cur.execute("INSERT INTO repositories (provider, full_name) VALUES (%s, %s) ON CONFLICT (full_name) DO UPDATE SET updated_at = NOW() RETURNING id", (self.provider, repo_name))
                    repo_id = cur.fetchone()[0]
                
                if self.provider == 'github':
                    self.collect_github(conn, repo_id, repo_name)
                # GitLab implementation would go here...
                
            conn.commit()
            self.update_health('OK', f'Procesados {len(self.repos)} repositorios')
        except Exception as e:
            logger.error(f"Error: {e}")
            self.update_health('ERROR', str(e))
        finally:
            if conn: conn.close()

def main():
    collector = GitCollector()
    interval = int(os.environ.get('GIT_POLL_INTERVAL', 3600))
    collector.collect_all()
    schedule.every(interval).seconds.do(collector.collect_all)
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == '__main__':
    main()
