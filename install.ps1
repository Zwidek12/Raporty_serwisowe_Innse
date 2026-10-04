param(
    [switch]$Uninstall,
    [switch]$Shared
)

$ErrorActionPreference = "Stop"
$ExtensionId = "com.innse.servicereport"
$Oxt = Join-Path $PSScriptRoot "dist\ServiceReport.oxt"

function Find-Unopkg {
    $candidates = @(
        "$env:ProgramFiles\LibreOffice\program\unopkg.com",
        "${env:ProgramFiles(x86)}\LibreOffice\program\unopkg.com"
    )
    foreach ($key in @("HKLM:\SOFTWARE\LibreOffice\UNO\InstallPath",
                       "HKLM:\SOFTWARE\WOW6432Node\LibreOffice\UNO\InstallPath")) {
        try {
            $dir = (Get-ItemProperty -Path $key -ErrorAction Stop)."(default)"
            if ($dir) { $candidates = @((Join-Path $dir "unopkg.com")) + $candidates }
        } catch {}
    }
    foreach ($c in $candidates) { if ($c -and (Test-Path $c)) { return $c } }
    throw "Nie znaleziono LibreOffice (unopkg.com). Zainstaluj LibreOffice."
}

if (Get-Process soffice*, swriter* -ErrorAction SilentlyContinue) {
    Write-Host "Zamknij wszystkie okna LibreOffice (również szybkie uruchamianie w zasobniku) i uruchom skrypt ponownie." -ForegroundColor Yellow
    exit 1
}

$unopkg = Find-Unopkg
$scope = @()
if ($Shared) { $scope = @("--shared") }

if ($Uninstall) {
    & $unopkg remove @scope $ExtensionId
    if ($LASTEXITCODE -ne 0) { throw "Odinstalowanie nie powiodło się (kod $LASTEXITCODE)." }
    Write-Host "Rozszerzenie zostało odinstalowane." -ForegroundColor Green
    exit 0
}

if (-not (Test-Path $Oxt)) { throw "Brak pliku $Oxt" }

$ErrorActionPreference = "Continue"
& $unopkg remove @scope $ExtensionId 2>&1 | Out-Null
& $unopkg add @scope --suppress-license $Oxt
$ErrorActionPreference = "Stop"
if ($LASTEXITCODE -ne 0) { throw "Instalacja nie powiodła się (kod $LASTEXITCODE)." }

Write-Host "Zainstalowano rozszerzenie Raport serwisowy." -ForegroundColor Green
Write-Host "Uruchom LibreOffice Writer - menu 'Raport serwisowy' oraz pasek narzędzi są dostępne."
