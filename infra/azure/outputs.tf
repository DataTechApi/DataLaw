# ============================================================
#  DataLaw — Terraform · Azure · Outputs
# ============================================================

output "frontend_public_ip" {
  description = "IP público da VM do Frontend (Spring Boot). Use para configurar o DNS e o secret AZURE_FRONTEND_VM_HOST no GitHub Actions."
  value       = azurerm_public_ip.frontend.ip_address
}

output "backend_public_ip" {
  description = "IP público da VM do Backend (Python). Use para configurar o secret AZURE_VM_HOST no GitHub Actions."
  value       = azurerm_public_ip.backend.ip_address
}

output "postgres_fqdn" {
  description = "FQDN do servidor PostgreSQL (acesso interno via VNet)."
  value       = azurerm_postgresql_flexible_server.datalaw.fqdn
}

output "postgres_connection_string_backend" {
  description = "String de conexão completa para o backend Python (psycopg)."
  value       = "postgresql+psycopg://${var.db_admin_user}:***@${azurerm_postgresql_flexible_server.datalaw.fqdn}:5432/${var.db_name}"
  sensitive   = false
}

output "postgres_connection_string_frontend" {
  description = "String de conexão JDBC para o frontend Java (Spring Boot)."
  value       = "jdbc:postgresql://${azurerm_postgresql_flexible_server.datalaw.fqdn}:5432/${var.db_name}"
}

output "resource_group_name" {
  description = "Nome do Resource Group criado."
  value       = azurerm_resource_group.datalaw.name
}

output "vnet_name" {
  description = "Nome da Virtual Network criada."
  value       = azurerm_virtual_network.datalaw.name
}

output "frontend_vm_name" {
  description = "Nome da VM do Frontend no Azure."
  value       = azurerm_linux_virtual_machine.frontend.name
}

output "backend_vm_name" {
  description = "Nome da VM do Backend no Azure."
  value       = azurerm_linux_virtual_machine.backend.name
}

output "github_actions_secrets" {
  description = "Valores a configurar como GitHub Actions secrets para o deploy.yml."
  value = {
    AZURE_FRONTEND_VM_HOST = azurerm_public_ip.frontend.ip_address
    AZURE_FRONTEND_VM_USER = var.vm_admin_user
    AZURE_VM_HOST          = azurerm_public_ip.backend.ip_address
    AZURE_VM_USER          = var.vm_admin_user
  }
}
