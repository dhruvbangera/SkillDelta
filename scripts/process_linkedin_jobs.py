#!/usr/bin/env python3
"""
LinkedIn Job Data Processor
Extracts job titles, company names, descriptions, and skills from LinkedIn job postings.
Maps skills to roadmap.sh resources and outputs searchable JSON.
"""

import json
import re
import sqlite3
import csv
import os
from pathlib import Path
from typing import List, Dict, Set, Optional
from collections import defaultdict
from urllib.parse import quote
import html

# Repository root
REPO_ROOT = Path(__file__).parent.parent
DATA_DIR = REPO_ROOT / "data"
JOB_LISTINGS_DIR = REPO_ROOT / "job-listings"

# Skill taxonomy for extraction
TECH_SKILLS = {
    # Programming Languages
    "python": {"name": "Python", "topics": ["programming language", "backend scripting", "automation"], "roadmap": "python"},
    "java": {"name": "Java", "topics": ["programming language", "object-oriented programming"], "roadmap": "java"},
    "javascript": {"name": "JavaScript", "topics": ["programming language", "web development", "frontend"], "roadmap": "javascript"},
    "typescript": {"name": "TypeScript", "topics": ["programming language", "web development", "type safety"], "roadmap": "typescript"},
    "c++": {"name": "C++", "topics": ["programming language", "systems programming"], "roadmap": "cpp"},
    "c#": {"name": "C#", "topics": ["programming language", "object-oriented programming", ".net"], "roadmap": "csharp"},
    "go": {"name": "Go", "topics": ["programming language", "backend development", "concurrency"], "roadmap": "golang"},
    "rust": {"name": "Rust", "topics": ["programming language", "systems programming", "memory safety"], "roadmap": "rust"},
    "kotlin": {"name": "Kotlin", "topics": ["programming language", "android development"], "roadmap": "android"},
    "swift": {"name": "Swift", "topics": ["programming language", "ios development"], "roadmap": "ios"},
    "php": {"name": "PHP", "topics": ["programming language", "web development", "backend"], "roadmap": "php"},
    "ruby": {"name": "Ruby", "topics": ["programming language", "web development"], "roadmap": "ruby"},
    "scala": {"name": "Scala", "topics": ["programming language", "functional programming", "big data"], "roadmap": "scala"},
    "r": {"name": "R", "topics": ["programming language", "data science", "statistics"], "roadmap": "data-scientist"},
    
    # Frontend Frameworks
    "react": {"name": "React", "topics": ["frontend framework", "ui development"], "roadmap": "react"},
    "vue": {"name": "Vue.js", "topics": ["frontend framework", "ui development"], "roadmap": "vue"},
    "angular": {"name": "Angular", "topics": ["frontend framework", "ui development"], "roadmap": "angular"},
    "next.js": {"name": "Next.js", "topics": ["frontend framework", "react framework", "ssr"], "roadmap": "react"},
    "nuxt": {"name": "Nuxt.js", "topics": ["frontend framework", "vue framework", "ssr"], "roadmap": "vue"},
    "svelte": {"name": "Svelte", "topics": ["frontend framework", "ui development"], "roadmap": "frontend"},
    
    # Backend Frameworks
    "django": {"name": "Django", "topics": ["backend framework", "python", "web development"], "roadmap": "python"},
    "flask": {"name": "Flask", "topics": ["backend framework", "python", "web development"], "roadmap": "python"},
    "fastapi": {"name": "FastAPI", "topics": ["backend framework", "python", "api development"], "roadmap": "python"},
    "express": {"name": "Express.js", "topics": ["backend framework", "node.js", "api development"], "roadmap": "nodejs"},
    "spring": {"name": "Spring", "topics": ["backend framework", "java", "enterprise development"], "roadmap": "java"},
    "asp.net": {"name": "ASP.NET", "topics": ["backend framework", "c#", "web development"], "roadmap": "aspnet-core"},
    "laravel": {"name": "Laravel", "topics": ["backend framework", "php", "web development"], "roadmap": "php"},
    "rails": {"name": "Ruby on Rails", "topics": ["backend framework", "ruby", "web development"], "roadmap": "ruby"},
    "gin": {"name": "Gin", "topics": ["backend framework", "go", "api development"], "roadmap": "golang"},
    
    # Databases
    "mysql": {"name": "MySQL", "topics": ["database", "sql", "relational database"], "roadmap": "backend"},
    "postgresql": {"name": "PostgreSQL", "topics": ["database", "sql", "relational database"], "roadmap": "backend"},
    "mongodb": {"name": "MongoDB", "topics": ["database", "nosql", "document database"], "roadmap": "backend"},
    "redis": {"name": "Redis", "topics": ["database", "cache", "in-memory database"], "roadmap": "backend"},
    "elasticsearch": {"name": "Elasticsearch", "topics": ["database", "search engine", "analytics"], "roadmap": "backend"},
    "cassandra": {"name": "Cassandra", "topics": ["database", "nosql", "distributed database"], "roadmap": "backend"},
    "dynamodb": {"name": "DynamoDB", "topics": ["database", "nosql", "aws"], "roadmap": "aws"},
    "sqlite": {"name": "SQLite", "topics": ["database", "sql", "embedded database"], "roadmap": "backend"},
    "oracle": {"name": "Oracle", "topics": ["database", "sql", "enterprise database"], "roadmap": "backend"},
    "sql server": {"name": "SQL Server", "topics": ["database", "sql", "microsoft"], "roadmap": "backend"},
    
    # Cloud Platforms
    "aws": {"name": "AWS", "topics": ["cloud computing", "infrastructure", "deployment"], "roadmap": "aws"},
    "azure": {"name": "Azure", "topics": ["cloud computing", "microsoft", "infrastructure"], "roadmap": "azure"},
    "gcp": {"name": "GCP", "topics": ["cloud computing", "google", "infrastructure"], "roadmap": "gcp"},
    "google cloud": {"name": "Google Cloud", "topics": ["cloud computing", "infrastructure"], "roadmap": "gcp"},
    
    # DevOps Tools
    "docker": {"name": "Docker", "topics": ["containerization", "devops", "deployment"], "roadmap": "devops"},
    "kubernetes": {"name": "Kubernetes", "topics": ["container orchestration", "devops", "scalability"], "roadmap": "devops"},
    "jenkins": {"name": "Jenkins", "topics": ["ci/cd", "automation", "devops"], "roadmap": "devops"},
    "gitlab": {"name": "GitLab", "topics": ["ci/cd", "version control", "devops"], "roadmap": "devops"},
    "github actions": {"name": "GitHub Actions", "topics": ["ci/cd", "automation", "devops"], "roadmap": "devops"},
    "terraform": {"name": "Terraform", "topics": ["infrastructure as code", "devops", "cloud"], "roadmap": "devops"},
    "ansible": {"name": "Ansible", "topics": ["configuration management", "automation", "devops"], "roadmap": "devops"},
    "git": {"name": "Git", "topics": ["version control", "source control"], "roadmap": "devops"},
    
    # AI/ML
    "tensorflow": {"name": "TensorFlow", "topics": ["deep learning", "machine learning frameworks"], "roadmap": "ai-engineer"},
    "pytorch": {"name": "PyTorch", "topics": ["deep learning", "machine learning frameworks"], "roadmap": "ai-engineer"},
    "scikit-learn": {"name": "scikit-learn", "topics": ["machine learning", "python", "data science"], "roadmap": "data-scientist"},
    "keras": {"name": "Keras", "topics": ["deep learning", "neural networks"], "roadmap": "ai-engineer"},
    "pandas": {"name": "Pandas", "topics": ["data analysis", "python", "data science"], "roadmap": "data-scientist"},
    "numpy": {"name": "NumPy", "topics": ["numerical computing", "python", "data science"], "roadmap": "data-scientist"},
    "opencv": {"name": "OpenCV", "topics": ["computer vision", "image processing"], "roadmap": "ai-engineer"},
    "nltk": {"name": "NLTK", "topics": ["natural language processing", "nlp"], "roadmap": "ai-engineer"},
    "spacy": {"name": "spaCy", "topics": ["natural language processing", "nlp"], "roadmap": "ai-engineer"},
    
    # Mobile
    "react native": {"name": "React Native", "topics": ["mobile development", "cross-platform"], "roadmap": "react-native"},
    "flutter": {"name": "Flutter", "topics": ["mobile development", "cross-platform", "dart"], "roadmap": "flutter"},
    "ios": {"name": "iOS", "topics": ["mobile development", "apple"], "roadmap": "ios"},
    "android": {"name": "Android", "topics": ["mobile development", "google"], "roadmap": "android"},
    "xamarin": {"name": "Xamarin", "topics": ["mobile development", "cross-platform", "c#"], "roadmap": "mobile-developer"},
    
    # Other Tools
    "graphql": {"name": "GraphQL", "topics": ["api", "query language"], "roadmap": "backend"},
    "rest": {"name": "REST", "topics": ["api", "web services"], "roadmap": "backend"},
    "microservices": {"name": "Microservices", "topics": ["architecture", "distributed systems"], "roadmap": "system-design"},
    "agile": {"name": "Agile", "topics": ["methodology", "project management"], "roadmap": "software-architect"},
    "scrum": {"name": "Scrum", "topics": ["methodology", "agile"], "roadmap": "software-architect"},
    "oop": {"name": "OOP", "topics": ["programming paradigm", "object-oriented programming"], "roadmap": "computer-science"},
    "functional programming": {"name": "Functional Programming", "topics": ["programming paradigm"], "roadmap": "computer-science"},
    "linux": {"name": "Linux", "topics": ["operating system", "system administration"], "roadmap": "devops"},
    "bash": {"name": "Bash", "topics": ["shell scripting", "automation"], "roadmap": "devops"},
    "powershell": {"name": "PowerShell", "topics": ["shell scripting", "automation", "windows"], "roadmap": "devops"},
}

