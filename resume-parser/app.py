#!/usr/bin/env python3
"""
Resume Parser - Flask Backend
Extracts skills from uploaded resumes using OpenAI and matches them to roadmap keywords.
"""

import os
import json
import re
from datetime import datetime
from pathlib import Path
from flask import Flask, request, render_template, jsonify
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from openai import OpenAI
import PyPDF2
from docx import Document

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'output'

# Create necessary directories
Path(app.config['UPLOAD_FOLDER']).mkdir(exist_ok=True)
Path(app.config['OUTPUT_FOLDER']).mkdir(exist_ok=True)

# Initialize OpenAI client
openai_api_key = os.getenv('OPENAI_API_KEY')
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

client = OpenAI(api_key=openai_api_key)

# Load roadmap skills for matching
ROADMAP_SKILLS_FILE = Path(__file__).parent.parent / 'data' / 'roadmaps_role_skill.json'
OUTPUT_JSON_FILE = Path(app.config['OUTPUT_FOLDER']) / 'resume_skills.json'
LINKEDIN_JOBS_FILE = Path(__file__).parent.parent / 'data' / 'linkedin_jobs_processed.json'

# Cache for roadmap data (loaded once at startup)
_ROADMAP_SKILL_LIST_CACHE = None

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt', 'doc'}


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_text_from_pdf(file_path):
    """Extract text from PDF file."""
    try:
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            print(f"PDF has {len(pdf_reader.pages)} pages")
            for i, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
                print(f"Extracted {len(page_text)} chars from page {i+1}")
        print(f"Total PDF text extracted: {len(text)} characters")
        return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        import traceback
        traceback.print_exc()
        return ""


def extract_text_from_docx(file_path):
    """Extract text from DOCX file."""
    try:
        doc = Document(file_path)
        paragraphs = [paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip()]
        text = "\n".join(paragraphs)
        print(f"Extracted {len(text)} characters from DOCX")
        return text
    except Exception as e:
        print(f"Error reading DOCX: {e}")
        import traceback
        traceback.print_exc()
        return ""


def extract_text_from_txt(file_path):
    """Extract text from TXT file."""
    try:
        # Try multiple encodings
        encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252']
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding, errors='ignore') as file:
                    text = file.read()
                    print(f"Extracted {len(text)} characters from TXT using {encoding}")
                    return text
            except UnicodeDecodeError:
                continue
        # Fallback
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            return file.read()
    except Exception as e:
        print(f"Error reading TXT: {e}")
        import traceback
        traceback.print_exc()
        return ""


def extract_text_from_resume(file_path, filename):
    """Extract text from resume based on file extension."""
    ext = filename.rsplit('.', 1)[1].lower()
    
    if ext == 'pdf':
        return extract_text_from_pdf(file_path)
    elif ext in ['docx', 'doc']:
        return extract_text_from_docx(file_path)
    elif ext == 'txt':
        return extract_text_from_txt(file_path)
    else:
        return ""


