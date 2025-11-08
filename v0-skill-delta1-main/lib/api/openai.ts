/**
 * OpenAI API Utilities
 * Handles all AI operations with retry logic and error handling
 */

import OpenAI from 'openai';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY
});

if (!process.env.OPENAI_API_KEY) {
  console.warn('WARNING: OPENAI_API_KEY not found in environment variables');
}

export interface AIResponse<T> {
  data: T;
  rawResponse: string;
  error?: string;
}

/**
 * Call OpenAI API with retry logic
 */
async function callOpenAI(
  messages: OpenAI.Chat.Completions.ChatCompletionMessageParam[],
  options: {
    model?: string;
    temperature?: number;
    maxTokens?: number;
    retries?: number;
  } = {}
): Promise<AIResponse<string>> {
  const {
    model = 'gpt-4o',
    temperature = 0.5,
    maxTokens = 5000,
    retries = 2
  } = options;

  let lastError: Error | null = null;

  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const response = await openai.chat.completions.create({
        model,
        messages,
        temperature,
        max_tokens: maxTokens
      });

      const content = response.choices[0]?.message?.content || '';
      
      return {
        data: content,
        rawResponse: JSON.stringify(response, null, 2)
      };
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error));
      console.error(`OpenAI API call failed (attempt ${attempt + 1}/${retries + 1}):`, lastError);
      
      if (attempt < retries) {
        // Wait before retry (exponential backoff)
        await new Promise(resolve => setTimeout(resolve, Math.pow(2, attempt) * 1000));
      }
    }
  }

  return {
    data: '',
    rawResponse: '',
    error: `OpenAI API call failed after ${retries + 1} attempts: ${lastError?.message || 'Unknown error'}`
  };
}

/**
 * Extract skills from resume text using AI
 */
export async function extractSkillsWithAI(
  resumeText: string,
  roadmapContext?: string
): Promise<AIResponse<string[]>> {
  const context = roadmapContext 
    ? `\n\nReference Skills Database:\n${roadmapContext.substring(0, 5000)}`
    : '';

  const prompt = `You are an expert at extracting technical skills from resumes. Extract ALL technical skills, programming languages, frameworks, tools, and technologies mentioned in the resume.

Return ONLY a comma-separated list of skill names. Do not include explanations, descriptions, or any other text. Just the skill names separated by commas.

Resume Text:
${resumeText.substring(0, 20000)}${context}

Return the skills as a comma-separated list:`;

  const result = await callOpenAI(
    [{ role: 'user', content: prompt }],
    { model: 'gpt-4o', temperature: 0.5, maxTokens: 2000 }
  );

  if (result.error) {
    return { ...result, data: [] };
  }

  // Parse comma-separated skills
  const skills = result.data
    .split(',')
    .map(s => s.trim())
    .filter(s => s.length > 0)
    .map(s => s.charAt(0).toUpperCase() + s.slice(1).toLowerCase());

  return {
    ...result,
    data: skills
  };
}

/**
 * Match skills to roadmap using AI (semantic matching)
 */
export async function matchSkillsToRoadmapAI(
  extractedSkills: string[],
  resumeText: string,
  roadmapData: string
): Promise<AIResponse<Array<{ skill: string; keywords: string[]; matched_from: string }>>> {
  const prompt = `You are an expert at matching technical skills. Match the extracted skills to the roadmap skills database using semantic understanding (not just keyword matching).

Extracted Skills:
${extractedSkills.join(', ')}

Resume Context (first 10000 chars):
${resumeText.substring(0, 10000)}

Roadmap Skills Database:
${roadmapData.substring(0, 10000)}

Return a JSON array of matched skills with this structure:
[
  {
    "skill": "Python",
    "keywords": ["python", "py"],
    "matched_from": "Python",
    "match_confidence": "exact"
  }
]

Return ONLY valid JSON, no explanations.`;

  const result = await callOpenAI(
    [{ role: 'user', content: prompt }],
    { model: 'gpt-4o', temperature: 0.5, maxTokens: 3000 }
  );

  if (result.error) {
    return { ...result, data: [] };
  }

  try {
    const matched = JSON.parse(result.data);
    return {
      ...result,
      data: Array.isArray(matched) ? matched : []
    };
  } catch {
    return {
      ...result,
      data: [],
      error: 'Failed to parse AI response as JSON'
    };
  }
}

