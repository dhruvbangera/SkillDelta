"use client"

import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { CheckCircle2, Circle } from "lucide-react"

interface Skill {
  name: string
  level?: string
}

interface SkillsComparisonProps {
  matchPercentage: number
  currentSkills: Skill[]
  missingSkills: Skill[]
  skillsAnalyzed?: boolean
}

export function SkillsComparison({
  matchPercentage,
  currentSkills,
  missingSkills,
  skillsAnalyzed = false,
}: SkillsComparisonProps) {
  if (!skillsAnalyzed) {
    return null
  }

  const totalSkills = currentSkills.length + missingSkills.length

  return (
    <div className="w-full space-y-6 pt-12 border-t border-border">
      {/* Match Percentage Card */}
      <Card className="p-8 md:p-12 bg-gradient-to-br from-cyan-50 to-blue-50 border-2 border-cyan-200">
        <div className="text-center space-y-4">
          <p className="text-muted-foreground text-lg">Based on your submissions, you currently possess</p>
          <div className="flex items-baseline justify-center gap-2">
            <span className="text-6xl md:text-7xl font-bold text-cyan-600">{matchPercentage}%</span>
            <span className="text-xl text-foreground font-semibold">of the required skills</span>
          </div>
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden mt-6">
            <div
              className="h-full bg-cyan-600 rounded-full transition-all duration-500"
              style={{ width: `${matchPercentage}%` }}
            />
          </div>
        </div>
      </Card>

      {/* Skills Breakdown */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Current Skills */}
        <Card className="p-6 border-2 border-border">
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-6 w-6 text-green-600" />
              <h3 className="text-xl font-bold text-foreground">Skills You Have</h3>
              <Badge variant="secondary" className="ml-auto">
                {currentSkills.length}
              </Badge>
            </div>
            <div className="space-y-2">
              {currentSkills.map((skill) => (
                <div key={skill.name} className="flex items-center gap-3 p-3 bg-green-50 rounded-lg text-sm">
                  <CheckCircle2 className="h-4 w-4 text-green-600 flex-shrink-0" />
                  <div className="flex-1">
                    <p className="font-medium text-foreground">{skill.name}</p>
                    {skill.level && <p className="text-xs text-muted-foreground">{skill.level}</p>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </Card>

        {/* Missing Skills */}
        <Card className="p-6 border-2 border-border">
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <Circle className="h-6 w-6 text-cyan-600" />
              <h3 className="text-xl font-bold text-foreground">Skills You Need</h3>
              <Badge variant="secondary" className="ml-auto">
                {missingSkills.length}
              </Badge>
            </div>
            <div className="space-y-2">
              {missingSkills.map((skill) => (
                <div key={skill.name} className="flex items-center gap-3 p-3 bg-cyan-50 rounded-lg text-sm">
                  <Circle className="h-4 w-4 text-cyan-600 flex-shrink-0" />
                  <div className="flex-1">
                    <p className="font-medium text-foreground">{skill.name}</p>
                    {skill.level && <p className="text-xs text-muted-foreground">{skill.level}</p>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </Card>
      </div>
    </div>
  )
}
