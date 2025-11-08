# Exact GPT Prompts Being Sent

This document contains the exact prompts being sent to OpenAI GPT-4o-mini in the resume parser system.

---

## 1. Job Description Expansion Prompt

**Function**: `expand_job_description()`  
**Model**: `gpt-4o-mini`  
**Temperature**: `0.4`  
**Max Tokens**: `800`

### System Message
```
You are a technical recruiter expanding job descriptions to clarify experience requirements. Provide detailed, specific information about skill proficiency expectations.
```

### User Prompt
```
You are a technical recruiter writing a detailed job description. Expand and elaborate on the following job posting to provide more substance about:
- Required experience levels for each skill
- Specific use cases and contexts where skills are needed
- Years of experience expected
- Project complexity and scale
- Team collaboration and leadership aspects
- Technical depth and expertise required

Job Title: {job_title}
Company: {company_name}

Original Description:
{job_description[:3000]}

Required Skills: {skills_list}

Expand the description to be more specific about:
1. What level of proficiency is needed for each skill (junior/mid/senior)
2. What kind of projects or work will use these skills
3. How many years of experience is expected
4. What specific tasks or responsibilities require these skills
5. Any advanced or specialized knowledge needed

Return an expanded job description (300-500 words) that provides more detail about experience requirements and skill expectations. Be specific and realistic.
```

---

## 2. Skill Extraction Prompt

**Function**: `extract_skills_with_openai()`  
**Model**: `gpt-4o-mini`  
**Temperature**: `0.3`  
**Max Tokens**: `2000`

### System Message
```
You are a technical recruiter extracting skills from resumes. Return only a comma-separated list of technical skills, tools, frameworks, and programming languages. Do not include explanations or formatting.
```

### User Prompt
```
Extract all technical skills, programming languages, frameworks, tools, libraries, and technologies mentioned in the following resume text.

Include:
- Programming languages (Python, Java, JavaScript, etc.)
- Frameworks (React, Django, Spring, etc.)
- Tools (Docker, Git, AWS, etc.)
- Libraries (Pandas, NumPy, etc.)
- Databases (MySQL, MongoDB, etc.)
- Cloud platforms (AWS, Azure, GCP, etc.)
- Testing frameworks (Jest, Cypress, etc.)
- Build tools (Webpack, Maven, etc.)
- Any other technical skills or technologies

Be thorough and extract ALL technical skills mentioned, including:
- HTML, CSS, C++, Vercel, Jest, Cypress, SLAM
- Any technologies mentioned in projects, work experience, or education
- Both explicit mentions and implied technologies

Return ONLY a comma-separated list of skills, nothing else. Example format:
Python, React, JavaScript, Docker, AWS, Git, HTML, CSS, C++, Vercel, Jest, Cypress

Resume text:
{resume_text[:20000]}
```

---

## 3. Proficiency Calculation Prompt

**Function**: `calculate_skill_proficiency()`  
**Model**: `gpt-4o-mini`  
**Temperature**: `0.45`  
**Max Tokens**: `2000`  
**Response Format**: `json_object`

### System Message
```
You are a technical recruiter analyzing resume proficiency against job requirements. Return only valid JSON with skill names and proficiency scores (1-5).
```

### User Prompt
```
Analyze the following resume text and rate the proficiency level (1-5) for each technical skill mentioned.

Proficiency Scale:
1 = Mentioned only briefly, no evidence of experience, or insufficient for job requirements
2 = Basic familiarity, mentioned in passing or education, minimal practical experience
3 = Some experience, used in projects or work, meets basic job requirements
4 = Strong experience, significant usage and understanding, exceeds basic requirements
5 = Expert level, deep expertise, leadership, or extensive experience, exceeds job requirements

For each skill, consider:
- How extensively it's mentioned in the resume
- Context of usage (projects, work experience, education)
- Years of experience if mentioned
- Depth of description and complexity of projects
- Relevance to job requirements (if job context provided)
- Quality and impact of work using the skill

{job_context}

PROFICIENCY COMPARISON LOGIC:
When job context is provided, compare required vs actual proficiency:
- If job requires skill at level X/5 and candidate has Y/5:
  * Y >= X: Score should reflect meeting/exceeding requirements
  * Y < X: Score should reflect gap (but still give credit for having the skill)
- Example: Job requires Python 4/5, candidate has 3/5 → Rate candidate's Python as 3/5 (they have it, but below requirement)
- Example: Job requires SQL 2/5, candidate has 5/5 → Rate candidate's SQL as 5/5 (overqualified, but still excellent)

Return a JSON object with skill names as keys and proficiency scores (1-5) as values.
Example: {"Python": 4, "React": 3, "Docker": 2}

Skills to evaluate: {skills_list}

Resume text:
{resume_text[:15000]}

Return ONLY valid JSON, no explanations.
```

**Note**: `{job_context}` is conditionally included and contains:
```
JOB REQUIREMENTS CONTEXT:
Job Description: {job_description}
Required Skills: {job_skills_list}

When rating proficiency, consider how well the candidate's experience matches the job requirements. A skill that is critical for the job should be rated higher if the candidate has strong experience, and lower if they lack relevant experience.
```

---

