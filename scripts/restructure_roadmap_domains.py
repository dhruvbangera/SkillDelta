#!/usr/bin/env python3
"""
Restructure roadmaps_domains.json to use specific roadmap.sh titles as domains.

Transforms broad categories into specific roadmap-based career paths.
"""

import json
import re
import sys
from pathlib import Path
from collections import defaultdict

REPO_ROOT = Path(__file__).parent.parent
INPUT_FILE = REPO_ROOT / "data" / "roadmaps_domains.json"
OUTPUT_FILE = REPO_ROOT / "data" / "roadmaps_roadmap_based.json"

# Roadmap title mappings (from roadmap.sh)
ROADMAP_DOMAINS = {
    # Web Development
    "Frontend Developer": {
        "description": "Step by step guide to becoming a modern frontend developer in 2025",
        "keywords": ["frontend", "html", "css", "javascript", "react", "vue", "angular"]
    },
    "Backend Developer": {
        "description": "Step by step guide to becoming a modern backend developer in 2025",
        "keywords": ["backend", "server", "api", "database", "nodejs", "python", "java"]
    },
    "Full Stack Developer": {
        "description": "Step by step guide to becoming a full stack developer",
        "keywords": ["fullstack", "full-stack", "frontend", "backend"]
    },
    "API Design": {
        "description": "Step by step guide to learning API design",
        "keywords": ["api", "rest", "graphql", "design"]
    },
    
    # Frameworks
    "React Developer": {
        "description": "Step by step guide to becoming a React developer",
        "keywords": ["react", "reactjs", "jsx"]
    },
    "Vue Developer": {
        "description": "Step by step guide to become a Vue Developer in 2025",
        "keywords": ["vue", "vuejs", "vue.js"]
    },
    "Angular Developer": {
        "description": "Step by step guide to becoming an Angular developer",
        "keywords": ["angular", "angularjs", "typescript"]
    },
    "Next.js Developer": {
        "description": "Step by step guide to becoming a Next.js developer",
        "keywords": ["nextjs", "next.js", "react"]
    },
    
    # Languages
    "JavaScript Developer": {
        "description": "Step by step guide to becoming a JavaScript developer",
        "keywords": ["javascript", "js", "ecmascript"]
    },
    "TypeScript Developer": {
        "description": "Step by step guide to becoming a TypeScript developer",
        "keywords": ["typescript", "ts"]
    },
    "Python Developer": {
        "description": "Step by step guide to becoming a Python developer",
        "keywords": ["python", "py", "django", "flask"]
    },
    "Java Developer": {
        "description": "Step by step guide to becoming a Java developer",
        "keywords": ["java", "spring", "jvm"]
    },
    "Go Developer": {
        "description": "Step by step guide to becoming a Go developer",
        "keywords": ["go", "golang", "gopher"]
    },
    "Rust Developer": {
        "description": "Step by step guide to becoming a Rust developer",
        "keywords": ["rust", "rustlang"]
    },
    "C++ Developer": {
        "description": "Step by step guide to becoming a C++ developer",
        "keywords": ["cpp", "c++", "cpp"]
    },
    "PHP Developer": {
        "description": "Step by step guide to becoming a PHP developer",
        "keywords": ["php", "laravel", "symfony"]
    },
    
    # Mobile
    "Android Developer": {
        "description": "Step by step guide to becoming an Android developer",
        "keywords": ["android", "kotlin", "java", "mobile"]
    },
    "iOS Developer": {
        "description": "Step by step guide to becoming an iOS developer",
        "keywords": ["ios", "swift", "swiftui", "mobile"]
    },
    "Flutter Developer": {
        "description": "Step by step guide to becoming a Flutter developer",
        "keywords": ["flutter", "dart", "mobile"]
    },
    "React Native Developer": {
        "description": "Step by step guide to becoming a React Native developer",
        "keywords": ["react-native", "reactnative", "mobile"]
    },
    
    # DevOps & Cloud
    "DevOps Engineer": {
        "description": "Step by step guide to becoming a DevOps engineer",
        "keywords": ["devops", "ci/cd", "docker", "kubernetes"]
    },
    "AWS Cloud Engineer": {
        "description": "Step by step guide to learning AWS",
        "keywords": ["aws", "amazon", "cloud", "ec2", "s3"]
    },
    "Kubernetes Engineer": {
        "description": "Step by step guide to learning Kubernetes",
        "keywords": ["kubernetes", "k8s", "container"]
    },
    "Docker Engineer": {
        "description": "Step by step guide to learning Docker",
        "keywords": ["docker", "container", "containerization"]
    },
    "Terraform Engineer": {
        "description": "Step by step guide to learning Terraform",
        "keywords": ["terraform", "iac", "infrastructure"]
    },
    "Linux System Administrator": {
        "description": "Step by step guide to learning Linux",
        "keywords": ["linux", "unix", "system", "administration"]
    },
    
    # AI & ML
    "AI Engineer": {
        "description": "Step by step guide to becoming an AI engineer",
        "keywords": ["ai", "artificial intelligence", "machine learning", "ml"]
    },
    "Machine Learning Engineer": {
        "description": "Step by step guide to becoming a machine learning engineer",
        "keywords": ["machine learning", "ml", "tensorflow", "pytorch"]
    },
    "AI Data Scientist": {
        "description": "Step by step guide to becoming an AI and data scientist",
        "keywords": ["data science", "ai", "analytics", "statistics"]
    },
    "Prompt Engineer": {
        "description": "Step by step guide to learning prompt engineering",
        "keywords": ["prompt", "llm", "gpt", "ai"]
    },
    "AI Agents Developer": {
        "description": "Step by step guide to learning AI agents",
        "keywords": ["ai agents", "agents", "llm", "autonomous"]
    },
    "MLOps Engineer": {
        "description": "Step by step guide to learning MLOps",
        "keywords": ["mlops", "machine learning ops", "deployment"]
    },
    
    # Data
    "Data Engineer": {
        "description": "Step by step guide to becoming a data engineer",
        "keywords": ["data engineering", "etl", "pipeline", "big data"]
    },
    "Data Analyst": {
        "description": "Step by step guide to becoming a data analyst",
        "keywords": ["data analysis", "analytics", "sql", "excel"]
    },
    "BI Analyst": {
        "description": "Step by step guide to becoming a BI analyst",
        "keywords": ["business intelligence", "bi", "reporting", "dashboard"]
    },
    
    # Databases
    "PostgreSQL DBA": {
        "description": "Step by step guide to becoming a PostgreSQL DBA",
        "keywords": ["postgresql", "postgres", "database", "dba"]
    },
    "SQL Developer": {
        "description": "Step by step guide to learning SQL",
        "keywords": ["sql", "database", "query"]
    },
    "MongoDB Developer": {
        "description": "Step by step guide to learning MongoDB",
        "keywords": ["mongodb", "nosql", "database"]
    },
    "Redis Developer": {
        "description": "Step by step guide to learning Redis",
        "keywords": ["redis", "cache", "database"]
    },
    
    # Security
    "Cybersecurity Engineer": {
        "description": "Step by step guide to becoming a cybersecurity engineer",
        "keywords": ["cybersecurity", "security", "penetration", "ethical hacking"]
    },
    
    # Other
    "Blockchain Developer": {
        "description": "Step by step guide to becoming a blockchain developer",
        "keywords": ["blockchain", "crypto", "smart contract", "web3"]
    },
    "Game Developer": {
        "description": "Step by step guide to becoming a game developer",
        "keywords": ["game", "gaming", "unity", "unreal"]
    },
    "Software Architect": {
        "description": "Step by step guide to becoming a software architect",
        "keywords": ["architecture", "design", "system design"]
    },
    "System Design Engineer": {
        "description": "Step by step guide to learning system design",
        "keywords": ["system design", "architecture", "scalability"]
    },
    "QA Engineer": {
        "description": "Step by step guide to becoming a QA engineer",
        "keywords": ["qa", "testing", "quality assurance", "test"]
    },
    "Product Manager": {
        "description": "Step by step guide to becoming a product manager",
        "keywords": ["product", "management", "pm", "strategy"]
    },
    "Engineering Manager": {
        "description": "Step by step guide to becoming an engineering manager",
        "keywords": ["engineering management", "leadership", "team"]
    },
    "UX Designer": {
        "description": "Step by step guide to becoming a UX designer",
        "keywords": ["ux", "user experience", "design", "ui"]
    },
    "Technical Writer": {
        "description": "Step by step guide to becoming a technical writer",
        "keywords": ["technical writing", "documentation", "writing"]
    },
    "DevRel Engineer": {
        "description": "Step by step guide to becoming a Developer Advocate",
        "keywords": ["devrel", "developer relations", "advocacy"]
    },
    "Computer Science": {
        "description": "Step by step guide to learning computer science",
        "keywords": ["computer science", "cs", "algorithms", "data structures"]
    },
    "GraphQL Developer": {
        "description": "Step by step guide to learning GraphQL",
        "keywords": ["graphql", "api", "query"]
    },
    "HTML Developer": {
        "description": "Step by step guide to learning HTML",
        "keywords": ["html", "markup", "web"]
    },
    "CSS Developer": {
        "description": "Step by step guide to learning CSS",
        "keywords": ["css", "styling", "design"]
    },
    "Node.js Developer": {
        "description": "Step by step guide to becoming a Node.js developer",
        "keywords": ["nodejs", "node.js", "server", "javascript"]
    },
    "Git and GitHub": {
        "description": "Step by step guide to learning Git and GitHub",
        "keywords": ["git", "github", "version control"]
    },
    "Bash/Shell Developer": {
        "description": "Step by step guide to learning Bash/Shell",
        "keywords": ["bash", "shell", "scripting", "linux"]
    },
    "Cloudflare Developer": {
        "description": "Step by step guide to learning Cloudflare",
        "keywords": ["cloudflare", "cdn", "cloud"]
    },
    "ASP.NET Core Developer": {
        "description": "Step by step guide to becoming an ASP.NET Core developer",
        "keywords": ["asp.net", "dotnet", "c#", "microsoft"]
    },
    "Spring Boot Developer": {
        "description": "Step by step guide to becoming a Spring Boot developer",
        "keywords": ["spring boot", "spring", "java"]
    },
    "Laravel Developer": {
        "description": "Step by step guide to becoming a Laravel developer",
        "keywords": ["laravel", "php", "framework"]
    },
    "Kotlin Developer": {
        "description": "Step by step guide to becoming a Kotlin developer",
        "keywords": ["kotlin", "android", "jvm"]
    },
    "Swift Developer": {
        "description": "Step by step guide to becoming a Swift developer",
        "keywords": ["swift", "ios", "swiftui"]
    },
    "Design System": {
        "description": "Step by step guide to learning design systems",
        "keywords": ["design system", "ui", "components"]
    },
    "Software Design and Architecture": {
        "description": "Step by step guide to learning software design and architecture",
        "keywords": ["design", "architecture", "patterns"]
    },
    "AI Red Teaming": {
        "description": "Step by step guide to learning AI red teaming",
        "keywords": ["ai red teaming", "security", "ai safety"]
    }
}


