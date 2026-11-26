# ============================================================
#  DataLaw — Terraform · AWS · Outputs
# ============================================================

output "frontend_public_ip" {
  description = "IP público (Elastic IP) da instância EC2 do Frontend (Spring Boot)."
  value       = aws_eip.frontend.public_ip
}

output "backend_public_ip" {
  description = "IP público (Elastic IP) da instância EC2 do Backend (Python)."
  value       = aws_eip.backend.public_ip
}

output "rds_endpoint" {
  description = "Endpoint do RDS PostgreSQL (host:porta — acesso interno via VPC)."
  value       = "${aws_db_instance.datalaw.address}:${aws_db_instance.datalaw.port}"
}

output "rds_address" {
  description = "Hostname do RDS PostgreSQL."
  value       = aws_db_instance.datalaw.address
}

output "postgres_connection_string_backend" {
  description = "String de conexão psycopg para o backend Python."
  value       = "postgresql+psycopg://${var.db_admin_user}:***@${aws_db_instance.datalaw.address}:5432/${var.db_name}"
}

output "postgres_connection_string_frontend" {
  description = "String de conexão JDBC para o frontend Java (Spring Boot)."
  value       = "jdbc:postgresql://${aws_db_instance.datalaw.address}:5432/${var.db_name}"
}

output "frontend_instance_id" {
  description = "ID da instância EC2 do Frontend."
  value       = aws_instance.frontend.id
}

output "backend_instance_id" {
  description = "ID da instância EC2 do Backend."
  value       = aws_instance.backend.id
}

output "rds_instance_id" {
  description = "Identifier da instância RDS."
  value       = aws_db_instance.datalaw.identifier
}

output "vpc_id" {
  description = "ID da VPC criada."
  value       = aws_vpc.datalaw.id
}

output "github_actions_secrets" {
  description = "Valores a configurar como GitHub Actions secrets (adapte os nomes conforme necessário)."
  value = {
    AWS_FRONTEND_VM_HOST = aws_eip.frontend.public_ip
    AWS_FRONTEND_VM_USER = "ubuntu"
    AWS_VM_HOST          = aws_eip.backend.public_ip
    AWS_VM_USER          = "ubuntu"
  }
}