## 4. Job Matching Prompt (Main Comparison)

**Function**: `compare_resume_to_job_ai()`  
**Model**: `gpt-4o-mini`  
**Temperature**: `0.45`  
**Max Tokens**: `5000`  
**Response Format**: `json_object`

### System Message
```
You are a technical recruiter. Analyze skill matches comprehensively using the FULL 0-100% range. Consider names, keywords, topics, proficiency comparison, partial matches, and alignment with expanded job description requirements. Return only valid JSON with nuanced percentage scores.
```

### User Prompt
```
You are a technical recruiter comparing a candidate's resume to a job requirement.

Analyze how well the candidate's skills match the job requirements. Consider:
1. Skill names (exact and similar matches)
2. Keywords and related terms
3. Topics and concepts
4. Proficiency levels (a skill with proficiency 5/5 is better than 2/5)
5. Context and experience depth from the resume
6. How well the candidate's experience matches the EXPANDED job description requirements
7. Partial matches for related skills (e.g., "React" when job needs "React + Redux" = 60-70%)

CRITICAL INSTRUCTIONS FOR SCORING:
- Use the FULL 0-100% range, NOT binary (0%, 50%, 100%)
- Provide nuanced scores: 12%, 23%, 47%, 67%, 78%, 84%, 93%, etc.
- Assign partial credit for related or partially covered skills
- Compare required vs actual proficiency to determine match
- Consider skill depth, context alignment, and relevance
- Avoid rounding or clustering results near 0/50/100
- Most realistic scores should be between 10-90%
- Partial matches: If job needs "React with Redux" and candidate has "React" → 60-70%
- Domain overlap: If job needs "Python for ML" and candidate has "Python for web" → 40-50%

PROFICIENCY COMPARISON LOGIC:
For each job skill, compare:
- Required proficiency level (from expanded job description)
- Candidate's actual proficiency (from resume analysis)
- Calculate match percentage based on this comparison
- Example: Job requires Python 4/5, candidate has 3/5 → 75% match
- Example: Job requires Python 2/5, candidate has 5/5 → 100% match (overqualified but excellent)
- Example: Job requires Python 4/5, candidate has 2/5 → 50% match (has skill but below requirement)
- Example: Job requires Python 4/5, candidate has 4/5 → 95% match (perfect alignment)

For EACH job skill, provide:
- A match percentage (0-100%) indicating how well the candidate matches this requirement
- Reasoning based on skills, keywords, topics, proficiency comparison, and how their experience aligns with the job description
- Matched resume skills that contributed to this match

Return a JSON object with this structure:
{
  "job_skills": [
    {
      "skill_name": "Python",
      "match_percentage": 78.5,
      "matched_resume_skills": ["Python", "Django"],
      "reasoning": "Candidate has Python with proficiency 4/5. The expanded job description requires 3+ years of Python for backend development at proficiency 4/5. The candidate's resume shows 4 years of Python experience with Django, closely matching the requirements. However, the job emphasizes API development which the candidate has experience with, resulting in a strong 78.5% match."
    }
  ],
  "overall_match_percentage": 72.3
}

EXPANDED JOB DESCRIPTION (provides detailed requirements):
{expanded_description}

Job Skills List:
{job_skills_str}

Candidate Skills (with proficiency):
{resume_skills_str}

Resume Context (first 15000 chars):
{resume_text[:15000]}

IMPORTANT: 
- When calculating match percentages, heavily weight how well the candidate's experience (from resume context) aligns with the specific requirements mentioned in the EXPANDED JOB DESCRIPTION
- A candidate with high proficiency in a skill that matches the job's specific use cases should score higher than someone with the same skill but different experience context
- Use the FULL percentage range - avoid binary thinking
- Provide detailed reasoning that explains the specific percentage score

Return ONLY valid JSON, no explanations.
```

---

## Variable Substitutions

The prompts use the following variable substitutions:

- `{job_title}` - Job title from job data
- `{company_name}` - Company name from job data
- `{job_description[:3000]}` - First 3000 characters of original job description
- `{skills_list}` - Comma-separated list of required skills (up to 20)
- `{job_description}` - Full expanded job description (not truncated)
- `{job_skills_list}` - List of required skills for proficiency context
- `{skills_list}` - Comma-separated list of extracted skills to evaluate (up to 50)
- `{resume_text[:15000]}` - First 15000 characters of resume text
- `{resume_text[:20000]}` - First 20000 characters of resume text (for skill extraction)
- `{expanded_description}` - Full expanded job description
- `{job_skills_str}` - Formatted list of job skills with topics
- `{resume_skills_str}` - Formatted list of candidate skills with proficiency scores

---

## Key Instructions Highlighted

The most important instructions in the job matching prompt are:

1. **Use FULL 0-100% range** - explicitly stated multiple times
2. **Provide nuanced scores** - examples given (12%, 23%, 47%, etc.)
3. **Avoid binary thinking** - explicitly warned against
4. **Most scores should be 10-90%** - guidance on distribution
5. **Proficiency comparison logic** - detailed examples provided
6. **Partial match recognition** - examples for related skills

These instructions are designed to prevent binary responses and encourage comprehensive percentage-based scoring.

