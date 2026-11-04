$ErrorActionPreference = 'Stop'
$documentPath = Join-Path (Split-Path -Parent $PSScriptRoot) 'docs\report\tieuluan_final_06_13_hungnbv.docx'
$ownedWord = $null
$ownedReport = $null
try {
    $ownedWord = New-Object -ComObject Word.Application
    $ownedWord.Visible = $false
    $ownedWord.DisplayAlerts = 0
    Write-Output 'Opening only the generated report.'
    $ownedReport = $ownedWord.Documents.Open($documentPath, $false, $false, $false)
    $ownedReport.Fields.Update() | Out-Null
    foreach ($toc in $ownedReport.TablesOfContents) { $toc.Update() }
    $ownedReport.Save()
    Write-Output 'DOCX fields and table of contents saved; no PDF export requested.'
} finally {
    if ($null -ne $ownedReport) { $ownedReport.Close(0) }
    if ($null -ne $ownedWord -and $ownedWord.Documents.Count -eq 0) { $ownedWord.Quit() }
}
