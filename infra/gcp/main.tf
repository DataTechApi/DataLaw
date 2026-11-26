# ============================================================
#  DataLaw — Terraform · GCP
#  Provisiona: VPC, Firewalls, 2 VMs Linux, Cloud SQL PostgreSQL
#  Região: southamerica-east1 (São Paulo)
# ============================================================

terraform {
  required_version = ">= 1.6.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 6.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

# ─────────────────────────────────────────────
# Sufixo aleatório para nomes únicos
# ─────────────────────────────────────────────
resource "random_id" "suffix" {
  byte_length = 4
}

# ─────────────────────────────────────────────
# VPC Network
# ─────────────────────────────────────────────
resource "google_compute_network" "datalaw" {
  name                    = "${var.project}-${var.environment}-vpc"
  auto_create_subnetworks = false
  routing_mode            = "REGIONAL"
}

resource "google_compute_subnetwork" "public" {
  name          = "${var.project}-${var.environment}-public-subnet"
  ip_cidr_range = "10.0.1.0/24"
  region        = var.region
  network       = google_compute_network.datalaw.id

  private_ip_google_access = true
}

# ─────────────────────────────────────────────
# Firewall Rules
# ─────────────────────────────────────────────

# Permite SSH de qualquer origem
resource "google_compute_firewall" "allow_ssh" {
  name    = "${var.project}-${var.environment}-allow-ssh"
  network = google_compute_network.datalaw.name

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["datalaw-vm"]
}

# Permite HTTP/8080 para o frontend
resource "google_compute_firewall" "allow_frontend" {
  name    = "${var.project}-${var.environment}-allow-frontend"
  network = google_compute_network.datalaw.name

  allow {
    protocol = "tcp"
    ports    = ["80", "443", "8080"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["datalaw-frontend"]
}

# Permite porta 8000 (FastAPI) somente de dentro da VPC
resource "google_compute_firewall" "allow_backend_internal" {
  name    = "${var.project}-${var.environment}-allow-backend-internal"
  network = google_compute_network.datalaw.name

  allow {
    protocol = "tcp"
    ports    = ["8000"]
  }

  source_ranges = ["10.0.0.0/8"]
  target_tags   = ["datalaw-backend"]
}

# Permite Health Check do GCP Load Balancer (opcional, mas recomendado)
resource "google_compute_firewall" "allow_health_check" {
  name    = "${var.project}-${var.environment}-allow-health-check"
  network = google_compute_network.datalaw.name

  allow {
    protocol = "tcp"
  }

  source_ranges = ["130.211.0.0/22", "35.191.0.0/16"]
  target_tags   = ["datalaw-vm"]
}

# ─────────────────────────────────────────────
# Static External IPs
# ─────────────────────────────────────────────
resource "google_compute_address" "frontend" {
  name   = "${var.project}-${var.environment}-frontend-ip"
  region = var.region
}

resource "google_compute_address" "backend" {
  name   = "${var.project}-${var.environment}-backend-ip"
  region = var.region
}

# ─────────────────────────────────────────────
# VM — Frontend (Java Spring Boot)
# ─────────────────────────────────────────────
resource "google_compute_instance" "frontend" {
  name         = "${var.project}-${var.environment}-frontend"
  machine_type = var.vm_frontend_type
  zone         = var.zone

  tags = ["datalaw-vm", "datalaw-frontend"]

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2204-lts"
      size  = 50
      type  = "pd-balanced"
    }
  }

  network_interface {
    network    = google_compute_network.datalaw.id
    subnetwork = google_compute_subnetwork.public.id

    access_config {
      nat_ip = google_compute_address.frontend.address
    }
  }

  metadata = {
    ssh-keys = "${var.vm_admin_user}:${var.ssh_public_key}"
  }

  # Script de inicialização: instala Java 21 e configura systemd
  metadata_startup_script = <<-EOF
    #!/bin/bash
    set -e
    export DEBIAN_FRONTEND=noninteractive

    apt-get update -y
    apt-get install -y openjdk-21-jre-headless curl

    mkdir -p /home/${var.vm_admin_user}/frontend
    chown ${var.vm_admin_user}:${var.vm_admin_user} /home/${var.vm_admin_user}/frontend

    cat <<ENV > /etc/datalaw-frontend.env
    SERVER_PORT=8080
    SPRING_DATASOURCE_URL=jdbc:postgresql://${google_sql_database_instance.datalaw.private_ip_address}:5432/${var.db_name}
    SPRING_DATASOURCE_USERNAME=${var.db_admin_user}
    SPRING_DATASOURCE_PASSWORD=${var.db_admin_password}
    ENV

    cat <<SERVICE > /etc/systemd/system/datalaw.service
    [Unit]
    Description=DataLaw Java Application (Spring Boot)
    After=network.target

    [Service]
    User=${var.vm_admin_user}
    EnvironmentFile=/etc/datalaw-frontend.env
    ExecStart=/usr/bin/java -jar /home/${var.vm_admin_user}/frontend/datalaw.jar
    SuccessExitStatus=143
    Restart=on-failure
    RestartSec=10

    [Install]
    WantedBy=multi-user.target
    SERVICE

    systemctl daemon-reload
    systemctl enable datalaw.service
    echo "Frontend VM provisionada com sucesso" > /tmp/setup-done
  EOF

  service_account {
    email  = google_service_account.datalaw_vm.email
    scopes = ["cloud-platform"]
  }

  labels = local.labels

  depends_on = [google_sql_database_instance.datalaw]
}

# ─────────────────────────────────────────────
# VM — Backend (Python FastAPI + ETL)
# ─────────────────────────────────────────────
resource "google_compute_instance" "backend" {
  name         = "${var.project}-${var.environment}-backend"
  machine_type = var.vm_backend_type
  zone         = var.zone

  tags = ["datalaw-vm", "datalaw-backend"]

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2204-lts"
      size  = 50
      type  = "pd-balanced"
    }
  }

  network_interface {
    network    = google_compute_network.datalaw.id
    subnetwork = google_compute_subnetwork.public.id

    access_config {
      nat_ip = google_compute_address.backend.address
    }
  }

  metadata = {
    ssh-keys = "${var.vm_admin_user}:${var.ssh_public_key}"
  }

  # Script de inicialização: instala Python 3.12 + uv
  metadata_startup_script = <<-EOF
    #!/bin/bash
    set -e
    export DEBIAN_FRONTEND=noninteractive

    apt-get update -y
    apt-get install -y curl build-essential git python3.12 python3.12-venv

    # Instala uv
    curl -LsSf https://astral.sh/uv/install.sh | bash

    mkdir -p /home/${var.vm_admin_user}/backend
    chown ${var.vm_admin_user}:${var.vm_admin_user} /home/${var.vm_admin_user}/backend

    cat <<ENV > /etc/datalaw-backend.env
    DATABASE_URL=postgresql+psycopg://${var.db_admin_user}:${var.db_admin_password}@${google_sql_database_instance.datalaw.private_ip_address}:5432/${var.db_name}
    DATAJUD_API_KEY=${var.datajud_api_key}
    LOG_LEVEL=INFO
    ENV

    cat <<SERVICE > /etc/systemd/system/datalaw-backend.service
    [Unit]
    Description=DataLaw Python Backend (FastAPI + ETL)
    After=network.target

    [Service]
    User=${var.vm_admin_user}
    WorkingDirectory=/home/${var.vm_admin_user}/backend
    EnvironmentFile=/etc/datalaw-backend.env
    ExecStart=/home/${var.vm_admin_user}/backend/start.sh
    Restart=on-failure
    RestartSec=10

    [Install]
    WantedBy=multi-user.target
    SERVICE

    systemctl daemon-reload
    systemctl enable datalaw-backend.service
    echo "Backend VM provisionada com sucesso" > /tmp/setup-done
  EOF

  service_account {
    email  = google_service_account.datalaw_vm.email
    scopes = ["cloud-platform"]
  }

  labels = local.labels

  depends_on = [google_sql_database_instance.datalaw]
}

