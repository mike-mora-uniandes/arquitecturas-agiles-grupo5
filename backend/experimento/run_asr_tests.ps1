# Script de ejecución para cada ASR
# Ejecuta desde la carpeta backend
# Ejemplo: .\experimento\run_asr_tests.ps1 ASR1

param(
    [Parameter(Position = 0)]
    [ValidateSet("ASR1", "ASR3", "ASR2", "BASE")]
    [string]$Scenario = "BASE"
)

$ErrorActionPreference = "Stop"

switch ($Scenario) {
    "BASE" {
        $env:E0_WEIGHT = "40"
        $env:E1_WEIGHT = "18"
        $env:E2_WEIGHT = "15"
        $env:E3_WEIGHT = "15"
        $env:E4_WEIGHT = "8"
        $env:E5_WEIGHT = "4"
    }
    "ASR1" {
        $env:E0_WEIGHT = "10"
        $env:E1_WEIGHT = "35"
        $env:E2_WEIGHT = "20"
        $env:E3_WEIGHT = "20"
        $env:E4_WEIGHT = "10"
        $env:E5_WEIGHT = "5"
    }
    "ASR3" {
        $env:E0_WEIGHT = "15"
        $env:E1_WEIGHT = "40"
        $env:E2_WEIGHT = "20"
        $env:E3_WEIGHT = "20"
        $env:E4_WEIGHT = "3"
        $env:E5_WEIGHT = "2"
    }
    "ASR2" {
        $env:E0_WEIGHT = "20"
        $env:E1_WEIGHT = "15"
        $env:E2_WEIGHT = "20"
        $env:E3_WEIGHT = "25"
        $env:E4_WEIGHT = "10"
        $env:E5_WEIGHT = "10"
    }
}

Write-Host "=================================================="
Write-Host "Ejecutando prueba: $Scenario"
Write-Host "E0=$env:E0_WEIGHT E1=$env:E1_WEIGHT E2=$env:E2_WEIGHT E3=$env:E3_WEIGHT E4=$env:E4_WEIGHT E5=$env:E5_WEIGHT"
Write-Host "=================================================="

# La UI de Locust queda disponible en http://localhost:8089
# en la pantalla de Start, usa:
# - Number of users: 10
# - Spawn rate: 1
# - Host: http://localhost:5001
# - Run time: 2m

Write-Host "Abre http://localhost:8089 y pulsa Start"
Write-Host "Host recomendado: http://localhost:5001"
Write-Host "Usuarios sugeridos: 10"
Write-Host "Spawn rate sugerido: 1"
Write-Host "Duración sugerida: 2m"
