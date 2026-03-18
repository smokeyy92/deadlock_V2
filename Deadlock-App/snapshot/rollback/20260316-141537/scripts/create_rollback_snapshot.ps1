param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
)

$ErrorActionPreference = "Stop"

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$snapshotRoot = Join-Path $ProjectRoot "snapshot\rollback"
$snapshotPath = Join-Path $snapshotRoot $timestamp

New-Item -ItemType Directory -Path $snapshotPath -Force | Out-Null

$includeItems = @(
    "src",
    "config",
    "data",
    "assets",
    "scripts",
    "snapshot\state.json",
    "requirements.txt",
    "README.md",
    "instructions.md"
)

foreach ($item in $includeItems) {
    $source = Join-Path $ProjectRoot $item
    if (-not (Test-Path $source)) {
        continue
    }

    $destination = Join-Path $snapshotPath $item
    $sourceItem = Get-Item $source

    if ($sourceItem.PSIsContainer) {
        New-Item -ItemType Directory -Path $destination -Force | Out-Null
        robocopy $source $destination /E /R:1 /W:1 /NFL /NDL /NJH /NJS /XF *.pyc /XD __pycache__ venv .git | Out-Null
        if ($LASTEXITCODE -ge 8) {
            throw "robocopy failed while copying $source"
        }
    }
    else {
        $destinationDir = Split-Path -Path $destination -Parent
        New-Item -ItemType Directory -Path $destinationDir -Force | Out-Null
        Copy-Item -Path $source -Destination $destination -Force
    }
}

$manifestPath = Join-Path $snapshotPath "manifest.txt"
@(
    "timestamp=$timestamp"
    "project_root=$ProjectRoot"
) | Set-Content -Path $manifestPath -Encoding UTF8

if (Get-Command git -ErrorAction SilentlyContinue) {
    Push-Location $ProjectRoot
    try {
        $isRepo = (& git rev-parse --is-inside-work-tree 2>$null)
        if ($LASTEXITCODE -eq 0 -and $isRepo -eq "true") {
            "git_head=$(& git rev-parse HEAD)" | Add-Content -Path $manifestPath -Encoding UTF8
            "" | Add-Content -Path $manifestPath -Encoding UTF8
            "# git status --short" | Add-Content -Path $manifestPath -Encoding UTF8
            (& git status --short) | Add-Content -Path $manifestPath -Encoding UTF8
        }
    }
    finally {
        Pop-Location
    }
}

Write-Host "Created rollback snapshot: $snapshotPath"