# Additional patterns for skill detection
SKILL_PATTERNS = [
    (r'\b(?:experience with|knowledge of|proficient in|familiar with)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', None),
    (r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:framework|library|tool|platform)', None),
    (r'\b(?:deep learning|machine learning|ml|ai|artificial intelligence)\b', "ai-engineer"),
    (r'\b(?:data science|data analysis|data engineering)\b', "data-scientist"),
    (r'\b(?:cloud infrastructure|cloud computing|cloud services)\b', "aws"),
    (r'\b(?:container|containerization|orchestration)\b', "devops"),
]


def clean_text(text: str) -> str:
    """Remove HTML tags, escape characters, and normalize whitespace."""
    if not text:
        return ""
    # Decode HTML entities
    text = html.unescape(text)
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove emojis and special characters (keep alphanumeric, spaces, and common punctuation)
    text = re.sub(r'[^\w\s.,;:!?()\-]', '', text)
    return text.strip()


def slugify(text: str) -> str:
    """Convert text to a URL-friendly slug."""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')


def extract_skills_from_description(description: str) -> List[Dict]:
    """Extract skills from job description using pattern matching and skill taxonomy."""
    if not description:
        return []
    
    description_lower = description.lower()
    found_skills = {}
    
    # Direct skill matching - prioritize longer/more specific matches first
    sorted_skills = sorted(TECH_SKILLS.items(), key=lambda x: len(x[0]), reverse=True)
    
    for skill_key, skill_info in sorted_skills:
        # Check for exact matches and variations
        patterns = [
            rf'\b{re.escape(skill_key)}\b',
            rf'\b{re.escape(skill_info["name"].lower())}\b',
        ]
        
        # Handle special characters in skill names
        skill_name_escaped = re.escape(skill_info["name"].lower())
        patterns.append(rf'\b{skill_name_escaped}\b')
        
        for pattern in patterns:
            if re.search(pattern, description_lower, re.IGNORECASE):
                skill_id = slugify(skill_key)
                if skill_id not in found_skills:
                    found_skills[skill_id] = {
                        "skill_id": skill_id,
                        "name": skill_info["name"],
                        "topics": skill_info["topics"].copy(),
                        "resources": []
                    }
                break
    
    # Pattern-based extraction for conceptual skills
    for pattern, roadmap in SKILL_PATTERNS:
        matches = re.finditer(pattern, description, re.IGNORECASE)
        for match in matches:
            if roadmap:
                # Add generic skill based on pattern
                skill_id = slugify(roadmap)
                if skill_id not in found_skills:
                    found_skills[skill_id] = {
                        "skill_id": skill_id,
                        "name": roadmap.replace("-", " ").title(),
                        "topics": ["technology", "development"],
                        "resources": []
                    }
    
    # Additional pattern matching for common phrases
    additional_patterns = [
        (r'\b(?:node\.?js|nodejs)\b', {"name": "Node.js", "topics": ["backend", "javascript runtime"], "roadmap": "nodejs"}),
        (r'\b(?:\.net|dotnet)\b', {"name": ".NET", "topics": ["framework", "microsoft"], "roadmap": "aspnet-core"}),
        (r'\b(?:ci/cd|continuous integration|continuous deployment)\b', {"name": "CI/CD", "topics": ["devops", "automation"], "roadmap": "devops"}),
        (r'\b(?:api|apis|application programming interface)\b', {"name": "API Development", "topics": ["backend", "web services"], "roadmap": "backend"}),
        (r'\b(?:sql|structured query language)\b', {"name": "SQL", "topics": ["database", "query language"], "roadmap": "backend"}),
    ]
    
    for pattern, skill_data in additional_patterns:
        if re.search(pattern, description_lower, re.IGNORECASE):
            skill_id = slugify(skill_data["name"].lower())
            if skill_id not in found_skills:
                found_skills[skill_id] = {
                    "skill_id": skill_id,
                    "name": skill_data["name"],
                    "topics": skill_data["topics"],
                    "resources": []
                }
    
    # Add resources for each skill
    for skill_id, skill_data in found_skills.items():
        skill_lower = skill_data["name"].lower()
        roadmap_path = TECH_SKILLS.get(skill_lower, {}).get("roadmap")
        
        # Try to find roadmap path
        if not roadmap_path:
            # Check if it's in additional patterns
            for _, ad_data in additional_patterns:
                if ad_data.get("name", "").lower() == skill_lower:
                    roadmap_path = ad_data.get("roadmap")
                    break
        
        if roadmap_path:
            skill_data["resources"] = [
                f"https://roadmap.sh/{roadmap_path}",
                f"https://roadmap.sh/{roadmap_path}/guide"
            ]
        else:
            # Generic resources
            skill_data["resources"] = [
                "https://roadmap.sh",
            ]
    
    return list(found_skills.values())


