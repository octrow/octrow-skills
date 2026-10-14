# Copy to <repo>/install.ps1, fill the four values below, then adapt or delete the `# PROJECT:` blocks.
# Worked example with every PROJECT block filled: https://github.com/octrow/repo-scout/blob/main/install.ps1
#
# CMD installer for Windows (PowerShell).
#   powershell -ExecutionPolicy ByPass -c "irm https://raw.githubusercontent.com/OWNER/REPO/main/install.ps1 | iex"
# Options are environment variables, since `irm | iex` cannot pass arguments:
#   $env:INSTALL_VERSION = "0.1.0"   # a specific release instead of the latest one
#   $env:INSTALL_MAIN = "1"          # current main branch instead of a release
#   $env:INSTALL_NO_LAUNCH = "1"     # install only, do not offer to start it
#   $env:INSTALL_UNINSTALL = "1"     # remove the app, keep its data
# Re-running it updates. $env:INSTALL_SOURCE = <path or uv spec> installs from there instead (CI, local testing).
# "Continue": in Windows PowerShell 5.1 "Stop" turns any stderr line of a redirected native command (uv)
# into a fatal error; native failures are checked through $LASTEXITCODE instead
$ErrorActionPreference = "Continue"

$Repo = "OWNER/REPO"
$Name = "PKG"      # distribution name from pyproject.toml [project] name
$Cmd = "CMD"       # the command from [project.scripts]
$Python = "3.12"   # pinned so binary wheels of the dependencies exist; bump when they ship for newer Pythons

function Say($m) { Write-Host "==> $m" -ForegroundColor Cyan }
function Note($m) { Write-Host "    $m" }
function Have($c) { [bool](Get-Command $c -ErrorAction SilentlyContinue) }
# installers update PATH in the registry, not in this session
function Refresh-Path {
  $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
              [Environment]::GetEnvironmentVariable("Path", "User") + ";$HOME\.local\bin"
}
$Interactive = [Environment]::UserInteractive -and -not [Console]::IsInputRedirected

Refresh-Path

if ($env:INSTALL_UNINSTALL -eq "1") {
  if (Have uv) { uv tool uninstall $Name }
  Say "$Cmd is removed."
  return
}

# 1. uv: installs Python and the app into an isolated environment, no system Python or admin rights needed
if (-not (Have uv)) {
  Say "Installing uv (it installs Python and $Cmd)"
  Invoke-RestMethod https://astral.sh/uv/install.ps1 -ErrorAction Stop | Invoke-Expression
  Refresh-Path
  if (-not (Have uv)) { throw "uv is installed, but this terminal does not see it. Open a new terminal and run this command again." }
}

# PROJECT: other tools the app calls (repo-scout installs `gh` here with winget, then Refresh-Path).
# Install what you can, otherwise say where to get it and carry on; don't stop the whole install for it.

# 2. the app: the release wheel built and tested by CI, or the main branch
$Version = ""
if ($env:INSTALL_SOURCE) {
  $Spec = $env:INSTALL_SOURCE
} elseif ($env:INSTALL_MAIN -eq "1") {
  $Spec = "$Name @ https://github.com/$Repo/archive/refs/heads/main.tar.gz"
} else {
  $Version = "$env:INSTALL_VERSION".TrimStart("v")
  if (-not $Version) {
    try { $Version = (Invoke-RestMethod "https://api.github.com/repos/$Repo/releases/latest" -ErrorAction Stop).tag_name.TrimStart("v") }
    catch { throw "No release found, or GitHub is not reachable. To install the main branch, set `$env:INSTALL_MAIN = `"1`" and run this command again." }
  }
  $Wheel = "$($Name -replace '-', '_')-$Version-py3-none-any.whl"
  $Spec = "$Name @ https://github.com/$Repo/releases/download/v$Version/$Wheel"
}
Say "Installing $Cmd $Version"
uv tool install --reinstall --python $Python $Spec
if ($LASTEXITCODE -ne 0) { throw "uv could not install $Cmd. See the uv output above." }
uv tool update-shell *> $null
$Bin = Join-Path (uv tool dir --bin) "$Cmd.exe"

# PROJECT: first run. Logins, model downloads, a `doctor` that says what is missing in plain words, an optional
# `config` for API keys (ask once with Read-Host when $Interactive, skip when a key is already saved).
# & $Bin doctor; if ($LASTEXITCODE -ne 0) { Write-Host "!! Fix the items marked above, then run: $Cmd doctor" -ForegroundColor Yellow }

Say "$Cmd is installed. To start it, run: $Cmd"
Note "Command not found? Open a new terminal or run: $Bin"

# PROJECT: offer to start it (GUI apps); delete for a plain CLI.
if ($env:INSTALL_NO_LAUNCH -ne "1" -and $Interactive) {
  $answer = Read-Host "Start $Cmd now? [Y/n]"
  if ($answer -notmatch '^[nN]') { & $Bin }
}
