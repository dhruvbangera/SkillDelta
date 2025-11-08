# Resume Skill Parser

A simple Flask-based web application that extracts skills from uploaded resumes using OpenAI and matches them to the roadmap skills format.

## Features

- ✅ Upload resumes in PDF, DOCX, or TXT format
- ✅ Extract skills using OpenAI GPT-4o-mini
- ✅ Match extracted skills to roadmap keywords format
- ✅ Save results to JSON file (updates with each upload)
- ✅ Simple, clean web interface

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure OpenAI API Key:**
   The API key is already set in `.env` file. If you need to change it, edit `.env`:
   ```
   OPENAI_API_KEY=your-api-key-here
   ```

3. **Run the application:**
   ```bash
   python app.py
   ```

4. **Open in browser:**
   Navigate to `http://127.0.0.1:5000`

## Usage

1. Click "Choose File" or drag and drop a resume file
2. Click "Process Resume"
3. View extracted and matched skills
4. Results are automatically saved to `output/resume_skills.json`

## Output Format

Each processed resume is saved to `output/resume_skills.json` with the following structure:

```json
{
  "resumes": [
    {
      "id": "20250108_123456_789012",
      "filename": "resume.pdf",
      "uploaded_at": "2025-01-08T12:34:56.789012",
      "extracted_skills_raw": ["Python", "React", "AWS", ...],
      "matched_skills": [
        {
          "skill": "Python",
          "keywords": ["python", "py"],
          "matched_from": "Python"
        },
        ...
      ],
      "total_skills_extracted": 15,
      "total_skills_matched": 12
    }
  ]
}
```

The `matched_skills` format matches the keywords structure from `roadmaps_role_skill.json`.

## File Structure

```
resume-parser/
├── app.py                 # Flask backend
├── templates/
│   └── index.html         # Web interface
├── uploads/               # Temporary storage for uploaded files
├── output/
│   └── resume_skills.json # Output file (auto-created)
├── requirements.txt       # Python dependencies
├── .env                   # API key configuration
└── README.md             # This file
```

## Integration

This is designed to be easily integrated into a larger system:

- **API Endpoints:**
  - `POST /upload` - Upload and process resume
  - `GET /resumes` - Get all processed resumes

- **Output File:**
  - `output/resume_skills.json` - Contains all processed resumes
  - Updates automatically with each new upload

- **Dependencies:**
  - Minimal dependencies (Flask, OpenAI, PyPDF2, python-docx)
  - No database required (uses JSON file)

## Notes

- Maximum file size: 16MB
- Supported formats: PDF, DOCX, DOC, TXT
- Skills are matched against `data/roadmaps_role_skill.json`
- Each resume gets a unique ID based on timestamp