def load_roadmap_skills():
    """Load skills and keywords from roadmap JSON."""
    try:
        with open(ROADMAP_SKILLS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Build a mapping of keywords to skills
        skill_keywords = {}
        for role in data.get('roles', []):
            for skill_obj in role.get('skills', []):
                skill_name = skill_obj.get('skill', '')
                keywords = skill_obj.get('keywords', [])
                
                # Add skill name as a keyword too
                all_keywords = [skill_name.lower()] + [k.lower() for k in keywords]
                
                for keyword in all_keywords:
                    if keyword not in skill_keywords:
                        skill_keywords[keyword] = []
                    skill_keywords[keyword].append({
                        'skill': skill_name,
                        'keywords': keywords,
                        'role': role.get('role', '')
                    })
        
        return skill_keywords
    except Exception as e:
        print(f"Error loading roadmap skills: {e}")
        return {}


def extract_roadmap_skill_list():
    """Extract comprehensive list of all skills, roles, and topics from roadmap JSON for prompt generation."""
    global _ROADMAP_SKILL_LIST_CACHE
    
    # Return cached data if available
    if _ROADMAP_SKILL_LIST_CACHE is not None:
        return _ROADMAP_SKILL_LIST_CACHE
    
    try:
        print("Loading roadmap skill list for prompt generation...")
        with open(ROADMAP_SKILLS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        all_skills = set()
        all_roles = set()
        all_topics = set()
        all_keywords = set()
        
        for role in data.get('roles', []):
            role_name = role.get('role', '')
            if role_name:
                all_roles.add(role_name)
            
            for skill_obj in role.get('skills', []):
                skill_name = skill_obj.get('skill', '')
                if skill_name:
                    all_skills.add(skill_name)
                
                # Add keywords
                keywords = skill_obj.get('keywords', [])
                for keyword in keywords:
                    if keyword:
                        all_keywords.add(keyword.lower())
                
                # Add topics
                topics = skill_obj.get('topics', [])
                for topic_obj in topics:
                    if isinstance(topic_obj, dict):
                        topic_name = topic_obj.get('topic', '')
                        if topic_name:
                            all_topics.add(topic_name)
                    elif isinstance(topic_obj, str):
                        all_topics.add(topic_obj)
        
        result = {
            'skills': sorted(list(all_skills)),
            'roles': sorted(list(all_roles)),
            'topics': sorted(list(all_topics))[:200],  # Limit topics to avoid token limits
            'keywords': sorted(list(all_keywords))
        }
        
        # Cache the result
        _ROADMAP_SKILL_LIST_CACHE = result
        print(f"Loaded {len(result['skills'])} skills, {len(result['roles'])} roles, {len(result['keywords'])} keywords from roadmap")
        
        return result
    except Exception as e:
        print(f"Error extracting roadmap skill list: {e}")
        import traceback
        traceback.print_exc()
        return {'skills': [], 'roles': [], 'topics': [], 'keywords': []}


def extract_skills_pattern_based(resume_text):
    """Fallback: Extract skills using pattern matching."""
    skills_found = set()
    resume_lower = resume_text.lower()
    
    # Common tech skills patterns - expanded list
    tech_patterns = [
        # Programming languages
        r'\b(python|java|javascript|typescript|c\+\+|c#|cpp|cxx|go|golang|rust|kotlin|swift|php|ruby|scala|r|dart|perl|html|css|scss|sass|less)\b',
        # Web technologies
        r'\b(html5?|css3?|scss|sass|less|webpack|babel|eslint|prettier)\b',
        # Frameworks
        r'\b(react|vue|angular|django|flask|fastapi|express|spring|laravel|rails|gin|next\.js|nuxt|svelte|remix)\b',
        # Testing frameworks
        r'\b(jest|cypress|mocha|chai|jasmine|karma|selenium|playwright|pytest|unittest|junit)\b',
        # Databases
        r'\b(mysql|postgresql|postgres|mongodb|mongo|redis|elasticsearch|cassandra|dynamodb|sqlite|oracle|sql server|prisma)\b',
        # Cloud/DevOps/Deployment
        r'\b(aws|azure|gcp|google cloud|docker|kubernetes|k8s|jenkins|gitlab|github actions|terraform|ansible|git|vercel|netlify|heroku|railway)\b',
        # AI/ML/Robotics
        r'\b(tensorflow|pytorch|scikit-learn|sklearn|keras|pandas|numpy|opencv|nltk|spacy|slam|ros|robot operating system)\b',
        # Mobile
        r'\b(react native|flutter|ios|android|xamarin|swiftui|kotlin multiplatform)\b',
        # Tools/Concepts
        r'\b(graphql|rest|restful|microservices|agile|scrum|oop|object-oriented|functional programming|linux|bash|powershell|zsh|fish)\b',
        # Version control and CI/CD
        r'\b(git|svn|mercurial|github|gitlab|bitbucket|circleci|travis|github actions|gitlab ci)\b',
        # Build tools
        r'\b(npm|yarn|pnpm|pip|conda|maven|gradle|cmake|make|gulp|grunt)\b',
    ]
    
    # Individual skill patterns (case-insensitive word boundaries)
    individual_skills = [
        'html', 'css', 'javascript', 'typescript', 'python', 'java', 'c++', 'cpp', 'c#', 'go', 'rust',
        'react', 'vue', 'angular', 'node.js', 'express', 'django', 'flask', 'spring',
        'mysql', 'postgresql', 'mongodb', 'redis',
        'docker', 'kubernetes', 'aws', 'azure', 'gcp',
        'git', 'github', 'gitlab',
        'jest', 'cypress', 'mocha', 'pytest',
        'vercel', 'netlify', 'heroku',
        'slam', 'ros', 'tensorflow', 'pytorch',
        'html5', 'css3', 'scss', 'sass'
    ]
    
    # Pattern matching
    for pattern in tech_patterns:
        matches = re.finditer(pattern, resume_lower, re.IGNORECASE)
        for match in matches:
            skill = match.group(1).strip()
            if len(skill) > 1:
                # Preserve original casing for known skills
                skill_clean = skill.lower()
                if skill_clean in ['c++', 'cpp', 'cxx']:
                    skills_found.add('C++')
                elif skill_clean == 'html5':
                    skills_found.add('HTML5')
                elif skill_clean == 'css3':
                    skills_found.add('CSS3')
                else:
                    skills_found.add(skill.title() if skill.islower() else skill)
    
    # Direct word matching for individual skills
    for skill in individual_skills:
        pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        if re.search(pattern, resume_lower, re.IGNORECASE):
            if skill.lower() == 'c++' or skill.lower() == 'cpp':
                skills_found.add('C++')
            elif skill.lower() == 'html5':
                skills_found.add('HTML5')
            elif skill.lower() == 'css3':
                skills_found.add('CSS3')
            elif skill.lower() == 'node.js':
                skills_found.add('Node.js')
            else:
                skills_found.add(skill.title() if skill.islower() else skill)
    
    return list(skills_found)


def extract_skills_with_openai(resume_text):
    """Use OpenAI to extract skills from resume text."""
    # Load comprehensive skill list from roadmap
    roadmap_data = extract_roadmap_skill_list()
    
    # Build comprehensive skill examples from roadmap
    skills_list = roadmap_data['skills']
    roles_list = roadmap_data['roles']
    keywords_list = roadmap_data['keywords']
    
    # Create categorized examples (sample from each category)
    programming_langs = [s for s in skills_list if any(kw in s.lower() for kw in ['python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'rust', 'kotlin', 'swift', 'php', 'ruby', 'scala', 'r', 'dart', 'html', 'css', 'sql'])]
    frameworks = [s for s in skills_list if any(kw in s.lower() for kw in ['react', 'vue', 'angular', 'django', 'flask', 'express', 'spring', 'next', 'nuxt', 'svelte', 'asp', 'net', 'laravel', 'rails'])]
    tools_platforms = [s for s in skills_list if any(kw in s.lower() for kw in ['docker', 'kubernetes', 'aws', 'azure', 'gcp', 'vercel', 'netlify', 'git', 'jenkins', 'terraform', 'ansible'])]
    databases = [s for s in skills_list if any(kw in s.lower() for kw in ['mysql', 'postgres', 'mongodb', 'redis', 'elasticsearch', 'cassandra', 'dynamodb', 'sqlite', 'oracle', 'cosmos', 'couch'])]
    testing = [s for s in skills_list if any(kw in s.lower() for kw in ['jest', 'cypress', 'mocha', 'selenium', 'playwright', 'pytest', 'junit', 'test'])]
    ai_ml = [s for s in skills_list if any(kw in s.lower() for kw in ['tensorflow', 'pytorch', 'pandas', 'numpy', 'opencv', 'nltk', 'spacy', 'slam', 'ros', 'machine learning', 'ai', 'neural'])]
    
    # Get unique sample skills (up to 30 per category to avoid token limits)
    sample_skills = list(set(
        programming_langs[:30] + 
        frameworks[:30] + 
        tools_platforms[:30] + 
        databases[:20] + 
        testing[:20] + 
        ai_ml[:20]
    ))
    
    # Build comprehensive prompt
    prompt = f"""You are extracting ALL technical skills from a resume. Be extremely thorough and comprehensive.

Extract EVERY technical skill, technology, tool, framework, library, platform, concept, and methodology mentioned in this resume.

REFERENCE SKILLS FROM ROADMAP DATABASE (these are examples - extract ALL skills mentioned, not just these):
{', '.join(sample_skills[:100])}

ALSO LOOK FOR THESE KEYWORDS AND VARIATIONS:
{', '.join(keywords_list[:150])}

ROLES TO CONSIDER (skills may be associated with these roles):
{', '.join(roles_list[:50])}

CATEGORIES TO EXTRACT FROM:

PROGRAMMING LANGUAGES: Python, Java, JavaScript, TypeScript, C++, C#, Go, Rust, Kotlin, Swift, PHP, Ruby, Scala, R, Dart, HTML, HTML5, CSS, CSS3, SCSS, SASS, SQL, etc.

FRAMEWORKS & LIBRARIES: React, Vue, Angular, Django, Flask, FastAPI, Express, Spring, Next.js, Nuxt, Svelte, ASP.NET, Laravel, Rails, Gin, etc.

TOOLS & PLATFORMS: Docker, Kubernetes, AWS, Azure, GCP, Vercel, Netlify, Heroku, Railway, Git, GitHub, GitLab, Jenkins, Terraform, Ansible, CircleCI, etc.

DATABASES: MySQL, PostgreSQL, MongoDB, Redis, Elasticsearch, Cassandra, DynamoDB, SQLite, Oracle, SQL Server, CosmosDB, CouchDB, etc.

TESTING FRAMEWORKS: Jest, Cypress, Mocha, Chai, Jasmine, Karma, Selenium, Playwright, pytest, unittest, JUnit, etc.

AI/ML/ROBOTICS: TensorFlow, PyTorch, scikit-learn, Keras, Pandas, NumPy, OpenCV, NLTK, spaCy, SLAM, ROS, Machine Learning, Deep Learning, etc.

BUILD TOOLS: npm, yarn, pnpm, pip, conda, webpack, babel, eslint, prettier, Maven, Gradle, CMake, etc.

CONCEPTS & METHODOLOGIES: REST, GraphQL, Microservices, Agile, Scrum, OOP, Functional Programming, CI/CD, DevOps, etc.

CYBERSECURITY: Security concepts, encryption, authentication, authorization, etc.

SPECIALIZED TOPICS: Any technical topics, concepts, or domain-specific knowledge mentioned.

CRITICAL INSTRUCTIONS:
- Extract skills even if mentioned only once, briefly, or in different contexts
- Include HTML, CSS, C++, and other fundamental technologies
- Include deployment platforms like Vercel, Netlify, Heroku, Railway
- Include testing tools like Jest, Cypress, Selenium, Playwright
- Include specialized terms like SLAM (Simultaneous Localization and Mapping), ROS (Robot Operating System)
- Include version control: Git, GitHub, GitLab, Bitbucket
- Include cloud services: AWS, Azure, GCP and their specific services
- Include databases: SQL and NoSQL varieties
- Include build tools and package managers
- Include any technology, tool, or concept that appears technical
- Be comprehensive - it's better to include too many than miss skills
- Match skills to the roadmap database when possible, but also include skills not in the roadmap

Return ONLY a comma-separated list of skill names. No explanations, no categories, no formatting - just skills separated by commas.

Resume text:
"""
    
    try:
        # Use more of the text - increase limit significantly
        text_to_analyze = resume_text[:20000] if len(resume_text) > 20000 else resume_text
        print(f"Sending {len(text_to_analyze)} characters to OpenAI for analysis")
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a technical skill extraction assistant. Your job is to extract EVERY technical skill, tool, framework, language, platform, and concept from resumes. Be extremely thorough. Always return a comma-separated list of skills with no explanations or formatting."
                },
                {"role": "user", "content": prompt + text_to_analyze}
            ],
            temperature=0.5,  # Increased for more nuanced extraction
            max_tokens=2000  # Significantly increased to get all skills
        )
        
        raw_ai_response = response.choices[0].message.content.strip()
        skills_text = raw_ai_response
        print(f"OpenAI FULL raw response: {skills_text}")  # Print full response for debugging
        
        # Parse comma-separated skills - handle various formats more robustly
        skills = []
        
        # First, try to clean up the response
        # Remove any markdown code blocks
        skills_text = re.sub(r'```[a-z]*\n?', '', skills_text)
        skills_text = re.sub(r'```', '', skills_text)
        
        # Split by comma, semicolon, newline, or pipe
        for item in re.split(r'[,;\n|]', skills_text):
            item = item.strip()
            
            # Remove common prefixes/suffixes and formatting
            item = re.sub(r'^(skills?|technologies?|tools?|frameworks?|languages?|libraries?|platforms?):\s*', '', item, flags=re.IGNORECASE)
            item = re.sub(r'^[-•*]\s*', '', item)  # Remove bullet points
            item = re.sub(r'^\d+[.)]\s*', '', item)  # Remove numbered lists
            item = re.sub(r'^\([^)]+\)\s*', '', item)  # Remove parenthetical notes
            item = re.sub(r'\s*\([^)]+\)\s*$', '', item)  # Remove trailing parenthetical notes
            
            # Clean up whitespace
            item = item.strip()
            
            # Skip empty items or very short items (unless they're known short skills like "C")
            if item and len(item) > 1:
                # Handle special cases
                if item.lower() in ['c++', 'cpp', 'cxx']:
                    skills.append('C++')
                elif item.lower() == 'html5':
                    skills.append('HTML5')
                elif item.lower() == 'css3':
                    skills.append('CSS3')
                elif item.lower() == 'node.js' or item.lower() == 'nodejs':
                    skills.append('Node.js')
                else:
                    skills.append(item)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_skills = []
        for skill in skills:
            skill_lower = skill.lower()
            if skill_lower not in seen:
                seen.add(skill_lower)
                unique_skills.append(skill)
        
        print(f"Extracted {len(unique_skills)} unique skills from OpenAI: {unique_skills[:10]}...")
        # Return skills with raw AI response for debugging
        return {
            'extracted_skills': unique_skills,
            'raw_ai_response': raw_ai_response
        }
    except Exception as e:
        print(f"Error calling OpenAI: {e}")
        import traceback
        traceback.print_exc()
        return {
            'extracted_skills': [],
            'raw_ai_response': f'Error: {str(e)}'
        }


def match_skills_to_roadmap_ai(extracted_skills, resume_text, roadmap_data):
    """Use AI to comprehensively match extracted skills to roadmap skills without keyword mapping."""
    try:
        # Get roadmap skills structure for AI context
        roadmap_skills_list = roadmap_data.get('skills', [])[:200]  # Limit to avoid token issues
        roadmap_roles_list = roadmap_data.get('roles', [])[:50]
        
        # Build roadmap context for AI
        roadmap_context = f"""
ROADMAP SKILLS DATABASE (sample - comprehensive matching should consider all skills):
{', '.join(roadmap_skills_list[:150])}

ROADMAP ROLES (skills may be associated with these roles):
{', '.join(roadmap_roles_list[:30])}
"""
        
        # Build extracted skills list
        skills_list = ', '.join(extracted_skills[:100])
        
        prompt = f"""You are a technical skill matching expert. Your task is to comprehensively match skills extracted from a resume to skills in the roadmap database.

IMPORTANT: Do NOT use simple keyword matching. Instead, use comprehensive semantic understanding:
- Consider skill variations, synonyms, and related technologies
- Match based on meaning and context, not just exact names
- Consider that "React" matches "React.js", "ReactJS", "React Native" concepts
- Consider that "Python" matches "Python 3", "Python programming", "Python development"
- Consider related frameworks and tools (e.g., "Django" is related to "Python")
- Consider domain knowledge (e.g., "Machine Learning" relates to "AI", "ML", "Deep Learning")
- Match skills even if they're mentioned in different contexts or with different terminology

EXTRACTED SKILLS FROM RESUME:
{skills_list}

{roadmap_context}

For each extracted skill, find the BEST matching skill(s) from the roadmap database. Consider:
1. Exact matches (same name)
2. Semantic matches (same meaning, different name)
3. Related matches (closely related technologies)
4. Contextual matches (skills used in similar contexts)

Return a JSON object with this structure:
{{
  "matched_skills": [
    {{
      "extracted_skill": "React",
      "roadmap_skill": "React",
      "match_confidence": "exact",
      "keywords": ["react", "reactjs", "react.js"],
      "reasoning": "Exact match - React is a core frontend framework"
    }},
    {{
      "extracted_skill": "Python for ML",
      "roadmap_skill": "Python",
      "match_confidence": "semantic",
      "keywords": ["python", "python3", "python programming"],
      "reasoning": "Semantic match - Python for ML is a specific use case of Python"
    }}
  ]
}}

Resume Context (first 10000 chars for skill context):
{resume_text[:10000]}

Return ONLY valid JSON, no explanations. Include all extracted skills that have reasonable matches in the roadmap."""
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a technical skill matching expert. Match skills comprehensively using semantic understanding, not keyword matching. Return only valid JSON."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=3000,
            response_format={"type": "json_object"}
        )
        
        raw_ai_response = response.choices[0].message.content
        match_data = json.loads(raw_ai_response)
        
        # Format matched skills
        matched_skills = []
        seen_roadmap_skills = set()
        
        for match in match_data.get('matched_skills', []):
            roadmap_skill = match.get('roadmap_skill', '')
            if roadmap_skill and roadmap_skill not in seen_roadmap_skills:
                # Get keywords from roadmap if available
                keywords = match.get('keywords', [])
                
                matched_skills.append({
                    'skill': roadmap_skill,
                    'keywords': keywords,
                    'matched_from': match.get('extracted_skill', ''),
                    'match_confidence': match.get('match_confidence', 'semantic'),
                    'reasoning': match.get('reasoning', '')
                })
                seen_roadmap_skills.add(roadmap_skill)
        
        print(f"AI matched {len(matched_skills)} skills to roadmap")
        # Return matched skills with raw AI response for debugging
        return {
            'matched_skills': matched_skills,
            'raw_ai_response': raw_ai_response
        }
        
    except Exception as e:
        print(f"Error in AI-based skill matching: {e}")
        import traceback
        traceback.print_exc()
        # Fallback: return empty list (don't use keyword matching)
        return []


def match_skills_to_roadmap(extracted_skills, roadmap_keywords):
    """Legacy function - kept for compatibility but should use match_skills_to_roadmap_ai instead."""
    # This function is deprecated - use match_skills_to_roadmap_ai for AI-based matching
    return []


def load_existing_resumes():
    """Load existing resume data from JSON file."""
    if OUTPUT_JSON_FILE.exists():
        try:
            with open(OUTPUT_JSON_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading existing resumes: {e}")
            return {'resumes': []}
    return {'resumes': []}


def save_resume_data(resume_data):
    """Save or update resume data in JSON file."""
    existing_data = load_existing_resumes()
    
    # Add new resume entry
    existing_data['resumes'].append(resume_data)
    
    # Save to file
    with open(OUTPUT_JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, indent=2, ensure_ascii=False)
    
    return existing_data


@app.route('/')
def index():
    """Render the upload page."""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_resume():
    """Handle resume upload and processing."""
    if 'resume' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['resume']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Allowed: PDF, DOCX, TXT'}), 400
    
    try:
        # Save uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Extract text from resume
        resume_text = extract_text_from_resume(filepath, filename)
        
        print(f"Extracted text length: {len(resume_text) if resume_text else 0} characters")
        print(f"First 200 chars: {resume_text[:200] if resume_text else 'None'}...")
        
        if not resume_text or len(resume_text.strip()) < 20:
            return jsonify({
                'error': f'Could not extract text from resume or file is too short. Extracted {len(resume_text) if resume_text else 0} characters.'
            }), 400
        
        # Extract skills using OpenAI
        skill_extraction_result = extract_skills_with_openai(resume_text)
        
        # Handle both old format (list) and new format (dict with raw_ai_response)
        if isinstance(skill_extraction_result, dict):
            extracted_skills = skill_extraction_result.get('extracted_skills', [])
            skill_extraction_ai_response = skill_extraction_result.get('raw_ai_response', '')
        else:
            extracted_skills = skill_extraction_result
            skill_extraction_ai_response = ''
        
        print(f"OpenAI extracted {len(extracted_skills)} skills")
        
        # ALWAYS also run pattern-based extraction to catch anything OpenAI might miss
        print("Running pattern-based extraction as supplement...")
        pattern_skills = extract_skills_pattern_based(resume_text)
        print(f"Pattern-based extraction found {len(pattern_skills)} skills")
        
        # Combine both methods - union of both sets
        all_skills_set = set()
        for skill in extracted_skills:
            all_skills_set.add(skill)
        for skill in pattern_skills:
            all_skills_set.add(skill)
        
        extracted_skills = list(all_skills_set)
        print(f"Combined extraction found {len(extracted_skills)} total unique skills")
        
        # If still very few skills, that's a problem
        if len(extracted_skills) < 3:
            print("WARNING: Very few skills extracted. Check text extraction.")
        
        if not extracted_skills:
            return jsonify({
                'error': 'No skills could be extracted from resume. Please ensure the resume contains technical skills and is in a readable format (PDF, DOCX, or TXT).',
                'debug': {
                    'text_length': len(resume_text),
                    'text_preview': resume_text[:500]
                }
            }), 400
        
        # Load roadmap data for AI-based comprehensive matching
        roadmap_data = extract_roadmap_skill_list()
        
        # Match skills to roadmap format using AI (comprehensive, not keyword-based)
        print("Using AI to comprehensively match skills to roadmap...")
        skill_matching_result = match_skills_to_roadmap_ai(extracted_skills, resume_text, roadmap_data)
        
        # Handle both old format (list) and new format (dict with raw_ai_response)
        if isinstance(skill_matching_result, dict):
            matched_skills = skill_matching_result.get('matched_skills', [])
            skill_matching_ai_response = skill_matching_result.get('raw_ai_response', '')
        else:
            matched_skills = skill_matching_result
            skill_matching_ai_response = ''
        
        # Get selected job for comparison (if provided) - need job context for proficiency calculation
        selected_job_id = request.form.get('selected_job_id')
        job_for_proficiency = None
        job_skills_for_proficiency = None
        
        if selected_job_id:
            job_for_proficiency = get_job_by_index(int(selected_job_id))
            if job_for_proficiency:
                job_skills_for_proficiency = job_for_proficiency.get('skills', [])
                # Expand job description first
                print("Expanding job description for proficiency assessment...")
                expanded_desc = expand_job_description(
                    job_for_proficiency.get('job_title', ''),
                    job_for_proficiency.get('company_name', ''),
                    job_for_proficiency.get('job_description', ''),
                    job_skills_for_proficiency
                )
                job_for_proficiency['expanded_description'] = expanded_desc
        
        # Calculate proficiency scores for each skill using AI (with job context if available)
        print("Calculating proficiency scores for skills...")
        job_description_for_proficiency = None
        if job_for_proficiency:
            job_description_for_proficiency = job_for_proficiency.get('expanded_description') or job_for_proficiency.get('job_description', '')
        
        proficiency_result = calculate_skill_proficiency(
            extracted_skills, 
            resume_text,
            job_description=job_description_for_proficiency,
            job_skills=job_skills_for_proficiency
        )
        
        # Handle both old format (list) and new format (dict with raw_ai_response)
        if isinstance(proficiency_result, dict):
            skills_with_proficiency = proficiency_result.get('skills_with_proficiency', [])
            proficiency_ai_response = proficiency_result.get('raw_ai_response', '')
        else:
            skills_with_proficiency = proficiency_result
            proficiency_ai_response = ''
        
        # Update matched_skills with proficiency scores
        proficiency_map = {skill['name'].lower(): skill['proficiency'] for skill in skills_with_proficiency}
        for skill in matched_skills:
            skill_name_lower = skill.get('skill', '').lower()
            if skill_name_lower in proficiency_map:
                skill['proficiency'] = proficiency_map[skill_name_lower]
            else:
                # Try to find proficiency from raw skills
                for raw_skill in extracted_skills:
                    if raw_skill.lower() == skill_name_lower:
                        skill['proficiency'] = proficiency_map.get(raw_skill.lower(), 3)  # Default to 3
                        break
                else:
                    skill['proficiency'] = 3  # Default proficiency
        
        # Perform comprehensive AI-based job matching (AI is the ONLY source of truth)
        job_match_data = None
        if selected_job_id:
            print("=" * 60)
            print("CALLING AI FOR JOB MATCHING - NO RULE-BASED LOGIC WILL BE USED")
            print("=" * 60)
            job_match_data = compare_resume_to_job_ai(matched_skills, extracted_skills, resume_text, selected_job_id, skills_with_proficiency)
            
            # Verify AI was used (not rule-based fallback)
            if job_match_data and job_match_data.get('ai_generated'):
                print("[OK] AI results received and will be used directly")
            elif job_match_data and job_match_data.get('error'):
                print(f"[ERROR] AI failed: {job_match_data.get('error')}")
            else:
                print("[WARNING] Unexpected response structure")
        
        # Create resume data entry
        resume_data = {
            'id': datetime.now().strftime('%Y%m%d_%H%M%S_%f'),
            'filename': filename,
            'uploaded_at': datetime.now().isoformat(),
            'extracted_skills_raw': extracted_skills,
            'matched_skills': matched_skills,
            'skills_with_proficiency': skills_with_proficiency,
            'total_skills_extracted': len(extracted_skills),
            'total_skills_matched': len(matched_skills),
            'debug_ai_responses': {
                'skill_extraction': skill_extraction_ai_response,
                'skill_matching': skill_matching_ai_response,
                'proficiency_calculation': proficiency_ai_response
            }
        }
        
        # Add job match data if available
        if job_match_data:
            resume_data['job_match'] = job_match_data
            # Add job matching AI response to debug
            if 'raw_ai_response' in job_match_data:
                resume_data['debug_ai_responses']['job_matching'] = job_match_data.get('raw_ai_response', '')
        
        # Save to JSON file
        save_resume_data(resume_data)
        
        # Clean up uploaded file (optional - you may want to keep it)
        # os.remove(filepath)
        
        return jsonify({
            'success': True,
            'message': 'Resume processed successfully',
            'data': resume_data
        })
        
    except Exception as e:
        print(f"Error processing resume: {e}")
        return jsonify({'error': f'Error processing resume: {str(e)}'}), 500


@app.route('/resumes', methods=['GET'])
def get_resumes():
    """Get all processed resumes."""
    data = load_existing_resumes()
    return jsonify(data)


def get_job_by_index(job_index):
    """Get a specific job by index from LinkedIn jobs data."""
    try:
        if not LINKEDIN_JOBS_FILE.exists():
            return None
        
        with open(LINKEDIN_JOBS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        jobs = data.get('jobs', [])
        
        # Get unique jobs
        unique_jobs = []
        seen_titles = set()
        
        for job in jobs:
            job_title = job.get('job_title', '')
            if job_title and job_title not in seen_titles:
                unique_jobs.append(job)
                seen_titles.add(job_title)
        
        if 0 <= job_index < len(unique_jobs):
            return unique_jobs[job_index]
        return None
    except Exception as e:
        print(f"Error loading job: {e}")
        return None


def expand_job_description(job_title, company_name, job_description, job_skills):
    """Use AI to expand and elaborate on the job description to add more substance about experience requirements."""
    try:
        skills_list = ', '.join([skill.get('name', '') if isinstance(skill, dict) else str(skill) for skill in job_skills[:20]])
        
        prompt = f"""You are a technical recruiter writing a detailed job description. Expand and elaborate on the following job posting to provide more substance about:
- Required experience levels for each skill
- Specific use cases and contexts where skills are needed
- Years of experience expected
- Project complexity and scale
- Team collaboration and leadership aspects
- Technical depth and expertise required

Job Title: {job_title}
Company: {company_name}

Original Description:
{job_description[:3000]}

Required Skills: {skills_list}

Expand the description to be more specific about:
1. What level of proficiency is needed for each skill (junior/mid/senior)
2. What kind of projects or work will use these skills
3. How many years of experience is expected
4. What specific tasks or responsibilities require these skills
5. Any advanced or specialized knowledge needed

Return an expanded job description (300-500 words) that provides more detail about experience requirements and skill expectations. Be specific and realistic."""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a technical recruiter expanding job descriptions to clarify experience requirements. Provide detailed, specific information about skill proficiency expectations."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,  # Increased for more detailed expansion
            max_tokens=1000  # Increased for more comprehensive expansion
        )
        
        expanded_description = response.choices[0].message.content.strip()
        print(f"Expanded job description (length: {len(expanded_description)} chars)")
        return expanded_description
        
    except Exception as e:
        print(f"Error expanding job description: {e}")
        import traceback
        traceback.print_exc()
        return job_description  # Return original if expansion fails


def calculate_skill_proficiency(extracted_skills, resume_text, job_description=None, job_skills=None):
    """Use AI to calculate proficiency (1-5) for each skill based on resume context and job requirements."""
    if not extracted_skills:
        return []
    
    try:
        # Prepare skills list for AI analysis
        skills_list = ', '.join(extracted_skills[:50])  # Limit to avoid token issues
        
        # Build context about job requirements if available
        job_context = ""
        if job_description and job_skills:
            job_skills_list = ', '.join([skill.get('name', '') if isinstance(skill, dict) else str(skill) for skill in job_skills[:15]])
            # Use full expanded description, not truncated
            job_context = f"""

JOB REQUIREMENTS CONTEXT:
Job Description: {job_description}
Required Skills: {job_skills_list}

When rating proficiency, consider how well the candidate's experience matches the job requirements. A skill that is critical for the job should be rated higher if the candidate has strong experience, and lower if they lack relevant experience."""
        
        prompt = f"""You are a technical recruiter analyzing resume proficiency. Rate each skill (1-5) using COMPREHENSIVE analysis based on the candidate's experience and the expanded job description requirements.

CRITICAL: Use comprehensive logic, not rule-based scoring. Consider:
- Depth and breadth of experience with the skill
- Complexity of projects where the skill was used
- Years of experience and progression
- How well the candidate's experience aligns with the job's specific requirements
- Quality indicators (leadership, mentoring, architecture decisions, etc.)
- Context from the expanded job description about what proficiency level is needed

Proficiency Scale (use full range, not binary):
1 = Mentioned only briefly, no evidence of experience, or insufficient for job requirements
2 = Basic familiarity, mentioned in passing or education, minimal practical experience
3 = Some experience, used in projects or work, meets basic job requirements
4 = Strong experience, significant usage and understanding, exceeds basic requirements
5 = Expert level, deep expertise, leadership, or extensive experience, exceeds job requirements

{job_context}

PROFICIENCY COMPARISON LOGIC (comprehensive AI analysis):
When job context is provided, use comprehensive analysis:
- Read the expanded job description carefully to understand required proficiency levels
- Compare candidate's actual experience (from resume) with job requirements
- Consider: Does the candidate have the depth needed? The breadth? The right context?
- Example: Job requires "3+ years Python for backend APIs" and candidate shows "2 years Python for data analysis" → Rate 2-3/5 (has Python but different context)
- Example: Job requires "Python for ML" and candidate shows "5 years Python for web development" → Rate 3-4/5 (strong Python but different domain)
- Example: Job requires "React with Redux" and candidate shows "React + Redux in production for 3 years" → Rate 4-5/5 (exact match)
- Use nuanced scoring: 2.5, 3.5, 4.5 are valid if the skill is between levels

Return a JSON object with skill names as keys and proficiency scores (1-5, can use decimals like 2.5, 3.5) as values.
Example: {{"Python": 4.5, "React": 3, "Docker": 2.5}}

Skills to evaluate: {skills_list}

Resume text (comprehensive context):
{resume_text[:20000]}

Return ONLY valid JSON, no explanations. Use comprehensive analysis, not simple rules."""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a technical recruiter analyzing resume proficiency using comprehensive logic. Consider experience depth, job requirements alignment, and context. Return only valid JSON with skill names and proficiency scores (1-5, can use decimals)."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,  # Increased for more nuanced scoring
            max_tokens=2500,  # Increased for more detailed analysis
            response_format={"type": "json_object"}
        )
        
        raw_ai_response = response.choices[0].message.content
        proficiency_data = json.loads(raw_ai_response)
        
        # Format as list
        skills_with_proficiency = []
        for skill_name, proficiency in proficiency_data.items():
            # Ensure proficiency is between 1-5 (allow decimals)
            proficiency = max(1.0, min(5.0, float(proficiency)))
            skills_with_proficiency.append({
                'name': skill_name,
                'proficiency': proficiency
            })
        
        print(f"Calculated proficiency for {len(skills_with_proficiency)} skills")
        # Return with raw AI response for debugging
        return {
            'skills_with_proficiency': skills_with_proficiency,
            'raw_ai_response': raw_ai_response
        }
        
    except Exception as e:
        print(f"Error calculating proficiency: {e}")
        import traceback
        traceback.print_exc()
        # Return default proficiency of 3 for all skills
        return [{'name': skill, 'proficiency': 3} for skill in extracted_skills]


def compare_resume_to_job_ai(matched_skills, extracted_skills_raw, resume_text, job_index, skills_with_proficiency):
    """Use AI to comprehensively compare resume skills to job requirements with percentage matching."""
    try:
        job = get_job_by_index(int(job_index))
        if not job:
            return None
        
        job_skills = job.get('skills', [])
        if not job_skills:
            return None
        
        # Use expanded description if already available, otherwise expand it
        expanded_description = job.get('expanded_description')
        if not expanded_description:
            print("Expanding job description for better matching...")
            original_description = job.get('job_description', '')
            expanded_description = expand_job_description(
                job.get('job_title', ''),
                job.get('company_name', ''),
                original_description,
                job_skills
            )
        
        # Build skill information for AI
        resume_skills_info = []
        proficiency_map = {s['name'].lower(): s['proficiency'] for s in skills_with_proficiency}
        
        for skill in matched_skills:
            skill_name = skill.get('skill', '')
            proficiency = skill.get('proficiency', proficiency_map.get(skill_name.lower(), 3))
            keywords = ', '.join(skill.get('keywords', []))
            resume_skills_info.append(f"{skill_name} (proficiency: {proficiency}/5, keywords: {keywords})")
        
        # Add raw skills not in matched_skills
        for skill_name in extracted_skills_raw:
            skill_lower = skill_name.lower()
            if not any(s.get('skill', '').lower() == skill_lower for s in matched_skills):
                proficiency = proficiency_map.get(skill_lower, 3)
                resume_skills_info.append(f"{skill_name} (proficiency: {proficiency}/5)")
        
        resume_skills_str = '\n'.join(resume_skills_info[:100])  # Limit to avoid token issues
        
        # Build job skills info
        job_skills_info = []
        for skill in job_skills:
            skill_name = skill.get('name', '')
            # Get topics from original job data if available
            topics = skill.get('topics', [])
            topics_str = ', '.join([t if isinstance(t, str) else t.get('topic', '') for t in topics[:3]])
            job_skills_info.append(f"{skill_name}" + (f" (topics: {topics_str})" if topics_str else ""))
        
        job_skills_str = '\n'.join(job_skills_info)
        
        prompt = f"""You are a technical recruiter comparing a candidate's resume to a job requirement.

Analyze how well the candidate's skills match the job requirements. Consider:
1. Skill names (exact and similar matches)
2. Keywords and related terms
3. Topics and concepts
4. Proficiency levels (a skill with proficiency 5/5 is better than 2/5)
5. Context and experience depth from the resume
6. How well the candidate's experience matches the EXPANDED job description requirements
7. Partial matches for related skills (e.g., "React" when job needs "React + Redux" = 60-70%)

CRITICAL INSTRUCTIONS FOR SCORING (MANDATORY):
- Use the FULL 0-100% range, NOT binary (0%, 50%, 100%)
- AVOID clustering around 0%, 50%, 100% - these are red flags
- Provide nuanced scores distributed across the range: 12%, 23%, 34%, 47%, 56%, 67%, 73%, 78%, 84%, 91%, 93%, etc.
- Assign partial credit for related or partially covered skills
- Compare required vs actual proficiency to determine match
- Consider skill depth, context alignment, and relevance
- Most realistic scores should be between 10-90% (avoid extremes unless truly warranted)
- Partial matches: If job needs "React with Redux" and candidate has "React" → 60-70% (NOT 50% or 100%)
- Domain overlap: If job needs "Python for ML" and candidate has "Python for web" → 40-50% (NOT 0% or 50%)
- Skill mentioned but weak context: 15-25% (NOT 0% or 50%)
- Skill strong but different use case: 45-65% (NOT 50% or 100%)
- Skill strong and aligned: 75-95% (NOT 50% or 100%)
- DO NOT round to nearest 10% or 25% - use precise percentages

PROFICIENCY COMPARISON LOGIC:
For each job skill, compare:
- Required proficiency level (from expanded job description)
- Candidate's actual proficiency (from resume analysis)
- Calculate match percentage based on this comparison
- Example: Job requires Python 4/5, candidate has 3/5 → 75% match
- Example: Job requires Python 2/5, candidate has 5/5 → 100% match (overqualified but excellent)
- Example: Job requires Python 4/5, candidate has 2/5 → 50% match (has skill but below requirement)
- Example: Job requires Python 4/5, candidate has 4/5 → 95% match (perfect alignment)

For EACH job skill, provide:
- A match percentage (0-100%) indicating how well the candidate matches this requirement
- Reasoning based on skills, keywords, topics, proficiency comparison, and how their experience aligns with the job description
- Matched resume skills that contributed to this match

Return a JSON object with this structure:
{{
  "job_skills": [
    {{
      "skill_name": "Python",
      "match_percentage": 78.5,
      "matched_resume_skills": ["Python", "Django"],
      "reasoning": "Candidate has Python with proficiency 4/5. The expanded job description requires 3+ years of Python for backend development at proficiency 4/5. The candidate's resume shows 4 years of Python experience with Django, closely matching the requirements. However, the job emphasizes API development which the candidate has experience with, resulting in a strong 78.5% match."
    }}
  ],
  "overall_match_percentage": 72.3
}}

EXPANDED JOB DESCRIPTION (provides detailed requirements):
{expanded_description}

Job Skills List:
{job_skills_str}

Candidate Skills (with proficiency):
{resume_skills_str}

Resume Context (comprehensive - first 20000 chars):
{resume_text[:20000]}

IMPORTANT: 
- When calculating match percentages, heavily weight how well the candidate's experience (from resume context) aligns with the specific requirements mentioned in the EXPANDED JOB DESCRIPTION
- A candidate with high proficiency in a skill that matches the job's specific use cases should score higher than someone with the same skill but different experience context
- Use the FULL percentage range - avoid binary thinking
- Provide detailed reasoning that explains the specific percentage score

Return ONLY valid JSON, no explanations."""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a technical recruiter analyzing skill matches. CRITICAL: Use the FULL 0-100% range with nuanced scores (12%, 34%, 67%, 84%, etc.). AVOID binary clustering (0%, 50%, 100%). Consider names, keywords, topics, proficiency comparison, partial matches, and alignment with expanded job description. Return only valid JSON with precise percentage scores distributed across the full range."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,  # Increased for more nuanced percentage scoring
            max_tokens=5000,
            response_format={"type": "json_object"}
        )
        
        raw_ai_response = response.choices[0].message.content
        match_data = json.loads(raw_ai_response)
        
        print(f"AI Response received. Job skills count: {len(match_data.get('job_skills', []))}")
        
        # Format the response - NO BINARY THRESHOLD, show all skills with percentages
        job_skill_matches = match_data.get('job_skills', [])
        overall_match = match_data.get('overall_match_percentage', 0)
        
        # Validate that we got proper data from AI
        if not job_skill_matches:
            print("ERROR: AI returned empty job_skills. This should not happen.")
            print(f"Full AI response: {match_data}")
            # DO NOT fall back to rule-based - return error structure instead
            return {
                'job_title': job.get('job_title', ''),
                'company_name': job.get('company_name', ''),
                'total_job_skills': len(job_skills),
                'overall_match_percentage': 0,
                'all_skills': [],
                'strong_count': 0,
                'moderate_count': 0,
                'weak_count': 0,
                'error': 'AI returned empty results',
                'expanded_description': expanded_description
            }
        
        # Debug: Print sample percentages to verify they're not binary
        sample_percentages = [s.get('match_percentage', 0) for s in job_skill_matches[:5]]
        print(f"AI-generated match percentages (sample): {sample_percentages}")
        print(f"Using AI results directly - NO rule-based processing applied")
        
        # Use AI results DIRECTLY - no rule-based logic, no thresholds, no modifications
        # Only format for display (status is purely cosmetic for UI)
        all_skills_with_matches = []
        
        for job_skill_match in job_skill_matches:
            skill_name = job_skill_match.get('skill_name', '')
            # Use AI percentage DIRECTLY - do not modify or apply rules
            match_pct = job_skill_match.get('match_percentage', 0)
            
            # Status is ONLY for UI color coding - does not affect the percentage
            # AI percentage is the source of truth
            if match_pct >= 75:
                status = 'strong'  # UI display only
            elif match_pct >= 50:
                status = 'moderate'  # UI display only
            else:
                status = 'weak'  # UI display only
            
            # Preserve ALL AI data - no filtering, no modification
            all_skills_with_matches.append({
                'skill': skill_name,
                'match_percentage': round(match_pct, 1),  # AI percentage used directly, round only for display
                'status': status,  # Purely cosmetic for UI color coding - does NOT affect percentage
                'matched_resume_skills': job_skill_match.get('matched_resume_skills', []),
                'reasoning': job_skill_match.get('reasoning', '')  # AI reasoning preserved exactly
            })
        
        # Sort by match percentage (highest first) for better UX
        all_skills_with_matches.sort(key=lambda x: x['match_percentage'], reverse=True)
        
        # Calculate counts by status for statistics (UI display only - does not affect AI percentages)
        strong_count = sum(1 for s in all_skills_with_matches if s['status'] == 'strong')
        moderate_count = sum(1 for s in all_skills_with_matches if s['status'] == 'moderate')
        weak_count = sum(1 for s in all_skills_with_matches if s['status'] == 'weak')
        
        # Return AI results directly - no rule-based processing
        # All percentages come from AI, status is only for UI display
        return {
            'job_title': job.get('job_title', ''),
            'company_name': job.get('company_name', ''),
            'total_job_skills': len(job_skills),
            'overall_match_percentage': overall_match,  # AI percentage used directly (no rounding)
            'all_skills': all_skills_with_matches,  # All AI results preserved exactly
            'strong_count': strong_count,  # Calculated from AI percentages (UI only)
            'moderate_count': moderate_count,  # Calculated from AI percentages (UI only)
            'weak_count': weak_count,  # Calculated from AI percentages (UI only)
            'detailed_matches': job_skill_matches,  # Raw AI response preserved
            'expanded_description': expanded_description,
            'raw_ai_response': raw_ai_response,  # Raw AI response for debugging
            'ai_generated': True  # Flag to indicate this is AI-generated, not rule-based
        }
        
    except Exception as e:
        print(f"ERROR in AI-based job comparison: {e}")
        import traceback
        traceback.print_exc()
        print("CRITICAL: AI comparison failed. Returning error structure instead of rule-based fallback.")
        # DO NOT use rule-based fallback - AI is the source of truth
        # Return error structure so frontend knows AI failed
        try:
            job = get_job_by_index(int(job_index))
            return {
                'job_title': job.get('job_title', '') if job else '',
                'company_name': job.get('company_name', '') if job else '',
                'total_job_skills': len(job.get('skills', [])) if job else 0,
                'overall_match_percentage': 0,
                'all_skills': [],
                'strong_count': 0,
                'moderate_count': 0,
                'weak_count': 0,
                'error': f'AI comparison failed: {str(e)}',
                'expanded_description': ''
            }
        except:
            return None


