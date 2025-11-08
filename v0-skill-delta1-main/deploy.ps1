# PowerShell deployment script for Vercel

Write-Host "🚀 Starting deployment process..." -ForegroundColor Cyan

# Check if Vercel CLI is installed
try {
    $null = Get-Command vercel -ErrorAction Stop
    Write-Host "✅ Vercel CLI found" -ForegroundColor Green
} catch {
    Write-Host "📦 Installing Vercel CLI..." -ForegroundColor Yellow
    npm install -g vercel
}

# Check if logged in
try {
    $null = vercel whoami 2>&1
    Write-Host "✅ Logged in to Vercel" -ForegroundColor Green
} catch {
    Write-Host "🔐 Please log in to Vercel..." -ForegroundColor Yellow
    vercel login
}

# Build the project first to check for errors
Write-Host "🔨 Building project..." -ForegroundColor Cyan
npm run build

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Build failed! Please fix errors before deploying." -ForegroundColor Red
    exit 1
}

Write-Host "✅ Build successful!" -ForegroundColor Green

# Deploy to Vercel
Write-Host "🚀 Deploying to Vercel..." -ForegroundColor Cyan
vercel --prod

Write-Host "✅ Deployment complete!" -ForegroundColor Green
Write-Host "📝 Don't forget to set environment variables in Vercel dashboard:" -ForegroundColor Yellow
Write-Host "   - OPENAI_API_KEY" -ForegroundColor White
Write-Host "   - NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY" -ForegroundColor White
Write-Host "   - CLERK_SECRET_KEY" -ForegroundColor White

