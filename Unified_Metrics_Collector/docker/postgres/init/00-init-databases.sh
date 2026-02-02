#!/bin/bash
set -e

# Crear bases de datos si no existen
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE jenkins_metrics;
    CREATE DATABASE sonarqube_metrics;
    GRANT ALL PRIVILEGES ON DATABASE jenkins_metrics TO $POSTGRES_USER;
    GRANT ALL PRIVILEGES ON DATABASE sonarqube_metrics TO $POSTGRES_USER;
EOSQL

echo "Bases de datos jenkins_metrics y sonarqube_metrics creadas exitosamente."
