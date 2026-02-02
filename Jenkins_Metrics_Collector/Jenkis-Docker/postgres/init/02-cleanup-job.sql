-- Script para configurar limpieza automática de datos antiguos
-- Ejecutar cleanup_old_builds() semanalmente para mantener retención de 1 año

-- Crear extensión pg_cron si está disponible (solo funciona en algunas instalaciones de PostgreSQL)
-- Si no está disponible, usar cron externo o ejecutar manualmente

-- Para verificar si pg_cron está disponible:
-- SELECT * FROM pg_extension WHERE extname = 'pg_cron';

-- Si pg_cron está disponible, descomentar las siguientes líneas:
-- CREATE EXTENSION IF NOT EXISTS pg_cron;
-- SELECT cron.schedule('weekly-cleanup', '0 3 * * 0', 'SELECT cleanup_old_builds()');

-- Alternativa: Crear una función que se puede llamar desde un cron externo
CREATE OR REPLACE FUNCTION run_maintenance()
RETURNS TABLE (
    builds_deleted INTEGER,
    versions_deleted INTEGER,
    message TEXT
) AS $$
DECLARE
    v_builds_deleted INTEGER;
    v_versions_deleted INTEGER;
BEGIN
    -- Contar antes de eliminar
    SELECT COUNT(*) INTO v_builds_deleted
    FROM jenkins_builds 
    WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '1 year';
    
    SELECT COUNT(*) INTO v_versions_deleted
    FROM jenkins_versions 
    WHERE last_seen < CURRENT_TIMESTAMP - INTERVAL '1 year';
    
    -- Ejecutar limpieza
    PERFORM cleanup_old_builds();
    
    -- Vacuum para recuperar espacio
    -- VACUUM ANALYZE jenkins_builds; -- Requiere ser ejecutado fuera de transacción
    
    RETURN QUERY SELECT 
        v_builds_deleted,
        v_versions_deleted,
        format('Mantenimiento completado: %s builds y %s versiones eliminadas', 
               v_builds_deleted, v_versions_deleted)::TEXT;
END;
$$ LANGUAGE plpgsql;

-- Vista para monitorear el tamaño de las tablas
CREATE OR REPLACE VIEW table_stats AS
SELECT 
    relname as table_name,
    pg_size_pretty(pg_total_relation_size(relid)) as total_size,
    pg_size_pretty(pg_relation_size(relid)) as data_size,
    pg_size_pretty(pg_indexes_size(relid)) as index_size,
    n_live_tup as row_count
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(relid) DESC;

-- Vista para verificar datos por antigüedad
CREATE OR REPLACE VIEW data_age_distribution AS
SELECT 
    CASE 
        WHEN timestamp >= CURRENT_TIMESTAMP - INTERVAL '7 days' THEN 'Última semana'
        WHEN timestamp >= CURRENT_TIMESTAMP - INTERVAL '30 days' THEN 'Último mes'
        WHEN timestamp >= CURRENT_TIMESTAMP - INTERVAL '90 days' THEN 'Últimos 3 meses'
        WHEN timestamp >= CURRENT_TIMESTAMP - INTERVAL '180 days' THEN 'Últimos 6 meses'
        WHEN timestamp >= CURRENT_TIMESTAMP - INTERVAL '365 days' THEN 'Último año'
        ELSE 'Más de 1 año (pendiente eliminación)'
    END as periodo,
    COUNT(*) as total_builds
FROM jenkins_builds
GROUP BY 1
ORDER BY MIN(timestamp) DESC;