def normalize_text(text):
    """Normalize text for matching."""
    return text.lower().strip()


def find_best_roadmap_domain(skill_name, skill_keywords, skill_links):
    """Find the best matching roadmap domain for a skill."""
    skill_text = normalize_text(skill_name)
    all_keywords = ' '.join([skill_text] + [normalize_text(k) for k in skill_keywords])
    links_text = ' '.join(skill_links).lower()
    combined_text = f"{all_keywords} {links_text}"
    
    # Score each domain
    domain_scores = {}
    for domain_name, domain_info in ROADMAP_DOMAINS.items():
        score = 0
        domain_keywords = [normalize_text(k) for k in domain_info['keywords']]
        domain_name_lower = normalize_text(domain_name)
        
        # High priority: exact domain name match
        if domain_name_lower in combined_text or any(word in combined_text for word in domain_name_lower.split() if len(word) > 3):
            score += 10
        
        # High priority: primary domain keywords
        primary_keywords = domain_keywords[:3]  # First 3 are most important
        for keyword in primary_keywords:
            if keyword in combined_text:
                score += 5
        
        # Medium priority: other domain keywords
        for keyword in domain_keywords[3:]:
            if keyword in combined_text:
                score += 2
        
        # Negative scoring for clearly wrong matches
        # Frontend shouldn't have ML/backend keywords
        if 'frontend' in domain_name_lower:
            if any(kw in combined_text for kw in ['machine learning', 'ml', 'backend', 'server', 'database', 'sql']):
                score -= 10
        
        # Backend shouldn't have frontend-specific keywords
        if 'backend' in domain_name_lower:
            if any(kw in combined_text for kw in ['html', 'css', 'react', 'vue', 'angular', 'frontend']):
                score -= 5
        
        # AI/ML domains should prioritize AI/ML keywords
        if any(term in domain_name_lower for term in ['ai', 'machine learning', 'ml']):
            if not any(kw in combined_text for kw in ['ai', 'machine learning', 'ml', 'neural', 'tensorflow', 'pytorch', 'llm', 'agent']):
                score -= 5
        
        domain_scores[domain_name] = score
    
    # Return best match only if score is positive
    if domain_scores:
        best_domain = max(domain_scores.items(), key=lambda x: x[1])
        if best_domain[1] > 0:
            return best_domain[0]
    
    return None


