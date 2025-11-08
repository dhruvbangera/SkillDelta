# Quick Deployment Guide

## Option 1: Deploy via Vercel Dashboard (Recommended)

1. **Push to GitHub** (if not already):
   ```bash
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```

2. **Go to Vercel Dashboard**:
   - Visit [vercel.com/new](https://vercel.com/new)
   - Click "Import Git Repository"
   - Select your repository
   - If the repo is in a subdirectory, set Root Directory to `v0-skill-delta1-main`

3. **Configure Project**:
   - Framework: Next.js (auto-detected)
   - Build Command: `npm run build` (default)
   - Output Directory: `.next` (default)

4. **Add Environment Variables**:
   Click "Environment Variables" and add:
   ```
   OPENAI_API_KEY=sk-proj-...
   NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
   CLERK_SECRET_KEY=sk_test_...
   ```

5. **Deploy**:
   - Click "Deploy"
   - Wait for build to complete (~2-5 minutes)

## Option 2: Deploy via CLI

1. **Install Vercel CLI**:
   ```bash
   npm install -g vercel
   ```

2. **Navigate to project**:
   ```bash
   cd v0-skill-delta1-main
   ```

3. **Install dependencies** (with legacy peer deps):
   ```bash
   npm install --legacy-peer-deps
   ```

4. **Login to Vercel**:
   ```bash
   vercel login
   ```

5. **Deploy**:
   ```bash
   vercel
   ```
   Follow prompts, then:
   ```bash
   vercel --prod
   ```

6. **Set Environment Variables**:
   ```bash
   vercel env add OPENAI_API_KEY
   vercel env add NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
   vercel env add CLERK_SECRET_KEY
   ```

7. **Redeploy with env vars**:
   ```bash
   vercel --prod
   ```

## Important Notes

### ⚠️ Data Storage Limitation

Vercel serverless functions have a **read-only filesystem** (except `/tmp`). 

**Current Implementation**: Uses `/tmp/data` for writes in production, but this is **temporary** and will be lost between function invocations.

**For Production**, you should:
- Use **Vercel KV** (Redis) for JSON storage
- Use **Vercel Blob** for file storage
- Or use external database (MongoDB, PostgreSQL, etc.)

### Environment Variables

Make sure to set these in Vercel dashboard:
- `OPENAI_API_KEY` - Your OpenAI API key
- `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` - Clerk publishable key
- `CLERK_SECRET_KEY` - Clerk secret key

### Clerk Configuration

After deployment:
1. Go to [Clerk Dashboard](https://dashboard.clerk.com)
2. Add your Vercel URL to allowed origins
3. Update redirect URLs if needed

## Testing Deployment

1. Visit your Vercel URL
2. Test authentication (login with Clerk)
3. Test file upload (may need storage fix)
4. Test API endpoints

## Troubleshooting

### Build Fails
- Check Node.js version (should be 18.x or 20.x)
- Check for TypeScript errors
- Check for missing dependencies

### Runtime Errors
- Check environment variables are set
- Check function logs in Vercel dashboard
- Verify Clerk configuration

### File Upload Errors
- Vercel serverless has read-only filesystem
- Need to use external storage (Blob, S3, etc.)

## Next Steps After Deployment

1. ✅ Set up proper data storage (KV/Blob/Database)
2. ✅ Configure Clerk production keys
3. ✅ Test all features
4. ✅ Set up monitoring
5. ✅ Configure custom domain (optional)

