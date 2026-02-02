-- Esquema de base de datos para métricas de Jenkins
-- Con retención automática de 1 año

\c jenkins_metrics

-- Tabla principal de builds
CREATE TABLE jenkins_builds (
    id SERIAL PRIMARY KEY,
    job_name VARCHAR(500) NOT NULL,
    build_number INTEGER NOT NULL,
    version VARCHAR(255),
    display_name VARCHAR(500),
    result VARCHAR(50),
    duration_ms BIGINT DEFAULT 0,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Índice único para evitar duplicados
    CONSTRAINT unique_job_build UNIQUE (job_name, build_number)
);

-- Índices para consultas frecuentes
CREATE INDEX idx_builds_job_name ON jenkins_builds(job_name);
CREATE INDEX idx_builds_timestamp ON jenkins_builds(timestamp DESC);
CREATE INDEX idx_builds_result ON jenkins_builds(result);
CREATE INDEX idx_builds_version ON jenkins_builds(version);
CREATE INDEX idx_builds_job_timestamp ON jenkins_builds(job_name, timestamp DESC);

-- Tabla de resumen de jobs (actualizada periódicamente)
CREATE TABLE jenkins_job_summary (
    id SERIAL PRIMARY KEY,
    job_name VARCHAR(500) NOT NULL UNIQUE,
    total_builds INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    unstable_count INTEGER DEFAULT 0,
    aborted_count INTEGER DEFAULT 0,
    avg_duration_ms BIGINT DEFAULT 0,
    last_build_number INTEGER,
    last_build_result VARCHAR(50),
    last_build_timestamp TIMESTAMP WITH TIME ZONE,
    last_version VARCHAR(255),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_job_summary_name ON jenkins_job_summary(job_name);

-- Tabla de historial de versiones
CREATE TABLE jenkins_versions (
    id SERIAL PRIMARY KEY,
    job_name VARCHAR(500) NOT NULL,
    version VARCHAR(255) NOT NULL,
    first_build_number INTEGER,
    last_build_number INTEGER,
    total_builds INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    first_seen TIMESTAMP WITH TIME ZONE,
    last_seen TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT unique_job_version UNIQUE (job_name, version)
);

CREATE INDEX idx_versions_job ON jenkins_versions(job_name);
CREATE INDEX idx_versions_version ON jenkins_versions(version);
CREATE INDEX idx_versions_last_seen ON jenkins_versions(last_seen DESC);

-- Función para limpiar datos antiguos (retención de 1 año)
CREATE OR REPLACE FUNCTION cleanup_old_builds()
RETURNS void AS $$
BEGIN
    -- Eliminar builds más antiguos de 1 año
    DELETE FROM jenkins_builds 
    WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '1 year';
    
    -- Limpiar versiones sin builds recientes
    DELETE FROM jenkins_versions 
    WHERE last_seen < CURRENT_TIMESTAMP - INTERVAL '1 year';
    
    RAISE NOTICE 'Limpieza completada: eliminados registros con más de 1 año de antigüedad';
END;
$$ LANGUAGE plpgsql;

-- Programar limpieza automática usando pg_cron (si está disponible)
-- Si no tienes pg_cron, ejecutar manualmente o con cron externo
-- SELECT cron.schedule('cleanup-old-builds', '0 2 * * 0', 'SELECT cleanup_old_builds()');

-- Vista para métricas por día
CREATE OR REPLACE VIEW daily_build_metrics AS
SELECT 
    job_name,
    DATE(timestamp) as build_date,
    COUNT(*) as total_builds,
    SUM(CASE WHEN result = 'SUCCESS' THEN 1 ELSE 0 END) as success_count,
    SUM(CASE WHEN result = 'FAILURE' THEN 1 ELSE 0 END) as failure_count,
    SUM(CASE WHEN result = 'UNSTABLE' THEN 1 ELSE 0 END) as unstable_count,
    SUM(CASE WHEN result = 'ABORTED' THEN 1 ELSE 0 END) as aborted_count,
    AVG(duration_ms) as avg_duration_ms,
    MIN(duration_ms) as min_duration_ms,
    MAX(duration_ms) as max_duration_ms
FROM jenkins_builds
GROUP BY job_name, DATE(timestamp);

-- Vista para historial de versiones
CREATE OR REPLACE VIEW version_history AS
SELECT 
    jb.job_name,
    jb.version,
    jb.build_number,
    jb.result,
    jb.duration_ms,
    jb.timestamp,
    jb.display_name
FROM jenkins_builds jb
WHERE jb.version IS NOT NULL AND jb.version != 'N/A'
ORDER BY jb.timestamp DESC;

-- Vista para últimas versiones por job
CREATE OR REPLACE VIEW latest_versions AS
SELECT DISTINCT ON (job_name)
    job_name,
    version,
    build_number,
    result,
    timestamp
FROM jenkins_builds
WHERE version IS NOT NULL AND version != 'N/A'
ORDER BY job_name, timestamp DESC;

-- Función para actualizar resumen de jobs
CREATE OR REPLACE FUNCTION update_job_summary(p_job_name VARCHAR)
RETURNS void AS $$
DECLARE
    v_stats RECORD;
    v_last_build RECORD;
BEGIN
    -- Obtener estadísticas
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN result = 'SUCCESS' THEN 1 ELSE 0 END) as success,
        SUM(CASE WHEN result = 'FAILURE' THEN 1 ELSE 0 END) as failure,
        SUM(CASE WHEN result = 'UNSTABLE' THEN 1 ELSE 0 END) as unstable,
        SUM(CASE WHEN result = 'ABORTED' THEN 1 ELSE 0 END) as aborted,
        AVG(duration_ms) as avg_duration
    INTO v_stats
    FROM jenkins_builds
    WHERE job_name = p_job_name;
    
    -- Obtener último build
    SELECT build_number, result, timestamp, version
    INTO v_last_build
    FROM jenkins_builds
    WHERE job_name = p_job_name
    ORDER BY timestamp DESC
    LIMIT 1;
    
    -- Insertar o actualizar resumen
    INSERT INTO jenkins_job_summary (
        job_name, total_builds, success_count, failure_count, 
        unstable_count, aborted_count, avg_duration_ms,
        last_build_number, last_build_result, last_build_timestamp, last_version
    ) VALUES (
        p_job_name, v_stats.total, v_stats.success, v_stats.failure,
        v_stats.unstable, v_stats.aborted, COALESCE(v_stats.avg_duration, 0),
        v_last_build.build_number, v_last_build.result, 
        v_last_build.timestamp, v_last_build.version
    )
    ON CONFLICT (job_name) DO UPDATE SET
        total_builds = EXCLUDED.total_builds,
        success_count = EXCLUDED.success_count,
        failure_count = EXCLUDED.failure_count,
        unstable_count = EXCLUDED.unstable_count,
        aborted_count = EXCLUDED.aborted_count,
        avg_duration_ms = EXCLUDED.avg_duration_ms,
        last_build_number = EXCLUDED.last_build_number,
        last_build_result = EXCLUDED.last_build_result,
        last_build_timestamp = EXCLUDED.last_build_timestamp,
        last_version = EXCLUDED.last_version,
        updated_at = CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- Trigger para actualizar versiones automáticamente
