# ============================================================
#  DataLaw — Terraform · AWS
#  Provisiona: VPC, Subnets, Security Groups, 2 EC2, RDS PostgreSQL
#  Região: sa-east-1 (São Paulo)
# ============================================================

terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "aws" {
  region = var.region
}

# ─────────────────────────────────────────────
# Data Sources
# ─────────────────────────────────────────────
data "aws_availability_zones" "available" {
  state = "available"
}

# ─────────────────────────────────────────────
# VPC
# ─────────────────────────────────────────────
resource "aws_vpc" "datalaw" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(local.tags, { Name = "${local.prefix}-vpc" })
}

# ─────────────────────────────────────────────
# Subnets
# ─────────────────────────────────────────────

# Subnets públicas (EC2)
resource "aws_subnet" "public_a" {
  vpc_id                  = aws_vpc.datalaw.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = false

  tags = merge(local.tags, { Name = "${local.prefix}-public-a" })
}

resource "aws_subnet" "public_b" {
  vpc_id                  = aws_vpc.datalaw.id
  cidr_block              = "10.0.2.0/24"
  availability_zone       = data.aws_availability_zones.available.names[1]
  map_public_ip_on_launch = false

  tags = merge(local.tags, { Name = "${local.prefix}-public-b" })
}

# Subnets privadas (RDS — requer ao menos 2 AZs)
resource "aws_subnet" "private_a" {
  vpc_id            = aws_vpc.datalaw.id
  cidr_block        = "10.0.10.0/24"
  availability_zone = data.aws_availability_zones.available.names[0]

  tags = merge(local.tags, { Name = "${local.prefix}-private-a" })
}

resource "aws_subnet" "private_b" {
  vpc_id            = aws_vpc.datalaw.id
  cidr_block        = "10.0.11.0/24"
  availability_zone = data.aws_availability_zones.available.names[1]

  tags = merge(local.tags, { Name = "${local.prefix}-private-b" })
}

# ─────────────────────────────────────────────
# Internet Gateway + Route Table
# ─────────────────────────────────────────────
resource "aws_internet_gateway" "datalaw" {
  vpc_id = aws_vpc.datalaw.id

  tags = merge(local.tags, { Name = "${local.prefix}-igw" })
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.datalaw.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.datalaw.id
  }

  tags = merge(local.tags, { Name = "${local.prefix}-public-rt" })
}

resource "aws_route_table_association" "public_a" {
  subnet_id      = aws_subnet.public_a.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "public_b" {
  subnet_id      = aws_subnet.public_b.id
  route_table_id = aws_route_table.public.id
}

# ─────────────────────────────────────────────
# Security Groups
# ─────────────────────────────────────────────

# SG — Frontend (Spring Boot)
resource "aws_security_group" "frontend" {
  name        = "${local.prefix}-frontend-sg"
  description = "DataLaw Frontend (Java Spring Boot)"
  vpc_id      = aws_vpc.datalaw.id

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Spring Boot"
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.tags, { Name = "${local.prefix}-frontend-sg" })
}

# SG — Backend (Python FastAPI)
resource "aws_security_group" "backend" {
  name        = "${local.prefix}-backend-sg"
  description = "DataLaw Backend (Python FastAPI + ETL)"
  vpc_id      = aws_vpc.datalaw.id

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "FastAPI (interno)"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.tags, { Name = "${local.prefix}-backend-sg" })
}

# SG — RDS PostgreSQL (acesso apenas das VMs)
resource "aws_security_group" "database" {
  name        = "${local.prefix}-database-sg"
  description = "DataLaw RDS PostgreSQL — acesso interno"
  vpc_id      = aws_vpc.datalaw.id

  ingress {
    description     = "PostgreSQL — do Frontend"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.frontend.id]
  }

  ingress {
    description     = "PostgreSQL — do Backend"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.backend.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.tags, { Name = "${local.prefix}-database-sg" })
}

# ─────────────────────────────────────────────
# Key Pair SSH
# ─────────────────────────────────────────────
resource "aws_key_pair" "datalaw" {
  key_name   = "${local.prefix}-key"
  public_key = var.ssh_public_key

  tags = local.tags
}

# ─────────────────────────────────────────────
# EC2 — Frontend (Java Spring Boot)
# ─────────────────────────────────────────────