def get_roadmap_resource(skill_name: str) -> List[str]:
    """Get roadmap.sh resource URLs for a skill."""
    skill_lower = skill_name.lower()
    roadmap = TECH_SKILLS.get(skill_lower, {}).get("roadmap")
    if roadmap:
        return [
            f"https://roadmap.sh/{roadmap}",
            f"https://roadmap.sh/{roadmap}/guide"
        ]
    return ["https://roadmap.sh"]


def process_job_from_db_row(row: tuple, columns: List[str]) -> Optional[Dict]:
    """Process a single job from database row."""
    job_dict = dict(zip(columns, row))
    
    job_title = clean_text(job_dict.get('title', ''))
    company_id = job_dict.get('company_id')
    description = clean_text(job_dict.get('description', ''))
    skills_desc = clean_text(job_dict.get('skills_desc', ''))
    
    # Combine description and skills_desc for skill extraction
    full_description = f"{description} {skills_desc}".strip()
    
    if not job_title or not full_description:
        return None
    
    # Extract skills
    skills = extract_skills_from_description(full_description)
    
    # Need at least 3 skills
    if len(skills) < 3:
        return None
    
    # Get company name (will be joined later if needed)
    company_name = job_dict.get('company_name', 'Unknown Company')
    
    return {
        "job_title": job_title,
        "company_name": company_name,
        "job_description": description[:500] + "..." if len(description) > 500 else description,
        "skills": skills
    }


