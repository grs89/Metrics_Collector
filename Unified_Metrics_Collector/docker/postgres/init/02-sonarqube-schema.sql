-- Esquema de base de datos para métricas de SonarQube
-- Retención de datos: 1 año (365 días)

-- Tabla de proyectos
CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    project_key VARCHAR(255) UNIQUE NOT NULL,
    project_name VARCHAR(500) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de métricas históricas
CREATE TABLE IF NOT EXISTS metrics_history (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    version VARCHAR(100),
    analysis_date TIMESTAMP WITH TIME ZONE NOT NULL,
    -- Métricas de calidad
    vulnerabilities INTEGER DEFAULT 0,
    bugs INTEGER DEFAULT 0,
    code_smells INTEGER DEFAULT 0,
    security_hotspots INTEGER DEFAULT 0,
    hotspots_reviewed_percentage DECIMAL(5,2) DEFAULT 0,
    -- Métricas de cobertura
    coverage DECIMAL(5,2) DEFAULT 0,
    lines_to_cover INTEGER DEFAULT 0,
    uncovered_lines INTEGER DEFAULT 0,
    -- Métricas de duplicación
    duplicated_lines_density DECIMAL(5,2) DEFAULT 0,
    duplicated_blocks INTEGER DEFAULT 0,
    duplicated_files INTEGER DEFAULT 0,
    duplicated_lines INTEGER DEFAULT 0,
    -- Métricas adicionales
    ncloc INTEGER DEFAULT 0,  -- Líneas de código (sin comentarios)
    sqale_index INTEGER DEFAULT 0,  -- Deuda técnica en minutos
    reliability_rating CHAR(1),  -- A, B, C, D, E
    security_rating CHAR(1),
    sqale_rating CHAR(1),  -- Maintainability rating
    -- Metadatos
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, analysis_date)
);

-- Índices para mejorar rendimiento
CREATE INDEX IF NOT EXISTS idx_metrics_project_id ON metrics_history(project_id);
CREATE INDEX IF NOT EXISTS idx_metrics_analysis_date ON metrics_history(analysis_date);
CREATE INDEX IF NOT EXISTS idx_metrics_version ON metrics_history(version);
CREATE INDEX IF NOT EXISTS idx_metrics_collected_at ON metrics_history(collected_at);
CREATE INDEX IF NOT EXISTS idx_projects_key ON projects(project_key);

-- Vista para consultas fáciles
CREATE OR REPLACE VIEW v_metrics_with_project AS
SELECT 
    p.project_key,
    p.project_name,
    m.version,
    m.analysis_date,
    m.vulnerabilities,
    m.bugs,
    m.code_smells,
    m.security_hotspots,
    m.hotspots_reviewed_percentage,
    m.coverage,
    m.duplicated_lines_density,
    m.duplicated_blocks,
    m.ncloc,
    m.sqale_index,
    m.reliability_rating,
    m.security_rating,
    m.sqale_rating,
    m.collected_at
FROM metrics_history m
JOIN projects p ON m.project_id = p.id
ORDER BY m.analysis_date DESC;

-- Función para limpiar datos antiguos (más de 365 días)
CREATE OR REPLACE FUNCTION cleanup_old_metrics(retention_days INTEGER DEFAULT 365)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM metrics_history 
    WHERE collected_at < NOW() - (retention_days || ' days')::INTERVAL;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Comentarios
COMMENT ON TABLE projects IS 'Tabla de proyectos de SonarQube';
COMMENT ON TABLE metrics_history IS 'Historial de métricas de SonarQube por proyecto y versión';
COMMENT ON COLUMN metrics_history.hotspots_reviewed_percentage IS 'Porcentaje de Security Hotspots revisados';
COMMENT ON COLUMN metrics_history.coverage IS 'Cobertura de código en porcentaje';
COMMENT ON COLUMN metrics_history.duplicated_lines_density IS 'Porcentaje de líneas duplicadas';
COMMENT ON COLUMN metrics_history.sqale_index IS 'Deuda técnica en minutos';
COMMENT ON FUNCTION cleanup_old_metrics IS 'Elimina métricas más antiguas que los días especificados';

