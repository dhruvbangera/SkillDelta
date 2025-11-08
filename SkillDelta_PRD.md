# 🧩 SkillDelta – MVP Product Requirements Document (PRD)

**Version:** 1.0  
**Date:** November 2025  
**Prepared For:** BDPA Indianapolis Hackathon  
**Prepared By:** Dhruv Bangera  
**Deployment Target:** Vercel (Next.js v0 App Router compatible)

---

## 🎯 1. Product Overview

**SkillDelta** is a web-based AI platform that identifies and bridges job skill gaps.  
Users input their current technical and professional skills, select a target role, and instantly see:
- Which skills they already have  
- Which skills they lack  
- A personalized learning roadmap extracted from **roadmap.sh** data  
- Readiness metrics powered by OpenAI-based analysis  

The app empowers students and professionals to close their *skill delta* — the measurable difference between where they are and where they need to be.

---

## ⚙️ 2. MVP Objective

Deliver a **functional, interactive, and data-driven MVP** that:
1. Allows users to log in and save skill profiles  
2. Performs **gap analysis** between current and required skills  
3. Displays **interactive skill paths** from scraped roadmap.sh data  
4. Provides **OpenAI-based readiness feedback**  
5. Stores all user inputs and reports in Supabase  

---

## 🧠 3. Core MVP Features (Non-Negotiable)

### 3.1 Simple Skills Input System

**Purpose:** Collect user’s current technical skills in a structured format.

**Requirements:**
- **Interface:**
  - Searchable multi-select field with autocomplete for popular tech skills  
  - Add/remove skill tags  
  - Resume upload option → OpenAI extracts skills  
  - LinkedIn link field (optional)
- **Backend:**
  - OpenAI parses resume text → standardized skill names  
  - Normalizes aliases (“JS” → “JavaScript”)
- **Storage (Supabase):**
  - `user_skills` table linked to Clerk user ID

**Data Example:**
```json
{
  "user_id": "clerk_123",
  "skills": ["JavaScript", "HTML", "CSS", "React"]
}
```

---

### 3.2 Target Role Selection

**Purpose:** Define the goal position and required skills.

**Requirements:**
- **Predefined Role List (JSON):**
  - Web Developer  
  - Frontend Developer  
  - Data Analyst  
  - Software Engineer  
  - UX/UI Designer  
  - Cloud Associate  
- **Each Role Object Includes:**
```json
{
  "role": "Frontend Developer",
  "description": "Builds user interfaces and client-side applications.",
  "required_skills": ["HTML", "CSS", "JavaScript", "React", "Git"]
}
```
- **UI:**
  - Card or dropdown selection  
  - Displays description and key responsibilities
- **Storage (Supabase):**
  - `user_targets` table linking chosen role to user ID

---

### 3.3 Basic Gap Analysis Engine

**Purpose:** Identify missing skills and measure readiness.

**Requirements:**
- Compare user’s `skills` array vs. selected role’s `required_skills`
- Output:
  - Matched skills  
  - Missing skills  
  - Readiness % = `(Matched / Required) × 100`
- OpenAI generates short feedback sentence:  
  *“You’re 65% ready for a Frontend Developer role. Focus on React and Git next.”*

**Output Example:**
```json
{
  "matched_skills": ["HTML", "CSS", "JavaScript"],
  "missing_skills": ["React", "Git"],
  "readiness": 65,
  "ai_feedback": "You’re well on your way! Focus on React and Git next."
}
```

- **Storage (Supabase):**
  - `user_results` table (versioned by timestamp)

---

### 3.4 Learning Path Integration (roadmap.sh)

**Purpose:** Provide structured learning paths for each missing skill.

**Requirements:**
- **Scraping Layer (Server-Side):**
  - Script crawls relevant roadmap.sh pages (e.g., `/frontend`, `/java`, `/react`)  
    and extracts:
    - Skill title  
    - Resource links  
    - Subtopics  
    - Recommended order
- **Local Caching:**
  - Store parsed data in `roadmap_data` table or static JSON cache for speed
- **Frontend:**
  - For each missing skill, display:
    - “Skill Path” list matching roadmap.sh sequence  
    - Resource links with icons (docs, videos, tutorials)
- **No direct embedding** of roadmap.sh pages; fully internalized UI

**Example:**
```json
{
  "skill": "React",
  "topics": ["JSX", "Components", "Hooks", "Routing"],
  "resources": [
    {"title": "React Docs", "url": "https://react.dev"},
    {"title": "freeCodeCamp React Course", "url": "https://freecodecamp.org"}
  ]
}
```

---

### 3.5 Simple Results Dashboard

**Purpose:** Visualize skill readiness and learning recommendations.

