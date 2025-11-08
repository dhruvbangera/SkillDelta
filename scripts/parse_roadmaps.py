#!/usr/bin/env python3
"""
Extract roadmap data from developer-roadmap repository.

This script parses markdown files to extract:
- Roles (from h1, folder name, or filename)
- Sections (from h2/h3 headings)
- Skills (from list items)
- Resource links (from anchor tags or plain URLs)

Outputs:
- data/roadmaps.json: Nested JSON structure
- data/roadmaps.csv: Flattened CSV for spreadsheet use
"""

import os
import re
import json
import csv
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse
from collections import defaultdict
import warnings

try:
    import markdown
    from bs4 import BeautifulSoup
except ImportError as e:
    print(f"ERROR: Missing required package: {e}")
    print("Please install: pip install markdown beautifulsoup4")
    sys.exit(1)


# Configuration
REPO_ROOT = Path(__file__).parent.parent
ROADMAPS_DIR = REPO_ROOT / "developer-roadmap" / "src" / "data" / "roadmaps"
OUTPUT_DIR = REPO_ROOT / "data"
JSON_OUTPUT = OUTPUT_DIR / "roadmaps.json"
CSV_OUTPUT = OUTPUT_DIR / "roadmaps.csv"

# Track warnings
PARSE_WARNINGS = []


def get_git_commit_hash():
    """Get the current git commit hash."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT / "developer-roadmap",
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def get_repo_info():
    """Extract owner/repo from git remote origin."""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=REPO_ROOT / "developer-roadmap",
            capture_output=True,
            text=True,
            check=True
        )
        url = result.stdout.strip()
        
        # Handle both https:// and git@ formats
        if url.startswith("https://github.com/"):
            match = re.search(r"github\.com/([^/]+)/([^/]+?)(?:\.git)?$", url)
            if match:
                return f"{match.group(1)}/{match.group(2)}"
        elif url.startswith("git@github.com:"):
            match = re.search(r"github\.com:([^/]+)/([^/]+?)(?:\.git)?$", url)
            if match:
                return f"{match.group(1)}/{match.group(2)}"
        
        return "kamranahmedse/developer-roadmap"  # default
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "kamranahmedse/developer-roadmap"  # default


def normalize_skill_text(text):
    """Normalize skill text by removing badges, trailing punctuation, etc."""
    if not text:
        return ""
    
    # Remove @type@ prefixes (e.g., @official@, @article@)
    text = re.sub(r'@\w+@', '', text)
    
    # Remove common badge patterns (e.g., ![alt](url), [![badge]](url))
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    text = re.sub(r'\[!\[.*?\]\(.*?\)\]\(.*?\)', '', text)
    
    # Remove trailing punctuation that's likely noise
    text = re.sub(r'[.,;:!?]+$', '', text)
    
    # Normalize whitespace
    text = ' '.join(text.split())
    
    return text.strip()


def extract_links_from_html(html_content):
    """Extract all links from HTML content."""
    soup = BeautifulSoup(html_content, 'html.parser')
    links = []
    
    # Find all anchor tags
    for a in soup.find_all('a', href=True):
        href = a.get('href', '').strip()
        text = a.get_text(strip=True)
        if href:
            links.append({"text": text or href, "href": href})
    
    # Also find plain URLs in text
    url_pattern = re.compile(r'https?://[^\s<>"{}|\\^`\[\]]+')
    for match in url_pattern.finditer(html_content):
        url = match.group(0)
        # Check if not already captured as an anchor
        if not any(link['href'] == url for link in links):
            links.append({"text": url, "href": url})
    
    return links


def normalize_url(url, base_path, repo_owner_repo, commit_hash):
    """Convert relative URLs to absolute GitHub raw URLs."""
    if not url:
        return url
    
    # Already absolute
    if url.startswith(('http://', 'https://')):
        return url
    
    # Remove anchor fragments
    url = url.split('#')[0]
    
    # Handle relative paths
    if url.startswith('/'):
        # Absolute path from repo root
        path = url.lstrip('/')
    else:
        # Relative to current file
        base_dir = base_path.parent if base_path.is_file() else base_path
        path = str((base_dir / url).resolve().relative_to(REPO_ROOT / "developer-roadmap"))
        # Normalize path separators
        path = path.replace('\\', '/')
    
    # Build raw GitHub URL
    if commit_hash and commit_hash != "unknown":
        return f"https://raw.githubusercontent.com/{repo_owner_repo}/{commit_hash}/{path}"
    else:
        # Fallback to file path
        return str(Path(REPO_ROOT / "developer-roadmap" / path).resolve())


def parse_content_file(file_path, repo_owner_repo, commit_hash):
    """Parse a content file (each file represents a skill)."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        PARSE_WARNINGS.append(f"Failed to read {file_path}: {e}")
        return None
    
    # Convert markdown to HTML
    try:
        md = markdown.Markdown(extensions=['tables', 'fenced_code'])
        html = md.convert(content)
    except Exception as e:
        PARSE_WARNINGS.append(f"Failed to parse markdown in {file_path}: {e}")
        return None
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Extract skill name from h1
    h1 = soup.find('h1')
    skill_text = h1.get_text(strip=True) if h1 else file_path.stem.split('@')[0].replace('-', ' ').title()
    skill_text = normalize_skill_text(skill_text)
    
    if not skill_text:
        return None
    
    # Extract links
    links = []
    seen_hrefs = set()
    
    # Find all anchor tags
    for a in soup.find_all('a', href=True):
        href = a.get('href', '').strip()
        link_text = a.get_text(strip=True) or href
        
        # Normalize link text
        normalized_link_text = normalize_skill_text(link_text) or link_text
        
        if href:
            normalized_href = normalize_url(href, file_path, repo_owner_repo, commit_hash)
            if normalized_href not in seen_hrefs:
                seen_hrefs.add(normalized_href)
                links.append({
                    "text": normalized_link_text,
                    "href": normalized_href
                })
    
    # Check for plain URLs (but avoid duplicates from markdown links)
    url_pattern = re.compile(r'https?://[^\s<>"{}|\\^`\[\]()]+')
    for match in url_pattern.finditer(content):
        url = match.group(0)
        # Remove trailing punctuation that might be from markdown syntax
        url = url.rstrip('.,;:!?)')
        if url not in seen_hrefs:
            seen_hrefs.add(url)
            links.append({"text": url, "href": url})
    
    return {
        "skill_text": skill_text,
        "parent_skill": None,
        "links": links
    }


