import { HeroSection } from "@/components/hero-section"
import { AnimatedSection } from "@/components/animated-section"
import { SkillMatcherPreview } from "@/components/skill-matcher/skill-matcher-preview"

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background relative overflow-hidden pb-0">
      <div className="relative z-10">
        <main className="max-w-[1320px] mx-auto relative">
          <HeroSection />
          {/* Dashboard Preview Wrapper */}
        </main>
        <AnimatedSection className="relative z-10 max-w-[1320px] mx-auto px-6 mt-8 md:mt-16" delay={0.1}>
          <SkillMatcherPreview />
        </AnimatedSection>
      </div>
    </div>
  )
}
