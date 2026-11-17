<#
.SYNOPSIS
    Guia para rodar o DataLaw localmente e ingerir mais dados.

.DESCRIPTION
    Sem parâmetros, abre um menu interativo. Com -Acao, executa uma etapa direto.
    O script sempre usa o PostgreSQL local do Docker Compose: ele sobrescreve
    DATABASE_URL nesta sessão para nunca gravar em um banco compartilhado.

.EXAMPLE
    .\scripts\datalaw-local.ps1
    .\scripts\datalaw-local.ps1 -Acao preparar
    .\scripts\datalaw-local.ps1 -Acao ingerir -Tribunal tjsp -Modo incremental
    .\scripts\datalaw-local.ps1 -Acao app -Porta 8080
#>
[CmdletBinding()]
param(
    [ValidateSet("menu", "preparar", "status", "ingerir", "brutos", "gold", "app", "testes")]
    [string]$Acao = "menu",
    [ValidateSet("tjsp", "stj", "tst")]
    [string]$Tribunal = "tjsp",
    [ValidateSet("incremental", "completa", "retomar")]
    [string]$Modo = "incremental",
    [string]$RunId = "",
    [int]$Porta = 8080
)

$ErrorActionPreference = "Stop"

$Raiz = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Raiz "backend"
$Frontend = Join-Path $Raiz "frontend"
$Container = "datalaw_db"
$BancoLocal = "postgresql+psycopg://datalaw:datalaw@localhost:5432/datalaw_db"
$JdbcLocal = "jdbc:postgresql://localhost:5432/datalaw_db"

function Escrever-Titulo([string]$Texto) {
    Write-Host ""
    Write-Host "== $Texto ==" -ForegroundColor Cyan
}

function Escrever-Ok([string]$Texto) { Write-Host "  OK  $Texto" -ForegroundColor Green }
function Escrever-Aviso([string]$Texto) { Write-Host "  !!  $Texto" -ForegroundColor Yellow }

function Executar([string]$Descricao, [scriptblock]$Comando) {
    Write-Host "  ->  $Descricao" -ForegroundColor Gray
    & $Comando
    if ($LASTEXITCODE -ne 0) {
        throw "Falhou: $Descricao (código $LASTEXITCODE)"
    }
}

function Usar-BancoLocal {
    if ($env:DATABASE_URL -and $env:DATABASE_URL -ne $BancoLocal) {
        Escrever-Aviso "DATABASE_URL apontava para outro banco; nesta sessão ele foi trocado pelo banco local."
    }
    $env:DATABASE_URL = $BancoLocal
}

function Consultar-Banco([string]$Sql) {
    $saida = docker exec $Container psql -U datalaw -d datalaw_db -Atc $Sql 2>$null
    if ($LASTEXITCODE -ne 0) { return $null }
    return $saida
}

function Verificar-Docker {
    docker info --format "{{.ServerVersion}}" *> $null
    if ($LASTEXITCODE -ne 0) {
        throw "O Docker não está respondendo. Abra o Docker Desktop, espere ele iniciar e rode de novo."
    }
    Escrever-Ok "Docker respondendo"
}

function Subir-Banco {
    Verificar-Docker
    Push-Location $Raiz
    try {
        Executar "Subindo o PostgreSQL (docker compose up -d)" { docker compose up -d }
    } finally {
        Pop-Location
    }
    for ($i = 0; $i -lt 30; $i++) {
        docker exec $Container pg_isready -U datalaw -d datalaw_db *> $null
        if ($LASTEXITCODE -eq 0) {
            Escrever-Ok "Banco aceitando conexões em localhost:5432"
            return
        }
        Start-Sleep -Seconds 2
    }
    throw "O banco não ficou pronto em 60 segundos. Veja: docker logs $Container"
}

function Preparar {
    Escrever-Titulo "1. Preparar o ambiente"
    Subir-Banco
    Usar-BancoLocal
    Push-Location $Backend
    try {
        Executar "Instalando dependências do backend (uv sync --all-groups)" { uv sync --all-groups }
        Executar "Aplicando migrações (alembic upgrade head)" { uv run alembic upgrade head }
    } finally {
        Pop-Location
    }
    Escrever-Ok "Ambiente pronto"
    Mostrar-Status
}