def merge_similar_skills(skills):
    """Merge overly specific skills into broader categories."""
    merged = {}
    
    # Group by base name (first 2-3 words)
    for skill in skills:
        name = skill['name']
        words = name.split()
        
        # Create base key from first meaningful words
        if len(words) >= 2:
            base_key = ' '.join(words[:2]).lower()
        else:
            base_key = name.lower()
        
        # Normalize base key
        base_key = re.sub(r'\s+(in|for|with|using|via)\s+.*$', '', base_key)
        base_key = re.sub(r'\s+-\s+.*$', '', base_key)
        
        if base_key not in merged:
            merged[base_key] = {
                'skill_id': skill['skill_id'],
                'name': name,
                'keywords': set(skill.get('keywords', [])),
                'links': list(set(skill.get('links', [])))
            }
        else:
            # Merge keywords and links
            merged[base_key]['keywords'].update(skill.get('keywords', []))
            merged[base_key]['links'].extend(skill.get('links', []))
            merged[base_key]['links'] = list(set(merged[base_key]['links']))
            # Keep longer/more descriptive name
            if len(name) > len(merged[base_key]['name']):
                merged[base_key]['name'] = name
    
    # Convert back to list format
    result = []
    for base_key, merged_skill in merged.items():
        result.append({
            'skill_id': merged_skill['skill_id'],
            'name': merged_skill['name'],
            'keywords': sorted(list(merged_skill['keywords'])),
            'links': merged_skill['links']
        })
    
    return result


