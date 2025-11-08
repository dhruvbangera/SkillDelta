/**
 * POST /api/skills/extract
 * Extract skills from uploaded resume files
 */

import { NextRequest, NextResponse } from 'next/server';
import { validateAuth } from '@/lib/api/auth';
import { extractTextFromResume, allowedFile, validateFileSize } from '@/lib/api/file-parser';
import { extractSkillsWithAI, matchSkillsToRoadmapAI, calculateSkillProficiency } from '@/lib/api/openai';
import { loadRoadmapData, extractRoadmapContext, generateResumeId, appendToJSONArray, loadJSONFile } from '@/lib/api/data-utils';
import { writeFile, mkdir } from 'fs/promises';
import { join } from 'path';
import { existsSync } from 'fs';

// Disable body parsing for file uploads
export const runtime = 'nodejs';

interface ResumeData {
  id: string;
  userId: string;
  filename: string;
  uploaded_at: string;
  extracted_skills_raw: string[];
  matched_skills: any[];
  skills_with_proficiency?: Array<{ name: string; proficiency: number }>;
  total_skills_extracted: number;
  total_skills_matched: number;
  debug_ai_responses: {
    skill_extraction?: string;
    skill_matching?: string;
    proficiency_calculation?: string;
  };
}

export async function POST(request: NextRequest) {
  try {
    // Validate authentication
    const auth = await validateAuth();
    if (!auth.isAuthenticated || !auth.userId) {
      return NextResponse.json(
        { error: 'Unauthorized', code: 401, details: auth.error },
        { status: 401 }
      );
    }

    const userId = auth.userId;

    // Parse form data
    const formData = await request.formData();
    const files = formData.getAll('files') as File[];
    const jobId = formData.get('jobId') as string | null;
    const jobDataStr = formData.get('jobData') as string | null;

    if (!files || files.length === 0) {
      return NextResponse.json(
        { error: 'No files provided', code: 400 },
        { status: 400 }
      );
    }

    // Validate files
    for (const file of files) {
      if (!allowedFile(file.name)) {
        return NextResponse.json(
          { error: `Invalid file type: ${file.name}. Allowed: PDF, DOCX, TXT`, code: 400 },
          { status: 400 }
        );
      }

      if (!validateFileSize(file.size))) {
        return NextResponse.json(
          { error: `File too large: ${file.name}. Max size: 16MB`, code: 400 },
          { status: 400 }
        );
      }
    }

    // Process first file (for now, handle single file)
    const file = files[0];
    const buffer = Buffer.from(await file.arrayBuffer());

    // Save file temporarily
    const uploadsDir = join(process.cwd(), 'uploads');
    if (!existsSync(uploadsDir)) {
      await mkdir(uploadsDir, { recursive: true });
    }

    const filePath = join(uploadsDir, file.name);
    await writeFile(filePath, buffer);

    // Extract text from file
    const parseResult = await extractTextFromResume(filePath, file.name);
    
    if (parseResult.error || !parseResult.text) {
      return NextResponse.json(
        { error: parseResult.error || 'Failed to extract text from file', code: 500 },
        { status: 500 }
      );
    }

    const resumeText = parseResult.text;

    // Load roadmap data for context
    const roadmapData = await loadRoadmapData();
    const roadmapContext = roadmapData ? extractRoadmapContext(roadmapData) : '';

    // Extract skills using AI
    const skillExtractionResult = await extractSkillsWithAI(resumeText, roadmapContext);
    
    if (skillExtractionResult.error || !skillExtractionResult.data.length) {
      return NextResponse.json(
        { 
          error: skillExtractionResult.error || 'Failed to extract skills', 
          code: 500,
          debug_ai_responses: {
            skill_extraction: skillExtractionResult.rawResponse
          }
        },
        { status: 500 }
      );
    }

    const extractedSkills = skillExtractionResult.data;

    // Match skills to roadmap
    const roadmapDataStr = roadmapData ? JSON.stringify(roadmapData).substring(0, 10000) : '';
    const skillMatchingResult = await matchSkillsToRoadmapAI(extractedSkills, resumeText, roadmapDataStr);
    const matchedSkills = skillMatchingResult.data || [];

    // Calculate proficiency if job context provided
    let skillsWithProficiency: Array<{ name: string; proficiency: number }> = [];
    let proficiencyResponse = '';

    if (jobId || jobDataStr) {
      let jobDescription = '';
      let jobSkills: string[] = [];

      if (jobDataStr) {
        try {
          const jobData = JSON.parse(jobDataStr);
          jobDescription = jobData.jobDescription || '';
          jobSkills = jobData.requiredSkills?.map((s: any) => s.name || s) || [];
        } catch (e) {
          console.error('Error parsing jobData:', e);
        }
      }

      const proficiencyResult = await calculateSkillProficiency(
        extractedSkills,
        resumeText,
        jobDescription,
        jobSkills
      );

      skillsWithProficiency = proficiencyResult.data || [];
      proficiencyResponse = proficiencyResult.rawResponse;
    }

    // Generate resume ID
    const resumeId = generateResumeId();

    // Prepare resume data
    const resumeData: ResumeData = {
      id: resumeId,
      userId,
      filename: file.name,
      uploaded_at: new Date().toISOString(),
      extracted_skills_raw: extractedSkills,
      matched_skills: matchedSkills,
      skills_with_proficiency: skillsWithProficiency.length > 0 ? skillsWithProficiency : undefined,
      total_skills_extracted: extractedSkills.length,
      total_skills_matched: matchedSkills.length,
      debug_ai_responses: {
        skill_extraction: skillExtractionResult.rawResponse,
        skill_matching: skillMatchingResult.rawResponse,
        proficiency_calculation: proficiencyResponse || undefined
      }
    };

    // Save resume data
    await appendToJSONArray('resumes.json', resumeData);

    // Prepare response
    const proficiency: Record<string, number> = {};
    for (const skill of skillsWithProficiency) {
      proficiency[skill.name] = skill.proficiency;
    }

    return NextResponse.json({
      extractedSkills,
      proficiency: Object.keys(proficiency).length > 0 ? proficiency : undefined,
      resumeId,
      debug_ai_responses: resumeData.debug_ai_responses
    });

  } catch (error) {
    console.error('Error in /api/skills/extract:', error);
    return NextResponse.json(
      {
        error: 'Internal server error',
        code: 500,
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
}

