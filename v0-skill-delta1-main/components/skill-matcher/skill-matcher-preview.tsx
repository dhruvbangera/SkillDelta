"use client"

import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { CheckCircle2, Circle, Zap } from "lucide-react"
import Link from "next/link"

export function SkillMatcherPreview() {
  const sampleSkills = {
    have: ["JavaScript", "React", "TypeScript"],
    need: ["PostgreSQL", "Docker", "GraphQL"],
  }

  return (
    <div className="space-y-8">
      <div className="text-center space-y-2">
        <h2 className="text-3xl md:text-4xl font-bold text-foreground">AI-Powered Skill Matching</h2>
        <p className="text-muted-foreground text-lg">Get personalized learning paths to land your dream job</p>
      </div>

      <div className="grid md:grid-cols-3 gap-4">
        {/* Step 1 */}
        <Card className="p-6 border-2 border-border hover:border-cyan-300 transition-colors">
          <div className="space-y-4">
            <div className="w-10 h-10 rounded-full bg-cyan-600 text-white flex items-center justify-center font-bold">
              1
            </div>
            <h3 className="text-lg font-bold text-foreground">Upload Resume</h3>
            <p className="text-sm text-muted-foreground">Share your resume or manually enter your skills</p>
          </div>
        </Card>

        {/* Step 2 */}
        <Card className="p-6 border-2 border-border hover:border-cyan-300 transition-colors">
          <div className="space-y-4">
            <div className="w-10 h-10 rounded-full bg-cyan-600 text-white flex items-center justify-center font-bold">
              2
            </div>
            <h3 className="text-lg font-bold text-foreground">Select Job</h3>
            <p className="text-sm text-muted-foreground">Choose from job options or paste a specific job link</p>
          </div>
        </Card>

        {/* Step 3 */}
        <Card className="p-6 border-2 border-border hover:border-cyan-300 transition-colors">
          <div className="space-y-4">
            <div className="w-10 h-10 rounded-full bg-cyan-600 text-white flex items-center justify-center font-bold">
              3
            </div>
            <h3 className="text-lg font-bold text-foreground">Get Path</h3>
            <p className="text-sm text-muted-foreground">Receive a personalized learning plan to reach your goal</p>
          </div>
        </Card>
      </div>

      {/* Preview Card */}
      <Card className="p-8 bg-gradient-to-br from-cyan-50 to-blue-50 border-2 border-cyan-200">
        <div className="grid md:grid-cols-2 gap-8">
          {/* Left Side - Skills Comparison */}
          <div className="space-y-4">
            <h3 className="font-bold text-foreground flex items-center gap-2">
              <Zap className="h-5 w-5 text-cyan-600" />
              Smart Matching
            </h3>
            <div className="space-y-3">
              <div>
                <p className="text-sm font-semibold text-foreground mb-2">Your Skills</p>
                <div className="flex flex-wrap gap-2">
                  {sampleSkills.have.map((skill) => (
                    <Badge key={skill} className="bg-green-100 text-green-800 flex items-center gap-1">
                      <CheckCircle2 className="h-3 w-3" />
                      {skill}
                    </Badge>
                  ))}
                </div>
              </div>
              <div>
                <p className="text-sm font-semibold text-foreground mb-2">Skills to Learn</p>
                <div className="flex flex-wrap gap-2">
                  {sampleSkills.need.map((skill) => (
                    <Badge key={skill} className="bg-cyan-100 text-cyan-800 flex items-center gap-1">
                      <Circle className="h-3 w-3" />
                      {skill}
                    </Badge>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Right Side - Personalized Path */}
          <div className="space-y-4">
            <h3 className="font-bold text-foreground">Your Learning Path</h3>
            <div className="space-y-2 text-sm">
              <p className="text-muted-foreground">We create a personalized learning plan with:</p>
              <ul className="space-y-1 text-foreground">
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-cyan-600 flex-shrink-0" />
                  Curated learning resources
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-cyan-600 flex-shrink-0" />
                  Estimated time to proficiency
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-cyan-600 flex-shrink-0" />
                  Difficulty progression
                </li>
              </ul>
            </div>
          </div>
        </div>

        {/* CTA Button */}
        <div className="mt-6 text-center">
          <Link href="/skill-matcher">
            <Button className="bg-cyan-600 hover:bg-cyan-700 text-white font-semibold px-8">
              Start Matching Skills
            </Button>
          </Link>
        </div>
      </Card>
    </div>
  )
}