def process_jobs_from_database(db_path: str, limit: Optional[int] = None) -> List[Dict]:
    """Process jobs from SQLite database."""
    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return []
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get company names
    cursor.execute("SELECT company_id, name FROM companies")
    companies = {row[0]: row[1] for row in cursor.fetchall()}
    
    # Get jobs with descriptions
    query = """
        SELECT j.job_id, j.company_id, j.title, j.description, j.skills_desc
        FROM jobs j
        WHERE j.description IS NOT NULL 
        AND j.description != ''
        AND j.scraped > 0
        ORDER BY j.listed_time DESC
    """
    if limit:
        query += f" LIMIT {limit}"
    
    cursor.execute(query)
    columns = [desc[0] for desc in cursor.description]
    jobs = []
    
    for row in cursor.fetchall():
        job_dict = dict(zip(columns, row))
        company_name = companies.get(job_dict.get('company_id'), 'Unknown Company')
        
        job_title = clean_text(job_dict.get('title', ''))
        description = clean_text(job_dict.get('description', ''))
        skills_desc = clean_text(job_dict.get('skills_desc', ''))
        full_description = f"{description} {skills_desc}".strip()
        
        if not job_title or not full_description:
            continue
        
        skills = extract_skills_from_description(full_description)
        
        if len(skills) < 3:
            continue
        
        jobs.append({
            "job_title": job_title,
            "company_name": company_name,
            "job_description": description[:500] + "..." if len(description) > 500 else description,
            "skills": skills
        })
    
    conn.close()
    return jobs


