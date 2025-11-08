/**
 * Data Utilities
 * Handles JSON file operations and data format conversions
 */

import fs from 'fs/promises';
import path from 'path';

// Use /tmp for Vercel serverless (writable) or data/ for local dev
const DATA_DIR = process.env.VERCEL 
  ? '/tmp/data' 
  : path.join(process.cwd(), 'data');

// Ensure data directory exists
async function ensureDataDir() {
  try {
    await fs.mkdir(DATA_DIR, { recursive: true });
  } catch (error) {
    console.error('Error creating data directory:', error);
  }
}

/**
 * Load JSON file
 */
export async function loadJSONFile<T>(filename: string, defaultValue: T): Promise<T> {
  await ensureDataDir();
  const filePath = path.join(DATA_DIR, filename);
  
  try {
    const content = await fs.readFile(filePath, 'utf-8');
    return JSON.parse(content) as T;
  } catch (error) {
    // File doesn't exist, return default
    return defaultValue;
  }
}

/**
 * Save JSON file
 */
export async function saveJSONFile<T>(filename: string, data: T): Promise<void> {
  await ensureDataDir();
  const filePath = path.join(DATA_DIR, filename);
  
  try {
    await fs.writeFile(filePath, JSON.stringify(data, null, 2), 'utf-8');
  } catch (error) {
    console.error(`Error saving ${filename}:`, error);
    throw error;
  }
}

/**
 * Append to JSON array file
 */
export async function appendToJSONArray<T>(filename: string, item: T): Promise<void> {
  const existing = await loadJSONFile<T[]>(filename, []);
  existing.push(item);
  await saveJSONFile(filename, existing);
}

/**
 * Convert proficiency number (1-5) to level string
 */
export function proficiencyToLevel(proficiency: number): string {
  if (proficiency >= 4.5) {
    return 'Advanced';
  } else if (proficiency >= 3.5) {
    return 'Intermediate';
  } else if (proficiency >= 2.5) {
    return 'Basic';
  } else {
    return 'Beginner';
  }
}

/**
 * Split skills into currentSkills and missingSkills based on match percentage
 */
export function splitSkillsByMatch(
  allSkills: Array<{
    skill: string;
    match_percentage: number;
    matched_resume_skills?: string[];
    reasoning?: string;
  }>,
  threshold: number = 50.0
): {
  currentSkills: Array<{
    name: string;
    level?: string;
    matchPercentage: number;
  }>;
  missingSkills: Array<{
    name: string;
    level?: string;
    matchPercentage: number;
  }>;
} {
  const current: Array<{ name: string; level?: string; matchPercentage: number }> = [];
  const missing: Array<{ name: string; level?: string; matchPercentage: number }> = [];

  for (const skill of allSkills) {
    const skillData = {
      name: skill.skill,
      matchPercentage: skill.match_percentage
    };

    if (skill.match_percentage >= threshold) {
      current.push(skillData);
    } else {
      missing.push(skillData);
    }
  }

  return { currentSkills: current, missingSkills: missing };
}

/**
 * Generate unique timestamp-based ID
 */
export function generateResumeId(): string {
  const now = new Date();
  const timestamp = now.getTime();
  const random = Math.floor(Math.random() * 1000000);
  return `${timestamp}_${random}`;
}

/**
 * Load roadmap data
 */
export async function loadRoadmapData(): Promise<any> {
  const roadmapPath = path.join(process.cwd(), '..', 'data', 'roadmaps_role_skill.json');
  
  try {
    const content = await fs.readFile(roadmapPath, 'utf-8');
    return JSON.parse(content);
  } catch (error) {
    console.error('Error loading roadmap data:', error);
    return null;
  }
}

/**
 * Extract roadmap context string for AI prompts
 */
export function extractRoadmapContext(roadmapData: any): string {
  if (!roadmapData || !roadmapData.roles) {
    return '';
  }

  const skills: string[] = [];
  const keywords: string[] = [];

  for (const role of roadmapData.roles) {
    if (role.skills) {
      for (const skill of role.skills) {
        if (skill.skill) {
          skills.push(skill.skill);
        }
        if (skill.keywords) {
          keywords.push(...skill.keywords);
        }
      }
    }
  }

  return `Skills: ${[...new Set(skills)].join(', ')}\nKeywords: ${[...new Set(keywords)].join(', ')}`;
}

/**
 * Load LinkedIn jobs data
 */
export async function loadLinkedInJobs(): Promise<any[]> {
  const jobsPath = path.join(process.cwd(), '..', 'data', 'linkedin_jobs_processed.json');
  
  try {
    const content = await fs.readFile(jobsPath, 'utf-8');
    const data = JSON.parse(content);
    return data.jobs || [];
  } catch (error) {
    console.error('Error loading LinkedIn jobs:', error);
    return [];
  }
}

