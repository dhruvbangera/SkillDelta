/**
 * Clerk Authentication Utilities
 * Validates Clerk session tokens for API routes
 */

import { auth } from '@clerk/nextjs/server';

export interface AuthResult {
  userId: string | null;
  isAuthenticated: boolean;
  error?: string;
}

/**
 * Validate Clerk session token and get user ID
 * @returns AuthResult with userId and authentication status
 */
export async function validateAuth(): Promise<AuthResult> {
  try {
    const { userId } = await auth();
    
    if (!userId) {
      return {
        userId: null,
        isAuthenticated: false,
        error: 'Unauthorized: No valid session token'
      };
    }

    return {
      userId,
      isAuthenticated: true
    };
  } catch (error) {
    console.error('Auth validation error:', error);
    return {
      userId: null,
      isAuthenticated: false,
      error: 'Unauthorized: Invalid session token'
    };
  }
}

