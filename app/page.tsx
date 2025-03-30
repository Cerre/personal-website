import Image from "next/image"
import Link from "next/link"
import { ProjectCard } from "@/components/project-card"

// Sample project data - you would replace this with your actual projects
const projects = [
  {
    id: "finger-counting-dart",
    title: "AI Finger Counting & KillerDart Backend",
    summary: "Developed a finger counting system using MediaPipe and XGBoost, alongside a backend server for the KillerDart application.",
    tags: ["MediaPipe", "XGBoost", "Python", "Backend", "Computer Vision"],
  },
  {
    id: "rag-sport-commentators",
    title: "RAG Search for Sport Commentators",
    summary: "Built a Retrieval-Augmented Generation (RAG) system to search and retrieve information about sport commentators.",
    tags: ["RAG", "LLM", "NLP", "Search", "AI"],
  },
  {
    id: "ai-agent-website-builder",
    title: "AI Agent Personal Website Builder",
    summary: "Leveraged AI agents to automate the process of building and deploying this personal website.",
    tags: ["AI Agents", "Automation", "Web Development", "Next.js", "Vercel"],
  },
]

export default function Home() {
  return (
    <main className="min-h-screen bg-background text-foreground">
      {/* Hero section with image and summary */}
      <section className="flex flex-col items-center justify-center py-20 px-4 md:px-6 lg:px-8">
        <div className="relative h-48 w-48 mb-8 rounded-full overflow-hidden border-4 border-primary">
          <Image
            src="/placeholder.svg?height=200&width=200"
            alt="Profile picture"
            fill
            className="object-cover"
            priority
          />
        </div>

        <h1 className="text-4xl md:text-5xl font-bold text-center mb-4">
          <span className="text-primary">Hello,</span> I'm Your Name
        </h1>

        <p className="text-xl text-center max-w-2xl mb-8 text-muted-foreground">
          I'm a passionate developer specializing in creating beautiful, functional, and user-friendly web applications.
          With expertise in modern technologies, I bring ideas to life through clean code and thoughtful design.
        </p>

        <div className="flex gap-4">
          <Link
            href="#projects"
            className="bg-primary hover:bg-primary/90 text-primary-foreground px-6 py-3 rounded-md font-medium transition-colors"
          >
            View Projects
          </Link>
          <Link
            href="/contact"
            className="bg-background hover:bg-accent text-foreground border border-border px-6 py-3 rounded-md font-medium transition-colors"
          >
            Contact Me
          </Link>
        </div>
      </section>

      {/* Projects section */}
      <section id="projects" className="py-20 px-4 md:px-6 lg:px-8 bg-accent/5">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl md:text-4xl font-bold mb-12 text-center">
            My <span className="text-primary">Projects</span>
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {projects.map((project) => (
              <ProjectCard key={project.id} project={project} />
            ))}
          </div>
        </div>
      </section>
    </main>
  )
}