def parse_markdown_file(file_path, repo_owner_repo, commit_hash):
    """Parse a markdown file and extract role, sections, skills, and links."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        PARSE_WARNINGS.append(f"Failed to read {file_path}: {e}")
        return None
    
    # Skip frontmatter if present
    frontmatter_end = 0
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            frontmatter_end = len(parts[0]) + len(parts[1]) + 6  # 6 for three '---'
            content = parts[2].lstrip()
    
    # If content is empty after frontmatter, skip
    if not content.strip():
        return None
    
    # Convert markdown to HTML
    try:
        md = markdown.Markdown(extensions=['tables', 'fenced_code'])
        html = md.convert(content)
    except Exception as e:
        PARSE_WARNINGS.append(f"Failed to parse markdown in {file_path}: {e}")
        return None
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Determine role name
    role_name = None
    h1 = soup.find('h1')
    if h1:
        role_name = h1.get_text(strip=True)
    
    if not role_name:
        # Use folder name
        folder_name = file_path.parent.name
        if folder_name and folder_name != 'content':
            role_name = folder_name.replace('-', ' ').title()
        else:
            # Go up one level for content files
            parent_folder = file_path.parent.parent.name if file_path.parent.name == 'content' else folder_name
            if parent_folder:
                role_name = parent_folder.replace('-', ' ').title()
            else:
                # Use filename without extension
                role_name = file_path.stem.replace('-', ' ').title()
    
    # Extract sections and skills
    sections = []
    current_section = None
    current_section_name = "main"
    
    # Find all headings and lists
    elements = soup.find_all(['h1', 'h2', 'h3', 'ul', 'ol', 'table'])
    
    for element in elements:
        if element.name in ['h2', 'h3']:
            # Save previous section if it has skills
            if current_section and current_section['skills']:
                sections.append(current_section)
            
            # Start new section
            current_section_name = element.get_text(strip=True)
            current_section = {
                "section_name": current_section_name,
                "skills": []
            }
        
        elif element.name in ['ul', 'ol']:
            # Process list items
            if not current_section:
                current_section = {
                    "section_name": "main",
                    "skills": []
                }
            
            for li in element.find_all('li', recursive=False):
                skill_data = parse_list_item(li, file_path, repo_owner_repo, commit_hash)
                if skill_data:
                    current_section['skills'].append(skill_data)
        
        elif element.name == 'table':
            # Process table for links
            if not current_section:
                current_section = {
                    "section_name": "main",
                    "skills": []
                }
            
            table_skills = parse_table(element, file_path, repo_owner_repo, commit_hash)
            current_section['skills'].extend(table_skills)
    
    # Save last section
    if current_section and current_section['skills']:
        sections.append(current_section)
    
    # If no sections found but we have content, create a main section
    if not sections:
        # Try to extract any lists from the document
        all_lists = soup.find_all(['ul', 'ol'])
        if all_lists:
            main_section = {
                "section_name": "main",
                "skills": []
            }
            for ul in all_lists:
                for li in ul.find_all('li', recursive=False):
                    skill_data = parse_list_item(li, file_path, repo_owner_repo, commit_hash)
                    if skill_data:
                        main_section['skills'].append(skill_data)
            
            if main_section['skills']:
                sections.append(main_section)
    
    if not sections:
        return None
    
    return {
        "role_name": role_name,
        "source_files": [str(file_path.relative_to(REPO_ROOT / "developer-roadmap"))],
        "sections": sections
    }


def parse_list_item(li_element, file_path, repo_owner_repo, commit_hash):
    """Parse a list item to extract skill text and links."""
    # Get the text content (excluding nested lists)
    text_parts = []
    for child in li_element.children:
        if child.name == 'ul' or child.name == 'ol':
            break
        if hasattr(child, 'get_text'):
            text_parts.append(child.get_text(strip=True))
        elif isinstance(child, str):
            text_parts.append(child.strip())
    
    text = ' '.join(text_parts)
    
    # Remove nested list markers from text
    text = re.sub(r'^\s*[-*+]\s+', '', text)
    
    # Extract links first (before normalizing text)
    links = []
    seen_hrefs = set()
    
    # Find all anchor tags
    for a in li_element.find_all('a', href=True):
        href = a.get('href', '').strip()
        link_text = a.get_text(strip=True) or href
        
        # Normalize link text (remove @type@ but keep meaningful text)
        normalized_link_text = normalize_skill_text(link_text) or link_text
        
        # Normalize URL
        normalized_href = normalize_url(href, file_path, repo_owner_repo, commit_hash)
        
        # Deduplicate
        if normalized_href not in seen_hrefs:
            seen_hrefs.add(normalized_href)
            links.append({
                "text": normalized_link_text,
                "href": normalized_href
            })
    
    # If the text is just link text, use normalized link text
    if not text.strip() and links:
        skill_text = links[0]["text"]
    else:
        # Normalize skill text
        skill_text = normalize_skill_text(text)
    
    if not skill_text:
        return None
    
    # Check for plain URLs in text (but avoid duplicates from anchor tags)
    url_pattern = re.compile(r'https?://[^\s<>"{}|\\^`\[\]()]+')
    for match in url_pattern.finditer(str(li_element)):
        url = match.group(0)
        # Remove trailing punctuation that might be from markdown syntax
        url = url.rstrip('.,;:!?)')
        if url not in seen_hrefs:
            seen_hrefs.add(url)
            links.append({"text": url, "href": url})
    
    # Check for nested lists (sub-skills)
    nested_ul = li_element.find('ul', recursive=False)
    nested_ol = li_element.find('ol', recursive=False)
    
    skill_data = {
        "skill_text": skill_text,
        "parent_skill": None,
        "links": links
    }
    
    # Process nested items as sub-skills
    if nested_ul or nested_ol:
        nested_list = nested_ul or nested_ol
        nested_skills = []
        for nested_li in nested_list.find_all('li', recursive=False):
            nested_skill = parse_list_item(nested_li, file_path, repo_owner_repo, commit_hash)
            if nested_skill:
                nested_skill["parent_skill"] = skill_text
                nested_skills.append(nested_skill)
        
        # Return parent skill, sub-skills will be added separately
        return skill_data
    
    return skill_data


def parse_table(table_element, file_path, repo_owner_repo, commit_hash):
    """Parse a table to extract links, associating them with the nearest preceding heading."""
    skills = []
    seen_hrefs = set()
    
    for row in table_element.find_all('tr'):
        cells = row.find_all(['td', 'th'])
        for cell in cells:
            for a in cell.find_all('a', href=True):
                href = a.get('href', '').strip()
                link_text = a.get_text(strip=True) or href
                
                if href:
                    normalized_href = normalize_url(href, file_path, repo_owner_repo, commit_hash)
                    
                    if normalized_href not in seen_hrefs:
                        seen_hrefs.add(normalized_href)
                        # Use cell text or link text as skill
                        cell_text = cell.get_text(strip=True)
                        skill_text = normalize_skill_text(cell_text or link_text)
                        
                        if skill_text:
                            skills.append({
                                "skill_text": skill_text,
                                "parent_skill": None,
                                "links": [{
                                    "text": link_text,
                                    "href": normalized_href
                                }]
                            })
    
    return skills


def find_markdown_files():
    """Find all markdown files in the roadmaps directory."""
    if not ROADMAPS_DIR.exists():
        PARSE_WARNINGS.append(f"Roadmaps directory not found: {ROADMAPS_DIR}")
        return []
    
    md_files = []
    for md_file in ROADMAPS_DIR.rglob("*.md"):
        # Skip files in content subdirectories for now (they're individual skills)
        # Focus on main roadmap files
        if 'content' not in md_file.parts:
            md_files.append(md_file)
        # Also include content files as they may have structure
        elif md_file.parent.name == 'content':
            md_files.append(md_file)
    
    return md_files


def process_roadmaps():
    """Main processing function."""
    commit_hash = get_git_commit_hash()
    repo_owner_repo = get_repo_info()
    
    md_files = find_markdown_files()
    
    if not md_files:
        PARSE_WARNINGS.append("No markdown files found")
        return None
    
    # Group by role
    roles_dict = defaultdict(lambda: {
        "role_name": None,
        "source_files": [],
        "sections": defaultdict(lambda: {"section_name": None, "skills": []})
    })
    
    # Process content files separately (they're individual skills)
    content_files_by_role = defaultdict(lambda: defaultdict(list))
    
    for md_file in md_files:
        # Check if it's a content file
        if md_file.parent.name == 'content':
            # Parse as content file (individual skill)
            skill_data = parse_content_file(md_file, repo_owner_repo, commit_hash)
            if skill_data:
                # Determine role from parent directory
                role_dir = md_file.parent.parent
                role_name = role_dir.name.replace('-', ' ').title()
                
                # Determine section from subdirectory or use "main"
                section_name = "main"
                if md_file.parent != role_dir / 'content':
                    # There might be subdirectories
                    rel_path = md_file.relative_to(role_dir / 'content')
                    if len(rel_path.parts) > 1:
                        section_name = rel_path.parts[0].replace('-', ' ').title()
                
                content_files_by_role[role_name][section_name].append({
                    "file": str(md_file.relative_to(REPO_ROOT / "developer-roadmap")),
                    "skill": skill_data
                })
        else:
            # Parse as regular markdown file
            result = parse_markdown_file(md_file, repo_owner_repo, commit_hash)
            if result:
                role_name = result["role_name"]
                roles_dict[role_name]["role_name"] = role_name
                roles_dict[role_name]["source_files"].extend(result["source_files"])
                
                # Merge sections
                for section in result["sections"]:
                    section_name = section["section_name"]
                    roles_dict[role_name]["sections"][section_name]["section_name"] = section_name
                    roles_dict[role_name]["sections"][section_name]["skills"].extend(section["skills"])
    
    # Merge content files into roles
    for role_name, sections_dict in content_files_by_role.items():
        roles_dict[role_name]["role_name"] = role_name
        for section_name, skills_list in sections_dict.items():
            roles_dict[role_name]["sections"][section_name]["section_name"] = section_name
            for item in skills_list:
                roles_dict[role_name]["source_files"].append(item["file"])
                roles_dict[role_name]["sections"][section_name]["skills"].append(item["skill"])
    
    # Convert to final structure
    roles_list = []
    for role_name, role_data in roles_dict.items():
        sections_list = []
        for section_name, section_data in role_data["sections"].items():
            sections_list.append({
                "section_name": section_data["section_name"],
                "skills": section_data["skills"]
            })
        
        roles_list.append({
            "role_name": role_data["role_name"],
            "source_files": sorted(list(set(role_data["source_files"]))),  # Deduplicate and sort
            "sections": sections_list
        })
    
    return {
        "meta": {
            "repo": repo_owner_repo,
            "repo_commit": commit_hash,
            "generated_at": datetime.now(timezone.utc).isoformat()
        },
        "roles": roles_list
    }


def write_json_output(data):
    """Write JSON output file."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(JSON_OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"[OK] Written JSON: {JSON_OUTPUT.relative_to(REPO_ROOT)}")


