#!/usr/bin/env python3
"""
Create Role > Skill > Topics > Resources structure from roadmap data.

Structure:
- Role (Frontend, Backend, AI Engineer, etc.)
  - Skill (JavaScript, React, SQL, etc.)
    - Topics (recursion, sorting algorithms, etc.)
      - Resources (with type: documentation, article, video, course, etc.)
"""

import json
import re
import sys
from pathlib import Path
from collections import defaultdict
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).parent.parent
INPUT_FILE = REPO_ROOT / "data" / "roadmaps.json"  # Use original to get @type@ info
ROADMAPS_DIR = REPO_ROOT / "developer-roadmap" / "src" / "data" / "roadmaps"
OUTPUT_FILE = REPO_ROOT / "data" / "roadmaps_role_skill.json"

# Common technology/skill names to extract
TECH_SKILLS = {
    # Languages
    'javascript': ['javascript', 'js', 'ecmascript', 'es6', 'es2015'],
    'typescript': ['typescript', 'ts'],
    'python': ['python', 'py', 'django', 'flask', 'fastapi'],
    'java': ['java', 'spring', 'jvm', 'maven'],
    'go': ['go', 'golang', 'gopher'],
    'rust': ['rust', 'rustlang'],
    'cpp': ['c++', 'cpp', 'cplusplus'],
    'php': ['php', 'laravel', 'symfony'],
    'ruby': ['ruby', 'rails', 'ror'],
    'swift': ['swift', 'swiftui'],
    'kotlin': ['kotlin', 'android'],
    'dart': ['dart', 'flutter'],
    'sql': ['sql', 'postgresql', 'mysql', 'sqlite'],
    'html': ['html', 'html5'],
    'css': ['css', 'css3', 'sass', 'scss', 'less'],
    'bash': ['bash', 'shell', 'sh', 'zsh'],
    
    # Frameworks & Libraries
    'react': ['react', 'reactjs', 'jsx'],
    'vue': ['vue', 'vuejs', 'nuxt'],
    'angular': ['angular', 'angularjs'],
    'nextjs': ['nextjs', 'next.js'],
    'nodejs': ['nodejs', 'node.js', 'express'],
    'react-native': ['react-native', 'reactnative'],
    'flutter': ['flutter', 'dart'],
    'spring-boot': ['spring boot', 'springboot'],
    'laravel': ['laravel'],
    'aspnet': ['asp.net', 'dotnet', 'c#'],
    
    # Databases
    'mongodb': ['mongodb', 'mongo'],
    'redis': ['redis'],
    'postgresql': ['postgresql', 'postgres'],
    
    # DevOps & Cloud
    'docker': ['docker', 'container'],
    'kubernetes': ['kubernetes', 'k8s'],
    'aws': ['aws', 'amazon', 'ec2', 's3', 'lambda'],
    'terraform': ['terraform'],
    'git': ['git', 'github'],
    'linux': ['linux', 'unix'],
    
    # AI/ML
    'tensorflow': ['tensorflow', 'tf'],
    'pytorch': ['pytorch'],
    'machine-learning': ['machine learning', 'ml', 'deep learning'],
    'ai': ['ai', 'artificial intelligence', 'llm', 'gpt'],
    
    # Other
    'graphql': ['graphql'],
    'rest': ['rest', 'restful', 'api'],
    'blockchain': ['blockchain', 'crypto', 'ethereum'],
    'cybersecurity': ['security', 'cybersecurity', 'penetration'],
}


