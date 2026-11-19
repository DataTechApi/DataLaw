# ============================================================
#  DataLaw — Terraform · AWS · Variables
# ============================================================

variable "region" {
  description = "Região AWS para deploy dos recursos."
  type        = string
  default     = "sa-east-1"
}

variable "project" {
  description = "Nome base do projeto (usado em tags e nomes de recursos)."
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

# ─────────────────────────────────────────────
# EC2
# ─────────────────────────────────────────────
variable "vm_frontend_type" {
  description = "Instance type EC2 para o Frontend. Mínimo: t3.small. Recomendado: t3.medium."
  type        = string
  default     = "t3.medium"
}

variable "vm_backend_type" {
  description = "Instance type EC2 para o Backend Python. Mínimo: t3.small. Recomendado: t3.medium."
  type        = string
  default     = "t3.medium"
}

variable "ssh_public_key" {
  description = "Chave SSH pública para acesso às instâncias EC2. Gere com: ssh-keygen -t ed25519 -C 'datalaw-deploy'"
  type        = string
  sensitive   = true
}

# ─────────────────────────────────────────────
# RDS PostgreSQL
# ─────────────────────────────────────────────
variable "db_instance_class" {
  description = "Classe da instância RDS. Mínimo: db.t3.micro. Recomendado: db.t3.small."
  type        = string
  default     = "db.t3.small"
}

variable "db_name" {
  description = "Nome do banco de dados PostgreSQL."
  type        = string
  default     = "datalaw_db"
}

variable "db_admin_user" {
  description = "Nome do usuário master do RDS PostgreSQL."
  type        = string
  default     = "datalaw"
}

variable "db_admin_password" {
  description = "Senha do usuário master do RDS PostgreSQL."
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