def write_csv_output(data):
    """Write CSV output file."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(CSV_OUTPUT, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            "role_name", "section_name", "skill_text", "parent_skill",
            "link_text", "link_href"
        ])
        
        for role in data["roles"]:
            for section in role["sections"]:
                for skill in section["skills"]:
                    if skill["links"]:
                        for link in skill["links"]:
                            writer.writerow([
                                role["role_name"],
                                section["section_name"],
                                skill["skill_text"],
                                skill["parent_skill"] or "",
                                link["text"],
                                link["href"]
                            ])
                    else:
                        # Empty row for skills with no links
                        writer.writerow([
                            role["role_name"],
                            section["section_name"],
                            skill["skill_text"],
                            skill["parent_skill"] or "",
                            "",
                            ""
                        ])
    
    print(f"[OK] Written CSV: {CSV_OUTPUT.relative_to(REPO_ROOT)}")


def generate_summary(data):
    """Generate and print summary statistics."""
    total_files = len(find_markdown_files())
    unique_roles = len(data["roles"])
    total_skills = sum(
        len(skill)
        for role in data["roles"]
        for section in role["sections"]
        for skill in [section["skills"]]
    )
    
    all_links = set()
    for role in data["roles"]:
        for section in role["sections"]:
            for skill in section["skills"]:
                for link in skill["links"]:
                    all_links.add(link["href"])
    
    total_links = len(all_links)
    
    print("\n" + "="*60)
    print("EXTRACTION SUMMARY")
    print("="*60)
    print(f"Markdown files scanned: {total_files}")
    print(f"Roles extracted: {unique_roles}")
    print(f"Total skills: {total_skills}")
    print(f"Total unique resource links: {total_links}")
    
    if PARSE_WARNINGS:
        print(f"\nWarnings ({len(PARSE_WARNINGS)}):")
        for warning in PARSE_WARNINGS[:10]:  # Show first 10
            print(f"  - {warning}")
        if len(PARSE_WARNINGS) > 10:
            print(f"  ... and {len(PARSE_WARNINGS) - 10} more warnings")
    else:
        print("\nNo warnings")
    
    print("="*60)


def run_sanity_checks():
    """Run sanity checks on random files."""
    import random
    
    md_files = find_markdown_files()
    if not md_files:
        print("No files to check")
        return
    
    sample_files = random.sample(md_files, min(5, len(md_files)))
    
    print("\n" + "="*60)
    print("SANITY CHECKS (Sample Files)")
    print("="*60)
    
    commit_hash = get_git_commit_hash()
    repo_owner_repo = get_repo_info()
    
    for sample_file in sample_files:
        print(f"\nFile: {sample_file.relative_to(REPO_ROOT / 'developer-roadmap')}")
        result = parse_markdown_file(sample_file, repo_owner_repo, commit_hash)
        if result:
            print(f"  Role: {result['role_name']}")
            print(f"  Sections: {len(result['sections'])}")
            total_skills = sum(len(s['skills']) for s in result['sections'])
            print(f"  Skills: {total_skills}")
            if result['sections']:
                first_section = result['sections'][0]
                if first_section['skills']:
                    first_skill = first_section['skills'][0]
                    print(f"  Sample skill: {first_skill['skill_text'][:50]}...")
                    if first_skill['links']:
                        print(f"  Sample link: {first_skill['links'][0]['text'][:40]}...")
        else:
            print("  (No data extracted)")


def validate_outputs():
    """Validate that outputs are readable."""
    print("\n" + "="*60)
    print("VALIDATION")
    print("="*60)
    
    # Validate JSON
    try:
        with open(JSON_OUTPUT, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        print("[OK] JSON is valid and readable")
    except Exception as e:
        print(f"[ERROR] JSON validation failed: {e}")
        return False
    
    # Validate CSV
    try:
        with open(CSV_OUTPUT, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
            if len(rows) > 0:
                print(f"[OK] CSV is valid and readable ({len(rows)-1} data rows)")
            else:
                print("[ERROR] CSV is empty")
                return False
    except Exception as e:
        print(f"[ERROR] CSV validation failed: {e}")
        return False
    
    return True


def main():
    """Main entry point."""
    print("Starting roadmap extraction...")
    print(f"Roadmaps directory: {ROADMAPS_DIR}")
    print(f"Output directory: {OUTPUT_DIR}")
    
    # Process roadmaps
    data = process_roadmaps()
    
    if not data:
        print("ERROR: No data extracted")
        sys.exit(1)
    
    # Write outputs
    write_json_output(data)
    write_csv_output(data)
    
    # Generate summary
    generate_summary(data)
    
    # Run sanity checks
    if __name__ == "__main__":
        run_sanity_checks()
        validate_outputs()
    
    print("\n[OK] Extraction complete!")


if __name__ == "__main__":
    main()