CREATE OR REPLACE FUNCTION update_version_stats()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO jenkins_versions (
        job_name, version, first_build_number, last_build_number,
        total_builds, success_count, failure_count, first_seen, last_seen
    ) VALUES (
        NEW.job_name, COALESCE(NEW.version, 'N/A'), NEW.build_number, NEW.build_number,
        1,
        CASE WHEN NEW.result = 'SUCCESS' THEN 1 ELSE 0 END,
        CASE WHEN NEW.result = 'FAILURE' THEN 1 ELSE 0 END,
        NEW.timestamp, NEW.timestamp
    )
    ON CONFLICT (job_name, version) DO UPDATE SET
        last_build_number = EXCLUDED.last_build_number,
        total_builds = jenkins_versions.total_builds + 1,
        success_count = jenkins_versions.success_count + EXCLUDED.success_count,
        failure_count = jenkins_versions.failure_count + EXCLUDED.failure_count,
        last_seen = EXCLUDED.last_seen;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_version_stats
    AFTER INSERT ON jenkins_builds
    FOR EACH ROW
    EXECUTE FUNCTION update_version_stats();

-- Datos de ejemplo (opcional, eliminar en producción)
-- INSERT INTO jenkins_builds (job_name, build_number, version, result, duration_ms, timestamp)
-- VALUES ('ejemplo-job', 1, '1.0.0', 'SUCCESS', 60000, CURRENT_TIMESTAMP);

COMMENT ON TABLE jenkins_builds IS 'Historial de builds de Jenkins con retención de 1 año';
COMMENT ON TABLE jenkins_job_summary IS 'Resumen estadístico por job';
COMMENT ON TABLE jenkins_versions IS 'Historial de versiones deployadas por job';

