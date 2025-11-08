"use client"

import type React from "react"

import { useState, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Loader2, Upload, FileText, X, Plus } from "lucide-react"

interface ResumeInputProps {
  onResumeSubmit: (files: File[], manualSkills?: string[]) => void
  isLoading?: boolean
}

export function ResumeInputSection({ onResumeSubmit, isLoading = false }: ResumeInputProps) {
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([])
  const [linkedinUrl, setLinkedinUrl] = useState("")
  const [manualSkills, setManualSkills] = useState<string[]>([])
  const [currentSkill, setCurrentSkill] = useState("")
  const [inputMethod, setInputMethod] = useState<"upload" | "manual">("upload")
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [error, setError] = useState("")

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    setUploadedFiles(files)
    setError("")

    // Auto-populate manual skills from resume
    if (files.length > 0) {
      // Simulate AI extraction - in real app, this would call an API
      const extractedSkills = ["JavaScript", "React", "TypeScript", "Node.js", "CSS", "HTML", "Git", "REST APIs"]
      setManualSkills(extractedSkills)
    }
  }

  const handleAddSkill = () => {
    if (currentSkill.trim() && !manualSkills.includes(currentSkill.trim())) {
      setManualSkills([...manualSkills, currentSkill.trim()])
      setCurrentSkill("")
      setError("")
    }
  }

  const handleRemoveSkill = (skillToRemove: string) => {
    setManualSkills(manualSkills.filter((skill) => skill !== skillToRemove))
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault()
      handleAddSkill()
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setError("")

    if (inputMethod === "upload" && uploadedFiles.length === 0 && !linkedinUrl.trim()) {
      setError("Please upload a resume or provide a LinkedIn URL")
      return
    }

    if (inputMethod === "manual" && manualSkills.length === 0) {
      setError("Please add at least one skill")
      return
    }

    onResumeSubmit(uploadedFiles, manualSkills.length > 0 ? manualSkills : undefined)
  }

  return (
    <div className="w-full space-y-6">
      <div className="text-center space-y-2">
        <h2 className="text-3xl md:text-4xl font-bold text-foreground">What skills do you currently have?</h2>
        <p className="text-muted-foreground text-lg">Upload your resume or manually enter your skills</p>
      </div>

      <Card className="p-6 md:p-8 border-2 border-border">
        <div className="flex gap-2 mb-6">
          <Button
            type="button"
            variant={inputMethod === "upload" ? "default" : "outline"}
            onClick={() => setInputMethod("upload")}
            className={
              inputMethod === "upload"
                ? "bg-cyan-600 hover:bg-cyan-700 text-white"
                : "border-border text-foreground hover:bg-cyan-50"
            }
          >
            Upload Resume
          </Button>
          <Button
            type="button"
            variant={inputMethod === "manual" ? "default" : "outline"}
            onClick={() => setInputMethod("manual")}
            className={
              inputMethod === "manual"
                ? "bg-cyan-600 hover:bg-cyan-700 text-white"
                : "border-border text-foreground hover:bg-cyan-50"
            }
          >
            Enter Skills Manually
          </Button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {inputMethod === "upload" ? (
            <>
              {/* File Upload Area */}
              <div className="space-y-3">
                <label className="text-sm font-semibold text-foreground">Upload Resume</label>
                <div
                  className="border-2 border-dashed border-cyan-300 rounded-lg p-8 text-center cursor-pointer hover:bg-cyan-50/50 transition-colors"
                  onClick={() => fileInputRef.current?.click()}
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    accept=".pdf,.doc,.docx,.txt"
                    onChange={handleFileChange}
                    disabled={isLoading}
                    className="hidden"
                  />
                  <Upload className="h-8 w-8 text-cyan-600 mx-auto mb-2" />
                  <p className="text-sm font-medium text-foreground">Click to upload or drag and drop</p>
                  <p className="text-xs text-muted-foreground mt-1">PDF, DOC, DOCX, or TXT (max 10MB)</p>
                </div>
              </div>

              {/* Uploaded Files Display */}
              {uploadedFiles.length > 0 && (
                <div className="space-y-2">
                  <p className="text-sm font-semibold text-foreground">Uploaded files:</p>
                  {uploadedFiles.map((file) => (
                    <div
                      key={file.name}
                      className="flex items-center gap-2 p-3 bg-cyan-50 rounded-lg text-sm text-foreground"
                    >
                      <FileText className="h-4 w-4 text-cyan-600" />
                      {file.name}
                    </div>
                  ))}
                </div>
              )}

              {/* LinkedIn URL Input */}
              <div className="space-y-3">
                <label className="text-sm font-semibold text-foreground">Or LinkedIn URL (optional)</label>
                <input
                  type="url"
                  placeholder="https://linkedin.com/in/yourprofile"
                  value={linkedinUrl}
                  onChange={(e) => setLinkedinUrl(e.target.value)}
                  disabled={isLoading}
                  className="w-full px-4 py-3 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500 text-base"
                />
              </div>
            </>
          ) : null}

          {(inputMethod === "manual" || manualSkills.length > 0) && (
            <>
              <div className="space-y-3">
                <label className="text-sm font-semibold text-foreground">
                  {inputMethod === "upload" ? "Review & Edit Extracted Skills" : "Add Your Skills"}
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    placeholder="e.g., JavaScript, React, Python..."
                    value={currentSkill}
                    onChange={(e) => setCurrentSkill(e.target.value)}
                    onKeyPress={handleKeyPress}
                    disabled={isLoading}
                    className="flex-1 px-4 py-3 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500 text-base"
                  />
                  <Button
                    type="button"
                    onClick={handleAddSkill}
                    disabled={isLoading || !currentSkill.trim()}
                    className="bg-cyan-600 hover:bg-cyan-700 text-white"
                  >
                    <Plus className="h-4 w-4" />
                  </Button>
                </div>
                <p className="text-xs text-muted-foreground">Press Enter or click + to add a skill</p>
              </div>

              {/* Display added skills */}
              {manualSkills.length > 0 && (
                <div className="space-y-2">
                  <p className="text-sm font-semibold text-foreground">Your Skills ({manualSkills.length}):</p>
                  <div className="flex flex-wrap gap-2">
                    {manualSkills.map((skill) => (
                      <Badge
                        key={skill}
                        className="bg-cyan-100 text-cyan-800 flex items-center gap-1 px-3 py-1 text-sm"
                      >
                        {skill}
                        <button
                          type="button"
                          onClick={() => handleRemoveSkill(skill)}
                          disabled={isLoading}
                          className="ml-1 hover:text-cyan-900"
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}

          {error && <p className="text-sm text-red-600">{error}</p>}

          <Button
            type="submit"
            disabled={
              isLoading ||
              (inputMethod === "upload" && uploadedFiles.length === 0 && !linkedinUrl.trim()) ||
              (inputMethod === "manual" && manualSkills.length === 0)
            }
            className="w-full h-11 text-base bg-cyan-600 hover:bg-cyan-700 text-white font-semibold"
          >
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Analyzing your skills...
              </>
            ) : (
              "Save My Skills"
            )}
          </Button>
        </form>
      </Card>
    </div>
  )
}
