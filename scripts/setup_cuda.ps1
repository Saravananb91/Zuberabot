# CUDA Setup Automation Script for Windows
# Run as Administrator

param(
    [switch]$SkipDriverCheck,
    [switch]$InstallCuDNN
)

Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "CUDA Setup Script for GTX 1650" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan

# Step 1: Check NVIDIA Drivers
Write-Host "`n[1/6] Checking NVIDIA Drivers..." -ForegroundColor Yellow

try {
    $nvidiaSmi = nvidia-smi
    Write-Host "✅ NVIDIA drivers installed" -ForegroundColor Green
    nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
} catch {
    Write-Host "❌ NVIDIA drivers not found!" -ForegroundColor Red
    Write-Host "Please install drivers from: https://www.nvidia.com/Download/index.aspx" -ForegroundColor Yellow
    if (-not $SkipDriverCheck) {
        exit 1
    }
}

# Step 2: Check CUDA Toolkit
Write-Host "`n[2/6] Checking CUDA Toolkit..." -ForegroundColor Yellow

try {
    $nvccVersion = nvcc --version
    Write-Host "✅ CUDA Toolkit installed" -ForegroundColor Green
    nvcc --version | Select-String "release"
} catch {
    Write-Host "⚠️  CUDA Toolkit not found" -ForegroundColor Yellow
    Write-Host "Download from: https://developer.nvidia.com/cuda-12-1-0-download-archive" -ForegroundColor Yellow
    Write-Host "After installation, restart PowerShell and run this script again." -ForegroundColor Yellow
}

# Step 3: Set Environment Variables
Write-Host "`n[3/6] Setting Environment Variables..." -ForegroundColor Yellow

$cudaPath = "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.1"

if (Test-Path $cudaPath) {
    [Environment]::SetEnvironmentVariable("CUDA_PATH", $cudaPath, "Machine")
    [Environment]::SetEnvironmentVariable("CUDA_PATH_V12_1", $cudaPath, "Machine")
    
    $cudaBin = "$cudaPath\bin"
    $cudaLib = "$cudaPath\libnvvp"
    
    $currentPath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    if ($currentPath -notlike "*$cudaBin*") {
        [Environment]::SetEnvironmentVariable("Path", "$currentPath;$cudaBin;$cudaLib", "Machine")
        Write-Host "✅ Environment variables set" -ForegroundColor Green
    } else {
        Write-Host "✅ Environment variables already configured" -ForegroundColor Green
    }
} else {
    Write-Host "❌ CUDA not found at $cudaPath" -ForegroundColor Red
}

# Step 4: Install PyTorch with CUDA
Write-Host "`n[4/6] Installing PyTorch with CUDA support..." -ForegroundColor Yellow

$pythonVersion = python --version 2>&1
Write-Host "Python version: $pythonVersion" -ForegroundColor Cyan

# Uninstall existing PyTorch
Write-Host "Uninstalling existing PyTorch (if any)..." -ForegroundColor Yellow
pip uninstall torch torchvision torchaudio -y 2>&1 | Out-Null

# Install PyTorch with CUDA 12.1
Write-Host "Installing PyTorch with CUDA 12.1..." -ForegroundColor Yellow
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ PyTorch installed successfully" -ForegroundColor Green
} else {
    Write-Host "❌ PyTorch installation failed" -ForegroundColor Red
}

# Step 5: Install LlamaCpp with CUDA
Write-Host "`n[5/6] Installing LlamaCpp with CUDA support..." -ForegroundColor Yellow

$env:CMAKE_ARGS = "-DLLAMA_CUBLAS=on"
pip install llama-cpp-python --force-reinstall --no-cache-dir

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ LlamaCpp installed successfully" -ForegroundColor Green
} else {
    Write-Host "❌ LlamaCpp installation failed" -ForegroundColor Red
    Write-Host "Trying alternative installation..." -ForegroundColor Yellow
    pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121
}

# Step 6: Verify Installation
Write-Host "`n[6/6] Verifying CUDA Setup..." -ForegroundColor Yellow

$verifyScript = @"
import sys
import torch

print('=' * 70)
print('CUDA Verification Report')
print('=' * 70)

# PyTorch
print(f'\nPyTorch version: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')

if torch.cuda.is_available():
    print(f'CUDA version: {torch.version.cuda}')
    print(f'GPU Device: {torch.cuda.get_device_name(0)}')
    print(f'GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB')
    
    # Test computation
    try:
        x = torch.randn(100, 100).cuda()
        y = torch.randn(100, 100).cuda()
        z = torch.mm(x, y)
        print('\n✅ GPU computation test: PASSED')
    except Exception as e:
        print(f'\n❌ GPU computation test: FAILED ({e})')
else:
    print('\n❌ CUDA is not available!')
    sys.exit(1)

# LlamaCpp
try:
    from llama_cpp import Llama
    print('✅ LlamaCpp imported successfully')
except Exception as e:
    print(f'❌ LlamaCpp import failed: {e}')

print('\n' + '=' * 70)
print('Setup complete! You can now use local models.')
print('=' * 70)
"@

$verifyScript | python

Write-Host "`n" + "=" * 70 -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "=" * 70 -ForegroundColor Cyan

Write-Host "`nNext Steps:" -ForegroundColor Yellow
Write-Host "1. Download Phi-2 model (see LOCAL_MODEL_SETUP.md)" -ForegroundColor White
Write-Host "2. Test the model with test scripts" -ForegroundColor White
Write-Host "3. Integrate with nanobot" -ForegroundColor White

Write-Host "`nNote: You may need to restart PowerShell for environment variables to take effect." -ForegroundColor Cyan
