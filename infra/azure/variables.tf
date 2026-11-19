# ============================================================
#  DataLaw — Terraform · Azure · Variables
# ============================================================

variable "subscription_id" {
  description = "ID da subscription Azure onde os recursos serão criados."
  type        = string
}

variable "project" {
  description = "Nome base do projeto (usado em nomes de recursos)."
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

variable "location" {
  description = "Região Azure para deploy dos recursos."
  type        = string
  default     = "brazilsouth"
}

# ─────────────────────────────────────────────
# VMs
# ─────────────────────────────────────────────
variable "vm_frontend_size" {
  description = "Tamanho da VM do Frontend (Spring Boot). Mínimo: Standard_B1ms. Recomendado: Standard_B2s."
  type        = string
  default     = "Standard_B2s"
}

variable "vm_backend_size" {
  description = "Tamanho da VM do Backend (Python FastAPI). Mínimo: Standard_B1ms. Recomendado: Standard_B2s."
  type        = string
  default     = "Standard_B2s"
}

variable "vm_admin_user" {
  description = "Nome do usuário administrador das VMs."
  type        = string
  default     = "azureuser"
}

variable "ssh_public_key" {
  description = "Chave SSH pública para acesso às VMs. Gere com: ssh-keygen -t ed25519 -C 'datalaw-deploy'"
  type        = string
  sensitive   = true
}

# ─────────────────────────────────────────────
# PostgreSQL
# ─────────────────────────────────────────────
variable "db_sku" {
  description = "SKU do PostgreSQL Flexible Server. Mínimo: B_Standard_B1ms. Recomendado: B_Standard_B2ms."
  type        = string
  default     = "B_Standard_B2ms"
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
  description = "Senha do administrador do PostgreSQL. Mínimo 8 caracteres, letras maiúsculas, minúsculas e números."
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