def extract_resource_type_from_markdown(content_file_path):
    """Extract resource types from markdown file if it exists."""
    resource_map = {}
    
    if not content_file_path or not content_file_path.exists():
        return resource_map
    
    try:
        with open(content_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find all @type@ patterns
        pattern = r'\[@(\w+)@([^\]]+)\]\(([^)]+)\)'
        matches = re.findall(pattern, content)
        
        for match_type, title, url in matches:
            # Normalize URL
            url = url.strip()
            # Map roadmap.sh types to our types
            type_mapping = {
                'official': 'documentation',
                'article': 'article',
                'video': 'video',
                'course': 'course',
                'book': 'book',
                'podcast': 'podcast',
                'opensource': 'official',
                'feed': 'article'
            }
            resource_type = type_mapping.get(match_type.lower(), 'article')
            resource_map[url] = resource_type
    except:
        pass
    
    return resource_map


def detect_resource_type(url, title="", content_file_path=None):
    """Detect resource type from URL, title, or markdown file."""
    if not url:
        return "article"
    
    # Try to get from markdown file first
    if content_file_path:
        resource_map = extract_resource_type_from_markdown(content_file_path)
        if url in resource_map:
            return resource_map[url]
    
    url_lower = url.lower()
    title_lower = title.lower()
    combined = f"{url_lower} {title_lower}"
    
    # Documentation (check first, most specific)
    if any(term in combined for term in ['/docs/', 'docs.', 'documentation', 'developer.mozilla.org', 'docs.rs', 'pkg.go.dev', 'api.', '.org/docs', '.com/docs']):
        return "documentation"
    
    # Video (check before course)
    if any(term in combined for term in ['youtube.com', 'youtu.be', 'watch?v=', 'playlist', '/video/', 'vimeo.com']):
        return "video"
    
    # Course
    if any(term in combined for term in ['course', 'udemy', 'coursera', 'edx', 'pluralsight', '/learn/', '/tutorial/', 'codecademy']):
        return "course"
    
    # Book
    if any(term in combined for term in ['book', '.pdf', 'epub', 'oreilly']):
        return "book"
    
    # Podcast
    if any(term in combined for term in ['podcast', 'soundcloud', 'spotify', 'apple.com/podcasts']):
        return "podcast"
    
    # Article/Blog (check after other types)
    if any(term in combined for term in ['medium.com', 'blog.', '/blog/', 'dev.to', 'hashnode', 'article']):
        return "article"
    
    # Official/GitHub
    if any(term in combined for term in ['github.com', 'official', '.org/', '.io/']):
        return "official"
    
    # Default to article
    return "article"


def extract_skill_from_name(skill_name, keywords, role_name=""):
    """Extract the main technology/skill name from skill name and keywords."""
    combined = f"{skill_name} {' '.join(keywords)} {role_name}".lower()
    
    # Check each tech skill (prioritize longer/more specific matches first)
    skill_matches = []
    for skill_key, skill_terms in TECH_SKILLS.items():
        for term in skill_terms:
            if term in combined:
                # Score by term length (longer = more specific)
                score = len(term)
                skill_matches.append((skill_key, score, term))
    
    if skill_matches:
        # Sort by score (highest first) and return best match
        skill_matches.sort(key=lambda x: x[1], reverse=True)
        return skill_matches[0][0]
    
    # If no match, try to extract from skill name
    # Remove common prefixes/suffixes
    name_clean = skill_name.lower()
    name_clean = re.sub(r'^(learn|understand|master|guide to|introduction to|getting started with|how to)\s+', '', name_clean)
    name_clean = re.sub(r'\s+(tutorial|guide|course|basics|advanced|introduction|fundamentals)$', '', name_clean)
    
    # Extract first meaningful word
    words = name_clean.split()
    if words:
        first_word = words[0]
        # Check if it's a known tech
        for skill_key, skill_terms in TECH_SKILLS.items():
            if first_word in skill_terms or first_word == skill_key:
                return skill_key
        
        # Check if first word is a common tech name
        if first_word in ['react', 'vue', 'angular', 'node', 'express', 'mongodb', 'redis', 'docker', 'kubernetes']:
            return first_word
    
    # If still no match, use the skill name itself (capitalized)
    if words:
        return words[0].replace('-', ' ').title()
    
    return "General"


def normalize_role_name(role_name):
    """Normalize role name to standard format."""
    # Map variations to standard names
    role_mapping = {
        'frontend': 'Frontend Developer',
        'backend': 'Backend Developer',
        'full stack': 'Full Stack Developer',
        'full-stack': 'Full Stack Developer',
        'ai engineer': 'AI Engineer',
        'ai agents': 'AI Agents Developer',
        'machine learning': 'Machine Learning Engineer',
        'data engineer': 'Data Engineer',
        'data analyst': 'Data Analyst',
        'devops': 'DevOps Engineer',
        'cybersecurity': 'Cybersecurity Engineer',
        'blockchain': 'Blockchain Developer',
        'game developer': 'Game Developer',
        'software architect': 'Software Architect',
        'qa': 'QA Engineer',
        'product manager': 'Product Manager',
        'engineering manager': 'Engineering Manager',
        'ux design': 'UX Designer',
        'technical writer': 'Technical Writer',
        'devrel': 'DevRel Engineer',
    }
    
    role_lower = role_name.lower()
    for key, value in role_mapping.items():
        if key in role_lower:
            return value
    
    # Capitalize properly
    return role_name.title()


def create_role_skill_structure(input_file, output_file):
    """Main restructuring function."""
    print(f"Loading {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Structure: role -> skill -> topics -> resources
    structure = defaultdict(lambda: defaultdict(list))
    
    print("Processing skills and organizing by role > skill > topic...")
    
    for role_obj in data.get('roles', []):
        role_name = role_obj.get('role_name', '')
        if not role_name:
            continue
        
        normalized_role = normalize_role_name(role_name)
        
        # Process sections and skills
        for section in role_obj.get('sections', []):
            for skill_obj in section.get('skills', []):
                skill_name = skill_obj.get('skill_text', '')
                skill_links = skill_obj.get('links', [])
                
                if not skill_name:
                    continue
                
                # Extract keywords from skill name (basic extraction)
                words = skill_name.lower().split()
                skill_keywords = [w for w in words if len(w) > 2]
                
                # Extract main skill/technology
                main_skill = extract_skill_from_name(skill_name, skill_keywords, role_name)
                
                # The skill name becomes the topic
                topic_name = skill_name.title()
                
                # Try to find source file for resource type extraction
                source_file = None
                if 'source_files' in role_obj and role_obj['source_files']:
                    # Use first source file
                    source_path = role_obj['source_files'][0]
                    # Convert to actual file path
                    if 'src\\data\\roadmaps' in source_path or 'src/data/roadmaps' in source_path:
                        file_path = REPO_ROOT / "developer-roadmap" / source_path.replace('\\', '/')
                        if file_path.exists():
                            source_file = file_path
                
                # Create resources from links (extract type from link text if available)
                resources = []
                for link_obj in skill_links:
                    if isinstance(link_obj, dict):
                        link_url = link_obj.get('href', '') or link_obj.get('url', '')
                        link_text = link_obj.get('text', '')
                    else:
                        link_url = link_obj
                        link_text = ''
                    
                    if link_url:
                        # Extract type from link text (e.g., "@article@Title")
                        resource_type = "article"  # default
                        if link_text:
                            type_match = re.search(r'@(\w+)@', link_text)
                            if type_match:
                                type_mapping = {
                                    'official': 'documentation',
                                    'article': 'article',
                                    'video': 'video',
                                    'course': 'course',
                                    'book': 'book',
                                    'podcast': 'podcast',
                                    'opensource': 'official',
                                    'feed': 'article'
                                }
                                resource_type = type_mapping.get(type_match.group(1).lower(), 'article')
                            else:
                                # Fallback to URL detection
                                resource_type = detect_resource_type(link_url, link_text, source_file)
                        else:
                            resource_type = detect_resource_type(link_url, skill_name, source_file)
                        
                        # Clean title from link text
                        title = link_text
                        if title:
                            title = re.sub(r'@\w+@', '', title).strip()
                        if not title:
                            title = skill_name.title()
                        
                        resources.append({
                            "link": link_url,
                            "type": resource_type,
                            "title": title
                        })
                
                if resources or skill_name:  # Include topics even without links
                    topic_entry = {
                        "topic": topic_name,
                        "resources": resources
                    }
                    structure[normalized_role][main_skill].append(topic_entry)
    
    print("Building final structure with keywords...")
    
    # Build final structure
    roles_list = []
    for role_name in sorted(structure.keys()):
        skills_list = []
        
        for skill_name in sorted(structure[role_name].keys()):
            topics = structure[role_name][skill_name]
            
            # Get keywords for this skill
            skill_keywords = []
            if skill_name in TECH_SKILLS:
                skill_keywords = TECH_SKILLS[skill_name][:5]  # Top 5 keywords
            else:
                # Generate keywords from skill name
                skill_keywords = [skill_name.lower()]
                words = skill_name.lower().split('-')
                skill_keywords.extend(words)
            
            # Add common variations
            skill_keywords = list(set(skill_keywords))[:10]  # Limit to 10 keywords
            
            skills_list.append({
                "skill": skill_name.replace('-', ' ').title(),
                "keywords": sorted(skill_keywords),
                "topics": topics
            })
        
        if skills_list:
            roles_list.append({
                "role": role_name,
                "skills": skills_list
            })
    
    output_data = {
        "roles": roles_list
    }
    
    print(f"Writing structured data to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    # Print summary
    total_roles = len(roles_list)
    total_skills = sum(len(r['skills']) for r in roles_list)
    total_topics = sum(
        sum(len(s['topics']) for s in r['skills'])
        for r in roles_list
    )
    total_resources = sum(
        sum(sum(len(t['resources']) for t in s['topics']) for s in r['skills'])
        for r in roles_list
    )
    
    print("\n" + "="*60)
    print("STRUCTURE SUMMARY")
    print("="*60)
    print(f"Roles: {total_roles}")
    print(f"Skills: {total_skills}")
    print(f"Topics: {total_topics}")
    print(f"Resources: {total_resources}")
    print(f"\nTop roles by skill count:")
    role_counts = [(r['role'], len(r['skills'])) for r in roles_list]
    role_counts.sort(key=lambda x: x[1], reverse=True)
    for role, count in role_counts[:10]:
        print(f"  - {role}: {count} skills")
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
    
    # Show sample structure
    if roles_list:
        sample_role = roles_list[0]
        print(f"\nSample structure for '{sample_role['role']}':")
        if sample_role['skills']:
            sample_skill = sample_role['skills'][0]
            print(f"  Skill: {sample_skill['skill']}")
            print(f"  Keywords: {', '.join(sample_skill['keywords'][:5])}")
            if sample_skill['topics']:
                sample_topic = sample_skill['topics'][0]
                print(f"  Topic: {sample_topic['topic']}")
                if sample_topic['resources']:
                    print(f"  Resources: {len(sample_topic['resources'])} ({sample_topic['resources'][0]['type']})")


if __name__ == "__main__":
    create_role_skill_structure(INPUT_FILE, OUTPUT_FILE)

