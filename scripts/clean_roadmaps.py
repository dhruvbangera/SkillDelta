#!/usr/bin/env python3
"""
Clean and restructure roadmaps.json for skill extraction and mapping.

Transforms the nested structure into a flattened, searchable format optimized
for resume parsing and skill mapping platforms.
"""

import json
import re
import sys
from pathlib import Path
from collections import defaultdict
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).parent.parent
INPUT_FILE = REPO_ROOT / "data" / "roadmaps.json"
OUTPUT_FILE = REPO_ROOT / "data" / "roadmaps_cleaned.json"

# Common stop words to remove
STOP_WORDS = {
    'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
    'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
    'to', 'was', 'will', 'with', 'the', 'this', 'these', 'those'
}

# Common skill synonyms and variations
SKILL_SYNONYMS = {
    'oop': ['object-oriented programming', 'object oriented programming'],
    'fp': ['functional programming'],
    'api': ['application programming interface'],
    'rest': ['representational state transfer', 'restful'],
    'graphql': ['graph ql', 'graph query language'],
    'sql': ['structured query language'],
    'nosql': ['not only sql'],
    'ci/cd': ['continuous integration', 'continuous deployment', 'continuous delivery'],
    'devops': ['development operations'],
    'ui': ['user interface'],
    'ux': ['user experience'],
    'html': ['hypertext markup language'],
    'css': ['cascading style sheets'],
    'js': ['javascript'],
    'ts': ['typescript'],
    'react': ['reactjs', 'react.js'],
    'vue': ['vuejs', 'vue.js'],
    'angular': ['angularjs', 'angular.js'],
    'node': ['nodejs', 'node.js'],
    'aws': ['amazon web services'],
    'gcp': ['google cloud platform'],
    'azure': ['microsoft azure'],
}


def slugify(text):
    """Convert text to a URL-friendly slug."""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')


def normalize_skill_name(name):
    """Normalize skill name: lowercase, remove stop words and punctuation."""
    if not name:
        return ""
    
    # Convert to lowercase
    name = name.lower()
    
    # Remove common prefixes/suffixes
    name = re.sub(r'^(learn|understand|master|explore|study|get started with|introduction to|guide to|tutorial on)\s+', '', name)
    name = re.sub(r'\s+(tutorial|guide|course|learning|basics|advanced|introduction)$', '', name)
    
    # Remove punctuation except hyphens and spaces
    name = re.sub(r'[^\w\s-]', ' ', name)
    
    # Remove stop words
    words = name.split()
    words = [w for w in words if w not in STOP_WORDS and len(w) > 1]
    
    # Rejoin and normalize whitespace
    name = ' '.join(words)
    name = re.sub(r'\s+', ' ', name).strip()
    
    return name


def extract_keywords(skill_name, role_name):
    """Generate keywords from skill name and role context."""
    keywords = set()
    
    # Add the skill name itself (split into words)
    skill_words = skill_name.split()
    keywords.update(skill_words)
    
    # Add role name words (if relevant)
    role_words = role_name.lower().split()
    keywords.update([w for w in role_words if w not in STOP_WORDS and len(w) > 2])
    
    # Check for synonyms
    skill_lower = skill_name.lower()
    for abbrev, expansions in SKILL_SYNONYMS.items():
        if abbrev in skill_lower:
            keywords.update(expansions)
        for expansion in expansions:
            if any(word in skill_lower for word in expansion.split()):
                keywords.add(abbrev)
    
    # Extract technical terms (words that look like tech terms)
    tech_patterns = [
        r'\b\w+\.(js|ts|py|java|go|rs|rb|php|swift|kt)\b',  # file extensions
        r'\b\w+js\b',  # *js frameworks
        r'\b\w+\.net\b',  # .NET
        r'\b\w+db\b',  # databases
        r'\b\w+sql\b',  # SQL variants
    ]
    
    for pattern in tech_patterns:
        matches = re.findall(pattern, skill_lower)
        keywords.update(matches)
    
    # Remove very short keywords
    keywords = {k for k in keywords if len(k) > 1}
    
    return sorted(list(keywords))


def normalize_url(url):
    """Normalize and validate URL."""
    if not url or not isinstance(url, str):
        return None
    
    url = url.strip()
    
    # Handle both string URLs and objects with href
    if isinstance(url, dict):
        url = url.get('href', '') or url.get('url', '')
    
    if not url:
        return None
    
    # Remove trailing punctuation
    url = url.rstrip('.,;:!?)')
    
    # Validate URL format
    if not url.startswith(('http://', 'https://')):
        return None
    
    # Basic validation
    try:
        parsed = urlparse(url)
        if not parsed.netloc:
            return None
    except:
        return None
    
    return url


def normalize_role_name(role_name):
    """Normalize role name: proper capitalization, remove redundant subtopics."""
    if not role_name:
        return ""
    
    # Remove common suffixes that make roles too specific
    role_name = re.sub(r'\s+(in|for|with|using|with|via)\s+[A-Z][a-z]+$', '', role_name)
    role_name = re.sub(r'\s+-\s+[A-Z][a-z]+$', '', role_name)
    
    # Title case (capitalize first letter of each word)
    words = role_name.split()
    words = [w.capitalize() if w.lower() not in ['and', 'or', 'of', 'the', 'for'] else w.lower() 
             for w in words]
    if words:
        words[0] = words[0].capitalize()
    
    role_name = ' '.join(words)
    
    # Handle common role name patterns
    role_name = re.sub(r'^(\w+)\s+Developer$', r'\1 Developer', role_name)
    role_name = re.sub(r'^(\w+)\s+Engineer$', r'\1 Engineer', role_name)
    
    return role_name


