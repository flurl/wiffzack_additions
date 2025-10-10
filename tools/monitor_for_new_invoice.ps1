param(
    [string]$watchFolder = ".\invoices_to_print",  # Default directory to monitor
    [string]$printScript = ".\print_invoice.ps1"   # Path to your print script
)

# Convert relative paths to absolute paths
$absoluteWatchFolder = $null
if (Test-Path -Path $watchFolder) {
    $absoluteWatchFolder = (Get-Item -Path $watchFolder).FullName
} else {
    # If path doesn't exist, create it first, then get absolute path
    Write-Host "Watch folder '$watchFolder' not found. Creating it."
    $created = New-Item -ItemType Directory -Path $watchFolder
    $absoluteWatchFolder = $created.FullName
}

$absolutePrintScript = $null
if (Test-Path -Path $printScript) {
    $absolutePrintScript = (Get-Item -Path $printScript).FullName
} else {
    Write-Error "Print script not found at path: $printScript"
    exit 1
}

Write-Host "Monitoring directory: $absoluteWatchFolder"
Write-Host "Print script: $absolutePrintScript"

# Create FileSystemWatcher object
$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = $absoluteWatchFolder
$watcher.Filter = "inv_*"
$watcher.IncludeSubdirectories = $false
$watcher.EnableRaisingEvents = $true

# Define the action to take when a file is created
$action = {
    $filePath = $Event.SourceEventArgs.FullPath
    $fileName = $Event.SourceEventArgs.Name
    
    # Extract invoice ID from filename (e.g., "inv_12345.txt")
    if ($fileName -match '^inv_(\d+)') {
        $invoiceID = $matches[1]
        Write-Host "Detected new invoice file: $fileName (ID: $invoiceID)"
        
        # Access the print script path passed via -MessageData
        $printScriptPath = $Event.MessageData[0]
        
        # Call the print script
        try {
            & $printScriptPath -invoiceID $invoiceID
            Write-Host "Successfully initiated printing for invoice $invoiceID."
            
            # Delete the processed invoice file
            try {
                # Wait a moment to ensure the file isn't locked by the print process
                #Start-Sleep -Seconds 2
                
                if (Test-Path -Path $filePath) {
                    Remove-Item -Path $filePath -Force
                    Write-Host "Successfully deleted processed file: $fileName" -ForegroundColor Green
                } else {
                    Write-Host "File $fileName was already removed or not found." -ForegroundColor Yellow
                }
            }
            catch {
                Write-Host ("Error deleting file " + $fileName + ": " + $_) -ForegroundColor Red
            }
        }
        catch {
            Write-Host ("Error processing invoice " + $invoiceID + ": " + $_) -ForegroundColor Red
            Write-Host "File $fileName will NOT be deleted due to processing error." -ForegroundColor Yellow
        }
    }
}

# Register the event handler and pass the printScript path to the action
$createdEvent = Register-ObjectEvent $watcher "Created" -Action $action -MessageData @($absolutePrintScript)

Write-Host "Monitoring directory '$absoluteWatchFolder' for new invoice files..."
Write-Host "Press CTRL+C to stop."

try {
    # Keep the script running
    while ($true) {
        Wait-Event -Timeout 1
    }
}
finally {
    # Clean up when the script is stopped
    Unregister-Event -SubscriptionId $createdEvent.Id
    $watcher.Dispose()
    Write-Host "Monitoring stopped and resources released."
}