def create_categories_for_domain(domain_name, skills):
    """Create logical categories for skills within a domain."""
    # Common category patterns
    category_patterns = {
        'Fundamentals': ['basic', 'fundamental', 'introduction', 'getting started', 'overview'],
        'Core Concepts': ['core', 'concept', 'theory', 'principles'],
        'Frameworks & Libraries': ['framework', 'library', 'package', 'module'],
        'Tools & Setup': ['tool', 'setup', 'installation', 'configuration', 'environment'],
        'Advanced Topics': ['advanced', 'expert', 'optimization', 'performance'],
        'Testing': ['test', 'testing', 'qa', 'quality'],
        'Deployment': ['deploy', 'deployment', 'production', 'hosting'],
        'Security': ['security', 'auth', 'authentication', 'authorization', 'encryption'],
        'APIs & Integration': ['api', 'rest', 'graphql', 'integration', 'endpoint'],
        'Database': ['database', 'db', 'sql', 'nosql', 'query'],
        'DevOps': ['devops', 'ci/cd', 'docker', 'kubernetes', 'terraform'],
        'Cloud': ['cloud', 'aws', 'azure', 'gcp', 'serverless'],
        'Mobile': ['mobile', 'android', 'ios', 'react native', 'flutter'],
        'Frontend': ['frontend', 'ui', 'ux', 'html', 'css', 'javascript'],
        'Backend': ['backend', 'server', 'nodejs', 'python', 'java']
    }
    
    # Group skills into categories
    categorized = defaultdict(list)
    uncategorized = []
    
    for skill in skills:
        skill_lower = skill['name'].lower()
        skill_keywords_lower = ' '.join([k.lower() for k in skill.get('keywords', [])])
        combined = f"{skill_lower} {skill_keywords_lower}"
        
        categorized_flag = False
        for category, patterns in category_patterns.items():
            if any(pattern in combined for pattern in patterns):
                categorized[category].append(skill)
                categorized_flag = True
                break
        
        if not categorized_flag:
            uncategorized.append(skill)
    
    # Create category list
    categories = []
    for category_name, category_skills in sorted(categorized.items()):
        if category_skills:
            categories.append({
                'category': category_name,
                'subskills': category_skills
            })
    
    # Add uncategorized as "General" if any
    if uncategorized:
        categories.append({
            'category': 'General',
            'subskills': uncategorized
        })
    
    # If no categories, create a default
    if not categories:
        categories.append({
            'category': 'Core Skills',
            'subskills': skills
        })
    
    return categories


