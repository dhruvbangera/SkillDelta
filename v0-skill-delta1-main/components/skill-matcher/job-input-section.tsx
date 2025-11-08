"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card } from "@/components/ui/card"
import { Loader2, Briefcase, ArrowLeft } from "lucide-react"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

interface JobInputProps {
  onJobSubmit: (jobUrl: string) => void
  onBack?: () => void
  isLoading?: boolean
  skillsAnalyzed?: boolean
}

const sampleJobs = [
  {
    id: "1",
    title: "Senior Full Stack Developer",
    company: "Tech Corp",
    url: "https://example.com/job/senior-fullstack-developer",
  },
  {
    id: "2",
    title: "Frontend Engineer (React/Next.js)",
    company: "Startup Inc",
    url: "https://example.com/job/frontend-engineer-react",
  },
  {
    id: "3",
    title: "Backend Developer (Node.js)",
    company: "Enterprise Solutions",
    url: "https://example.com/job/backend-nodejs-developer",
  },
  {
    id: "4",
    title: "DevOps Engineer",
    company: "Cloud Systems",
    url: "https://example.com/job/devops-engineer",
  },
  {
    id: "5",
    title: "Mobile Developer (React Native)",
    company: "Mobile Apps Co",
    url: "https://example.com/job/mobile-react-native",
  },
]

export function JobInputSection({ onJobSubmit, onBack, isLoading = false, skillsAnalyzed = false }: JobInputProps) {
  const [jobUrl, setJobUrl] = useState("")
  const [inputMode, setInputMode] = useState<"dropdown" | "custom">("dropdown")
  const [selectedJob, setSelectedJob] = useState<string>("")
  const [error, setError] = useState("")

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setError("")

    if (inputMode === "dropdown") {
      if (!selectedJob) {
        setError("Please select a job from the list")
        return
      }
      onJobSubmit(selectedJob)
    } else {
      if (!jobUrl.trim()) {
        setError("Please enter a job listing URL")
        return
      }

      try {
        new URL(jobUrl)
        onJobSubmit(jobUrl)
      } catch {
        setError("Please enter a valid URL")
      }
    }
  }

  return (
    <div className="w-full space-y-6">
      <div className="text-center space-y-2">
        <h2 className="text-3xl md:text-4xl font-bold text-foreground">What job do you want to get?</h2>
        <p className="text-muted-foreground text-lg">Choose from popular jobs or paste your own job link</p>
      </div>

      <Card className="p-6 md:p-8 border-2 border-border">
        {onBack && (
          <Button
            type="button"
            variant="ghost"
            onClick={onBack}
            disabled={isLoading}
            className="mb-4 text-cyan-600 hover:text-cyan-700 hover:bg-cyan-50"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Skills
          </Button>
        )}

        <div className="flex gap-2 mb-6">
          <Button
            type="button"
            variant={inputMode === "dropdown" ? "default" : "outline"}
            onClick={() => setInputMode("dropdown")}
            className={
              inputMode === "dropdown"
                ? "bg-cyan-600 hover:bg-cyan-700 text-white"
                : "border-border text-foreground hover:bg-cyan-50"
            }
          >
            <Briefcase className="h-4 w-4 mr-2" />
            Choose Job
          </Button>
          <Button
            type="button"
            variant={inputMode === "custom" ? "default" : "outline"}
            onClick={() => setInputMode("custom")}
            className={
              inputMode === "custom"
                ? "bg-cyan-600 hover:bg-cyan-700 text-white"
                : "border-border text-foreground hover:bg-cyan-50"
            }
          >
            Paste Job Link
          </Button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {inputMode === "dropdown" ? (
            <div className="space-y-2">
              <label className="text-sm font-semibold text-foreground">Select a Job Role</label>
              <Select value={selectedJob} onValueChange={setSelectedJob} disabled={isLoading}>
                <SelectTrigger className="h-12 text-base">
                  <SelectValue placeholder="Choose a job role..." />
                </SelectTrigger>
                <SelectContent>
                  {sampleJobs.map((job) => (
                    <SelectItem key={job.id} value={job.url}>
                      <div className="flex flex-col items-start">
                        <span className="font-medium">{job.title}</span>
                        <span className="text-xs text-muted-foreground">{job.company}</span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          ) : (
            <div className="space-y-2">
              <label className="text-sm font-semibold text-foreground">Job Listing URL</label>
              <Input
                type="url"
                placeholder="https://example.com/job/senior-developer"
                value={jobUrl}
                onChange={(e) => setJobUrl(e.target.value)}
                disabled={isLoading}
                className="h-12 text-base"
              />
            </div>
          )}

          {error && <p className="text-sm text-red-600">{error}</p>}

          <Button
            type="submit"
            disabled={isLoading}
            className="w-full h-11 text-base bg-cyan-600 hover:bg-cyan-700 text-white font-semibold"
          >
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Analyzing job listing...
              </>
            ) : (
              "Analyze Job Match"
            )}
          </Button>
        </form>
      </Card>
    </div>
  )
}
