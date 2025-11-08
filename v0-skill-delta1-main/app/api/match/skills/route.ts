/**
 * POST /api/match/skills
 * Match user skills to job requirements
 */

import { NextRequest, NextResponse } from 'next/server';
import { validateAuth } from '@/lib/api/auth';
import { compareResumeToJobAI, expandJobDescription } from '@/lib/api/openai';
import { loadJSONFile, loadLinkedInJobs, proficiencyToLevel, splitSkillsByMatch } from '@/lib/api/data-utils';

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

    const body = await request.json();
    const {
      userSkills,
      userSkillsWithProficiency,
      resumeText,
      jobId,
      jobData
    } = body;

    if (!userSkills || !Array.isArray(userSkills) || userSkills.length === 0) {
      return NextResponse.json(
        { error: 'userSkills array is required', code: 400 },
        { status: 400 }
      );
    }

    // Get job data
    let jobTitle = '';
    let companyName = '';
    let jobDescription = '';
    let expandedDescription = '';
    let jobSkillsList: Array<{ name: string; level?: string }> = [];

    if (jobData) {
      // Use provided job data
      jobTitle = jobData.jobTitle || '';
      companyName = jobData.companyName || '';
      jobDescription = jobData.jobDescription || '';
      jobSkillsList = jobData.requiredSkills || [];
    } else if (jobId) {
      // Load from LinkedIn jobs
      const jobs = await loadLinkedInJobs();
      const job = jobs[parseInt(jobId)];
      
      if (!job) {
        return NextResponse.json(
          { error: `Job with ID ${jobId} not found`, code: 404 },
          { status: 404 }
        );
      }

      jobTitle = job.job_title || '';
      companyName = job.company_name || '';
      jobDescription = job.job_description || '';
      jobSkillsList = (job.skills || []).map((s: any) => ({
        name: s.name || s,
        level: s.level
      }));
    } else {
      return NextResponse.json(
        { error: 'Either jobId or jobData is required', code: 400 },
        { status: 400 }
      );
    }

    // Expand job description
    const jobSkillsNames = jobSkillsList.map(s => s.name);
    const expandResult = await expandJobDescription(
      jobTitle,
      companyName,
      jobDescription,
      jobSkillsNames
    );

    if (expandResult.error) {
      return NextResponse.json(
        { error: `Failed to expand job description: ${expandResult.error}`, code: 500 },
        { status: 500 }
      );
    }

    expandedDescription = expandResult.data;

    // Prepare matched skills with proficiency
    const matchedSkills = userSkills.map(skillName => {
      const proficiencyData = userSkillsWithProficiency?.find(
        (s: { name: string; proficiency: number }) => s.name === skillName
      );
      return {
        skill: skillName,
        proficiency: proficiencyData?.proficiency
      };
    });

    // Compare resume to job using AI
    const matchResult = await compareResumeToJobAI(
      matchedSkills,
      userSkills,
      resumeText || '',
      jobTitle,
      companyName,
      expandedDescription,
      jobSkillsList
    );

    if (matchResult.error) {
      return NextResponse.json(
        { error: `Failed to match skills: ${matchResult.error}`, code: 500 },
        { status: 500 }
      );
    }

    const matchData = matchResult.data;

    // Convert to frontend format
    const allSkills = matchData.job_skills.map((js: any) => ({
      skill: js.skill_name,
      match_percentage: js.match_percentage,
      matched_resume_skills: js.matched_resume_skills || [],
      reasoning: js.reasoning || ''
    }));

    // Split into currentSkills and missingSkills
    const { currentSkills, missingSkills } = splitSkillsByMatch(allSkills, 50.0);

    // Add levels to skills (convert from proficiency if available)
    const currentSkillsWithLevels = currentSkills.map(skill => {
      // Try to find proficiency from userSkillsWithProficiency
      const proficiencyData = userSkillsWithProficiency?.find(
        (us: { name: string; proficiency: number }) => us.name === skill.name
      );
      
      return {
        ...skill,
        level: proficiencyData ? proficiencyToLevel(proficiencyData.proficiency) : undefined
      };
    });

    const missingSkillsWithLevels = missingSkills.map(skill => {
      // Find level from job requirements
      const jobSkill = jobSkillsList.find(js => js.name === skill.name);
      return {
        ...skill,
        level: jobSkill?.level || 'Required'
      };
    });

    return NextResponse.json({
      matchPercentage: matchData.overall_match_percentage,
      currentSkills: currentSkillsWithLevels,
      missingSkills: missingSkillsWithLevels,
      allSkills: allSkills,
      reasoning: {
        expandedDescription,
        raw_ai_response: matchResult.rawResponse
      }
    });

  } catch (error) {
    console.error('Error in /api/match/skills:', error);
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

