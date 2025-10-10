param(
  [Parameter(Mandatory=$true)]
  [string]$ExecutablePath,

  [Parameter(Mandatory=$false)]
  [string]$AppCommandLineArgs, # Changed from [string[]] to [string]

  [Parameter(Mandatory=$false)]
  [string]$AdditionalArgument # New parameter for an extra argument
)

# Function to set a window to be topmost
function Set-TopMost($handle) {
  $FnDef = '
  [DllImport("user32.dll")]
  public static extern bool SetWindowPos(int hWnd, int hAfter, int x, int y, int cx, int cy, uint Flags);
  ';
  $user32 = Add-Type -MemberDefinition $FnDef -Name 'User32' -Namespace 'Win32' -PassThru
  
  # SWP_NOMOVE (0x0002) | SWP_NOSIZE (0x0001) | HWND_TOPMOST (-1)
  # Flags: 0x0001 (SWP_NOSIZE) | 0x0002 (SWP_NOMOVE) = 3
  $user32::SetWindowPos($handle, -1, 0, 0, 0, 0, 3)
}

# --- Parse the single string of arguments into an array ---
$appArgumentsArray = @()
if (-not [string]::IsNullOrEmpty($AppCommandLineArgs)) {
    # Split the string by comma and then trim any leading/trailing whitespace from each resulting argument.
    $appArgumentsArray = $AppCommandLineArgs.Split(',', [System.StringSplitOptions]::RemoveEmptyEntries) | ForEach-Object { $_.Trim() }
}

# --- NEW: Add the additional argument to the array if provided ---
if (-not [string]::IsNullOrEmpty($AdditionalArgument)) {
    $appArgumentsArray += $AdditionalArgument
}
# --- END NEW ---

# Get the process name without extension from the executable path
$processName = [System.IO.Path]::GetFileNameWithoutExtension($ExecutablePath)

Write-Host "Attempting to find or start process: '$processName' using executable: '$ExecutablePath'"

# Try to find an existing process with a main window handle
$process = (Get-Process $processName -ErrorAction "SilentlyContinue") | Where-Object { $_.MainWindowHandle -ne 0 }

# If the process is not found, start it
if ($process -eq $null) {
  Write-Host "Process '$processName' not found. Starting '$ExecutablePath' with arguments: $($appArgumentsArray -join ' ')"
  
  # Start the process with arguments using the call operator (&)
  # Use splatting (@) with the newly created array
  & $ExecutablePath @appArgumentsArray
  
  Write-Host "Waiting for process '$processName' to start..."
  
  # Wait until the process starts and has a main window handle
  while ($process -eq $null) {
    Start-Sleep -Milliseconds 200 # Wait a bit longer to give the process time to initialize its window
    $process = (Get-Process $processName -ErrorAction "SilentlyContinue") | Where-Object { $_.MainWindowHandle -ne 0 }
  }
  Write-Host "Process '$processName' started successfully."
} else {
  Write-Host "Process '$processName' already running."
}

# Check if a main window handle was found for the process
if ($process.MainWindowHandle -ne 0) {
  Write-Host "Setting window to topmost for process '$processName' (Handle: $($process.MainWindowHandle))."
  Set-TopMost $process.MainWindowHandle
} else {
  Write-Host "Could not find a main window handle for process '$processName'. It might be a background process or not yet fully initialized."
}
