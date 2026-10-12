param(
    [string]$Destino = "C:\Locutor",
    [switch]$SoCopiar
)

$ErrorActionPreference = "Stop"

New-Item -ItemType Directory -Force $Destino | Out-Null
foreach ($nome in "Iniciar-Locucao.ps1", "Iniciar-Locucao.bat", "silencio-5s.wav") {
    Copy-Item (Join-Path $PSScriptRoot $nome) $Destino -Force
}
Write-Host "Arquivos copiados para $Destino"

if ($SoCopiar) { exit 0 }

$area = [Environment]::GetFolderPath("Desktop")
$atalho = (New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path $area "Iniciar locução.lnk"))
$atalho.TargetPath = Join-Path $Destino "Iniciar-Locucao.bat"
$atalho.WorkingDirectory = $Destino
$atalho.IconLocation = "shell32.dll,168"
$atalho.Save()
Write-Host "Atalho 'Iniciar locução' criado na área de trabalho."

schtasks /Create /F /SC DAILY /ST 20:00 /TN "Locutor Camisa Treze - Encerrar as 20h" /TR "taskkill /IM vlc.exe /F" | Out-Null
Write-Host "Tarefa criada: o VLC é fechado todo dia às 20h."

if (-not (Test-Path "$env:ProgramFiles\VideoLAN\VLC\vlc.exe") -and -not (Test-Path "${env:ProgramFiles(x86)}\VideoLAN\VLC\vlc.exe")) {
    Write-Host "Atenção: o VLC ainda não está instalado. Instale-o em videolan.org." -ForegroundColor Yellow
}
Read-Host "Pronto. Pressione Enter para fechar"
