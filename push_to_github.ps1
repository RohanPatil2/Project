# PowerShell script to push code to GitHub via WSL
# Repository: https://github.com/RohanPatil2/uncertainty-aware-slam.git

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Pushing code to GitHub via WSL" -ForegroundColor Cyan
Write-Host "Repository: https://github.com/RohanPatil2/uncertainty-aware-slam.git" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Check if WSL is available
try {
    wsl --version | Out-Null
    Write-Host "✓ WSL detected" -ForegroundColor Green
} catch {
    Write-Host "✗ WSL not found. Please install WSL first." -ForegroundColor Red
    Write-Host "  Install: wsl --install" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "Running git commands in WSL..." -ForegroundColor Yellow
Write-Host ""

# Define the bash commands
$bashCommands = @"
cd /home/rohan/slam_uncertainty_ws

echo '→ Initializing git repository...'
if [ ! -d '.git' ]; then
    git init
    echo '✓ Git repository initialized'
else
    echo '✓ Git repository already initialized'
fi

echo ''
echo '→ Configuring git...'
git config user.name 'RohanPatil2'
git config user.email 'rohanpatil@example.com'
echo '✓ Git configured'

echo ''
echo '→ Setting up remote...'
if ! git remote | grep -q 'origin'; then
    git remote add origin https://github.com/RohanPatil2/uncertainty-aware-slam.git
    echo '✓ Remote origin added'
else
    git remote set-url origin https://github.com/RohanPatil2/uncertainty-aware-slam.git
    echo '✓ Remote origin updated'
fi

echo ''
echo '→ Staging all files...'
git add .
echo '✓ Files staged'

echo ''
echo '→ Creating commit...'
git commit -m 'Complete uncertainty-aware SLAM implementation

- Real-time entropy quantification
- Synthetic robot for testing
- Advanced exploration algorithms
- Active SLAM with frontier detection
- Publication-quality visualizations
- Complete system launcher
- Comprehensive documentation' || echo 'ℹ No new changes to commit'

echo ''
echo '→ Setting branch to main...'
git branch -M main
echo '✓ Branch set to main'

echo ''
echo '========================================='
echo 'Ready to push to GitHub!'
echo '========================================='
echo ''
echo 'IMPORTANT: You will need to authenticate'
echo ''
echo 'Use your GitHub Personal Access Token (PAT)'
echo 'Generate at: https://github.com/settings/tokens'
echo ''
echo 'Attempting to push...'
echo ''

git push -u origin main

if [ \$? -eq 0 ]; then
    echo ''
    echo '========================================='
    echo '✅ Successfully pushed to GitHub!'
    echo '========================================='
    echo ''
    echo 'View your repository at:'
    echo 'https://github.com/RohanPatil2/uncertainty-aware-slam'
else
    echo ''
    echo '========================================='
    echo '❌ Push failed'
    echo '========================================='
    echo ''
    echo 'Common issues:'
    echo '1. Authentication - Use Personal Access Token'
    echo '2. Network connection'
    echo '3. Repository permissions'
    echo ''
    echo 'See PUSH_TO_GITHUB.md for detailed help'
fi
"@

# Execute in WSL
wsl bash -c $bashCommands

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Script completed" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "If push failed, see PUSH_TO_GITHUB.md for alternative methods" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