function Mostrar-Status {
    Escrever-Titulo "Situação do banco local"
    $resumo = Consultar-Banco @"
select 'Processos (Silver): ' || count(*) from silver.processo
union all select 'Tribunais: ' || coalesce(string_agg(distinct tribunal_sigla, ', '), 'nenhum') from silver.processo
union all select 'Decisões com resultado (219/220/221): ' || count(distinct processo_id) from silver.movimento where codigo in (219, 220, 221)
union all select 'Precedentes (Silver): ' || count(*) from silver.jurisprudencia
union all select 'Teses com direção registrada: ' || count(*) from silver.precedente_direcao where direcao in ('autor', 'reu')
"@
    if ($null -eq $resumo) {
        Escrever-Aviso "Não foi possível consultar o banco. Rode a opção 1 (preparar)."
        return
    }
    $resumo | ForEach-Object { Write-Host "  $_" }

    $cargas = Consultar-Banco "select tribunal_alias || ': última carga ' || to_char(last_successful_at at time zone 'America/Sao_Paulo', 'DD/MM/YYYY HH24:MI') from bronze.datajud_ingestion_state order by 1"
    if ($cargas) {
        Write-Host "  Cargas do DataJud concluídas:"
        $cargas | ForEach-Object { Write-Host "    $_" }
    } else {
        Write-Host "  Nenhuma carga do DataJud registrada neste banco."
    }

    $gold = Consultar-Banco "select table_name from information_schema.tables where table_schema = 'gold' order by 1"
    if ($gold) {
        Write-Host ("  Tabelas Gold: " + (($gold | ForEach-Object { $_ }) -join ", "))
    } else {
        Escrever-Aviso "Camada Gold vazia: rode a opção 5 (recalcular Gold)."
    }
}

function Ler-ChaveDataJud {
    if ($env:DATAJUD_API_KEY) {
        Escrever-Ok "Usando DATAJUD_API_KEY já definida nesta sessão"
        return
    }
    $envFile = Join-Path $Backend ".env"
    if ((Test-Path $envFile) -and (Select-String -Path $envFile -Pattern "^\s*DATAJUD_API_KEY\s*=" -Quiet)) {
        Escrever-Ok "Usando DATAJUD_API_KEY do arquivo backend/.env"
        return
    }
    Write-Host "  A chave pública do DataJud fica em https://datajud-wiki.cnj.jus.br/api-publica/acesso/"
    $segura = Read-Host "  Cole a chave do DataJud (não aparece na tela)" -AsSecureString
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($segura)
    try {
        $env:DATAJUD_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
    } finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    }
    if (-not $env:DATAJUD_API_KEY) { throw "Nenhuma chave informada." }
}

function Ingerir([string]$TribunalEscolhido, [string]$ModoEscolhido, [string]$RunIdEscolhido) {
    Escrever-Titulo "3. Ingerir dados do DataJud ($TribunalEscolhido, $ModoEscolhido)"
    if ($TribunalEscolhido -eq "tst") {
        Escrever-Aviso "O TST é da Justiça do Trabalho e fica fora do escopo de direito civil do projeto."
    }
    Subir-Banco
    Usar-BancoLocal
    Ler-ChaveDataJud

    $alias = "api_publica_$TribunalEscolhido"
    $jaCarregado = Consultar-Banco "select count(*) from bronze.datajud_ingestion_state where tribunal_alias = '$alias'"
    if ($ModoEscolhido -eq "incremental" -and $jaCarregado -eq "0") {
        Escrever-Aviso "Este tribunal ainda não tem carga histórica neste banco; a carga incremental exige uma. Trocando para carga completa."
        $ModoEscolhido = "completa"
    }

    $argumentos = @("run", "python", "-m", "data_law.main", "--tribunal", $TribunalEscolhido)
    if ($ModoEscolhido -eq "completa") {
        $argumentos += "--full"
        Escrever-Aviso "A carga completa busca processos encerrados desde março de 2026 e pode levar bastante tempo. Se for interrompida, use o modo 'retomar' com o RUN_ID mostrado no log."
    } elseif ($ModoEscolhido -eq "retomar") {
        if (-not $RunIdEscolhido) { $RunIdEscolhido = Read-Host "  RUN_ID da execução interrompida" }
        if (-not $RunIdEscolhido) { throw "Informe o RUN_ID para retomar." }
        $argumentos += @("--resume", $RunIdEscolhido)
    }

    Push-Location $Backend
    try {
        Executar "Ingerindo (Raw -> Bronze -> Silver -> Gold)" { uv @argumentos }
    } finally {
        Pop-Location
    }
    Escrever-Ok "Ingestão concluída; Silver e Gold já foram atualizadas"
    Mostrar-Status
}

