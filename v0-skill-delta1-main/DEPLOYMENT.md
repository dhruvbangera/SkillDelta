# Deployment Guide

## Vercel Deployment

### Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **GitHub Repository**: Push your code to GitHub
3. **Environment Variables**: Prepare your API keys

### Step 1: Install Vercel CLI (Optional)

```bash
npm install -g vercel
```

### Step 2: Set Up Environment Variables

Before deploying, you need to set these environment variables in Vercel:

1. Go to your Vercel project settings
2. Navigate to "Environment Variables"
3. Add the following:

```
OPENAI_API_KEY=sk-proj-...
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
```

### Step 3: Deploy via Vercel Dashboard

1. **Connect Repository**:
   - Go to [vercel.com/new](https://vercel.com/new)
   - Import your GitHub repository
   - Select the `v0-skill-delta1-main` directory (or root if it's the only project)

2. **Configure Project**:
   - Framework Preset: Next.js (auto-detected)
   - Root Directory: `v0-skill-delta1-main` (if needed)
   - Build Command: `npm run build`
   - Output Directory: `.next` (default)

3. **Add Environment Variables**:
   - Add all required environment variables (see Step 2)

4. **Deploy**:
   - Click "Deploy"
   - Wait for build to complete

### Step 4: Deploy via CLI (Alternative)

```bash
cd v0-skill-delta1-main
vercel login
vercel
```

Follow the prompts:
- Set up and deploy? **Yes**
- Which scope? **Your account**
- Link to existing project? **No** (first time) or **Yes** (subsequent)
- What's your project's name? **skilldelta** (or your choice)
- In which directory is your code located? **./**

Then add environment variables:
```bash
vercel env add OPENAI_API_KEY
vercel env add NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
vercel env add CLERK_SECRET_KEY
```

Redeploy:
```bash
vercel --prod
```

### Step 5: Configure Data Storage

**Important**: Vercel serverless functions have read-only filesystem. You have two options:

#### Option A: Use Vercel Blob Storage (Recommended)

1. Install Vercel Blob:
```bash
npm install @vercel/blob
```

2. Update API routes to use Blob storage instead of local filesystem

#### Option B: Use External Database/Storage

- Use MongoDB, PostgreSQL, or similar for data storage
- Use AWS S3, Cloudinary, or similar for file storage

#### Option C: Use Vercel KV (Redis) for JSON Storage

1. Enable Vercel KV in your project
2. Update `data-utils.ts` to use KV instead of filesystem

### Step 6: Update Clerk Configuration

1. Go to [Clerk Dashboard](https://dashboard.clerk.com)
2. Add your Vercel deployment URL to allowed origins
3. Update redirect URLs if needed

### Step 7: Test Deployment

1. Visit your Vercel deployment URL
2. Test authentication (Clerk login)
3. Test file upload
4. Test API endpoints

## Environment Variables Reference

### Required for Production

```env
# OpenAI
OPENAI_API_KEY=sk-proj-...

# Clerk Authentication
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_...
CLERK_SECRET_KEY=sk_live_...

# Optional: API URL (if different from default)
NEXT_PUBLIC_API_URL=https://your-app.vercel.app
```

### Development vs Production

- **Development**: Use `.env.local` file
- **Production**: Set in Vercel dashboard

## Troubleshooting

### Build Errors

1. **Module not found**: Run `npm install` locally first
2. **Type errors**: Run `npm run build` locally to catch errors
3. **API route errors**: Check function timeout settings (max 60s on Hobby plan)

### Runtime Errors

1. **File system errors**: Use external storage (see Step 5)
2. **Environment variable errors**: Verify all variables are set in Vercel
3. **Clerk auth errors**: Check Clerk dashboard configuration

### Data Storage Issues

Since Vercel serverless functions have read-only filesystem (except `/tmp`):

1. **For file uploads**: Use Vercel Blob or external storage
2. **For JSON storage**: Use Vercel KV, MongoDB, or similar
3. **For temporary files**: Use `/tmp` directory (limited to function execution)

## Post-Deployment Checklist

- [ ] Environment variables set in Vercel
- [ ] Clerk configured with production URLs
- [ ] Data storage configured (Blob/KV/Database)
- [ ] File uploads working
- [ ] API endpoints responding
- [ ] Authentication working
- [ ] Error handling tested
- [ ] Performance acceptable

## Monitoring

- Check Vercel dashboard for:
  - Function execution logs
  - Error rates
  - Response times
  - Build logs

## Custom Domain (Optional)

1. Go to Vercel project settings
2. Navigate to "Domains"
3. Add your custom domain
4. Configure DNS as instructed

