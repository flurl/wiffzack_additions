param (
    [string]$server = "http://localhost:5000/api/invoice/print/",
    [Parameter(Mandatory=$true)][string]$invoiceID
)

$job = Start-Job -ScriptBlock {
    param($s, $id)
    Invoke-WebRequest -Uri "$s$id"
} -ArgumentList $server, $invoiceID

# Wait for job completion (max 30 seconds)
$job | Wait-Job -Timeout 30 | Out-Null

# Get results/errors
Receive-Job $job -ErrorAction SilentlyContinue -ErrorVariable jobError
if ($jobError) { Write-Error "Job failed: $jobError" }

# Clean up
Remove-Job $job -Force