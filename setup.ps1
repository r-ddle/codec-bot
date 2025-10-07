# Quick Setup Script for TXRails Bot

Write-Host "🎮 TXRails Discord Bot Setup" -ForegroundColor Cyan
Write-Host "================================`n" -ForegroundColor Cyan

# Check Python installation
Write-Host "Checking Python installation..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Python installed: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "❌ Python not found! Please install Python 3.8+" -ForegroundColor Red
    exit 1
}

# Check if .env exists
Write-Host "`nChecking for .env file..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "✅ .env file found" -ForegroundColor Green
}
else {
    Write-Host "⚠️  .env file not found. Creating template..." -ForegroundColor Yellow

    $envTemplate = @"
# Discord Bot Token (Required)
DISCORD_TOKEN=your_discord_token_here

# Neon PostgreSQL Database (Optional but recommended)
NEON_DATABASE_URL=postgres://user:pass@host/db?sslmode=require

# News API Key (Optional)
NEWS_API_KEY=your_news_api_key

# Welcome Channel ID (Optional)
WELCOME_CHANNEL_ID=your_channel_id
"@

    $envTemplate | Out-File -FilePath ".env" -Encoding UTF8
    Write-Host "📝 Created .env template - Please fill in your tokens!" -ForegroundColor Cyan
    Write-Host "   Edit the .env file with your Discord token" -ForegroundColor White
}

# Install dependencies
Write-Host "`nInstalling dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Dependencies installed successfully" -ForegroundColor Green
}
else {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Check if old tx.py exists
if (Test-Path "src/tx.py") {
    Write-Host "`n⚠️  Old tx.py file found!" -ForegroundColor Yellow
    Write-Host "   This should be renamed to prevent conflicts." -ForegroundColor White

    $rename = Read-Host "Rename tx.py to tx.py.backup? (y/n)"
    if ($rename -eq 'y') {
        Move-Item "src/tx.py" "src/tx.py.backup" -Force
        Write-Host "✅ Renamed tx.py to tx.py.backup" -ForegroundColor Green
    }
}

Write-Host "`n================================" -ForegroundColor Cyan
Write-Host "🎉 Setup Complete!" -ForegroundColor Green
Write-Host "================================`n" -ForegroundColor Cyan

Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Edit .env file with your Discord token" -ForegroundColor White
Write-Host "2. (Optional) Add Neon database URL for cloud backup" -ForegroundColor White
Write-Host "3. Run the bot: cd src; python bot.py" -ForegroundColor White
Write-Host "`n📚 For deployment guide, see DEPLOYMENT_GUIDE.md" -ForegroundColor Cyan