def merge_duplicate_roles(roles_dict):
    """Merge roles that represent the same topic."""
    # Role name mappings for merging
    role_mergers = {
        'ci/cd': ['continuous integration', 'continuous deployment'],
        'devops': ['development operations'],
        'frontend': ['front-end', 'front end'],
        'backend': ['back-end', 'back end'],
        'fullstack': ['full-stack', 'full stack'],
    }
    
    merged = {}
    seen_variants = set()
    
    for role_name, role_data in roles_dict.items():
        role_lower = role_name.lower()
        
        # Check if this is a variant of an existing role
        merged_into = None
        for canonical, variants in role_mergers.items():
            if role_lower == canonical or role_lower in variants:
                merged_into = canonical.title()
                break
            if any(v in role_lower for v in variants):
                merged_into = canonical.title()
                break
        
        if merged_into and merged_into in merged:
            # Merge skills into existing role
            merged[merged_into]['skills'].extend(role_data['skills'])
        elif role_lower not in seen_variants:
            merged[role_name] = role_data
            seen_variants.add(role_lower)
        else:
            # Keep the first occurrence
            merged[role_name] = role_data
    
    return merged


def clean_roadmaps(input_file, output_file):
    """Main cleaning function."""
    print(f"Loading {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    roles_dict = defaultdict(lambda: {'role': '', 'skills': []})
    skill_ids_seen = set()
    
    print("Processing roles and skills...")
    for role_obj in data.get('roles', []):
        role_name = role_obj.get('role_name', '')
        if not role_name:
            continue
        
        # Normalize role name
        normalized_role = normalize_role_name(role_name)
        if not normalized_role:
            continue
        
        # Process all sections and skills
        for section in role_obj.get('sections', []):
            section_name = section.get('section_name', 'main')
            if section_name == 'main':
                section_name = None
            
            for skill in section.get('skills', []):
                skill_text = skill.get('skill_text', '').strip()
                if not skill_text:
                    continue
                
                # Normalize skill name
                normalized_skill = normalize_skill_name(skill_text)
                if not normalized_skill or len(normalized_skill) < 2:
                    continue
                
                # Generate skill_id
                skill_id = slugify(normalized_skill)
                if skill_id in skill_ids_seen:
                    # Handle duplicates by appending role context
                    skill_id = f"{skill_id}-{slugify(normalized_role)}"
                skill_ids_seen.add(skill_id)
                
                # Extract and normalize links
                links = []
                link_hrefs = set()
                
                for link_obj in skill.get('links', []):
                    url = normalize_url(link_obj if isinstance(link_obj, str) else link_obj.get('href', ''))
                    if url and url not in link_hrefs:
                        links.append(url)
                        link_hrefs.add(url)
                
                # Generate keywords
                keywords = extract_keywords(normalized_skill, normalized_role)
                
                # Create skill entry
                skill_entry = {
                    'skill_id': skill_id,
                    'name': normalized_skill,
                    'category': section_name if section_name and section_name != 'main' else None,
                    'keywords': keywords,
                    'links': links
                }
                
                roles_dict[normalized_role]['role'] = normalized_role
                roles_dict[normalized_role]['skills'].append(skill_entry)
    
    print("Merging duplicate roles...")
    roles_dict = merge_duplicate_roles(roles_dict)
    
    # Remove roles with no skills and validate
    print("Validating and finalizing...")
    cleaned_roles = []
    for role_name, role_data in roles_dict.items():
        skills = role_data.get('skills', [])
        
        # Remove skills with no links and no meaningful content
        skills = [s for s in skills if s.get('links') or len(s.get('name', '')) > 3]
        
        if skills:
            # Deduplicate skills by name within role
            seen_names = set()
            unique_skills = []
            for skill in skills:
                skill_name = skill.get('name', '')
                if skill_name and skill_name not in seen_names:
                    seen_names.add(skill_name)
                    unique_skills.append(skill)
            
            cleaned_roles.append({
                'role': role_name,
                'skills': unique_skills
            })
    
    # Sort roles alphabetically
    cleaned_roles.sort(key=lambda x: x['role'])
    
    output_data = {
        'roles': cleaned_roles
    }
    
    print(f"Writing cleaned data to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    # Print summary
    total_skills = sum(len(r['skills']) for r in cleaned_roles)
    total_links = sum(sum(len(s['links']) for s in r['skills']) for r in cleaned_roles)
    
    print("\n" + "="*60)
    print("CLEANING SUMMARY")
    print("="*60)
    print(f"Roles: {len(cleaned_roles)}")
    print(f"Total skills: {total_skills}")
    print(f"Total links: {total_links}")
    print(f"Output file: {output_file.relative_to(REPO_ROOT)}")
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
    clean_roadmaps(INPUT_FILE, OUTPUT_FILE)