# ─────────────────────────────────────────────
# Service Account para as VMs
# ─────────────────────────────────────────────
resource "google_service_account" "datalaw_vm" {
  account_id   = "${var.project}-${var.environment}-sa"
  display_name = "DataLaw VM Service Account"
}

# ─────────────────────────────────────────────
# Cloud SQL — PostgreSQL
# ─────────────────────────────────────────────

# Allocate IP range for private service access
resource "google_compute_global_address" "private_ip_alloc" {
  name          = "${var.project}-${var.environment}-sql-ip-range"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.datalaw.id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.datalaw.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_alloc.name]
}

resource "google_sql_database_instance" "datalaw" {
  name             = "${var.project}-${var.environment}-postgres-${random_id.suffix.hex}"
  database_version = "POSTGRES_16"
  region           = var.region

  deletion_protection = false

  settings {
    tier              = var.db_tier
    availability_type = "ZONAL"
    disk_size         = 20
    disk_type         = "PD_SSD"
    disk_autoresize   = true

    backup_configuration {
      enabled                        = true
      start_time                     = "03:00"
      point_in_time_recovery_enabled = false
      transaction_log_retention_days = 7
      backup_retention_settings {
        retained_backups = 7
      }
    }

    ip_configuration {
      ipv4_enabled                                  = false
      private_network                               = google_compute_network.datalaw.id
      enable_private_path_for_google_cloud_services = true
    }

    maintenance_window {
      day          = 7 # Domingo
      hour         = 2
      update_track = "stable"
    }

    database_flags {
      name  = "log_min_duration_statement"
      value = "1000"
    }
  }

  depends_on = [google_service_networking_connection.private_vpc_connection]
}

resource "google_sql_database" "datalaw" {
  name     = var.db_name
  instance = google_sql_database_instance.datalaw.name
}

resource "google_sql_user" "datalaw" {
  name     = var.db_admin_user
  instance = google_sql_database_instance.datalaw.name
  password = var.db_admin_password
}

# ─────────────────────────────────────────────
# Locals
# ─────────────────────────────────────────────
locals {
  labels = {
    project     = var.project
    environment = var.environment
    managed_by  = "terraform"
    team        = "datatech"
  }
}
