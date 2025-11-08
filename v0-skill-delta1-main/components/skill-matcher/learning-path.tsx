"use client"

import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { BookOpen, Clock, ArrowRight } from "lucide-react"

interface PathStep {
  id: string
  title: string
  description: string
  duration: string
  resources: string[]
  difficulty: "beginner" | "intermediate" | "advanced"
}

interface LearningPathProps {
  steps: PathStep[]
  skillsAnalyzed?: boolean
}

export function LearningPath({ steps, skillsAnalyzed = false }: LearningPathProps) {
  if (!skillsAnalyzed) {
    return null
  }

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case "beginner":
        return "bg-green-100 text-green-800"
      case "intermediate":
        return "bg-yellow-100 text-yellow-800"
      case "advanced":
        return "bg-red-100 text-red-800"
      default:
        return "bg-gray-100 text-gray-800"
    }
  }

  return (
    <div className="w-full space-y-6 pt-12 border-t border-border">
      <div className="text-center space-y-2">
        <h2 className="text-3xl md:text-4xl font-bold text-foreground">Your Personalized Learning Path</h2>
        <p className="text-muted-foreground text-lg">
          Here's a step-by-step guide to gain the remaining skills you need
        </p>
      </div>

      <div className="space-y-4">
        {steps.map((step, index) => (
          <Card key={step.id} className="p-6 border-2 border-border hover:border-cyan-300 transition-colors">
            <div className="flex gap-6">
              {/* Step Number */}
              <div className="flex-shrink-0">
                <div className="w-12 h-12 rounded-full bg-cyan-600 text-white flex items-center justify-center font-bold text-lg">
                  {index + 1}
                </div>
              </div>

              {/* Step Content */}
              <div className="flex-1 min-w-0">
                <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
                  <div className="flex-1">
                    <h3 className="text-lg font-bold text-foreground mb-2">{step.title}</h3>
                    <p className="text-muted-foreground text-sm mb-4">{step.description}</p>

                    {/* Metadata */}
                    <div className="flex flex-wrap items-center gap-3 mb-4">
                      <div className="flex items-center gap-1 text-sm text-muted-foreground">
                        <Clock className="h-4 w-4" />
                        {step.duration}
                      </div>
                      <Badge className={getDifficultyColor(step.difficulty)}>
                        {step.difficulty.charAt(0).toUpperCase() + step.difficulty.slice(1)}
                      </Badge>
                    </div>

                    {/* Resources */}
                    {step.resources.length > 0 && (
                      <div className="space-y-2">
                        <p className="text-xs font-semibold text-foreground flex items-center gap-1">
                          <BookOpen className="h-4 w-4" />
                          Recommended Resources:
                        </p>
                        <ul className="space-y-1">
                          {step.resources.map((resource, idx) => (
                            <li key={idx} className="text-sm text-cyan-600 hover:text-cyan-700">
                              • {resource}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Arrow */}
              {index < steps.length - 1 && (
                <div className="hidden md:flex flex-col items-center justify-between h-full py-2">
                  <ArrowRight className="h-6 w-6 text-gray-300 rotate-90" />
                </div>
              )}
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}