def restructure_to_roadmap_domains(input_file, output_file):
    """Main restructuring function."""
    print(f"Loading {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Collect all skills from current structure
    all_skills = []
    for domain in data.get('domains', []):
        for skill_group in domain.get('skills', []):
            for subskill in skill_group.get('subskills', []):
                all_skills.append(subskill)
    
    print(f"Found {len(all_skills)} total skills")
    print("Mapping skills to roadmap domains...")
    
    # Map skills to roadmap domains
    domain_skills = defaultdict(list)
    unmapped_skills = []
    
    for skill in all_skills:
        skill_name = skill.get('name', '')
        skill_keywords = skill.get('keywords', [])
        skill_links = skill.get('links', [])
        
        domain = find_best_roadmap_domain(skill_name, skill_keywords, skill_links)
        if domain:
            domain_skills[domain].append(skill)
        else:
            unmapped_skills.append(skill)
    
    # Handle unmapped skills - assign to closest domain
    print(f"Handling {len(unmapped_skills)} unmapped skills...")
    for skill in unmapped_skills:
        # Try to find a match based on keywords
        best_match = None
        best_score = 0
        
        for domain_name, domain_info in ROADMAP_DOMAINS.items():
            score = 0
            skill_text = ' '.join([skill.get('name', '')] + skill.get('keywords', [])).lower()
            for keyword in domain_info['keywords']:
                if keyword.lower() in skill_text:
                    score += 1
            
            if score > best_score:
                best_score = score
                best_match = domain_name
        
        if best_match:
            domain_skills[best_match].append(skill)
        else:
            # Default to "General" or most common domain
            domain_skills["Frontend Developer"].append(skill)
    
    print("Merging similar skills and creating categories...")
    
    # Build final structure
    domains_list = []
    for domain_name in sorted(ROADMAP_DOMAINS.keys()):
        if domain_name not in domain_skills or not domain_skills[domain_name]:
            continue
        
        skills = domain_skills[domain_name]
        
        # Merge similar skills
        merged_skills = merge_similar_skills(skills)
        
        # Create categories
        categories = create_categories_for_domain(domain_name, merged_skills)
        
        # Get description
        description = ROADMAP_DOMAINS[domain_name]['description']
        
        domains_list.append({
            'domain': domain_name,
            'description': description,
            'categories': categories
        })
    
    output_data = {
        'domains': domains_list
    }
    
    print(f"Writing restructured data to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    # Print summary
    total_domains = len(domains_list)
    total_categories = sum(len(d['categories']) for d in domains_list)
    total_subskills = sum(
        sum(len(cat['subskills']) for cat in d['categories'])
        for d in domains_list
    )
    
    print("\n" + "="*60)
    print("RESTRUCTURING SUMMARY")
    print("="*60)
    print(f"Domains: {total_domains}")
    print(f"Categories: {total_categories}")
    print(f"Subskills: {total_subskills}")
    print(f"\nTop domains by subskill count:")
    domain_counts = [(d['domain'], sum(len(c['subskills']) for c in d['categories'])) for d in domains_list]
    domain_counts.sort(key=lambda x: x[1], reverse=True)
    for domain, count in domain_counts[:10]:
        print(f"  - {domain}: {count} subskills")
    print(f"\nOutput file: {output_file.relative_to(REPO_ROOT)}")
    print("="*60)
    
    # Validate JSON
    try:
        with open(output_file, 'r', encoding='utf-8') as f:
            json.load(f)
        print("\n[OK] Output JSON is valid")
    except Exception as e:
        print(f"\n[ERROR] JSON validation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    restructure_to_roadmap_domains(INPUT_FILE, OUTPUT_FILE)

