# Roadmap Data Extraction Script

This directory contains scripts for extracting structured data from the developer-roadmap repository.

## parse_roadmaps.py

Extracts roadmap data from markdown files and produces two outputs:
- `data/roadmaps.json` - Nested JSON structure with roles, sections, skills, and links
- `data/roadmaps.csv` - Flattened CSV format for spreadsheet use

### Requirements

Install required Python packages:

```bash
pip install markdown beautifulsoup4
```

### Usage

Run from the repository root:

```bash
python3 scripts/parse_roadmaps.py
```

The script will:
1. Scan all markdown files in `developer-roadmap/src/data/roadmaps/`
2. Extract roles, sections, skills, and resource links
3. Convert relative links to absolute GitHub raw URLs
4. Write outputs to `data/roadmaps.json` and `data/roadmaps.csv`
5. Print a summary with statistics and any warnings

### Output Format

#### JSON Structure

```json
{
  "meta": {
    "repo": "owner/repo",
    "repo_commit": "abc123...",
    "generated_at": "2025-01-08T12:34:56Z"
  },
  "roles": [
    {
      "role_name": "Frontend",
      "source_files": ["roadmaps/frontend/README.md"],
      "sections": [
        {
          "section_name": "Fundamentals",
          "skills": [
            {
              "skill_text": "HTML",
              "parent_skill": null,
              "links": [
                {"text": "MDN - HTML", "href": "https://..."}
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

#### CSV Structure

Each row represents one link for a skill:
- `role_name` - The roadmap role/topic
- `section_name` - Section within the role
- `skill_text` - The skill name
- `parent_skill` - Parent skill if this is a sub-skill
- `link_text` - Link anchor text
- `link_href` - Link URL

Skills with no links will have empty `link_text` and `link_href` columns.

### Extraction Rules

1. **Role Detection** (in order of priority):
   - H1 heading in the file
   - Top-level folder name containing the file
   - Filename (without extension)

2. **Section Detection**:
   - H2 or H3 headings define sections
   - If no headings exist, uses "main" as the section name

3. **Skill Extraction**:
   - List items (`<li>`) under sections are treated as skills
   - Nested list items become sub-skills with `parent_skill` reference
   - Skills are normalized (badges, trailing punctuation removed)

4. **Link Extraction**:
   - All `<a>` tags within list items
   - Plain URLs in text (http/https)
   - Links are deduplicated per skill
   - Relative links are converted to absolute GitHub raw URLs

5. **Table Processing**:
   - Links in table cells are associated with the nearest preceding heading
   - Each link becomes a separate skill entry

### Link Resolution

The script attempts to convert relative links to absolute GitHub raw URLs using:
- Git commit hash (from `git rev-parse HEAD`)
- Repository owner/repo (from `git remote get-url origin`)

Format: `https://raw.githubusercontent.com/{owner}/{repo}/{commit}/{path}`

If git information is unavailable, relative paths are preserved as file system paths.

### Changing Base URL Logic

To modify how links are resolved, edit the `normalize_url()` function in `parse_roadmaps.py`:

```python
def normalize_url(url, base_path, repo_owner_repo, commit_hash):
    # Customize link resolution logic here
    ...
```

For private repositories or different hosting:
1. Modify `get_repo_info()` to extract different remote URL format
2. Update `normalize_url()` to use a different base URL pattern
3. Or disable URL normalization by returning the original URL

### Handling Client-Side Rendered Content

If you encounter markdown files that are client-side rendered (e.g., React/Vue components that generate content dynamically), the static parser will not be able to extract the content.

For such cases, consider using a headless browser approach:

#### Playwright-Based Approach (Suggested)

```python
from playwright.sync_api import sync_playwright

def extract_with_playwright(url):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)
        # Wait for content to render
        page.wait_for_selector('main', timeout=10000)
        # Extract rendered HTML
        html = page.content()
        browser.close()
        return html
```

To implement this:
1. Install: `pip install playwright`
2. Install browser: `playwright install chromium`
3. Modify `parse_markdown_file()` to detect client-rendered files
4. Use Playwright to fetch rendered HTML before parsing

**Note**: This approach is not implemented by default as it requires additional dependencies and is slower. Only use if you encounter files that cannot be parsed statically.

### Troubleshooting

**No data extracted:**
- Check that `developer-roadmap/src/data/roadmaps/` exists
- Verify markdown files are present
- Check parse warnings in the output

**Missing links:**
- Some files may use non-standard markdown formats
- Check warnings for specific files that failed to parse
- Links in code blocks or special syntax may not be extracted

**Incorrect role names:**
- The script uses H1 → folder name → filename priority
- If role names are wrong, check the markdown file structure
- You can manually adjust the `normalize_skill_text()` function

### Assumptions and Limitations

1. **File Structure**: Assumes markdown files follow standard markdown with headings and lists. Files with only frontmatter and no content will be skipped.

2. **Content Files**: Content files in `{role}/content/` subdirectories are treated as individual skills. Each content file becomes a skill entry.

3. **Link Deduplication**: Links are deduplicated per skill based on normalized href. Different anchor texts pointing to the same URL are merged.

4. **Whitespace Normalization**: Skill text is normalized to remove extra whitespace, badges, and trailing punctuation while preserving meaning.

5. **Error Handling**: Files that fail to parse are logged as warnings but don't stop processing. Only unrecoverable errors (missing dependencies, file system errors) cause the script to exit with non-zero code.

### Idempotency

The script is idempotent: re-running it will overwrite `data/roadmaps.json` and `data/roadmaps.csv` cleanly. No incremental updates or merging is performed.

