# ============================================================
#  DataLaw — Terraform · Azure
#  Provisiona: VNet, NSG, 2 VMs Linux, PostgreSQL Flexible Server
#  Região: brazilsouth
# ============================================================

terraform {
  required_version = ">= 1.6.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }
}

provider "azurerm" {
  features {
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
  }
  subscription_id = var.subscription_id
}

# ─────────────────────────────────────────────
# Resource Group
# ─────────────────────────────────────────────
resource "azurerm_resource_group" "datalaw" {
  name     = "${var.project}-${var.environment}-rg"
  location = var.location

  tags = local.tags
}

# ─────────────────────────────────────────────
# Virtual Network + Subnets
# ─────────────────────────────────────────────
resource "azurerm_virtual_network" "datalaw" {
  name                = "${var.project}-${var.environment}-vnet"
  location            = azurerm_resource_group.datalaw.location
  resource_group_name = azurerm_resource_group.datalaw.name
  address_space       = ["10.0.0.0/16"]

  tags = local.tags
}

resource "azurerm_subnet" "public" {
  name                 = "public-subnet"
  resource_group_name  = azurerm_resource_group.datalaw.name
  virtual_network_name = azurerm_virtual_network.datalaw.name
  address_prefixes     = ["10.0.1.0/24"]
}

resource "azurerm_subnet" "database" {
  name                 = "database-subnet"
  resource_group_name  = azurerm_resource_group.datalaw.name
  virtual_network_name = azurerm_virtual_network.datalaw.name
  address_prefixes     = ["10.0.2.0/24"]

  delegation {
    name = "fs"
    service_delegation {
      name = "Microsoft.DBforPostgreSQL/flexibleServers"
      actions = [
        "Microsoft.Network/virtualNetworks/subnets/join/action",
      ]
    }
  }
}

# ─────────────────────────────────────────────
# Network Security Groups
# ─────────────────────────────────────────────

# NSG — Frontend (Spring Boot)
resource "azurerm_network_security_group" "frontend" {
  name                = "${var.project}-${var.environment}-frontend-nsg"
  location            = azurerm_resource_group.datalaw.location
  resource_group_name = azurerm_resource_group.datalaw.name

  security_rule {
    name                       = "allow-ssh"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "22"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "allow-http"
    priority                   = 110
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "80"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "allow-spring-boot"
    priority                   = 120
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "8080"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  tags = local.tags
}

# NSG — Backend (Python FastAPI)
resource "azurerm_network_security_group" "backend" {
  name                = "${var.project}-${var.environment}-backend-nsg"
  location            = azurerm_resource_group.datalaw.location
  resource_group_name = azurerm_resource_group.datalaw.name

  security_rule {
    name                       = "allow-ssh"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "22"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "allow-fastapi"
    priority                   = 110
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "8000"
    source_address_prefix      = "10.0.0.0/16"
    destination_address_prefix = "*"
  }

  tags = local.tags
}

# ─────────────────────────────────────────────
# Public IPs
# ─────────────────────────────────────────────
resource "azurerm_public_ip" "frontend" {
  name                = "${var.project}-${var.environment}-frontend-pip"
  location            = azurerm_resource_group.datalaw.location
  resource_group_name = azurerm_resource_group.datalaw.name
  allocation_method   = "Static"
  sku                 = "Standard"

  tags = local.tags
}

resource "azurerm_public_ip" "backend" {
  name                = "${var.project}-${var.environment}-backend-pip"
  location            = azurerm_resource_group.datalaw.location
  resource_group_name = azurerm_resource_group.datalaw.name
  allocation_method   = "Static"
  sku                 = "Standard"

  tags = local.tags
}

# ─────────────────────────────────────────────
# Network Interfaces
# ─────────────────────────────────────────────
resource "azurerm_network_interface" "frontend" {
  name                = "${var.project}-${var.environment}-frontend-nic"
  location            = azurerm_resource_group.datalaw.location
  resource_group_name = azurerm_resource_group.datalaw.name

  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.public.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.frontend.id
  }

  tags = local.tags
}

resource "azurerm_network_interface" "backend" {
  name                = "${var.project}-${var.environment}-backend-nic"
  location            = azurerm_resource_group.datalaw.location
  resource_group_name = azurerm_resource_group.datalaw.name

  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.public.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.backend.id
  }

  tags = local.tags
}

# Associações NIC ↔ NSG
resource "azurerm_network_interface_security_group_association" "frontend" {
  network_interface_id      = azurerm_network_interface.frontend.id
  network_security_group_id = azurerm_network_security_group.frontend.id
}

resource "azurerm_network_interface_security_group_association" "backend" {
  network_interface_id      = azurerm_network_interface.backend.id
  network_security_group_id = azurerm_network_security_group.backend.id
}

