/**
 * POST /api/learning-path/generate
 * Generate personalized learning path for missing skills
 */

import { NextRequest, NextResponse } from 'next/server';
import { validateAuth } from '@/lib/api/auth';
import { generateLearningPath } from '@/lib/api/openai';

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
      missingSkills,
      currentSkills,
      jobContext
    } = body;

    if (!missingSkills || !Array.isArray(missingSkills) || missingSkills.length === 0) {
      return NextResponse.json(
        { error: 'missingSkills array is required', code: 400 },
        { status: 400 }
      );
    }

    // Generate learning path using AI
    const pathResult = await generateLearningPath(
      missingSkills,
      currentSkills,
      jobContext
    );

    if (pathResult.error) {
      return NextResponse.json(
        { error: `Failed to generate learning path: ${pathResult.error}`, code: 500 },
        { status: 500 }
      );
    }

    // Ensure all steps have required fields
    const steps = pathResult.data.map((step, index) => ({
      id: step.id || String(index + 1),
      title: step.title || `Step ${index + 1}`,
      description: step.description || '',
      duration: step.duration || '2-4 weeks',
      difficulty: step.difficulty || 'intermediate' as 'beginner' | 'intermediate' | 'advanced',
      resources: Array.isArray(step.resources) ? step.resources : []
    }));

    return NextResponse.json({
      steps,
      debug_ai_response: pathResult.rawResponse
    });

  } catch (error) {
    console.error('Error in /api/learning-path/generate:', error);
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

