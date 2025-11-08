"use client"

import { useState } from "react"
import { Header } from "@/components/header"
import { JobInputSection } from "@/components/skill-matcher/job-input-section"
import { ResumeInputSection } from "@/components/skill-matcher/resume-input-section"
import { SkillsComparison } from "@/components/skill-matcher/skills-comparison"
import { LearningPath } from "@/components/skill-matcher/learning-path"
import { FooterSection } from "@/components/footer-section"

// Mock data for demonstration - replace with actual API calls
const mockMatchResult = {
  matchPercentage: 65,
  currentSkills: [
    { name: "JavaScript", level: "Advanced" },
    { name: "React", level: "Advanced" },
    { name: "TypeScript", level: "Intermediate" },
    { name: "Node.js", level: "Intermediate" },
    { name: "CSS/Tailwind", level: "Advanced" },
  ],
  missingSkills: [
    { name: "NextAuth.js", level: "Required" },
    { name: "PostgreSQL", level: "Required" },
    { name: "Docker", level: "Nice to have" },
    { name: "GraphQL", level: "Required" },
  ],
}

const mockLearningPath = [
  {
    id: "1",
    title: "Master NextAuth.js",
    description: "Learn authentication and authorization with NextAuth.js in Next.js applications",
    duration: "4 weeks",
    difficulty: "intermediate" as const,
    resources: [
      "NextAuth.js Official Documentation",
      "freeCodeCamp NextAuth.js Tutorial",
      "Build a Full Auth System Course",
    ],
  },
  {
    id: "2",
    title: "PostgreSQL Fundamentals",
    description: "Database design, SQL queries, and optimization for PostgreSQL",
    duration: "3 weeks",
    difficulty: "intermediate" as const,
    resources: ["PostgreSQL Documentation", "SQL for Data Analysis", "Database Design Principles"],
  },
  {
    id: "3",
    title: "Docker & Containerization",
    description: "Containerize your applications and learn Docker best practices",
    duration: "2 weeks",
    difficulty: "beginner" as const,
    resources: ["Docker Official Tutorial", "Containerization Essentials", "DevOps with Docker"],
  },
  {
    id: "4",
    title: "GraphQL Mastery",
    description: "Build efficient APIs with GraphQL and integrate with existing systems",
    duration: "5 weeks",
    difficulty: "advanced" as const,
    resources: ["How to GraphQL Tutorial", "Apollo GraphQL Documentation", "Advanced GraphQL Patterns"],
  },
]

export default function SkillMatcherPage() {
  const [currentStep, setCurrentStep] = useState<"skills" | "job" | "results">("skills")
  const [resumeUploaded, setResumeUploaded] = useState(false)
  const [jobUrl, setJobUrl] = useState<string>("")
  const [skillsAnalyzing, setSkillsAnalyzing] = useState(false)
  const [jobAnalyzing, setJobAnalyzing] = useState(false)
  const [userSkills, setUserSkills] = useState<string[]>([])

  const handleResumeSubmit = async (files: File[], manualSkills?: string[]) => {
    setSkillsAnalyzing(true)
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 2500))
    setResumeUploaded(true)
    if (manualSkills) {
      setUserSkills(manualSkills)
    }
    setSkillsAnalyzing(false)
    setCurrentStep("job")
  }

  const handleJobSubmit = async (url: string) => {
    setJobAnalyzing(true)
    setJobUrl(url)
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 2000))
    setJobAnalyzing(false)
    setCurrentStep("results")
  }

  const handleChangeResume = () => {
    setCurrentStep("skills")
    setResumeUploaded(false)
    setUserSkills([])
  }

  const handleChangeJob = () => {
    setCurrentStep("job")
    setJobUrl("")
  }

  const handleStartOver = () => {
    setCurrentStep("skills")
    setResumeUploaded(false)
    setUserSkills([])
    setJobUrl("")
  }

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="max-w-4xl mx-auto px-6 py-12">
        <div className="relative">
          {currentStep === "skills" && (
            <div className="animate-in fade-in duration-500">
              <ResumeInputSection onResumeSubmit={handleResumeSubmit} isLoading={skillsAnalyzing} />
            </div>
          )}

          {currentStep === "job" && (
            <div className="animate-in fade-in duration-500">
              <JobInputSection
                onJobSubmit={handleJobSubmit}
                onBack={handleChangeResume}
                isLoading={jobAnalyzing}
                skillsAnalyzed={true}
              />
            </div>
          )}

          {currentStep === "results" && (
            <div className="animate-in fade-in duration-500 space-y-8">
              <SkillsComparison
                matchPercentage={mockMatchResult.matchPercentage}
                currentSkills={mockMatchResult.currentSkills}
                missingSkills={mockMatchResult.missingSkills}
                skillsAnalyzed={true}
              />

              <LearningPath steps={mockLearningPath} skillsAnalyzed={true} />

              <div className="flex flex-col sm:flex-row gap-3 justify-center pt-8 border-t border-border">
                <button
                  onClick={handleChangeJob}
                  className="px-6 py-2 border-2 border-cyan-600 text-cyan-600 rounded-lg font-semibold hover:bg-cyan-50 transition-colors"
                >
                  Try Different Job
                </button>
                <button
                  onClick={handleStartOver}
                  className="px-6 py-2 bg-gray-100 text-gray-700 rounded-lg font-semibold hover:bg-gray-200 transition-colors"
                >
                  Start Over
                </button>
              </div>
            </div>
          )}
        </div>
      </main>
      <FooterSection />
    </div>
  )
}
