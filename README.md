# 📊 Metrics Collector All-in-One

> 🌍 **Select Language**: 🇪🇸 [Español](#-español) | 🇧🇷 [Português](#-português)

---

<a name="-español"></a>
## 🇪🇸 Español

Una solución integral y unificada para la recolección, almacenamiento y visualización de métricas críticas de **Jenkins**, **SonarQube**, **Jira**, **ArgoCD** y mas . Este proyecto optimiza la infraestructura mediante el uso de contenedores compartidos para base de datos y visualización, facilitando el monitoreo de la salud del ciclo de vida de desarrollo de software (SDLC).

### 🚀 Características Principales

*   **Centralización Total**: Monitoreo de Jenkins, SonarQube, Jira, ArgoCD, Argo Rollouts y Git (DORA) en un solo ecosistema.
*   **Notificaciones Proativas**: Sistema de alertas autónomo que notifica fallos vía Slack/Discord.
*   **Infraestructura Eficiente**: Uso de una única instancia de PostgreSQL y Grafana para múltiples fuentes de datos.
*   **Inicialización Auto-Suficiente**: Scripts SQL automáticos que crean bases de datos, tablas y permisos al arrancar.
*   **Dashboards "Out-of-the-Box"**: Paneles de Grafana pre-configurados para visualización inmediata.
*   **Gestión de Retención**: Limpieza automática de datos antiguos (configurable en días) para mantener el rendimiento.
*   **Dual-Deployment**: Soporte nativo y optimizado tanto para **Docker Compose** como para **Kubernetes**.

---

### 🛠️ Tech Stack

*   **Backend**: Python 3.11 (Exporters personalizados).
*   **Database**: PostgreSQL 15 (Alpine based).
*   **Visualization**: Grafana 10.
*   **Orchestration**: Docker Compose & Kubernetes (Kustomize ready).

---

### 📂 Estructura del Proyecto

```text
.
├── Metrics_Collector-docker/         # Configuración para Docker Compose
│   ├── .env.example                  # Variables de entorno de referencia
│   ├── docker-compose.yml            # Orquestación de todos los servicios
│   ├── exporters/                    # Fuente de los recolectores (Python 3.11)
│   │   ├── argocd/                   # Recolector de Apps ArgoCD
│   │   ├── argorollouts/             # Recolector de Canary Rollouts
│   │   ├── git/                      # Recolector DORA (GitHub/GitLab)
│   │   ├── jenkins/                  # Recolector de Jobs y Builds
│   │   ├── jira/                     # Recolector de Tickets y Sprints
│   │   └── sonarqube/                # Recolector de Calidad de Código
│   ├── grafana/                      # Visualización y Provisioning
│   │   ├── dashboards/               # Definiciones JSON de dashboards
│   │   └── provisioning/             # Configuración automática de Grafana
│   └── postgres/                     # Persistencia de Datos
│       └── init/                     # Scripts SQL de inicialización (00-07)
├── Metrics_Collector-kubernetes/      # Manifiestos para K8s (Kustomize)
│   ├── base/                         # Infraestructura base (DB, Grafana)
│   └── [collector]/                  # Manifiestos por cada servicio
├── ARCHITECTURE.md                   # Diagramas y flujo de datos
└── README.md                         # Esta guía
```

---

### ⚙️ Instalación y Despliegue

#### 🐳 Docker Compose (Recomendado para inicio rápido)

1.  **Configura el entorno**:
    ```bash
    cd Metrics_Collector-docker
    cp .env.example .env
    ```
    *Edita el archivo `.env` con las URLs y Tokens de tus servidores Jenkins y SonarQube.*

2.  **Inicia los servicios**:
    ```bash
    docker-compose up -d --build
    ```

3.  **Acceso**:
    *   **Grafana**: `http://localhost:3000` (Usuario/Pass definidos en `.env`).
    *   **Dashboard Jira**: `http://localhost:3000/d/jira-overview`
    *   **Postgres**: Accesible internamente en el puerto `5432`.

#### ☸️ Kubernetes

1.  **Desplegar Infraestructura Base**:
    ```bash
    kubectl apply -f Metrics_Collector-kubernetes/base/
    ```

2.  **Configurar Secretos**:
    Completa los archivos en `Metrics_Collector-kubernetes/jenkins/secrets` y `Metrics_Collector-kubernetes/sonarqube/secrets`.

3.  **Desplegar Colectores**:
    ```bash
    # Desplegar Jenkins Collector
    kubectl apply -k Metrics_Collector-kubernetes/jenkins/
    
    # Desplegar SonarQube Collector
    kubectl apply -k Metrics_Collector-kubernetes/sonarqube/
    
    # Desplegar Jira Collector
    kubectl apply -k Metrics_Collector-kubernetes/jira/
    ```

---

### 🔧 Configuración Avanzada

#### Variables de Entorno Clave

| Variable | Descripción | Default |
| :--- | :--- | :--- |
| `JENKINS_POLL_INTERVAL` | Frecuencia de escaneo de Jenkins (segundos) | `60` |
| `SONARQUBE_POLL_INTERVAL`| Frecuencia de escaneo de SonarQube (segundos)| `3600` |
| `DATA_RETENTION_DAYS` | Días que se conservan las métricas históricas | `365` |
| `POSTGRES_DB` | Base de datos principal de configuración | `metrics_main` |

#### Monitoreo de Logs
Para verificar la salud de los colectores:
```bash
docker logs jenkins-metrics-collector -f
docker logs metrics-notifier -f
```

---

### 📜 Licencia

Este proyecto está bajo la licencia MIT. Consulta el archivo [LICENSE](LICENSE) para más detalles.

---
---

<a name="-português"></a>
## 🇧🇷 Português

Uma solução integral e unificada para coleta, armazenamento e visualização de métricas críticas de **Jenkins**, **SonarQube**, **Jira**, **ArgoCD** e mais. Este projeto otimiza a infraestrutura através do uso de contêineres compartilhados para banco de dados e visualização, facilitando o monitoramento da saúde do ciclo de vida de desenvolvimento de software (SDLC).

### 🚀 Principais Características

*   **Centralização Total**: Monitoramento de Jenkins, SonarQube, Jira, ArgoCD, Argo Rollouts e Git (DORA) em um único ecossistema.
*   **Notificações Proativas**: Sistema de alertas autônomo que notifica falhas via Slack/Discord.
*   **Infraestrutura Eficiente**: Uso de uma única instância de PostgreSQL e Grafana para múltiplas fontes de dados.
*   **Inicialização Autossuficiente**: Scripts SQL automáticos que criam bancos de dados, tabelas e permissões ao iniciar.
*   **Dashboards "Out-of-the-Box"**: Painéis do Grafana pré-configurados para visualização imediata.
*   **Gestão de Retenção**: Limpeza automática de dados antigos (configurável em dias) para manter o desempenho.
*   **Dual-Deployment**: Suporte nativo e otimizado tanto para **Docker Compose** quanto para **Kubernetes**.

---

### 🛠️ Tech Stack

*   **Backend**: Python 3.11 (Exporters personalizados).
*   **Database**: PostgreSQL 15 (Baseado em Alpine).
*   **Visualization**: Grafana 10.
*   **Orchestration**: Docker Compose & Kubernetes (Pronto para Kustomize).

---

### 📂 Estrutura do Projeto

```text
.
├── Metrics_Collector-docker/         # Configuração para Docker Compose
│   ├── .env.example                  # Variáveis de ambiente de referência
│   ├── docker-compose.yml            # Orquestração de todos os serviços
│   ├── exporters/                    # Código fonte dos coletores (Python 3.11)
│   │   ├── argocd/                   # Coletor de Apps ArgoCD
│   │   ├── argorollouts/             # Coletor de Canary Rollouts
│   │   ├── git/                      # Coletor DORA (GitHub/GitLab)
│   │   ├── jenkins/                  # Coletor de Jobs y Builds
│   │   ├── jira/                     # Coletor de Tickets e Sprints
│   │   └── sonarqube/                # Coletor de Qualidade de Código
│   ├── grafana/                      # Visualização e Provisionamento
│   │   ├── dashboards/               # Definições JSON de dashboards
│   │   └── provisioning/             # Configuração automática do Grafana
│   └── postgres/                     # Persistência de Dados
│       └── init/                     # Scripts SQL de inicialização (00-07)
├── Metrics_Collector-kubernetes/      # Manifestos para K8s (Kustomize)
│   ├── base/                         # Infraestrutura base (DB, Grafana)
│   └── [collector]/                  # Manifestos por cada serviço
├── ARCHITECTURE.md                   # Diagramas e fluxo de dados
└── README.md                         # Guia Multilíngue
```

---

### ⚙️ Instalação e Implantação

#### 🐳 Docker Compose (Recomendado para início rápido)

1.  **Configure o ambiente**:
    ```bash
    cd Metrics_Collector-docker
    cp .env.example .env
    ```
    *Edite o arquivo `.env` com as URLs e Tokens dos seus servidores Jenkins e SonarQube.*

2.  **Inicie os serviços**:
    ```bash
    docker-compose up -d --build
    ```

3.  **Acesso**:
    *   **Grafana**: `http://localhost:3000` (Usuário/Senha definidos no `.env`).
    *   **Dashboard Jira**: `http://localhost:3000/d/jira-overview`
    *   **Postgres**: Acessível internamente na porta `5432`.

#### ☸️ Kubernetes

1.  **Implantar Infraestrutura Base**:
    ```bash
    kubectl apply -f Metrics_Collector-kubernetes/base/
    ```

2.  **Configurar Segredos**:
    Preencha os arquivos em `Metrics_Collector-kubernetes/jenkins/secrets` e `Metrics_Collector-kubernetes/sonarqube/secrets`.

3.  **Implantar Coletores**:
    ```bash
    # Implantar Jenkins Collector
    kubectl apply -k Metrics_Collector-kubernetes/jenkins/
    
    # Implantar SonarQube Collector
    kubectl apply -k Metrics_Collector-kubernetes/sonarqube/
    
    # Implantar Jira Collector
    kubectl apply -k Metrics_Collector-kubernetes/jira/
    ```

---

### 🔧 Configuração Avançada

#### Variáveis de Ambiente Chave

| Variável | Descrição | Padrão |
| :--- | :--- | :--- |
| `JENKINS_POLL_INTERVAL` | Frequência de varredura do Jenkins (segundos) | `60` |
| `SONARQUBE_POLL_INTERVAL`| Frequência de varredura do SonarQube (segundos)| `3600` |
| `DATA_RETENTION_DAYS` | Dias que as métricas históricas são mantidas | `365` |
| `POSTGRES_DB` | Banco de dados principal de configuração | `metrics_main` |

#### Monitoramento de Logs
Para verificar a saúde dos coletores:
```bash
docker logs jenkins-metrics-collector -f
docker logs metrics-notifier -f
```

---

### 📜 Licença

Este projeto está sob a licença MIT. Consulte o arquivo [LICENSE](LICENSE) para mais detalhes.