function Reprocessar-Brutos {
    Escrever-Titulo "4. Reprocessar arquivos brutos já baixados"
    Write-Host "  Usa os arquivos em backend/data/raw, sem chamar a API do DataJud."
    Subir-Banco
    Usar-BancoLocal
    Push-Location $Backend
    try {
        Executar "Carregando Raw -> Bronze -> Silver (bronze-load)" { uv run task bronze-load }
    } finally {
        Pop-Location
    }
    Recalcular-Gold
}

function Recalcular-Gold {
    Escrever-Titulo "5. Recalcular a camada Gold"
    Usar-BancoLocal
    Push-Location $Backend
    try {
        Executar "Materializando todas as tabelas Gold (gold-load)" { uv run task gold-load }
    } finally {
        Pop-Location
    }
}

function Subir-App([int]$PortaApp) {
    Escrever-Titulo "6. Subir a aplicação"
    Subir-Banco
    $ocupada = Get-NetTCPConnection -LocalPort $PortaApp -State Listen -ErrorAction SilentlyContinue
    if ($ocupada) {
        throw "A porta $PortaApp já está em uso (processo $($ocupada[0].OwningProcess)). Feche a outra instância ou use -Porta 8081."
    }
    Write-Host "  Quando aparecer 'Started DatalawApplication', abra http://localhost:$PortaApp"
    Write-Host "  e pesquise um tema (por exemplo: Penhora). Para parar, use Ctrl+C."
    $argumentos = "--server.port=$PortaApp --spring.datasource.url=$JdbcLocal --spring.datasource.username=datalaw --spring.datasource.password=datalaw"
    Push-Location $Frontend
    try {
        & .\mvnw.cmd spring-boot:run "-Dspring-boot.run.arguments=$argumentos"
    } finally {
        Pop-Location
    }
}

function Rodar-Testes {
    Escrever-Titulo "7. Rodar os testes"
    Subir-Banco
    Usar-BancoLocal
    Push-Location $Backend
    try {
        Executar "Backend: lint" { uv run ruff check src tests }
        Executar "Backend: testes unitários e de integração" { uv run pytest -q }
    } finally {
        Pop-Location
    }
    Push-Location $Frontend
    try {
        Executar "Frontend: testes" { .\mvnw.cmd -q test }
    } finally {
        Pop-Location
    }
    Escrever-Ok "Todos os testes passaram"
}

function Mostrar-Menu {
    while ($true) {
        Escrever-Titulo "DataLaw local"
        Write-Host "  1  Preparar o ambiente (banco, dependências e migrações)"
        Write-Host "  2  Ver a situação do banco"
        Write-Host "  3  Ingerir mais dados do DataJud (precisa de chave da API)"
        Write-Host "  4  Reprocessar os arquivos brutos já baixados"
        Write-Host "  5  Recalcular a camada Gold"
        Write-Host "  6  Subir a aplicação"
        Write-Host "  7  Rodar os testes"
        Write-Host "  0  Sair"
        $opcao = Read-Host "Escolha"
        try {
            switch ($opcao) {
                "1" { Preparar }
                "2" { Mostrar-Status }
                "3" {
                    $t = Read-Host "  Tribunal [tjsp, stj, tst] (Enter = tjsp)"
                    if (-not $t) { $t = "tjsp" }
                    if (@("tjsp", "stj", "tst") -notcontains $t) { throw "Tribunal inválido: $t" }
                    $m = Read-Host "  Modo [incremental, completa, retomar] (Enter = incremental)"
                    if (-not $m) { $m = "incremental" }
                    if (@("incremental", "completa", "retomar") -notcontains $m) { throw "Modo inválido: $m" }
                    Ingerir $t $m ""
                }
                "4" { Reprocessar-Brutos }
                "5" { Recalcular-Gold }
                "6" {
                    $p = Read-Host "  Porta (Enter = 8080)"
                    if (-not $p) { $p = "8080" }
                    Subir-App ([int]$p)
                }
                "7" { Rodar-Testes }
                "0" { return }
                default { Escrever-Aviso "Opção inválida" }
            }
        } catch {
            Write-Host "  ERRO  $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}

try {
    switch ($Acao) {
        "menu" { Mostrar-Menu }
        "preparar" { Preparar }
        "status" { Subir-Banco; Mostrar-Status }
        "ingerir" { Ingerir $Tribunal $Modo $RunId }
        "brutos" { Reprocessar-Brutos }
        "gold" { Subir-Banco; Recalcular-Gold }
        "app" { Subir-App $Porta }
        "testes" { Rodar-Testes }
    }
} catch {
    Write-Host "  ERRO  $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