**UI Components:**
- Readiness score (progress circle / bar)  
- Current vs. required skills comparison table  
- Missing skills list with progress indicators  
- Roadmap-based skill path display  
- Clickable resource links  

**Responsive Design:**
- TailwindCSS for layout  
- Works on both mobile and desktop  

---

## 🔐 4. Authentication (Clerk)

**Requirements:**
- User must sign in **before** accessing any feature  
- Integration: Clerk Next.js SDK  
- Supports:
  - Email/password  
  - Google OAuth  
- After login → redirect to `/dashboard`  
- Each authenticated user’s data (skills, results, targets) keyed by Clerk user ID

---

## 🧱 5. Data Model (Supabase)

| Table | Fields | Purpose |
|--------|---------|----------|
| `users` | `id`, `email`, `name` | Clerk-managed user reference |
| `user_skills` | `user_id`, `skills[]` | Stores user’s current skills |
| `user_targets` | `user_id`, `target_role`, `target_skills[]` | Tracks selected career goal |
| `user_results` | `user_id`, `readiness_score`, `matched_skills[]`, `missing_skills[]`, `feedback`, `created_at` | Stores gap analysis outputs |
| `roadmap_data` | `skill_name`, `topics[]`, `resources[]`, `source_url` | Stores parsed roadmap.sh data |

---

## 🤖 6. AI Integration (OpenAI)

| Function | Model | Description |
|-----------|--------|-------------|
| Skill Extraction | `gpt-4o-mini` | Extracts technical skills from uploaded resumes |
| Feedback Generation | `gpt-4o-mini` | Generates short natural feedback on readiness |
| Normalization | `gpt-4o-mini` | Converts informal skill names into canonical labels |

All keys stored in `.env.local` → injected into Vercel environment variables during deployment.

---

## 🧩 7. Architecture Overview

### Frontend (Vercel / Next.js)
- Pages: `/login`, `/dashboard`, `/skills`, `/role`, `/results`
- UI: TailwindCSS + Shadcn/UI
- Auth: Clerk  
- API Calls: `/api/analyze`, `/api/roadmap`, `/api/feedback`

### Backend (Next.js API Routes)
- `/api/analyze` → compares user vs. role skills  
- `/api/feedback` → calls OpenAI for readiness statement  
- `/api/roadmap` → fetches cached roadmap.sh data  
- Supabase client handles persistent data

### Database (Supabase)
- Tables as defined above  
- Row-level security enabled for each Clerk user

---

## 🎨 8. Design Principles

| Aspect | Direction |
|--------|------------|
| Theme | Modern SaaS (inspired by Notion / Linear) |
| Color Palette | Deep blue (#1C2C4C), cyan accents (#37C7DA), neutral backgrounds |
| Typography | Inter / Satoshi |
| Icons | Lucide / Heroicons |
| Animations | Framer Motion (subtle transitions only) |

---

## ✅ 9. Acceptance Criteria (MVP Completion Checklist)

| Module | Acceptance Criteria |
|---------|----------------------|
| Skills Input | Users can add/edit/remove skills; resume parsing works; data saved to Supabase |
| Role Selection | User can pick from predefined list; selection stored |
| Gap Analysis | Missing skills + readiness % calculated and shown |
| Roadmap Integration | Missing skills display structured learning paths (from roadmap.sh data) |
| Dashboard | Displays readiness meter, lists skills, links to resources |
| Auth | Clerk login/signup functional; each user sees only their own data |
| Persistence | All data saved and retrievable from Supabase |
| Deployment | Runs on Vercel with working environment vars |

---

## 🚀 10. Future Enhancements (Post-MVP)

| Feature | Description |
|----------|--------------|
| AI Chat Assistant | Conversational learning recommendations |
| Progress Tracker | Users can mark completed topics |
| Dynamic Roles | Fetch real-time job role data from APIs (Indeed, LinkedIn) |
| Gamification | Badges and levels for completing paths |
| PDF Export | Generate career readiness reports |

---

## 🧭 11. Milestone Plan

| Phase | Deliverable | Owner | Deadline |
|--------|--------------|--------|-----------|
| Phase 1 | Clerk + Supabase setup | Dev | Day 1 |
| Phase 2 | Skills input + role selection UI | Frontend | Day 1–2 |
| Phase 3 | Gap analysis engine + OpenAI feedback | Backend | Day 2 |
| Phase 4 | Roadmap data integration | Backend | Day 3 |
| Phase 5 | Dashboard & responsive UI polish | Frontend | Day 3 |
| Phase 6 | Testing & Vercel deployment | Team | Day 4 |

---

### Final Output Summary

> A live, user-authenticated **SkillDelta MVP** hosted on Vercel, using Supabase for storage and OpenAI for intelligence, providing skill gap detection and structured learning paths derived from roadmap.sh — meeting all BDPA non-negotiable MVP requirements.
