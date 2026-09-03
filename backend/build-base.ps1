# Equivalente de build-base.sh para PowerShell (Windows).
#
# Uso:
#   ./build-base.ps1            # construye base + docker compose up -d --build
#   ./build-base.ps1 -NoUp      # solo construye la imagen base
param(
    [switch]$NoUp
)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

if (-not (Test-Path ".env")) {
    Write-Host ">> Creando .env desde .env.example"
    Copy-Item ".env.example" ".env"
}

Write-Host ">> Construyendo solventa/flask-base:latest ..."
docker build -t solventa/flask-base:latest ./base-image

if ($NoUp) {
    Write-Host ">> Imagen base construida. Fin."
    exit 0
}

Write-Host ">> Levantando el stack ..."
docker compose up -d --build

Write-Host ">> Estado:"
docker compose ps
