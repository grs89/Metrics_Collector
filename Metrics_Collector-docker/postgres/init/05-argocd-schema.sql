-- Esquema de base de datos para métricas de ArgoCD
-- Retención de datos: 1 año

\c argocd_metrics

-- Tabla de Aplicaciones
CREATE TABLE IF NOT EXISTS applications (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    project VARCHAR(255),
    sync_status VARCHAR(50), -- Synced, OutOfSync
    health_status VARCHAR(50), -- Healthy, Degraded, Progressing, Suspended, Missing, Unknown
    repo_url TEXT,
    target_revision VARCHAR(100),
    destination_server TEXT,
    destination_namespace VARCHAR(255),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Historial de sincronizaciones
CREATE TABLE IF NOT EXISTS sync_history (
    id SERIAL PRIMARY KEY,
    app_name VARCHAR(255) NOT NULL,
    sync_status VARCHAR(50),
    revision VARCHAR(100),
    started_at TIMESTAMP WITH TIME ZONE,
    finished_at TIMESTAMP WITH TIME ZONE,
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Función de limpieza
CREATE OR REPLACE FUNCTION cleanup_old_argocd_data(days_to_keep INTEGER) 
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM sync_history 
    WHERE collected_at < CURRENT_DATE - (days_to_keep || ' days')::INTERVAL;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;
