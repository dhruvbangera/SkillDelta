#!/usr/bin/env python3
"""
Restructure roadmaps_cleaned.json into hierarchical domains format.

Groups skills under umbrella categories optimized for resume matching
and hierarchical search.
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

REPO_ROOT = Path(__file__).parent.parent
INPUT_FILE = REPO_ROOT / "data" / "roadmaps_cleaned.json"
OUTPUT_FILE = REPO_ROOT / "data" / "roadmaps_domains.json"

# Domain mappings based on roadmap.sh structure
DOMAIN_MAPPINGS = {
    # Web Development
    'Web Development': {
        'roles': [
            'Frontend', 'Backend', 'Full Stack', 'API Design', 'QA',
            'GraphQL', 'Git and GitHub', 'HTML', 'CSS', 'JavaScript',
            'TypeScript', 'React', 'Vue', 'Angular', 'Next.js',
            'Node.js', 'PHP', 'Laravel', 'ASP.NET Core', 'Spring Boot'
        ],
        'description': 'Core web development technologies, frameworks, and practices for building modern web applications and APIs.'
    },
    
    # Mobile Development
    'Mobile Development': {
        'roles': [
            'Android', 'iOS', 'React Native', 'Flutter', 'Swift UI',
            'Kotlin', 'Mobile Apps', 'Android Studio', 'Xcode'
        ],
        'description': 'Mobile app development platforms, frameworks, and tools for iOS and Android applications.'
    },
    
    # Artificial Intelligence & Machine Learning
    'Artificial Intelligence & Machine Learning': {
        'roles': [
            'AI Engineer', 'AI Agents', 'AI Data Scientist', 'AI Red Teaming',
            'Machine Learning', 'MLOps', 'Prompt Engineering', 'Data Science'
        ],
        'description': 'AI and ML technologies including model development, agent systems, MLOps, and AI safety practices.'
    },
    
    # Data Engineering & Analytics
    'Data Engineering & Analytics': {
        'roles': [
            'Data Engineer', 'Data Analyst', 'BI Analyst', 'Data Structures',
            'SQL', 'PostgreSQL DBA', 'MongoDB', 'Redis'
        ],
        'description': 'Data processing, storage, analysis, and business intelligence tools and techniques.'
    },
    
    # DevOps & Cloud
    'DevOps & Cloud': {
        'roles': [
            'DevOps', 'AWS', 'Cloudflare', 'Terraform', 'Docker', 'Kubernetes',
            'Linux', 'CI/CD', 'Shell Bash', 'Git and GitHub'
        ],
        'description': 'Cloud infrastructure, containerization, orchestration, and DevOps practices for scalable systems.'
    },
    
    # Programming Languages
    'Programming Languages': {
        'roles': [
            'Python', 'Java', 'C++', 'Go', 'Rust', 'JavaScript', 'TypeScript',
            'PHP', 'Ruby', 'Swift', 'Kotlin', 'Dart', 'C#', 'Shell Bash'
        ],
        'description': 'Core programming languages and their ecosystems for software development.'
    },
    
    # Computer Science Fundamentals
    'Computer Science Fundamentals': {
        'roles': [
            'Computer Science', 'Data Structures and Algorithms',
            'System Design', 'Software Design Architecture', 'Software Architect',
            'Code Review', 'Datastructures and Algorithms'
        ],
        'description': 'Fundamental computer science concepts, algorithms, data structures, and software architecture principles.'
    },
    
    # Databases
    'Databases': {
        'roles': [
            'PostgreSQL DBA', 'MongoDB', 'Redis', 'SQL', 'Databases'
        ],
        'description': 'Database systems, query languages, and data storage technologies for managing structured and unstructured data.'
    },
    
    # Game Development
    'Game Development': {
        'roles': [
            'Game Developer', 'Server Side Game Developer'
        ],
        'description': 'Game development frameworks, engines, and server-side game architecture.'
    },
    
    # Design & UX
    'Design & UX': {
        'roles': [
            'UX Design', 'Design System'
        ],
        'description': 'User experience design, design systems, and visual design principles for digital products.'
    },
    
    # Blockchain
    'Blockchain': {
        'roles': [
            'Blockchain'
        ],
        'description': 'Blockchain technology, cryptocurrencies, smart contracts, and decentralized applications.'
    },
    
    # Cyber Security
    'Cyber Security': {
        'roles': [
            'Cyber Security'
        ],
        'description': 'Cybersecurity practices, threat detection, security protocols, and secure development methodologies.'
    },
    
    # Management & Leadership
    'Management & Leadership': {
        'roles': [
            'Product Manager', 'Engineering Manager', 'Technical Writer', 'DevRel'
        ],
        'description': 'Product management, engineering leadership, technical communication, and developer relations.'
    },
    
    # Specialized Tools & Frameworks
    'Specialized Tools & Frameworks': {
        'roles': [
            'Flutter', 'React', 'Vue', 'Angular', 'Next.js', 'React Native',
            'Docker', 'Kubernetes', 'Terraform', 'GraphQL'
        ],
        'description': 'Specialized development tools, frameworks, and platforms for specific use cases.'
    }
}

# Category mappings for organizing skills within domains
CATEGORY_MAPPINGS = {
    'Web Development': {
        'Frontend Fundamentals': ['HTML', 'CSS', 'JavaScript', 'TypeScript', 'Accessibility'],
        'Frontend Frameworks': ['React', 'Vue', 'Angular', 'Next.js'],
        'Backend Development': ['Backend', 'Node.js', 'PHP', 'Laravel', 'ASP.NET Core', 'Spring Boot'],
        'API & Integration': ['API Design', 'GraphQL', 'REST'],
        'Tools & Workflow': ['Git and GitHub', 'Build Tools', 'Testing']
    },
    
    'Mobile Development': {
        'Native Development': ['Android', 'iOS', 'Swift UI', 'Kotlin'],
        'Cross-Platform': ['React Native', 'Flutter'],
        'Mobile Tools': ['Android Studio', 'Xcode', 'Mobile Apps']
    },
    
    'Artificial Intelligence & Machine Learning': {
        'AI Fundamentals': ['AI Engineer', 'AI Agents', 'AI Data Scientist', 'Prompt Engineering'],
        'Machine Learning': ['Machine Learning', 'MLOps', 'Data Science'],
        'AI Safety': ['AI Red Teaming']
    },
    
    'Data Engineering & Analytics': {
        'Data Engineering': ['Data Engineer', 'ETL', 'Data Pipelines'],
        'Data Analysis': ['Data Analyst', 'BI Analyst'],
        'Data Storage': ['SQL', 'PostgreSQL', 'MongoDB', 'Redis']
    },
    
    'DevOps & Cloud': {
        'Cloud Platforms': ['AWS', 'Cloudflare', 'Azure'],
        'Infrastructure as Code': ['Terraform', 'Cloudformation'],
        'Containers & Orchestration': ['Docker', 'Kubernetes'],
        'CI/CD': ['CI/CD', 'Continuous Integration', 'Continuous Deployment'],
        'System Administration': ['Linux', 'Shell Bash']
    },
    
    'Programming Languages': {
        'General Purpose': ['Python', 'Java', 'JavaScript', 'TypeScript', 'Go', 'Rust'],
        'Web Languages': ['PHP', 'Ruby'],
        'Mobile Languages': ['Swift', 'Kotlin', 'Dart'],
        'Systems Languages': ['C++', 'C#', 'Rust']
    },
    
    'Computer Science Fundamentals': {
        'Core Concepts': ['Computer Science', 'Algorithms', 'Data Structures'],
        'System Design': ['System Design', 'Architecture'],
        'Software Engineering': ['Code Review', 'Software Architect']
    },
    
    'Databases': {
        'Relational Databases': ['PostgreSQL', 'SQL', 'MySQL'],
        'NoSQL Databases': ['MongoDB', 'Redis']
    },
    
    'Game Development': {
        'Game Engines': ['Game Developer', 'Game Development'],
        'Server Architecture': ['Server Side Game Developer']
    },
    
    'Design & UX': {
        'User Experience': ['UX Design', 'User Research'],
        'Design Systems': ['Design System']
    },
    
    'Blockchain': {
        'Blockchain Fundamentals': ['Blockchain', 'Cryptocurrency', 'Smart Contracts']
    },
    
    'Cyber Security': {
        'Security Practices': ['Cyber Security', 'Security', 'Threat Detection']
    },
    
    'Management & Leadership': {
        'Product Management': ['Product Manager'],
        'Engineering Leadership': ['Engineering Manager'],
        'Technical Communication': ['Technical Writer', 'DevRel']
    }
}


def normalize_role_name(role_name):
    """Normalize role name for matching."""
    return role_name.lower().strip()


def find_domain_for_role(role_name, all_roles):
    """Find the best matching domain for a role."""
    role_lower = normalize_role_name(role_name)
    
    # Check each domain
    for domain, config in DOMAIN_MAPPINGS.items():
        for mapped_role in config['roles']:
            if normalize_role_name(mapped_role) in role_lower or role_lower in normalize_role_name(mapped_role):
                return domain
    
    # Check for partial matches
    for domain, config in DOMAIN_MAPPINGS.items():
        for mapped_role in config['roles']:
            mapped_lower = normalize_role_name(mapped_role)
            # Check if any word matches
            role_words = set(role_lower.split())
            mapped_words = set(mapped_lower.split())
            if role_words & mapped_words:
                return domain
    
    # Default to "Specialized Tools & Frameworks" if no match
    return "Specialized Tools & Frameworks"


def find_category_for_skill(skill_name, role_name, domain):
    """Find the best matching category for a skill within a domain."""
    skill_lower = skill_name.lower()
    role_lower = role_name.lower()
    
    if domain not in CATEGORY_MAPPINGS:
        return "General"
    
    categories = CATEGORY_MAPPINGS[domain]
    
    # Check each category
    for category, keywords in categories.items():
        for keyword in keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in skill_lower or keyword_lower in role_lower:
                return category
    
    # Default category based on domain
    default_categories = {
        'Web Development': 'Web Technologies',
        'Mobile Development': 'Mobile Technologies',
        'Artificial Intelligence & Machine Learning': 'AI/ML Technologies',
        'Data Engineering & Analytics': 'Data Technologies',
        'DevOps & Cloud': 'DevOps Tools',
        'Programming Languages': 'Language Features',
        'Computer Science Fundamentals': 'CS Concepts',
        'Databases': 'Database Technologies',
        'Game Development': 'Game Technologies',
        'Design & UX': 'Design Principles',
        'Blockchain': 'Blockchain Technologies',
        'Cyber Security': 'Security Practices',
        'Management & Leadership': 'Management Skills',
        'Specialized Tools & Frameworks': 'Tools & Frameworks'
    }
    
    return default_categories.get(domain, 'General')


def restructure_to_domains(input_file, output_file):
    """Main restructuring function."""
    print(f"Loading {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Build domain structure
    domains_dict = defaultdict(lambda: {
        'umbrella': '',
        'description': '',
        'skills': defaultdict(lambda: {'category': '', 'subskills': []})
    })
    
    print("Processing roles and mapping to domains...")
    all_roles = [r['role'] for r in data['roles']]
    
    for role_obj in data['roles']:
        role_name = role_obj.get('role', '')
        if not role_name:
            continue
        
        # Find domain
        domain = find_domain_for_role(role_name, all_roles)
        
        # Initialize domain if needed
        if not domains_dict[domain]['umbrella']:
            domains_dict[domain]['umbrella'] = domain
            domains_dict[domain]['description'] = DOMAIN_MAPPINGS.get(domain, {}).get('description', 
                f'Skills and technologies related to {domain.lower()}.')
        
        # Process skills
        for skill in role_obj.get('skills', []):
            skill_name = skill.get('name', '')
            if not skill_name:
                continue
            
            # Find category
            category = find_category_for_skill(skill_name, role_name, domain)
            
            # Create subskill entry
            subskill = {
                'skill_id': skill.get('skill_id', ''),
                'name': skill_name,
                'keywords': skill.get('keywords', []),
                'links': skill.get('links', [])
            }
            
            # Add to domain
            category_key = category
            if not domains_dict[domain]['skills'][category_key]['category']:
                domains_dict[domain]['skills'][category_key]['category'] = category
            
            domains_dict[domain]['skills'][category_key]['subskills'].append(subskill)
    
    # Convert to final structure
    print("Building final domain structure...")
    domains_list = []
    
    for domain_name, domain_data in sorted(domains_dict.items()):
        skills_list = []
        
        for category_name, category_data in sorted(domain_data['skills'].items()):
            if category_data['subskills']:
                skills_list.append({
                    'category': category_data['category'],
                    'subskills': category_data['subskills']
                })
        
        if skills_list:
            domains_list.append({
                'umbrella': domain_data['umbrella'],
                'description': domain_data['description'],
                'skills': skills_list
            })
    
    output_data = {
        'domains': domains_list
    }
    
    print(f"Writing restructured data to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    # Print summary
    total_domains = len(domains_list)
    total_categories = sum(len(d['skills']) for d in domains_list)
    total_subskills = sum(
        sum(len(cat['subskills']) for cat in d['skills'])
        for d in domains_list
    )
    
    print("\n" + "="*60)
    print("RESTRUCTURING SUMMARY")
    print("="*60)
    print(f"Domains (umbrellas): {total_domains}")
    print(f"Categories: {total_categories}")
    print(f"Subskills: {total_subskills}")
    print(f"\nDomains:")
    for domain in domains_list:
        categories_count = len(domain['skills'])
        subskills_count = sum(len(cat['subskills']) for cat in domain['skills'])
        print(f"  - {domain['umbrella']}: {categories_count} categories, {subskills_count} subskills")
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
    restructure_to_domains(INPUT_FILE, OUTPUT_FILE)

