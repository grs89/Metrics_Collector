-- Esquema de base de datos para métricas de Jira
-- Retención de datos: 1 año (365 días)

\c jira_metrics

-- Tabla de proyectos de Jira
CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    project_key VARCHAR(50) UNIQUE NOT NULL,
    project_name VARCHAR(255) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de Sprints
CREATE TABLE IF NOT EXISTS sprints (
    id SERIAL PRIMARY KEY,
    jira_sprint_id INTEGER UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    state VARCHAR(50),
    start_date TIMESTAMP WITH TIME ZONE,
    end_date TIMESTAMP WITH TIME ZONE,
    complete_date TIMESTAMP WITH TIME ZONE,
    board_id INTEGER
);

-- Tabla de Issues (Estado actual)
CREATE TABLE IF NOT EXISTS issues (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id),
    issue_key VARCHAR(50) UNIQUE NOT NULL,
    issue_type VARCHAR(50),
    priority VARCHAR(50),
    status VARCHAR(50),
    resolution VARCHAR(50),
    assignee_name VARCHAR(255),
    reporter_name VARCHAR(255),
    summary TEXT,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    sprint_id INTEGER REFERENCES sprints(id),
    story_points FLOAT,
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Historial de transiciones de estado (Para Cycle Time)
CREATE TABLE IF NOT EXISTS status_history (
    id SERIAL PRIMARY KEY,
    issue_key VARCHAR(50) NOT NULL,
    from_status VARCHAR(50),
    to_status VARCHAR(50),
    transition_date TIMESTAMP WITH TIME ZONE NOT NULL,
    author_name VARCHAR(255)
);

-- Vista para cálculo de Cycle Time
CREATE OR REPLACE VIEW issue_cycle_time AS
SELECT 
    issue_key,
    MIN(transition_date) FILTER (WHERE to_status IN ('In Progress', 'In Development')) as started_at,
    MIN(transition_date) FILTER (WHERE to_status IN ('Done', 'Resolved', 'Closed')) as finished_at
FROM status_history
GROUP BY issue_key;

-- Función de limpieza de datos antiguos
CREATE OR REPLACE FUNCTION cleanup_old_jira_data(days_to_keep INTEGER) 
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Eliminar historial de estados antiguo
    DELETE FROM status_history 
    WHERE transition_date < CURRENT_DATE - (days_to_keep || ' days')::INTERVAL;
    
    -- Eliminar métricas recolectadas antiguas
    DELETE FROM issues 
    WHERE collected_at < CURRENT_DATE - (days_to_keep || ' days')::INTERVAL;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;
