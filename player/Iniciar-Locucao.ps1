param(
    [string]$BaseUrl = "https://lucasbenevidev.github.io/locutor-camisa-treze",
    [switch]$NaoIniciar
)

$ErrorActionPreference = "Stop"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$audios = Join-Path $PSScriptRoot "audios"
$playlist = Join-Path $PSScriptRoot "playlist.m3u"
$silencio = Join-Path $PSScriptRoot "silencio-5s.wav"
$manifestoLocal = Join-Path $PSScriptRoot "manifest-local.json"
New-Item -ItemType Directory -Force $audios | Out-Null

function Encerrar($mensagem) {
    Write-Host $mensagem -ForegroundColor Red
    if (-not $NaoIniciar) { Read-Host "Pressione Enter para fechar" }
    exit 1
}

function Baixar($caminho, $destino) {
    $url = "$BaseUrl/$caminho" + "?_=" + [DateTimeOffset]::Now.ToUnixTimeSeconds()
    Invoke-WebRequest -Uri $url -OutFile $destino -UseBasicParsing -TimeoutSec 60
}

Write-Host "Buscando os anúncios no ar..."
$agora = [DateTimeOffset]::Now
$conectado = $true
try {
    $temporario = Join-Path $PSScriptRoot "manifest-novo.json"
    Baixar "manifest.json" $temporario
    Move-Item -Force $temporario $manifestoLocal
} catch {
    $conectado = $false
    Write-Host "Sem conexão com o servidor de anúncios. Usando os áudios já baixados." -ForegroundColor Yellow
}
if (-not (Test-Path $manifestoLocal)) {
    Encerrar "Sem internet e nenhum áudio foi baixado antes. Conecte o notebook à internet e tente de novo."
}
$manifesto = Get-Content $manifestoLocal -Raw -Encoding UTF8 | ConvertFrom-Json

$ativos = @()
foreach ($audio in @($manifesto.audios)) {
    if ([DateTimeOffset]::Parse($audio.valido_ate) -lt $agora) { continue }
    $arquivo = Join-Path $audios ("{0}_{1}.mp3" -f $audio.id, $audio.sha)
    if (-not (Test-Path $arquivo)) {
        if (-not $conectado) { continue }
        Write-Host "Baixando $($audio.id)..."
        try {
            Baixar $audio.arquivo $arquivo
        } catch {
            Remove-Item -Force $arquivo -ErrorAction SilentlyContinue
            Write-Host "Não foi possível baixar $($audio.id)." -ForegroundColor Yellow
            continue
        }
    }
    $ativos += $arquivo
}

Get-ChildItem $audios -Filter *.mp3 | Where-Object { $ativos -notcontains $_.FullName } | Remove-Item -Force

if ($ativos.Count -eq 0) {
    Encerrar "Nenhum anúncio no ar no momento. Peça para aprovar um anúncio na planilha."
}

$linhas = @("#EXTM3U")
foreach ($arquivo in $ativos) {
    $linhas += $arquivo
    $linhas += $silencio
}
[IO.File]::WriteAllLines($playlist, $linhas, [Text.Encoding]::ASCII)
Write-Host "Playlist pronta com $($ativos.Count) anúncio(s)." -ForegroundColor Green

if ($NaoIniciar) { exit 0 }

$vlc = @("$env:ProgramFiles\VideoLAN\VLC\vlc.exe", "${env:ProgramFiles(x86)}\VideoLAN\VLC\vlc.exe") |
    Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $vlc) {
    Encerrar "O VLC não está instalado. Instale-o em videolan.org e tente de novo."
}

Get-Process vlc -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Process $vlc -ArgumentList @("--loop", "--no-video-title-show", "`"$playlist`"")
Write-Host "Locução iniciada. Para parar, clique no botão de parar do VLC ou feche a janela dele."
Start-Sleep -Seconds 3