# AMI mais recente do Ubuntu 22.04 LTS
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_instance" "frontend" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.vm_frontend_type
  key_name               = aws_key_pair.datalaw.key_name
  subnet_id              = aws_subnet.public_a.id
  vpc_security_group_ids = [aws_security_group.frontend.id]

  root_block_device {
    volume_type           = "gp3"
    volume_size           = 30
    delete_on_termination = true
    encrypted             = true
  }

  user_data = base64encode(<<-EOF
    #!/bin/bash
    set -e
    export DEBIAN_FRONTEND=noninteractive

    apt-get update -y
    apt-get install -y openjdk-21-jre-headless curl

    mkdir -p /home/ubuntu/frontend
    chown ubuntu:ubuntu /home/ubuntu/frontend

    cat <<ENV > /etc/datalaw-frontend.env
    SERVER_PORT=8080
    SPRING_DATASOURCE_URL=jdbc:postgresql://${aws_db_instance.datalaw.address}:5432/${var.db_name}
    SPRING_DATASOURCE_USERNAME=${var.db_admin_user}
    SPRING_DATASOURCE_PASSWORD=${var.db_admin_password}
    ENV

    cat <<SERVICE > /etc/systemd/system/datalaw.service
    [Unit]
    Description=DataLaw Java Application (Spring Boot)
    After=network.target

    [Service]
    User=ubuntu
    EnvironmentFile=/etc/datalaw-frontend.env
    ExecStart=/usr/bin/java -jar /home/ubuntu/frontend/datalaw.jar
    SuccessExitStatus=143
    Restart=on-failure
    RestartSec=10

    [Install]
    WantedBy=multi-user.target
    SERVICE

    systemctl daemon-reload
    systemctl enable datalaw.service
    echo "Frontend EC2 provisionada com sucesso" > /tmp/setup-done
  EOF
  )

  tags = merge(local.tags, { Name = "${local.prefix}-frontend" })

  depends_on = [aws_db_instance.datalaw]
}

resource "aws_eip" "frontend" {
  instance = aws_instance.frontend.id
  domain   = "vpc"

  tags = merge(local.tags, { Name = "${local.prefix}-frontend-eip" })
}

# ─────────────────────────────────────────────
# EC2 — Backend (Python FastAPI + ETL)
# ─────────────────────────────────────────────
resource "aws_instance" "backend" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.vm_backend_type
  key_name               = aws_key_pair.datalaw.key_name
  subnet_id              = aws_subnet.public_b.id
  vpc_security_group_ids = [aws_security_group.backend.id]

  root_block_device {
    volume_type           = "gp3"
    volume_size           = 30
    delete_on_termination = true
    encrypted             = true
  }

  user_data = base64encode(<<-EOF
    #!/bin/bash
    set -e
    export DEBIAN_FRONTEND=noninteractive

    apt-get update -y
    apt-get install -y curl build-essential git python3.12 python3.12-venv

    # Instala uv
    curl -LsSf https://astral.sh/uv/install.sh | bash

    mkdir -p /home/ubuntu/backend
    chown ubuntu:ubuntu /home/ubuntu/backend

    cat <<ENV > /etc/datalaw-backend.env
    DATABASE_URL=postgresql+psycopg://${var.db_admin_user}:${var.db_admin_password}@${aws_db_instance.datalaw.address}:5432/${var.db_name}
    DATAJUD_API_KEY=${var.datajud_api_key}
    LOG_LEVEL=INFO
    ENV

    cat <<SERVICE > /etc/systemd/system/datalaw-backend.service
    [Unit]
    Description=DataLaw Python Backend (FastAPI + ETL)
    After=network.target

    [Service]
    User=ubuntu
    WorkingDirectory=/home/ubuntu/backend
    EnvironmentFile=/etc/datalaw-backend.env
    ExecStart=/home/ubuntu/backend/start.sh
    Restart=on-failure
    RestartSec=10

    [Install]
    WantedBy=multi-user.target
    SERVICE

    systemctl daemon-reload
    systemctl enable datalaw-backend.service
    echo "Backend EC2 provisionada com sucesso" > /tmp/setup-done
  EOF
  )

  tags = merge(local.tags, { Name = "${local.prefix}-backend" })

  depends_on = [aws_db_instance.datalaw]
}

resource "aws_eip" "backend" {
  instance = aws_instance.backend.id
  domain   = "vpc"

  tags = merge(local.tags, { Name = "${local.prefix}-backend-eip" })
}

# ─────────────────────────────────────────────
# RDS — PostgreSQL
# ─────────────────────────────────────────────
resource "aws_db_subnet_group" "datalaw" {
  name       = "${local.prefix}-db-subnet-group"
  subnet_ids = [aws_subnet.private_a.id, aws_subnet.private_b.id]

  tags = merge(local.tags, { Name = "${local.prefix}-db-subnet-group" })
}

resource "aws_db_instance" "datalaw" {
  identifier = "${local.prefix}-postgres"

  engine               = "postgres"
  engine_version       = "16"
  instance_class       = var.db_instance_class
  allocated_storage    = 20
  max_allocated_storage = 100
  storage_type         = "gp3"
  storage_encrypted    = true

  db_name  = var.db_name
  username = var.db_admin_user
  password = var.db_admin_password
  port     = 5432

  db_subnet_group_name   = aws_db_subnet_group.datalaw.name
  vpc_security_group_ids = [aws_security_group.database.id]
  publicly_accessible    = false

  backup_retention_period = 7
  backup_window           = "03:00-04:00"
  maintenance_window      = "sun:04:00-sun:05:00"

  deletion_protection = false
  skip_final_snapshot = true

  tags = merge(local.tags, { Name = "${local.prefix}-rds-postgres" })
}

# ─────────────────────────────────────────────
# Locals
# ─────────────────────────────────────────────
locals {
  prefix = "${var.project}-${var.environment}"

  tags = {
    Project     = var.project
    Environment = var.environment
    ManagedBy   = "terraform"
    Team        = "datatech"
  }
}