def compare_resume_to_job(matched_skills, extracted_skills_raw, job_index):
    """DEPRECATED: Rule-based fallback function. DO NOT USE - use compare_resume_to_job_ai() instead.
    
    This function uses keyword-based matching and rule-based logic, which produces binary results.
    All job matching should use compare_resume_to_job_ai() which uses comprehensive AI analysis.
    """
    try:
        job = get_job_by_index(int(job_index))
        if not job:
            return None
        
        job_skills = job.get('skills', [])
        if not job_skills:
            return None
        
        # Load roadmap data for keyword and topic matching
        roadmap_keywords = load_roadmap_skills()
        
        # Build comprehensive resume skill sets
        resume_skill_names = set()
        resume_keywords = set()
        resume_topics = set()
        
        # From matched skills (roadmap format) - includes keywords
        for skill in matched_skills:
            skill_name = skill.get('skill', '').lower()
            if skill_name:
                resume_skill_names.add(skill_name)
            # Add keywords
            for keyword in skill.get('keywords', []):
                resume_keywords.add(keyword.lower())
        
        # From raw extracted skills
        for skill in extracted_skills_raw:
            resume_skill_names.add(skill.lower())
        
        # Build comprehensive job skill sets with keywords and topics
        job_skill_names = set()
        job_keywords = set()
        job_topics = set()
        
        for skill in job_skills:
            skill_name = skill.get('name', '').lower()
            if skill_name:
                job_skill_names.add(skill_name)
            
            # Get keywords and topics from roadmap for each job skill
            if skill_name in roadmap_keywords:
                for skill_data in roadmap_keywords[skill_name]:
                    # Add keywords
                    for keyword in skill_data.get('keywords', []):
                        job_keywords.add(keyword.lower())
        
        # Also check original job data for topics if available
        # (The job skills might have topics in the original data structure)
        for skill in job.get('skills', []):
            if 'topics' in skill:
                for topic in skill.get('topics', []):
                    if isinstance(topic, str):
                        job_topics.add(topic.lower())
                    elif isinstance(topic, dict):
                        topic_name = topic.get('topic', '')
                        if topic_name:
                            job_topics.add(topic_name.lower())
        
        # Calculate matches using multiple strategies
        exact_matches = resume_skill_names.intersection(job_skill_names)
        
        # Keyword-based matches
        keyword_matches = set()
        for job_skill in job_skill_names:
            # Check if resume has keywords matching job skill
            if job_skill in roadmap_keywords:
                for skill_data in roadmap_keywords[job_skill]:
                    for keyword in skill_data.get('keywords', []):
                        if keyword.lower() in resume_keywords or keyword.lower() in resume_skill_names:
                            keyword_matches.add(job_skill)
                            break
        
        # Partial/containment matches
        partial_matches = set()
        for job_skill in job_skill_names:
            for resume_skill in resume_skill_names:
                # Check if one contains the other (handles variations)
                if job_skill in resume_skill or resume_skill in job_skill:
                    if len(job_skill) >= 3 and len(resume_skill) >= 3:  # Only if significant
                        partial_matches.add(job_skill)
                # Also check if keywords match
                if job_skill in resume_keywords or resume_skill in job_keywords:
                    partial_matches.add(job_skill)
        
        # Topic-based matches (if topics are available)
        topic_matches = set()
        if job_topics:
            for job_topic in job_topics:
                # Check if resume keywords match job topics
                if job_topic in resume_keywords or job_topic in resume_skill_names:
                    # Find which job skill this topic belongs to
                    for skill in job_skills:
                        skill_name = skill.get('name', '').lower()
                        if skill_name:
                            topic_matches.add(skill_name)
        
        # Combine all matches (union of all match types)
        all_matched_skills = exact_matches.union(keyword_matches).union(partial_matches).union(topic_matches)
        
        # Calculate percentage
        total_job_skills = len(job_skill_names)
        matched_count = len(all_matched_skills)
        match_percentage = (matched_count / total_job_skills * 100) if total_job_skills > 0 else 0
        
        # Create unified skill list with match percentages (for fallback, use simple scoring)
        all_skills_with_matches = []
        
        # Skills that matched (assign 80-100% based on match type)
        for skill_name in all_matched_skills:
            # Determine match strength based on match type
            if skill_name in exact_matches:
                match_pct = 95.0  # Exact match
            elif skill_name in keyword_matches:
                match_pct = 75.0  # Keyword match
            elif skill_name in partial_matches:
                match_pct = 60.0  # Partial match
            else:
                match_pct = 50.0  # Topic match
            
            status = 'strong' if match_pct >= 75 else 'moderate' if match_pct >= 50 else 'weak'
            all_skills_with_matches.append({
                'skill': skill_name.title(),
                'match_percentage': match_pct,
                'status': status,
                'matched_resume_skills': [],
                'reasoning': f"Matched via {'exact' if skill_name in exact_matches else 'keyword' if skill_name in keyword_matches else 'partial' if skill_name in partial_matches else 'topic'} matching"
            })
        
        # Skills that didn't match (assign 0-30% based on partial relevance)
        for skill_name in (job_skill_names - all_matched_skills):
            all_skills_with_matches.append({
                'skill': skill_name.title(),
                'match_percentage': 15.0,  # Low but not zero
                'status': 'weak',
                'matched_resume_skills': [],
                'reasoning': 'Skill not found in resume'
            })
        
        # Sort by match percentage
        all_skills_with_matches.sort(key=lambda x: x['match_percentage'], reverse=True)
        
        # Calculate counts
        strong_count = sum(1 for s in all_skills_with_matches if s['status'] == 'strong')
        moderate_count = sum(1 for s in all_skills_with_matches if s['status'] == 'moderate')
        weak_count = sum(1 for s in all_skills_with_matches if s['status'] == 'weak')
        
        return {
            'job_title': job.get('job_title', ''),
            'company_name': job.get('company_name', ''),
            'total_job_skills': total_job_skills,
            'overall_match_percentage': round(match_percentage, 1),
            'all_skills': all_skills_with_matches,  # Unified list
            'strong_count': strong_count,
            'moderate_count': moderate_count,
            'weak_count': weak_count,
            'exact_matches': len(exact_matches),
            'keyword_matches': len(keyword_matches),
            'partial_matches': len(partial_matches),
            'topic_matches': len(topic_matches)
        }
    except Exception as e:
        print(f"Error comparing resume to job: {e}")
        import traceback
        traceback.print_exc()
        return None