# ─────────────────────────────────────────────
# VM — Frontend (Java Spring Boot)
# ─────────────────────────────────────────────
resource "azurerm_linux_virtual_machine" "frontend" {
  name                = "${var.project}-${var.environment}-frontend-vm"
  location            = azurerm_resource_group.datalaw.location
  resource_group_name = azurerm_resource_group.datalaw.name
  size                = var.vm_frontend_size
  admin_username      = var.vm_admin_user

  network_interface_ids = [
    azurerm_network_interface.frontend.id,
  ]

  admin_ssh_key {
    username   = var.vm_admin_user
    public_key = var.ssh_public_key
  }

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
    disk_size_gb         = 64
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-jammy"
    sku       = "22_04-lts-gen2"
    version   = "latest"
  }

  # Script de inicialização: instala Java 21 e configura o serviço systemd
  custom_data = base64encode(<<-EOF
    #!/bin/bash
    set -e
    export DEBIAN_FRONTEND=noninteractive

    apt-get update -y
    apt-get install -y openjdk-21-jre-headless curl

    # Cria diretório da aplicação
    mkdir -p /home/${var.vm_admin_user}/frontend
    chown ${var.vm_admin_user}:${var.vm_admin_user} /home/${var.vm_admin_user}/frontend

    # Cria variáveis de ambiente para a aplicação
    cat <<ENV > /etc/datalaw-frontend.env
    SERVER_PORT=8080
    SPRING_DATASOURCE_URL=jdbc:postgresql://${azurerm_postgresql_flexible_server.datalaw.fqdn}:5432/${var.db_name}
    SPRING_DATASOURCE_USERNAME=${var.db_admin_user}
    SPRING_DATASOURCE_PASSWORD=${var.db_admin_password}
    ENV

    # Cria o serviço systemd (o JAR será copiado pelo CI/CD)
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
  )

  tags = local.tags
}

# ─────────────────────────────────────────────
# VM — Backend (Python FastAPI + ETL)
# ─────────────────────────────────────────────
resource "azurerm_linux_virtual_machine" "backend" {
  name                = "${var.project}-${var.environment}-backend-vm"
  location            = azurerm_resource_group.datalaw.location
  resource_group_name = azurerm_resource_group.datalaw.name
  size                = var.vm_backend_size
  admin_username      = var.vm_admin_user

  network_interface_ids = [
    azurerm_network_interface.backend.id,
  ]

  admin_ssh_key {
    username   = var.vm_admin_user
    public_key = var.ssh_public_key
  }

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
    disk_size_gb         = 64
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-jammy"
    sku       = "22_04-lts-gen2"
    version   = "latest"
  }

  # Script de inicialização: instala Python 3.12 + uv e configura o serviço systemd
  custom_data = base64encode(<<-EOF
    #!/bin/bash
    set -e
    export DEBIAN_FRONTEND=noninteractive

    apt-get update -y
    apt-get install -y curl build-essential git python3.12 python3.12-venv

    # Instala uv (gerenciador de pacotes Python)
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"

    # Cria diretório da aplicação
    mkdir -p /home/${var.vm_admin_user}/backend
    chown ${var.vm_admin_user}:${var.vm_admin_user} /home/${var.vm_admin_user}/backend

    # Cria arquivo de variáveis de ambiente
    cat <<ENV > /etc/datalaw-backend.env
    DATABASE_URL=postgresql+psycopg://${var.db_admin_user}:${var.db_admin_password}@${azurerm_postgresql_flexible_server.datalaw.fqdn}:5432/${var.db_name}
    DATAJUD_API_KEY=${var.datajud_api_key}
    LOG_LEVEL=INFO
    ENV

    # Cria o serviço systemd (os arquivos serão copiados pelo CI/CD)
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
  )

  tags = local.tags
}

# ─────────────────────────────────────────────
# DNS Private Zone para PostgreSQL
# ─────────────────────────────────────────────
resource "azurerm_private_dns_zone" "postgres" {
  name                = "${var.project}.postgres.database.azure.com"
  resource_group_name = azurerm_resource_group.datalaw.name

  tags = local.tags
}

resource "azurerm_private_dns_zone_virtual_network_link" "postgres" {
  name                  = "${var.project}-${var.environment}-dns-link"
  private_dns_zone_name = azurerm_private_dns_zone.postgres.name
  resource_group_name   = azurerm_resource_group.datalaw.name
  virtual_network_id    = azurerm_virtual_network.datalaw.id

  tags = local.tags
}

# ─────────────────────────────────────────────
# Azure Database for PostgreSQL Flexible Server
# ─────────────────────────────────────────────
resource "azurerm_postgresql_flexible_server" "datalaw" {
  name                          = "${var.project}-${var.environment}-pgserver"
  resource_group_name           = azurerm_resource_group.datalaw.name
  location                      = azurerm_resource_group.datalaw.location
  version                       = "16"
  delegated_subnet_id           = azurerm_subnet.database.id
  private_dns_zone_id           = azurerm_private_dns_zone.postgres.id
  public_network_access_enabled = false

  administrator_login    = var.db_admin_user
  administrator_password = var.db_admin_password

  sku_name   = var.db_sku
  storage_mb = 32768 # 32 GB

  backup_retention_days        = 7
  geo_redundant_backup_enabled = false

  depends_on = [azurerm_private_dns_zone_virtual_network_link.postgres]

  tags = local.tags
}

resource "azurerm_postgresql_flexible_server_database" "datalaw" {
  name      = var.db_name
  server_id = azurerm_postgresql_flexible_server.datalaw.id
  collation = "en_US.utf8"
  charset   = "utf8"
}

# ─────────────────────────────────────────────
# Locals
# ─────────────────────────────────────────────
locals {
  tags = {
    project     = var.project
    environment = var.environment
    managed_by  = "terraform"
    team        = "datatech"
  }
}