/**
 * Calculate skill proficiency using AI
 */
export async function calculateSkillProficiency(
  extractedSkills: string[],
  resumeText: string,
  jobDescription?: string,
  jobSkills?: string[]
): Promise<AIResponse<Array<{ name: string; proficiency: number }>>> {
  const jobContext = jobDescription 
    ? `\n\nJob Description:\n${jobDescription.substring(0, 10000)}`
    : '';
  
  const jobSkillsContext = jobSkills && jobSkills.length > 0
    ? `\n\nRequired Job Skills:\n${jobSkills.join(', ')}`
    : '';

  const prompt = `You are an expert at evaluating skill proficiency. Rate each skill on a scale of 1.0 to 5.0 based on the resume context and job requirements.

Skills to Rate:
${extractedSkills.join(', ')}

Resume Context (first 20000 chars):
${resumeText.substring(0, 20000)}${jobContext}${jobSkillsContext}

Return a JSON array with this structure:
[
  {
    "name": "Python",
    "proficiency": 4.5
  }
]

Use decimal scores (e.g., 2.5, 3.5, 4.5) for nuanced ratings. Base your ratings on:
- Years of experience mentioned
- Depth of projects and responsibilities
- Complexity of work described
- Alignment with job requirements

Return ONLY valid JSON, no explanations.`;

  const result = await callOpenAI(
    [{ role: 'user', content: prompt }],
    { model: 'gpt-4o', temperature: 0.5, maxTokens: 2500 }
  );

  if (result.error) {
    return { ...result, data: [] };
  }

  try {
    const proficiency = JSON.parse(result.data);
    return {
      ...result,
      data: Array.isArray(proficiency) ? proficiency : []
    };
  } catch {
    return {
      ...result,
      data: [],
      error: 'Failed to parse AI response as JSON'
    };
  }
}

/**
 * Expand job description using AI
 */
export async function expandJobDescription(
  jobTitle: string,
  companyName: string,
  jobDescription: string,
  jobSkills: string[]
): Promise<AIResponse<string>> {
  const prompt = `Expand and elaborate on this job description to provide more detailed requirements and context.

Job Title: ${jobTitle}
Company: ${companyName}

Original Job Description:
${jobDescription}

Required Skills:
${jobSkills.join(', ')}

Expand this job description to 300-500 words, providing:
- Detailed responsibilities
- Required experience levels
- Specific technical requirements
- Team and company context
- Growth opportunities

Return the expanded description only, no additional text.`;

  const result = await callOpenAI(
    [{ role: 'user', content: prompt }],
    { model: 'gpt-4o', temperature: 0.5, maxTokens: 1000 }
  );

  return result;
}

/**
 * Match resume to job using AI
 */