@app.route('/jobs', methods=['GET'])
def get_top_jobs():
    """Get top 5 jobs from LinkedIn jobs data."""
    try:
        if not LINKEDIN_JOBS_FILE.exists():
            return jsonify({'error': 'LinkedIn jobs file not found'}), 404
        
        with open(LINKEDIN_JOBS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        jobs = data.get('jobs', [])
        
        # Get top 5 jobs (first 5 unique job titles)
        top_jobs = []
        seen_titles = set()
        
        for job in jobs:
            job_title = job.get('job_title', '')
            if job_title and job_title not in seen_titles and len(top_jobs) < 5:
                # Format job data without topics
                formatted_job = {
                    'job_title': job.get('job_title', ''),
                    'company_name': job.get('company_name', ''),
                    'job_description': job.get('job_description', ''),
                    'skills': []
                }
                
                # Extract skills (only name, no topics)
                for skill in job.get('skills', []):
                    formatted_job['skills'].append({
                        'name': skill.get('name', '')
                    })
                
                top_jobs.append(formatted_job)
                seen_titles.add(job_title)
        
        return jsonify({'jobs': top_jobs})
    except Exception as e:
        print(f"Error loading jobs: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error loading jobs: {str(e)}'}), 500


if __name__ == '__main__':
    print(f"Starting Resume Parser server...")
    print(f"Roadmap skills file: {ROADMAP_SKILLS_FILE}")
    print(f"Output JSON file: {OUTPUT_JSON_FILE}")
    print(f"OpenAI API key loaded: {'Yes' if openai_api_key else 'No'}")
    app.run(debug=True, host='127.0.0.1', port=5000)

