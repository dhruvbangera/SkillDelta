/**
 * GET /api/jobs
 * Get list of available jobs (hardcoded + Chrome extension jobs)
 * POST /api/jobs
 * Save a job from Chrome extension
 */

import { NextRequest, NextResponse } from 'next/server';
import { validateAuth } from '@/lib/api/auth';
import { loadLinkedInJobs, loadJSONFile, saveJSONFile, appendToJSONArray } from '@/lib/api/data-utils';

// GET: List jobs
export async function GET(request: NextRequest) {
  try {
    // Validate authentication
    const auth = await validateAuth();
    if (!auth.isAuthenticated || !auth.userId) {
      return NextResponse.json(
        { error: 'Unauthorized', code: 401, details: auth.error },
        { status: 401 }
      );
    }

    // Get query parameters
    const searchParams = request.nextUrl.searchParams;
    const limit = parseInt(searchParams.get('limit') || '10');
    const offset = parseInt(searchParams.get('offset') || '0');
    const search = searchParams.get('search') || '';

    // Load LinkedIn jobs
    const linkedInJobs = await loadLinkedInJobs();

    // Load saved jobs (Chrome extension jobs)
    const savedJobs = await loadJSONFile<any[]>('saved_jobs.json', []);

    // Combine all jobs
    const allJobs = [
      ...linkedInJobs.map((job, index) => ({
        id: String(index),
        jobTitle: job.job_title,
        companyName: job.company_name,
        jobDescription: job.job_description,
        url: job.url || '',
        requiredSkills: (job.skills || []).map((s: any) => ({
          name: s.name || s,
          level: s.level || 'Required'
        }))
      })),
      ...savedJobs.map((job, index) => ({
        id: `saved_${index}`,
        ...job
      }))
    ];

    // Filter by search term if provided
    let filteredJobs = allJobs;
    if (search) {
      const searchLower = search.toLowerCase();
      filteredJobs = allJobs.filter(job =>
        job.jobTitle?.toLowerCase().includes(searchLower) ||
        job.companyName?.toLowerCase().includes(searchLower) ||
        job.jobDescription?.toLowerCase().includes(searchLower)
      );
    }

    // Paginate
    const paginatedJobs = filteredJobs.slice(offset, offset + limit);

    return NextResponse.json({
      jobs: paginatedJobs,
      total: filteredJobs.length,
      limit,
      offset
    });

  } catch (error) {
    console.error('Error in GET /api/jobs:', error);
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

// POST: Save job from Chrome extension
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
      jobTitle,
      companyName,
      jobDescription,
      url,
      requiredSkills
    } = body;

    if (!jobTitle || !companyName || !jobDescription) {
      return NextResponse.json(
        { error: 'jobTitle, companyName, and jobDescription are required', code: 400 },
        { status: 400 }
      );
    }

    // Save job
    const jobData = {
      id: `saved_${Date.now()}`,
      userId: auth.userId,
      jobTitle,
      companyName,
      jobDescription,
      url: url || '',
      requiredSkills: requiredSkills || [],
      saved_at: new Date().toISOString()
    };

    await appendToJSONArray('saved_jobs.json', jobData);

    return NextResponse.json({
      success: true,
      job: jobData
    });

  } catch (error) {
    console.error('Error in POST /api/jobs:', error);
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

