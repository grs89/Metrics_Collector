-- Creación de las bases de datos de métricas
CREATE DATABASE jenkins_metrics;
CREATE DATABASE sonarqube_metrics;
CREATE DATABASE jira_metrics;
CREATE DATABASE argocd_metrics;
CREATE DATABASE argorollouts_metrics;
CREATE DATABASE git_metrics;

-- Permisos
GRANT ALL PRIVILEGES ON DATABASE jenkins_metrics TO admin;
GRANT ALL PRIVILEGES ON DATABASE sonarqube_metrics TO admin;
GRANT ALL PRIVILEGES ON DATABASE jira_metrics TO admin;
GRANT ALL PRIVILEGES ON DATABASE argocd_metrics TO admin;
GRANT ALL PRIVILEGES ON DATABASE argorollouts_metrics TO admin;
GRANT ALL PRIVILEGES ON DATABASE git_metrics TO admin;
