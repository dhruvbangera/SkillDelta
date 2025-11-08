/**
 * File Parsing Utilities
 * Extracts text from PDF, DOCX, and TXT files
 */

import pdfParse from 'pdf-parse';
import mammoth from 'mammoth';
import fs from 'fs/promises';
import path from 'path';

export interface ParseResult {
  text: string;
  error?: string;
}

/**
 * Extract text from PDF file
 */
export async function extractTextFromPDF(filePath: string): Promise<ParseResult> {
  try {
    const fileBuffer = await fs.readFile(filePath);
    const data = await pdfParse(fileBuffer);
    return {
      text: data.text || ''
    };
  } catch (error) {
    console.error('PDF parsing error:', error);
    return {
      text: '',
      error: `Failed to parse PDF: ${error instanceof Error ? error.message : 'Unknown error'}`
    };
  }
}

/**
 * Extract text from DOCX file
 */
export async function extractTextFromDOCX(filePath: string): Promise<ParseResult> {
  try {
    const fileBuffer = await fs.readFile(filePath);
    const result = await mammoth.extractRawText({ buffer: fileBuffer });
    return {
      text: result.value || ''
    };
  } catch (error) {
    console.error('DOCX parsing error:', error);
    return {
      text: '',
      error: `Failed to parse DOCX: ${error instanceof Error ? error.message : 'Unknown error'}`
    };
  }
}

/**
 * Extract text from TXT file
 */
export async function extractTextFromTXT(filePath: string): Promise<ParseResult> {
  try {
    // Try multiple encodings
    const encodings: BufferEncoding[] = ['utf-8', 'utf-16', 'latin1'];
    
    for (const encoding of encodings) {
      try {
        const text = await fs.readFile(filePath, encoding);
        return { text };
      } catch {
        continue;
      }
    }
    
    // Fallback: read as buffer and convert
    const buffer = await fs.readFile(filePath);
    return {
      text: buffer.toString('utf-8')
    };
  } catch (error) {
    console.error('TXT parsing error:', error);
    return {
      text: '',
      error: `Failed to parse TXT: ${error instanceof Error ? error.message : 'Unknown error'}`
    };
  }
}

/**
 * Extract text from resume file based on file extension
 */
export async function extractTextFromResume(filePath: string, filename: string): Promise<ParseResult> {
  const ext = filename.split('.').pop()?.toLowerCase();
  
  switch (ext) {
    case 'pdf':
      return extractTextFromPDF(filePath);
    case 'docx':
      return extractTextFromDOCX(filePath);
    case 'doc':
      // DOC files need special handling - for now, return error
      return {
        text: '',
        error: 'DOC files are not supported. Please convert to DOCX or PDF.'
      };
    case 'txt':
      return extractTextFromTXT(filePath);
    default:
      return {
        text: '',
        error: `Unsupported file type: ${ext}`
      };
  }
}

/**
 * Validate file type
 */
export function allowedFile(filename: string): boolean {
  const allowedExtensions = ['pdf', 'docx', 'txt', 'doc'];
  const ext = filename.split('.').pop()?.toLowerCase();
  return ext ? allowedExtensions.includes(ext) : false;
}

/**
 * Validate file size (max 16MB)
 */
export function validateFileSize(size: number): boolean {
  const maxSize = 16 * 1024 * 1024; // 16MB
  return size <= maxSize;
}

