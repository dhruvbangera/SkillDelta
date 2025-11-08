# LinkedIn Job Data Processor

This script processes LinkedIn job postings from the [LinkedIn Job Scraper](https://github.com/ArshKA/LinkedIn-Job-Scraper) repository and extracts skills, mapping them to roadmap.sh resources.

## Overview

The script extracts:
1. **Job Title** - Normalized and capitalized
2. **Company Name** - Cleaned text
3. **Job Description** - Full text, HTML cleaned
4. **Extracted Skills** - Automatically detected using NLP-based keyword extraction

Each skill is mapped to:
- `skill_id` - URL-friendly slug
- `name` - Proper capitalized name
- `topics` - Relevant topic categories
- `resources` - Links to roadmap.sh guides

## Data Sources

### Option 1: Kaggle Dataset (Recommended)
The polished dataset is available on Kaggle:
- **URL**: https://www.kaggle.com/datasets/arshkon/linkedin-job-postings
- **Format**: CSV files or SQLite database
- **Size**: Large dataset with thousands of job postings

### Option 2: Scrape Your Own Data
Use the LinkedIn Job Scraper repository to collect fresh data:
1. Set up LinkedIn credentials in `logins.csv`
2. Run `search_retriever.py` and `details_retriever.py`
3. Export to CSV using `to_csv.py`

## Usage

### Basic Usage (Auto-detect data source)

```bash
python scripts/process_linkedin_jobs.py
```

The script will automatically search for:
- `job-listings/linkedin_jobs.db` (SQLite database)
- `job-listings/csv_files/job_postings.csv` (CSV file)
- `data/linkedin_jobs.db` or `data/job_postings.csv`

### Specify Database File

```bash
python scripts/process_linkedin_jobs.py --database path/to/linkedin_jobs.db
```

### Specify CSV File

```bash
python scripts/process_linkedin_jobs.py --csv path/to/job_postings.csv
```

### Limit Number of Jobs

```bash
python scripts/process_linkedin_jobs.py --csv data.csv --limit 100
```

### Custom Output Path

```bash
python scripts/process_linkedin_jobs.py --csv data.csv --output data/custom_output.json
```

## Output Format

The script generates a JSON file with the following structure:

```json
{
  "jobs": [
    {
      "job_title": "Machine Learning Engineer",
      "company_name": "OpenAI",
      "job_description": "We are looking for a Machine Learning Engineer...",
      "skills": [
        {
          "skill_id": "python",
          "name": "Python",
          "topics": [
            "programming language",
            "backend scripting",
            "automation"
          ],
          "resources": [
            "https://roadmap.sh/python",
            "https://roadmap.sh/python/guide"
          ]
        },
        {
          "skill_id": "pytorch",
          "name": "PyTorch",
          "topics": [
            "deep learning",
            "machine learning frameworks"
          ],
          "resources": [
            "https://roadmap.sh/ai-engineer",
            "https://roadmap.sh/ai-engineer/guide"
          ]
        }
      ]
    }
  ]
}
```

## Skill Extraction

The script uses pattern matching and a comprehensive skill taxonomy to extract:

### Programming Languages
Python, Java, JavaScript, TypeScript, C++, C#, Go, Rust, Kotlin, Swift, PHP, Ruby, Scala, R

### Frameworks
- **Frontend**: React, Vue.js, Angular, Next.js, Nuxt, Svelte
- **Backend**: Django, Flask, FastAPI, Express.js, Spring, ASP.NET, Laravel, Rails, Gin

### Databases
MySQL, PostgreSQL, MongoDB, Redis, Elasticsearch, Cassandra, DynamoDB, SQLite, Oracle, SQL Server

### Cloud Platforms
AWS, Azure, GCP (Google Cloud)

### DevOps Tools
Docker, Kubernetes, Jenkins, GitLab, GitHub Actions, Terraform, Ansible, Git

### AI/ML
TensorFlow, PyTorch, scikit-learn, Keras, Pandas, NumPy, OpenCV, NLTK, spaCy

### Mobile
React Native, Flutter, iOS, Android, Xamarin

### Concepts
REST, GraphQL, Microservices, Agile, Scrum, OOP, Functional Programming

## Requirements

The script uses only Python standard library modules:
- `json`
- `re`
- `sqlite3`
- `csv`
- `os`
- `pathlib`
- `html`
- `collections`
- `typing`
- `argparse`

No external dependencies required!

## Database Schema

If using the SQLite database, the script expects these tables:
- `jobs` - Contains job postings with columns: `job_id`, `company_id`, `title`, `description`, `skills_desc`
- `companies` - Contains company information with columns: `company_id`, `name`

## CSV Format

If using CSV files, the script expects columns:
- `title` or `job_title` - Job title
- `company_name` or `name` - Company name
- `description` - Job description
- `skills_desc` (optional) - Additional skills description

## Validation

The script ensures:
- ✅ Each job has at least 3 extracted skills
- ✅ All fields are valid JSON types
- ✅ No null or empty required fields
- ✅ Skills are deduplicated per job
- ✅ All URLs are valid roadmap.sh links

## Output Location

By default, the output is saved to:
```
data/linkedin_jobs_processed.json
```

## Sample Output Statistics

When processing real data, you'll see:
```
============================================================
PROCESSING SUMMARY
============================================================
Total jobs processed: 1000
Total skills extracted: 8500
Average skills per job: 8.5

Output file: data/linkedin_jobs_processed.json
============================================================
```

## Troubleshooting

### No data found
If you see "No database or CSV file found":
1. Download the Kaggle dataset
2. Extract the files to the appropriate location
3. Use `--database` or `--csv` flags to specify the path

### Low skill extraction
If jobs have fewer than 3 skills:
- The job description may be too short or vague
- Try processing more jobs to get better results
- The script will skip jobs with < 3 skills

### Missing roadmap resources
Some skills may only have generic roadmap.sh links if they don't match a specific roadmap category. This is expected for niche or emerging technologies.

## Integration with Skill Delta

The output JSON is designed to integrate seamlessly with the Skill Delta platform:
- Skills are normalized and searchable
- Each skill includes keywords for matching
- Resources link to learning paths
- Structure matches the roadmap dataset format

## Next Steps

1. Download the Kaggle dataset
2. Run the processing script
3. Use the output JSON for skill matching and analysis
4. Integrate with your skill-matching engine

