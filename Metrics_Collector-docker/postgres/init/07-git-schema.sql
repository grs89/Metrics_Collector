-- Esquema de base de datos para métricas de Git (GitHub/GitLab)
-- Retención de datos: 1 año

\c git_metrics

-- Tabla de Repositorios
CREATE TABLE IF NOT EXISTS repositories (
    id SERIAL PRIMARY KEY,
    provider VARCHAR(20), -- github, gitlab
    full_name VARCHAR(255) UNIQUE NOT NULL,
    url TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de Pull Requests / Merge Requests
CREATE TABLE IF NOT EXISTS pull_requests (
    id SERIAL PRIMARY KEY,
    repo_id INTEGER REFERENCES repositories(id),
    pr_number INTEGER NOT NULL,
    title TEXT,
    state VARCHAR(50), -- open, closed, merged
    author VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    closed_at TIMESTAMP WITH TIME ZONE,
    merged_at TIMESTAMP WITH TIME ZONE,
    draft BOOLEAN DEFAULT FALSE,
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(repo_id, pr_number)
);

-- Vista para métricas DORA: Lead Time for Changes (PR Creation to Merge)
CREATE OR REPLACE VIEW lead_time_metrics AS
SELECT 
    r.full_name as repository,
    pr.pr_number,
    pr.created_at,
    pr.merged_at,
    EXTRACT(EPOCH FROM (pr.merged_at - pr.created_at))/3600 as lead_time_hours
FROM pull_requests pr
JOIN repositories r ON pr.repo_id = r.id
WHERE pr.merged_at IS NOT NULL;

-- Función de limpieza
CREATE OR REPLACE FUNCTION cleanup_old_git_data(days_to_keep INTEGER) 
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM pull_requests 
    WHERE collected_at < CURRENT_DATE - (days_to_keep || ' days')::INTERVAL;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;
