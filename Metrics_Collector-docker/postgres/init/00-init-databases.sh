#!/bin/bash
set -e

# Crear bases de datos si no existen
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    SELECT 'CREATE DATABASE jenkins_metrics'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'jenkins_metrics')\gexec
    
    SELECT 'CREATE DATABASE sonarqube_metrics'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'sonarqube_metrics')\gexec
    
    GRANT ALL PRIVILEGES ON DATABASE jenkins_metrics TO $POSTGRES_USER;
    GRANT ALL PRIVILEGES ON DATABASE sonarqube_metrics TO $POSTGRES_USER;
EOSQL

echo "Bases de datos jenkins_metrics y sonarqube_metrics creadas exitosamente."