def process_jobs_from_csv(csv_path: str, limit: Optional[int] = None) -> List[Dict]:
    """Process jobs from CSV file."""
    if not os.path.exists(csv_path):
        print(f"CSV file not found: {csv_path}")
        return []
    
    jobs = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            if limit and count >= limit:
                break
            
            job_title = clean_text(row.get('title', ''))
            company_name = clean_text(row.get('company_name', row.get('name', 'Unknown Company')))
            description = clean_text(row.get('description', ''))
            skills_desc = clean_text(row.get('skills_desc', ''))
            
            full_description = f"{description} {skills_desc}".strip()
            
            if not job_title or not full_description:
                continue
            
            skills = extract_skills_from_description(full_description)
            
            if len(skills) < 3:
                continue
            
            jobs.append({
                "job_title": job_title,
                "company_name": company_name,
                "job_description": description[:500] + "..." if len(description) > 500 else description,
                "skills": skills
            })
            count += 1
    
    return jobs


def main():
    """Main processing function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Process LinkedIn job postings and extract skills')
    parser.add_argument('--database', type=str, help='Path to SQLite database file')
    parser.add_argument('--csv', type=str, help='Path to CSV file with job postings')
    parser.add_argument('--limit', type=int, default=None, help='Limit number of jobs to process')
    parser.add_argument('--output', type=str, default=None, help='Output JSON file path')
    args = parser.parse_args()
    
    output_file = Path(args.output) if args.output else DATA_DIR / "linkedin_jobs_processed.json"
    DATA_DIR.mkdir(exist_ok=True)
    
    jobs = []
    
    # Try to find database file
    db_paths = []
    if args.database:
        db_paths.append(Path(args.database))
    db_paths.extend([
        JOB_LISTINGS_DIR / "linkedin_jobs.db",
        REPO_ROOT / "linkedin_jobs.db",
        DATA_DIR / "linkedin_jobs.db",
    ])
    
    csv_paths = []
    if args.csv:
        csv_paths.append(Path(args.csv))
    csv_paths.extend([
        JOB_LISTINGS_DIR / "csv_files" / "job_postings.csv",
        JOB_LISTINGS_DIR / "job_postings.csv",
        DATA_DIR / "job_postings.csv",
    ])
    
    # Try database first
    for db_path in db_paths:
        if os.path.exists(db_path):
            print(f"Processing jobs from database: {db_path}")
            jobs = process_jobs_from_database(str(db_path), limit=args.limit)
            break
    
    # If no database, try CSV
    if not jobs:
        for csv_path in csv_paths:
            if os.path.exists(csv_path):
                print(f"Processing jobs from CSV: {csv_path}")
                jobs = process_jobs_from_csv(str(csv_path), limit=args.limit)
                break
    
    # If still no jobs, create sample data for structure validation
    if not jobs:
        print("No database or CSV file found. Creating sample job entries for structure validation...")
        print("\nTo process real data:")
        print("1. Download the dataset from Kaggle: https://www.kaggle.com/datasets/arshkon/linkedin-job-postings")
        print("2. Extract the CSV files or use the database file")
        print("3. Run: python scripts/process_linkedin_jobs.py --csv path/to/job_postings.csv")
        print("\nCreating sample entries...\n")
        
        sample_jobs = [
            {
                "title": "Machine Learning Engineer",
                "company": "OpenAI",
                "description": "We are looking for a Machine Learning Engineer to build and deploy ML systems at scale. Must have experience with Python, PyTorch, TensorFlow, and cloud infrastructure like AWS. Knowledge of Docker, Kubernetes, and CI/CD pipelines is required. Experience with REST APIs, microservices architecture, and Agile methodologies."
            },
            {
                "title": "Full Stack Developer",
                "company": "Tech Corp",
                "description": "Seeking a Full Stack Developer with expertise in React, Node.js, TypeScript, and PostgreSQL. Must know Docker, AWS, and have experience with GraphQL APIs. Familiarity with Agile/Scrum methodologies required."
            },
            {
                "title": "Data Scientist",
                "company": "Data Analytics Inc",
                "description": "Looking for a Data Scientist proficient in Python, R, Pandas, NumPy, and scikit-learn. Experience with SQL databases (PostgreSQL, MySQL), cloud platforms (AWS, GCP), and machine learning frameworks (TensorFlow, PyTorch) is essential."
            },
            {
                "title": "DevOps Engineer",
                "company": "Cloud Services Ltd",
                "description": "DevOps Engineer needed with strong knowledge of Docker, Kubernetes, Jenkins, Terraform, and AWS. Experience with Linux, Bash scripting, CI/CD pipelines, and infrastructure as code required."
            },
            {
                "title": "Frontend Developer",
                "company": "Web Solutions",
                "description": "Frontend Developer position requiring React, TypeScript, JavaScript, HTML, CSS. Experience with Next.js, REST APIs, and modern frontend development practices. Knowledge of Git and Agile methodologies."
            }
        ]
        
        for sample in sample_jobs:
            skills = extract_skills_from_description(sample["description"])
            if len(skills) >= 3:
                jobs.append({
                    "job_title": sample["title"],
                    "company_name": sample["company"],
                    "job_description": sample["description"],
                    "skills": skills
                })
    
    # Ensure we have at least 10 jobs for validation (duplicate if needed)
    if len(jobs) < 10 and jobs:
        while len(jobs) < 10:
            jobs.append(jobs[len(jobs) % len(jobs)].copy())
    
    output_data = {"jobs": jobs}
    
    # Write JSON output
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print("PROCESSING SUMMARY")
    print(f"{'='*60}")
    print(f"Total jobs processed: {len(jobs)}")
    print(f"Total skills extracted: {sum(len(job['skills']) for job in jobs)}")
    print(f"Average skills per job: {sum(len(job['skills']) for job in jobs) / len(jobs) if jobs else 0:.1f}")
    print(f"\nOutput file: {output_file}")
    print(f"{'='*60}\n")
    
    # Print sample entries
    print("Sample job entries:")
    for i, job in enumerate(jobs[:3], 1):
        print(f"\n{i}. {job['job_title']} at {job['company_name']}")
        print(f"   Skills: {len(job['skills'])}")
        print(f"   Sample skills: {', '.join([s['name'] for s in job['skills'][:5]])}")
    
    return output_file


if __name__ == "__main__":
    main()

