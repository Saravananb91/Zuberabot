# Mistral-7B Configuration Script for Windows
# Automates Ollama setup and model download

param(
    [switch]$SkipModelDownload,
    [switch]$TestOnly
)

Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "Mistral-7B Configuration for Financial Chatbot" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan

# Step 1: Check Ollama Installation
Write-Host "`n[1/5] Checking Ollama installation..." -ForegroundColor Yellow

try {
    $ollamaVersion = ollama --version
    Write-Host "✅ Ollama installed: $ollamaVersion" -ForegroundColor Green
}
catch {
    Write-Host "❌ Ollama not found!" -ForegroundColor Red
    Write-Host "Install from: https://ollama.ai/download" -ForegroundColor Yellow
    exit 1
}

# Step 2: Check if Ollama is running
Write-Host "`n[2/5] Checking Ollama service..." -ForegroundColor Yellow

try {
    $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✅ Ollama service is running" -ForegroundColor Green
}
catch {
    Write-Host "⚠️  Ollama service not running. Starting..." -ForegroundColor Yellow
    Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 3
    Write-Host "✅ Ollama service started" -ForegroundColor Green
}

# Step 3: Set Ollama Environment Variables for GTX 1650
Write-Host "`n[3/5] Configuring Ollama for GTX 1650..." -ForegroundColor Yellow

# Optimize for 4GB VRAM
[Environment]::SetEnvironmentVariable("OLLAMA_NUM_GPU", "35", "User")  # 35 layers for Mistral-7B
[Environment]::SetEnvironmentVariable("OLLAMA_MAX_LOADED_MODELS", "1", "User")
[Environment]::SetEnvironmentVariable("OLLAMA_NUM_PARALLEL", "1", "User")
[Environment]::SetEnvironmentVariable("OLLAMA_KEEP_ALIVE", "24h", "User")

Write-Host "✅ Environment variables configured:" -ForegroundColor Green
Write-Host "  - OLLAMA_NUM_GPU: 35 (use 35 GPU layers)" -ForegroundColor Gray
Write-Host "  - OLLAMA_MAX_LOADED_MODELS: 1 (keep 1 model in memory)" -ForegroundColor Gray
Write-Host "  - OLLAMA_NUM_PARALLEL: 1 (process 1 request at a time)" -ForegroundColor Gray
Write-Host "  - OLLAMA_KEEP_ALIVE: 24h (keep model loaded)" -ForegroundColor Gray

# Step 4: Pull Mistral-7B Model
if (-not $SkipModelDownload) {
    Write-Host "`n[4/5] Downloading Mistral-7B model..." -ForegroundColor Yellow
    Write-Host "This will download ~4.1GB. Please wait..." -ForegroundColor Cyan
    
    $modelName = "mistral:7b-instruct-q4_K_M"
    
    # Check if model already exists
    $existingModels = ollama list | Out-String
    
    if ($existingModels -match $modelName) {
        Write-Host "✅ Model already downloaded: $modelName" -ForegroundColor Green
    }
    else {
        Write-Host "Downloading $modelName..." -ForegroundColor Cyan
        ollama pull $modelName
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Model downloaded successfully" -ForegroundColor Green
        }
        else {
            Write-Host "❌ Model download failed" -ForegroundColor Red
            exit 1
        }
    }
}
else {
    Write-Host "`n[4/5] Skipping model download (--SkipModelDownload)" -ForegroundColor Yellow
}

# Step 5: Test the Model
if (-not $TestOnly) {
    Write-Host "`n[5/5] Testing model..." -ForegroundColor Yellow
    
    $testQuery = "What is compound interest? Answer in one sentence."
    
    Write-Host "Test query: $testQuery" -ForegroundColor Cyan
    Write-Host "Waiting for response..." -ForegroundColor Gray
    
    $startTime = Get-Date
    $response = ollama run mistral:7b-instruct-q4_K_M $testQuery --verbose 2>&1
    $endTime = Get-Date
    $duration = ($endTime - $startTime).TotalSeconds
    
    Write-Host "`nResponse:" -ForegroundColor Green
    Write-Host $response -ForegroundColor White
    
    Write-Host "`n📊 Response time: $($duration.ToString('0.00'))s" -ForegroundColor Cyan
    
    if ($duration -lt 5) {
        Write-Host "✅ Performance is good!" -ForegroundColor Green
    }
    elseif ($duration -lt 10) {
        Write-Host "⚠️  Performance is acceptable" -ForegroundColor Yellow
    }
    else {
        Write-Host "❌ Performance is slow. Check GPU configuration." -ForegroundColor Red
    }
}

# Summary
Write-Host "`n" + "=" * 70 -ForegroundColor Cyan
Write-Host "Configuration Complete!" -ForegroundColor Green
Write-Host "=" * 70 -ForegroundColor Cyan

Write-Host "`nNext Steps:" -ForegroundColor Yellow
Write-Host "1. Run Python test: python test_mistral_financial.py" -ForegroundColor White
Write-Host "2. Review setup guide: MISTRAL_SETUP.md" -ForegroundColor White
Write-Host "3. Integrate with nanobot agent loop" -ForegroundColor White

Write-Host "`n💡 Quick test command:" -ForegroundColor Cyan
Write-Host "ollama run mistral:7b-instruct-q4_K_M 'Explain mutual funds briefly'" -ForegroundColor Gray

Write-Host "`n⚠️  Note: Restart PowerShell for environment variables to take full effect" -ForegroundColor Yellow
