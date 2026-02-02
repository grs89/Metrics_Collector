-- Esquema común para salud de recolectores
-- Se ejecuta en la base de datos principal (metrics_main)

\c metrics_main

CREATE TABLE IF NOT EXISTS collector_status (
    id SERIAL PRIMARY KEY,
    collector_name VARCHAR(50) UNIQUE NOT NULL,
    last_run TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL, -- 'OK', 'ERROR', 'WARNING'
    details TEXT,
    version VARCHAR(20)
);

-- Insertar placeholders para los colectores conocidos
INSERT INTO collector_status (collector_name, status, details)
VALUES 
    ('jenkins', 'UNKNOWN', 'Esperando primera ejecución...'),
    ('sonarqube', 'UNKNOWN', 'Esperando primera ejecución...'),
    ('jira', 'UNKNOWN', 'Esperando primera ejecución...'),
    ('argocd', 'UNKNOWN', 'Esperando primera ejecución...')
ON CONFLICT (collector_name) DO NOTHING;
