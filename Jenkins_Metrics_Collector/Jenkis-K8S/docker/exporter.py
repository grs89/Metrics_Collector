#!/usr/bin/env python3
"""
Jenkins Metrics Exporter para PostgreSQL
Exporta historial de builds, versiones y métricas de cada job de Jenkins existente
"""

import os
import sys
import time
import logging
import re
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any

import requests
from requests.auth import HTTPBasicAuth
import psycopg2
from psycopg2.extras import execute_values

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Configuración desde variables de entorno
JENKINS_URL = os.getenv('JENKINS_URL', 'http://localhost:8080')
JENKINS_USER = os.getenv('JENKINS_USER', 'admin')
JENKINS_TOKEN = os.getenv('JENKINS_TOKEN', '')

POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'postgres-service')
POSTGRES_PORT = int(os.getenv('POSTGRES_PORT', '5432'))
POSTGRES_DB = os.getenv('POSTGRES_DB', 'jenkins_metrics')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'jenkins_metrics')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'jenkins_metrics_password')

POLL_INTERVAL = int(os.getenv('POLL_INTERVAL', '60'))


class JenkinsClient:
    """Cliente para interactuar con la API de Jenkins"""
    
    def __init__(self, url: str, user: str, token: str):
        self.url = url.rstrip('/')
        self.auth = HTTPBasicAuth(user, token) if token else None
        self.session = requests.Session()
        if token:
            self.session.auth = self.auth
        
    def _get(self, endpoint: str, params: Optional[dict] = None) -> Optional[dict]:
        """Realizar petición GET a Jenkins"""
        try:
            url = f"{self.url}{endpoint}"
            response = self.session.get(
                url,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error al conectar con Jenkins: {e}")
            return None
            
    def get_all_jobs(self) -> List[Dict[str, Any]]:
        """Obtener todos los jobs de Jenkins (incluyendo jobs en carpetas)"""
        jobs = []
        self._get_jobs_recursive('', jobs)
        return jobs
    
    def _get_jobs_recursive(self, path: str, jobs: List[Dict[str, Any]]):
        """Obtener jobs recursivamente incluyendo carpetas"""
        endpoint = f"{path}/api/json" if path else "/api/json"
        data = self._get(endpoint, {'tree': 'jobs[name,url,color,_class]'})
        
        if not data or 'jobs' not in data:
            return
            
        for job in data['jobs']:
            job_class = job.get('_class', '')
            job_name = job.get('name', '')
            job_path = f"{path}/job/{job_name}" if path else f"/job/{job_name}"
            
            # Si es una carpeta, buscar recursivamente
            if 'folder' in job_class.lower() or 'organizationfolder' in job_class.lower():
                self._get_jobs_recursive(job_path, jobs)
            else:
                job['path'] = job_path
                job['full_name'] = job_path.replace('/job/', '/').lstrip('/')
                jobs.append(job)
                
    def get_job_builds(self, job_path: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Obtener historial de builds de un job"""
        endpoint = f"{job_path}/api/json"
        params = {
            'tree': f'builds[number,url,result,timestamp,duration,displayName,description]{{0,{limit}}}'
        }
        data = self._get(endpoint, params)
        return data.get('builds', []) if data else []
    
    def is_available(self) -> bool:
        """Verificar si Jenkins está disponible"""
        try:
            response = self.session.get(f"{self.url}/api/json", timeout=10)
            return response.status_code in [200, 401, 403]
        except:
            return False


class PostgresExporter:
    """Exportador de métricas a PostgreSQL"""
    
    def __init__(self, host: str, port: int, database: str, user: str, password: str):
        self.connection_params = {
            'host': host,
            'port': port,
            'database': database,
            'user': user,
            'password': password
        }
        self.conn = None
        
    def connect(self):
        """Establecer conexión con PostgreSQL"""
        try:
            self.conn = psycopg2.connect(**self.connection_params)
            self.conn.autocommit = False
            logger.info("Conexión a PostgreSQL establecida")
            return True
        except psycopg2.Error as e:
            logger.error(f"Error conectando a PostgreSQL: {e}")
            return False
    
    def close(self):
        """Cerrar conexión"""
        if self.conn:
            self.conn.close()
            
    def get_existing_builds(self, job_name: str) -> set:
        """Obtener números de build ya existentes para un job"""
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    "SELECT build_number FROM jenkins_builds WHERE job_name = %s",
                    (job_name,)
                )
                return {row[0] for row in cur.fetchall()}
        except psycopg2.Error as e:
            logger.error(f"Error obteniendo builds existentes: {e}")
            return set()
    
    def insert_builds(self, builds: List[Dict[str, Any]]) -> int:
        """Insertar múltiples builds en la base de datos"""
        if not builds:
            return 0
            
        try:
            with self.conn.cursor() as cur:
                # Preparar datos para inserción
                values = []
                for build in builds:
                    values.append((
                        build['job_name'],
                        build['build_number'],
                        build.get('version'),
                        build.get('display_name'),
                        build.get('result'),
                        build.get('duration_ms', 0),
                        build['timestamp'],
                        build.get('description')
                    ))
                
                # Insertar con ON CONFLICT DO NOTHING para evitar duplicados
                execute_values(
                    cur,
                    """
                    INSERT INTO jenkins_builds 
                        (job_name, build_number, version, display_name, result, 
                         duration_ms, timestamp, description)
                    VALUES %s
                    ON CONFLICT (job_name, build_number) DO UPDATE SET
                        version = EXCLUDED.version,
                        display_name = EXCLUDED.display_name,
                        result = EXCLUDED.result,
                        duration_ms = EXCLUDED.duration_ms,
                        description = EXCLUDED.description
                    """,
                    values
                )
                
                self.conn.commit()
                return len(values)
                
        except psycopg2.Error as e:
            logger.error(f"Error insertando builds: {e}")
            self.conn.rollback()
            return 0
    
    def update_job_summary(self, job_name: str):
        """Actualizar resumen del job"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT update_job_summary(%s)", (job_name,))
                self.conn.commit()
        except psycopg2.Error as e:
            logger.error(f"Error actualizando resumen del job: {e}")
            self.conn.rollback()
    
    def run_cleanup(self):
        """Ejecutar limpieza de datos antiguos"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT cleanup_old_builds()")
                self.conn.commit()
                logger.info("Limpieza de datos antiguos completada")
        except psycopg2.Error as e:
            logger.error(f"Error en limpieza: {e}")
            self.conn.rollback()


def extract_version(build: Dict[str, Any]) -> str:
    """Extraer versión del build desde displayName o description"""
    display_name = build.get('displayName', '')
    description = build.get('description', '') or ''
    
    # Buscar patrones comunes de versión
    version_patterns = [
        r'v?(\d+\.\d+\.\d+(?:-[\w.]+)?)',  # v1.2.3 o 1.2.3-beta
        r'version[:\s]+(\S+)',              # version: xxx
        r'release[:\s]+(\S+)',              # release: xxx
        r'tag[:\s]+(\S+)',                  # tag: xxx
        r'\[(\d+\.\d+(?:\.\d+)?)\]',        # [1.2.3]
    ]
    
    for text in [display_name, description]:
        if not text:
            continue
        for pattern in version_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
    
    # Si no se encuentra versión, usar displayName si es diferente del número de build
    build_number = str(build.get('number', ''))
    if display_name and display_name != f"#{build_number}" and display_name != build_number:
        return display_name
    
    return 'N/A'


def wait_for_services(jenkins_url: str, pg_params: dict, max_retries: int = 30):
    """Esperar a que Jenkins y PostgreSQL estén disponibles"""
    
    logger.info("Esperando a que los servicios estén disponibles...")
    
    for i in range(max_retries):
        jenkins_ready = False
        postgres_ready = False
        
        # Verificar Jenkins
        try:
            response = requests.get(f"{jenkins_url}/api/json", timeout=5)
            jenkins_ready = response.status_code in [200, 401, 403]
        except:
            pass
            
        # Verificar PostgreSQL
        try:
            conn = psycopg2.connect(**pg_params, connect_timeout=5)
            conn.close()
            postgres_ready = True
        except:
            pass
            
        if jenkins_ready and postgres_ready:
            logger.info("✓ Todos los servicios están disponibles")
            return True
            
        status = f"Jenkins: {'✓' if jenkins_ready else '✗'}, PostgreSQL: {'✓' if postgres_ready else '✗'}"
        logger.info(f"Esperando... {status} ({i+1}/{max_retries})")
        time.sleep(10)
        
    logger.error("Timeout esperando servicios")
    return False


def export_metrics(jenkins: JenkinsClient, postgres: PostgresExporter):
    """Función principal de exportación"""
    
    try:
        # Reconectar si es necesario
        if not postgres.conn or postgres.conn.closed:
            if not postgres.connect():
                return
        
        # Obtener todos los jobs
        jobs = jenkins.get_all_jobs()
        logger.info(f"Encontrados {len(jobs)} jobs en Jenkins")
        
        total_new_builds = 0
        
        for job in jobs:
            job_name = job.get('full_name', job.get('name', 'unknown'))
            job_path = job.get('path', '')
            
            # Obtener builds existentes en la BD
            existing_builds = postgres.get_existing_builds(job_name)
            
            # Obtener builds del job desde Jenkins
            builds = jenkins.get_job_builds(job_path, limit=100)
            
            if not builds:
                continue
            
            # Filtrar solo builds nuevos
            new_builds = []
            for build in builds:
                build_number = build.get('number', 0)
                
                if build_number not in existing_builds:
                    # Convertir timestamp de milisegundos
                    timestamp_ms = build.get('timestamp', 0)
                    if timestamp_ms:
                        build_time = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
                    else:
                        build_time = datetime.now(tz=timezone.utc)
                    
                    new_builds.append({
                        'job_name': job_name,
                        'build_number': build_number,
                        'version': extract_version(build),
                        'display_name': build.get('displayName', str(build_number)),
                        'result': build.get('result', 'UNKNOWN'),
                        'duration_ms': build.get('duration', 0),
                        'timestamp': build_time,
                        'description': build.get('description')
                    })
            
            # Insertar nuevos builds
            if new_builds:
                inserted = postgres.insert_builds(new_builds)
                total_new_builds += inserted
                logger.info(f"Job '{job_name}': {inserted} nuevos builds exportados")
                
                # Actualizar resumen del job
                postgres.update_job_summary(job_name)
        
        if total_new_builds > 0:
            logger.info(f"Total: {total_new_builds} nuevos builds exportados")
                
    except Exception as e:
        logger.error(f"Error durante la exportación: {e}")


def main():
    """Punto de entrada principal"""
    logger.info("=" * 60)
    logger.info("Jenkins Metrics Exporter para PostgreSQL (Kubernetes)")
    logger.info("=" * 60)
    logger.info(f"Jenkins URL: {JENKINS_URL}")
    logger.info(f"PostgreSQL: {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")
    logger.info(f"Intervalo de polling: {POLL_INTERVAL}s")
    logger.info("=" * 60)
    
    pg_params = {
        'host': POSTGRES_HOST,
        'port': POSTGRES_PORT,
        'database': POSTGRES_DB,
        'user': POSTGRES_USER,
        'password': POSTGRES_PASSWORD
    }
    
    # Esperar a que los servicios estén disponibles
    if not wait_for_services(JENKINS_URL, pg_params):
        sys.exit(1)
    
    # Crear clientes
    jenkins = JenkinsClient(JENKINS_URL, JENKINS_USER, JENKINS_TOKEN)
    postgres = PostgresExporter(
        POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, 
        POSTGRES_USER, POSTGRES_PASSWORD
    )
    
    if not postgres.connect():
        logger.error("No se pudo conectar a PostgreSQL")
        sys.exit(1)
    
    # Exportar métricas iniciales
    logger.info("Ejecutando exportación inicial...")
    export_metrics(jenkins, postgres)
    
    # Ejecutar limpieza inicial de datos antiguos
    postgres.run_cleanup()
    
    # Bucle principal de polling
    logger.info(f"Iniciando bucle de polling cada {POLL_INTERVAL} segundos...")
    cleanup_counter = 0
    
    while True:
        time.sleep(POLL_INTERVAL)
        try:
            export_metrics(jenkins, postgres)
            
            # Ejecutar limpieza una vez al día (cada ~1440 iteraciones con 60s de intervalo)
            cleanup_counter += 1
            if cleanup_counter >= 1440:
                postgres.run_cleanup()
                cleanup_counter = 0
                
        except Exception as e:
            logger.error(f"Error en el bucle de polling: {e}")
            # Intentar reconectar
            time.sleep(30)
            postgres.connect()


if __name__ == "__main__":
    main()