export async function compareResumeToJobAI(
  matchedSkills: Array<{ skill: string; proficiency?: number }>,
  extractedSkillsRaw: string[],
  resumeText: string,
  jobTitle: string,
  companyName: string,
  expandedDescription: string,
  jobSkills: Array<{ name: string; level?: string }>
): Promise<AIResponse<{
  overall_match_percentage: number;
  job_skills: Array<{
    skill_name: string;
    match_percentage: number;
    matched_resume_skills: string[];
    reasoning: string;
  }>;
}>> {
  const resumeSkillsStr = matchedSkills
    .map(s => `${s.skill}${s.proficiency ? ` (${s.proficiency}/5)` : ''}`)
    .join(', ');

  const jobSkillsStr = jobSkills
    .map(s => `${s.name}${s.level ? ` (${s.level})` : ''}`)
    .join(', ');

  const prompt = `You are an expert at matching candidates to job requirements. Analyze how well the candidate's skills and experience match the job requirements.

Job Title: ${jobTitle}
Company: ${companyName}

Expanded Job Description:
${expandedDescription}

Job Required Skills:
${jobSkillsStr}

Candidate Skills (with proficiency):
${resumeSkillsStr}

Candidate Resume Context (first 20000 chars):
${resumeText.substring(0, 20000)}

For EACH job skill, provide:
- A match percentage (0-100%) indicating how well the candidate matches this requirement
- Reasoning based on skills, experience, and alignment with job description
- Matched resume skills that contributed to this match

Calculate an overall match percentage (0-100%) that represents the candidate's overall fit.

Return a JSON object with this structure:
{
  "overall_match_percentage": 72.3,
  "job_skills": [
    {
      "skill_name": "Python",
      "match_percentage": 78.5,
      "matched_resume_skills": ["Python", "Django"],
      "reasoning": "Candidate has Python with proficiency 4/5. The expanded job description requires 3+ years of Python for backend development at proficiency 4/5. The candidate's resume shows 4 years of Python experience with Django, closely matching the requirements."
    }
  ]
}

IMPORTANT:
- Use the FULL percentage range (0-100%) - avoid binary thinking
- Provide nuanced scores (e.g., 72.3, 45.7, 88.9)
- Base percentages on comprehensive analysis of experience, proficiency, and job alignment
- Return ONLY valid JSON, no explanations`;

  const result = await callOpenAI(
    [{ role: 'user', content: prompt }],
    { model: 'gpt-4o', temperature: 0.5, maxTokens: 5000 }
  );

  if (result.error) {
    return {
      ...result,
      data: {
        overall_match_percentage: 0,
        job_skills: []
      }
    };
  }

  try {
    const matchData = JSON.parse(result.data);
    return {
      ...result,
      data: matchData
    };
  } catch {
    return {
      ...result,
      data: {
        overall_match_percentage: 0,
        job_skills: []
      },
      error: 'Failed to parse AI response as JSON'
    };
  }
}

/**
 * Generate learning path using AI
 */
export async function generateLearningPath(
  missingSkills: string[],
  currentSkills?: string[],
  jobContext?: { jobTitle?: string; jobDescription?: string }
): Promise<AIResponse<Array<{
  id: string;
  title: string;
  description: string;
  duration: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  resources: string[];
}>>> {
  const currentSkillsContext = currentSkills && currentSkills.length > 0
    ? `\n\nCurrent Skills (for context):\n${currentSkills.join(', ')}`
    : '';

  const jobContextStr = jobContext?.jobTitle
    ? `\n\nJob Context:\nTitle: ${jobContext.jobTitle}\nDescription: ${jobContext.jobDescription?.substring(0, 2000) || ''}`
    : '';

  const prompt = `You are an expert at creating personalized learning paths. Generate a step-by-step learning plan for acquiring the missing skills.

Missing Skills to Learn:
${missingSkills.join(', ')}${currentSkillsContext}${jobContextStr}

Create a comprehensive learning path with multiple steps. Each step should:
- Focus on one or a few related skills
- Include a clear title and description
- Estimate duration (e.g., "2 weeks", "1 month", "3-4 weeks")
- Assign difficulty level (beginner, intermediate, or advanced)
- Provide 3-5 specific learning resources (tutorials, courses, documentation, books, etc.)

Return a JSON array with this structure:
[
  {
    "id": "1",
    "title": "Master Docker Fundamentals",
    "description": "Learn containerization basics, Docker commands, and container orchestration concepts.",
    "duration": "4 weeks",
    "difficulty": "intermediate",
    "resources": [
      "Docker Official Tutorial",
      "Containerization Essentials Course",
      "Docker Documentation"
    ]
  }
]

Return ONLY valid JSON, no explanations.`;

  const result = await callOpenAI(
    [{ role: 'user', content: prompt }],
    { model: 'gpt-4o', temperature: 0.5, maxTokens: 3000 }
  );

  if (result.error) {
    return { ...result, data: [] };
  }

  try {
    const steps = JSON.parse(result.data);
    return {
      ...result,
      data: Array.isArray(steps) ? steps : []
    };
  } catch {
    return {
      ...result,
      data: [],
      error: 'Failed to parse AI response as JSON'
    };
  }
}

