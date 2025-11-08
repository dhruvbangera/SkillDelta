/**
 * POST /api/job/analyze
 * Analyze job listing and extract required skills
 */

import { NextRequest, NextResponse } from 'next/server';
import { validateAuth } from '@/lib/api/auth';
import { expandJobDescription } from '@/lib/api/openai';
import { loadLinkedInJobs, loadJSONFile } from '@/lib/api/data-utils';

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
    const { jobId, jobData, jobUrl } = body;

    let jobTitle = '';
    let companyName = '';
    let jobDescription = '';
    let jobSkills: Array<{ name: string; level?: string }> = [];
    let jobIdFinal = jobId;

    // Get job data
    if (jobData) {
      // Use provided job data
      jobTitle = jobData.jobTitle || '';
      companyName = jobData.companyName || '';
      jobDescription = jobData.jobDescription || '';
      jobSkills = jobData.requiredSkills || [];
    } else if (jobId) {
      // Load from LinkedIn jobs or saved jobs
      const linkedInJobs = await loadLinkedInJobs();
      const savedJobs = await loadJSONFile<any[]>('saved_jobs.json', []);

      // Check LinkedIn jobs first
      const linkedInJob = linkedInJobs[parseInt(jobId)];
      if (linkedInJob) {
        jobTitle = linkedInJob.job_title || '';
        companyName = linkedInJob.company_name || '';
        jobDescription = linkedInJob.job_description || '';
        jobSkills = (linkedInJob.skills || []).map((s: any) => ({
          name: s.name || s,
          level: s.level || 'Required'
        }));
      } else {
        // Check saved jobs
        const savedJob = savedJobs.find((j, idx) => `saved_${idx}` === jobId || j.id === jobId);
        if (savedJob) {
          jobTitle = savedJob.jobTitle || '';
          companyName = savedJob.companyName || '';
          jobDescription = savedJob.jobDescription || '';
          jobSkills = savedJob.requiredSkills || [];
        } else {
          return NextResponse.json(
            { error: `Job with ID ${jobId} not found`, code: 404 },
            { status: 404 }
          );
        }
      }
    } else if (jobUrl) {
      // TODO: Implement job URL fetching/scraping
      // For now, return error
      return NextResponse.json(
        { error: 'Job URL fetching not yet implemented. Please provide jobId or jobData.', code: 501 },
        { status: 501 }
      );
    } else {
      return NextResponse.json(
        { error: 'Either jobId, jobData, or jobUrl is required', code: 400 },
        { status: 400 }
      );
    }

    if (!jobTitle || !jobDescription) {
      return NextResponse.json(
        { error: 'Job data is incomplete', code: 400 },
        { status: 400 }
      );
    }

    // Expand job description using AI
    const jobSkillsNames = jobSkills.map(s => s.name);
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

    const expandedDescription = expandResult.data;

    // Ensure all skills have levels
    const requiredSkills = jobSkills.map(skill => ({
      name: skill.name,
      level: skill.level || 'Required'
    }));

    return NextResponse.json({
      jobId: jobIdFinal || 'unknown',
      jobTitle,
      companyName,
      jobDescription,
      expandedDescription,
      requiredSkills,
      debug_ai_response: expandResult.rawResponse
    });

  } catch (error) {
    console.error('Error in /api/job/analyze:', error);
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

