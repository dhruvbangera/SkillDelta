/**
 * Extract skills and resource links from developer-roadmap repository
 * This script parses the roadmap data structure to extract:
 * - Skills for each role
 * - Resource links for each skill
 */

const fs = require('fs');
const path = require('path');

const ROADMAP_DIR = path.join(__dirname, '..', 'developer-roadmap', 'src', 'data', 'roadmaps');

/**
 * Extract resource links from markdown content
 * Resources are in format: - [@type@Title](url)
 */
function extractResources(content) {
  const resourceRegex = /- \[@(\w+)@([^\]]+)\]\(([^)]+)\)/g;
  const resources = [];
  let match;

  while ((match = resourceRegex.exec(content)) !== null) {
    resources.push({
      type: match[1], // roadmap, course, official, article, feed, etc.
      title: match[2],
      url: match[3]
    });
  }

  return resources;
}

/**
 * Parse a skill content markdown file
 */
function parseSkillFile(filePath) {
  try {
    const content = fs.readFileSync(filePath, 'utf-8');
    const lines = content.split('\n');
    
    // Extract title (first line after #)
    const titleMatch = content.match(/^# (.+)$/m);
    const title = titleMatch ? titleMatch[1].trim() : path.basename(filePath, '.md');
    
    // Extract description (text before "Visit the following resources")
    const descriptionMatch = content.match(/^# .+\n\n(.+?)\n\nVisit the following resources:/s);
    const description = descriptionMatch ? descriptionMatch[1].trim() : '';
    
    // Extract resources
    const resources = extractResources(content);
    
    return {
      title,
      description,
      resources
    };
  } catch (error) {
    console.error(`Error parsing ${filePath}:`, error.message);
    return null;
  }
}

/**
 * Get all skills for a roadmap
 */
function getRoadmapSkills(roadmapName) {
  const roadmapPath = path.join(ROADMAP_DIR, roadmapName);
  const contentPath = path.join(roadmapPath, 'content');
  
  if (!fs.existsSync(contentPath)) {
    console.warn(`Content directory not found for ${roadmapName}`);
    return [];
  }

  const skillFiles = fs.readdirSync(contentPath)
    .filter(file => file.endsWith('.md'))
    .map(file => path.join(contentPath, file));

  const skills = skillFiles
    .map(parseSkillFile)
    .filter(skill => skill !== null);

  return skills;
}

/**
 * Get role-to-roadmap mapping
 */
function getRoleRoadmapMapping() {
  // Map common roles to roadmap names
  return {
    'Frontend Developer': 'frontend',
    'Backend Developer': 'backend',
    'Full Stack Developer': 'full-stack',
    'Data Analyst': 'data-analyst',
    'Software Engineer': 'backend', // or full-stack
    'UX/UI Designer': 'ux-design',
    'Cloud Associate': 'aws', // or cloudflare
    'React Developer': 'react',
    'Node.js Developer': 'nodejs',
    'Python Developer': 'python',
    'DevOps Engineer': 'devops',
    'Data Engineer': 'data-engineer',
    'Machine Learning Engineer': 'machine-learning',
    'AI Engineer': 'ai-engineer'
  };
}

/**
 * Extract all roadmap data
 */
function extractAllRoadmapData() {
  if (!fs.existsSync(ROADMAP_DIR)) {
    console.error(`Roadmap directory not found: ${ROADMAP_DIR}`);
    console.error('Make sure developer-roadmap repository is cloned in the root directory');
    return null;
  }

  const roadmaps = fs.readdirSync(ROADMAP_DIR, { withFileTypes: true })
    .filter(dirent => dirent.isDirectory())
    .map(dirent => dirent.name);

  const roadmapData = {};
  const roleMapping = getRoleRoadmapMapping();

  // Extract data for each roadmap
  for (const roadmap of roadmaps) {
    const skills = getRoadmapSkills(roadmap);
    if (skills.length > 0) {
      roadmapData[roadmap] = {
        skills,
        skillCount: skills.length
      };
    }
  }

  // Create role-based mapping
  const roleData = {};
  for (const [role, roadmap] of Object.entries(roleMapping)) {
    if (roadmapData[roadmap]) {
      roleData[role] = {
        roadmap,
        skills: roadmapData[roadmap].skills,
        skillCount: roadmapData[roadmap].skillCount
      };
    }
  }

  return {
    roadmaps: roadmapData,
    roles: roleData,
    roleMapping
  };
}

/**
 * Get skills for a specific role
 */
function getSkillsForRole(roleName) {
  const roleMapping = getRoleRoadmapMapping();
  const roadmapName = roleMapping[roleName];
  
  if (!roadmapName) {
    console.warn(`No roadmap mapping found for role: ${roleName}`);
    return [];
  }

  return getRoadmapSkills(roadmapName);
}

/**
 * Find a skill by name across all roadmaps
 */
function findSkillByName(skillName) {
  const roadmaps = fs.readdirSync(ROADMAP_DIR, { withFileTypes: true })
    .filter(dirent => dirent.isDirectory())
    .map(dirent => dirent.name);

  for (const roadmap of roadmaps) {
    const skills = getRoadmapSkills(roadmap);
    const skill = skills.find(s => 
      s.title.toLowerCase().includes(skillName.toLowerCase()) ||
      skillName.toLowerCase().includes(s.title.toLowerCase())
    );
    
    if (skill) {
      return {
        ...skill,
        roadmap
      };
    }
  }

  return null;
}

// CLI usage
if (require.main === module) {
  const args = process.argv.slice(2);
  
  if (args[0] === '--role' && args[1]) {
    // Get skills for a specific role
    const skills = getSkillsForRole(args[1]);
    console.log(JSON.stringify(skills, null, 2));
  } else if (args[0] === '--skill' && args[1]) {
    // Find a specific skill
    const skill = findSkillByName(args[1]);
    console.log(JSON.stringify(skill, null, 2));
  } else if (args[0] === '--all') {
    // Extract all data
    const data = extractAllRoadmapData();
    console.log(JSON.stringify(data, null, 2));
  } else {
    console.log(`
Usage:
  node extract-roadmap-data.js --role "Frontend Developer"  # Get skills for a role
  node extract-roadmap-data.js --skill "React"              # Find a specific skill
  node extract-roadmap-data.js --all                        # Extract all roadmap data
    `);
  }
}

module.exports = {
  extractAllRoadmapData,
  getSkillsForRole,
  findSkillByName,
  getRoadmapSkills
};

