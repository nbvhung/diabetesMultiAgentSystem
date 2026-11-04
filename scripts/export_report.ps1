$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
# Native Word PDF export did not complete on the verification host. Use the
# verified Chromium renderer; DOCX TOC updates remain a separate optional step.
Push-Location -LiteralPath $projectRoot
try {
    python scripts/build_report_pdf.py
    if ($LASTEXITCODE -ne 0) { throw 'Report PDF rendering failed.' }
    python scripts/inspect_report.py
    if ($LASTEXITCODE -ne 0) { throw 'Report layout verification failed.' }
} finally {
    Pop-Location
}
