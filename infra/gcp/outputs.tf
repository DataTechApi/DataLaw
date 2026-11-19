# ============================================================
#  DataLaw — Terraform · GCP · Outputs
# ============================================================

output "frontend_public_ip" {
  description = "IP público estático da VM do Frontend (Spring Boot)."
  value       = google_compute_address.frontend.address
}

output "backend_public_ip" {
  description = "IP público estático da VM do Backend (Python)."
  value       = google_compute_address.backend.address
}

output "postgres_private_ip" {
  description = "IP privado do Cloud SQL (acesso interno via VPC)."
  value       = google_sql_database_instance.datalaw.private_ip_address
}

output "postgres_connection_string_backend" {
  description = "String de conexão psycopg para o backend Python."
  value       = "postgresql+psycopg://${var.db_admin_user}:***@${google_sql_database_instance.datalaw.private_ip_address}:5432/${var.db_name}"
}

output "postgres_connection_string_frontend" {
  description = "String de conexão JDBC para o frontend Java (Spring Boot)."
  value       = "jdbc:postgresql://${google_sql_database_instance.datalaw.private_ip_address}:5432/${var.db_name}"
}

output "frontend_vm_name" {
  description = "Nome da instância Compute Engine do Frontend."
  value       = google_compute_instance.frontend.name
}

output "backend_vm_name" {
  description = "Nome da instância Compute Engine do Backend."
  value       = google_compute_instance.backend.name
}

output "cloud_sql_instance_name" {
  description = "Nome da instância Cloud SQL."
  value       = google_sql_database_instance.datalaw.name
}

output "service_account_email" {
  description = "E-mail da Service Account criada para as VMs."
  value       = google_service_account.datalaw_vm.email
}

output "github_actions_secrets" {
  description = "Valores a configurar como GitHub Actions secrets (adapte os nomes conforme necessário)."
  value = {
    GCP_FRONTEND_VM_HOST = google_compute_address.frontend.address
    GCP_FRONTEND_VM_USER = var.vm_admin_user
    GCP_VM_HOST          = google_compute_address.backend.address
    GCP_VM_USER          = var.vm_admin_user
  }
}
