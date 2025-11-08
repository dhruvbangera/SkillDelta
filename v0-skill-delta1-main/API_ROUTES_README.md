# Next.js API Routes Documentation

This document describes the Next.js API routes that integrate the Flask backend logic into the frontend.

## Overview

All API routes are:
- **Clerk-authenticated** - Require valid session token
- **AI-powered** - Use OpenAI GPT-4o for all AI operations
- **JSON-based storage** - Store data in JSON files (no database)
- **Error-handled** - Include retry logic and standardized error responses

## Environment Variables

Required environment variables in `.env.local`:

```env
# OpenAI API Key
OPENAI_API_KEY=sk-proj-...

# Clerk Authentication
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
```

## API Endpoints

### 1. POST /api/skills/extract

Extract skills from uploaded resume files.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body:
  - `files`: File[] (PDF, DOCX, TXT - max 16MB)
  - `jobId`: string (optional) - For proficiency calculation
  - `jobData`: string (optional) - JSON string of job data for proficiency

**Response:**
```json
{
  "extractedSkills": ["Python", "React", "TypeScript", ...],
  "proficiency": {
    "Python": 4.5,
    "React": 3.0
  },
  "resumeId": "1234567890_123456",
  "debug_ai_responses": {
    "skill_extraction": "...",
    "skill_matching": "...",
    "proficiency_calculation": "..."
  }
}
```

**Error Responses:**
- `401`: Unauthorized (invalid Clerk token)
- `400`: Invalid file type or size
- `500`: AI extraction failed

---

### 2. POST /api/match/skills

Match user skills to job requirements.

**Request:**
```json
{
  "userSkills": ["Python", "React", ...],
  "userSkillsWithProficiency": [
    {"name": "Python", "proficiency": 4.5},
    ...
  ],
  "resumeText": "...",  // Optional
  "jobId": "1",  // OR
  "jobData": {
    "jobTitle": "...",
    "companyName": "...",
    "jobDescription": "...",
    "requiredSkills": [...]
  }
}
```

**Response:**
```json
{
  "matchPercentage": 72.3,
  "currentSkills": [
    {
      "name": "Python",
      "level": "Advanced",
      "matchPercentage": 78.5
    },
    ...
  ],
  "missingSkills": [
    {
      "name": "Docker",
      "level": "Required",
      "matchPercentage": 15.0
    },
    ...
  ],
  "allSkills": [...],
  "reasoning": {
    "expandedDescription": "...",
    "raw_ai_response": "..."
  }
}
```

**Error Responses:**
- `401`: Unauthorized
- `400`: Missing required fields
- `404`: Job not found
- `500`: AI matching failed

---

### 3. POST /api/learning-path/generate

Generate personalized learning path for missing skills.

**Request:**
```json
{
  "missingSkills": ["Docker", "GraphQL", ...],
  "currentSkills": ["Python", "React", ...],  // Optional
  "jobContext": {
    "jobTitle": "...",
    "jobDescription": "..."  // Optional
  }
}
```

**Response:**
```json
{
  "steps": [
    {
      "id": "1",
      "title": "Master Docker",
      "description": "Learn containerization basics...",
      "duration": "4 weeks",
      "difficulty": "intermediate",
      "resources": [
        "Docker Official Tutorial",
        "Containerization Essentials",
        ...
      ]
    },
    ...
  ],
  "debug_ai_response": "..."
}
```

**Error Responses:**
- `401`: Unauthorized
- `400`: Missing missingSkills
- `500`: AI generation failed

---

### 4. GET /api/jobs

Get list of available jobs.

**Query Parameters:**
- `limit`: number (default: 10) - Number of jobs to return
- `offset`: number (default: 0) - Pagination offset
- `search`: string (optional) - Search term

**Response:**
```json
{
  "jobs": [
    {
      "id": "0",
      "jobTitle": "Senior Full Stack Developer",
      "companyName": "Tech Corp",
      "jobDescription": "...",
      "url": "https://...",
      "requiredSkills": [
        {"name": "Python", "level": "Required"},
        ...
      ]
    },
    ...
  ],
  "total": 50,
  "limit": 10,
  "offset": 0
}
```

