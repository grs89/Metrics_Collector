-- Esquema de base de datos para métricas de Argo Rollouts
-- Retención de datos: 1 año

\c argorollouts_metrics

-- Tabla de Rollouts (Estado Actual)
CREATE TABLE IF NOT EXISTS rollouts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    namespace VARCHAR(255) NOT NULL,
    strategy VARCHAR(50), -- Canary, BlueGreen
    status VARCHAR(50), -- Healthy, Degraded, Progressing, Paused, Aborted
    current_step_index INTEGER,
    total_steps INTEGER,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name, namespace)
);

-- Historial de transiciones y eventos de Rollout
CREATE TABLE IF NOT EXISTS rollout_history (
    id SERIAL PRIMARY KEY,
    rollout_name VARCHAR(255) NOT NULL,
    namespace VARCHAR(255) NOT NULL,
    event_type VARCHAR(50), -- Promotion, StepCompleted, Aborted, Reset
    old_status VARCHAR(50),
    new_status VARCHAR(50),
    message TEXT,
    event_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Función de limpieza
CREATE OR REPLACE FUNCTION cleanup_old_rollouts_data(days_to_keep INTEGER) 
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM rollout_history 
    WHERE event_timestamp < CURRENT_DATE - (days_to_keep || ' days')::INTERVAL;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;
