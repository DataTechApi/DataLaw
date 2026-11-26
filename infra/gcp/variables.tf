# ============================================================
#  DataLaw — Terraform · GCP · Variables
# ============================================================

variable "project_id" {
  description = "ID do projeto GCP onde os recursos serão criados."
  type        = string
}

variable "project" {
  description = "Nome base do projeto (usado em labels e nomes de recursos)."
  type        = string
  default     = "datalaw"
}

variable "environment" {
  description = "Ambiente de deploy (ex: dev, staging, prod)."
  type        = string
  default     = "prod"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "O environment deve ser 'dev', 'staging' ou 'prod'."
  }
}

variable "region" {
  description = "Região GCP para deploy dos recursos."
  type        = string
  default     = "southamerica-east1"
}

variable "zone" {
  description = "Zona GCP para as instâncias de Compute Engine."
  type        = string
  default     = "southamerica-east1-b"
}

# ─────────────────────────────────────────────
# VMs
# ─────────────────────────────────────────────
variable "vm_frontend_type" {
  description = "Tipo de máquina Compute Engine para o Frontend. Mínimo: e2-small. Recomendado: e2-medium."
  type        = string
  default     = "e2-medium"
}

variable "vm_backend_type" {
  description = "Tipo de máquina Compute Engine para o Backend Python. Mínimo: e2-small. Recomendado: e2-medium."
  type        = string
  default     = "e2-medium"
}

variable "vm_admin_user" {
  description = "Nome do usuário SSH nas VMs."
  type        = string
  default     = "datalaw"
}

variable "ssh_public_key" {
  description = "Chave SSH pública para acesso às VMs. Gere com: ssh-keygen -t ed25519 -C 'datalaw-deploy'"
  type        = string
  sensitive   = true
}

# ─────────────────────────────────────────────
# Cloud SQL PostgreSQL
# ─────────────────────────────────────────────
variable "db_tier" {
  description = "Tier do Cloud SQL. Mínimo: db-f1-micro. Recomendado: db-g1-small."
  type        = string
  default     = "db-g1-small"
}

variable "db_name" {
  description = "Nome do banco de dados PostgreSQL."
  type        = string
  default     = "datalaw_db"
}

variable "db_admin_user" {
  description = "Nome do usuário administrador do PostgreSQL."
  type        = string
  default     = "datalaw"
}

variable "db_admin_password" {
  description = "Senha do administrador do PostgreSQL."
  type        = string
  sensitive   = true

  validation {
    condition     = length(var.db_admin_password) >= 8
    error_message = "A senha do banco de dados deve ter pelo menos 8 caracteres."
  }
}

# ─────────────────────────────────────────────
# Aplicação
# ─────────────────────────────────────────────
variable "datajud_api_key" {
  description = "Chave de API do DataJud (CNJ) para o backend Python."
  type        = string
  sensitive   = true
}