**Error Responses:**
- `401`: Unauthorized
- `500`: Failed to load jobs

---

### 5. POST /api/jobs

Save a job from Chrome extension.

**Request:**
```json
{
  "jobTitle": "...",
  "companyName": "...",
  "jobDescription": "...",
  "url": "https://...",
  "requiredSkills": [
    {"name": "Python", "level": "Required"},
    ...
  ]
}
```

**Response:**
```json
{
  "success": true,
  "job": {
    "id": "saved_1234567890",
    "userId": "user_...",
    "jobTitle": "...",
    "companyName": "...",
    "jobDescription": "...",
    "url": "...",
    "requiredSkills": [...],
    "saved_at": "2025-01-08T12:34:56.789Z"
  }
}
```

**Error Responses:**
- `401`: Unauthorized
- `400`: Missing required fields
- `500`: Failed to save job

---

### 6. POST /api/job/analyze

Analyze job listing and extract required skills.

**Request:**
```json
{
  "jobId": "1",  // OR
  "jobData": {
    "jobTitle": "...",
    "companyName": "...",
    "jobDescription": "...",
    "requiredSkills": [...]
  },  // OR
  "jobUrl": "https://..."  // Not yet implemented
}
```

**Response:**
```json
{
  "jobId": "1",
  "jobTitle": "Senior Full Stack Developer",
  "companyName": "Tech Corp",
  "jobDescription": "...",
  "expandedDescription": "...",  // AI-expanded
  "requiredSkills": [
    {"name": "Python", "level": "Required"},
    ...
  ],
  "debug_ai_response": "..."
}
```

**Error Responses:**
- `401`: Unauthorized
- `400`: Missing jobId or jobData
- `404`: Job not found
- `500`: AI analysis failed
- `501`: Job URL fetching not implemented

---

## Data Storage

All data is stored in JSON files in the `data/` directory:

- `data/resumes.json` - Processed resumes with extracted skills
- `data/saved_jobs.json` - Jobs saved from Chrome extension
- `data/roadmaps_role_skill.json` - Roadmap skills database (from parent directory)
- `data/linkedin_jobs_processed.json` - LinkedIn jobs (from parent directory)

## Authentication

All endpoints require Clerk authentication. The session token is automatically validated using `@clerk/nextjs/server`.

**How it works:**
1. Frontend sends requests with Clerk session token (automatically handled by Clerk)
2. Backend validates token using `validateAuth()`
3. If invalid, returns `401 Unauthorized`
4. If valid, extracts `userId` and associates data with user

## Error Handling

All endpoints return standardized error responses:

```json
{
  "error": "Error message",
  "code": 500,
  "details": "Additional error details"
}
```

## AI Integration

All AI operations use OpenAI GPT-4o with:
- **Retry logic**: Up to 2 retries on failure
- **Debug responses**: Raw AI responses included in responses
- **Temperature**: 0.5 for balanced creativity/consistency
- **Token limits**: Appropriate limits per operation

## File Parsing

Supported file types:
- **PDF**: Using `pdf-parse`
- **DOCX**: Using `mammoth`
- **TXT**: Multiple encoding support

File size limit: **16MB**

## Proficiency to Level Conversion

AI proficiency scores (1-5) are converted to levels:
- `4.5-5.0` → `"Advanced"`
- `3.5-4.49` → `"Intermediate"`
- `2.5-3.49` → `"Basic"`
- `<2.5` → `"Beginner"`

## Development Setup

1. Install dependencies:
```bash
npm install
# or
pnpm install
```

2. Set up environment variables in `.env.local`

3. Ensure data directories exist:
```bash
mkdir -p data uploads
```

4. Run development server:
```bash
npm run dev
```

## Production Deployment

For Vercel deployment:
1. Set environment variables in Vercel dashboard
2. Ensure `data/` and `uploads/` directories are writable (may need to use external storage)
3. Consider using Vercel Blob Storage or similar for file storage in production

## Notes

- **Job URL fetching**: Not yet implemented (returns 501)
- **LinkedIn profile parsing**: Not yet implemented
- **Database migration**: Currently using JSON files; can be migrated to database later
- **File storage**: Files are stored temporarily in `uploads/` directory

