import Link from "next/link"
import Image from "next/image"
import { ArrowLeft } from "lucide-react"

// Define the structure for project details
interface ProjectDetails {
  id: string;
  title: string;
  summary: string;
  tags: string[];
  imageUrl: string;
  idea: string;
  learned: string;
  tools: string[];
  thoughts: string;
  link: string;
  github: string;
}

// Project data using the defined interface
const projects: { [key: string]: ProjectDetails } = {
  "finger-counting-dart": {
    id: "finger-counting-dart",
    title: "AI Finger Counting & KillerDart Backend",
    summary: "Developed a finger counting system using MediaPipe and XGBoost, alongside a backend server for the KillerDart application.",
    tags: ["MediaPipe", "XGBoost", "Python", "Backend", "Computer Vision"],
    imageUrl: "/placeholder.svg?height=400&width=800", // TODO: Replace with actual image
    idea: "Placeholder: Describe the core idea and motivation behind the project.",
    learned: "Placeholder: What were the key takeaways and skills gained?",
    tools: ["MediaPipe", "XGBoost", "Python", "OpenCV", "Flask/FastAPI"], // TODO: Update with actual tools
    thoughts: "Placeholder: Final reflections, challenges overcome, or future improvements.",
    link: "#", // TODO: Add link if available
    github: "#", // TODO: Add link if available
  },
  "rag-sport-commentators": {
    id: "rag-sport-commentators",
    title: "RAG Search for Sport Commentators",
    summary: "Built a Retrieval-Augmented Generation (RAG) system to search and retrieve information about sport commentators.",
    tags: ["RAG", "LLM", "NLP", "Search", "AI"],
    imageUrl: "/placeholder.svg?height=400&width=800", // TODO: Replace with actual image
    idea: "Placeholder: Describe the core idea and motivation behind the project.",
    learned: "Placeholder: What were the key takeaways and skills gained?",
    tools: ["Python", "LangChain/LlamaIndex", "Vector DB", "LLM APIs"], // TODO: Update with actual tools
    thoughts: "Placeholder: Final reflections, challenges overcome, or future improvements.",
    link: "#", // TODO: Add link if available
    github: "#", // TODO: Add link if available
  },
  "ai-agent-website-builder": {
    id: "ai-agent-website-builder",
    title: "AI Agent Personal Website Builder",
    summary: "Leveraged AI agents to automate the process of building and deploying this personal website.",
    tags: ["AI Agents", "Automation", "Web Development", "Next.js", "Vercel"],
    imageUrl: "/placeholder.svg?height=400&width=800", // TODO: Replace with actual image
    idea: "Placeholder: Describe the core idea and motivation behind the project.",
    learned: "Placeholder: What were the key takeaways and skills gained?",
    tools: ["AI Assistants", "Next.js", "React", "Tailwind CSS", "Vercel", "Git"], // TODO: Update with actual tools
    thoughts: "Placeholder: Final reflections, challenges overcome, or future improvements.",
    link: "#", // TODO: Add link if available
    github: "https://github.com/Cerre/personal-website", // Link to this repo
  },
}

export default function ProjectPage({ params }: { params: { slug: string } }) {
  // Explicitly type the accessed project or undefined
  const project: ProjectDetails | undefined = projects[params.slug]

  if (!project) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <h1 className="text-3xl font-bold mb-4">Project not found</h1>
          <Link href="/" className="text-primary hover:text-primary/80 flex items-center justify-center gap-2">
            <ArrowLeft size={16} />
            Back to home
          </Link>
        </div>
      </div>
    )
  }

  return (
    <main className="min-h-screen bg-background text-foreground">
      <div className="max-w-4xl mx-auto px-4 py-12 md:py-20">
        <Link href="/" className="inline-flex items-center text-primary hover:text-primary/80 mb-8 transition-colors">
          <ArrowLeft size={16} className="mr-2" />
          Back to home
        </Link>

        <div className="mb-8">
          <h1 className="text-3xl md:text-4xl font-bold mb-4">{project.title}</h1>
          <p className="text-xl text-muted-foreground mb-6">{project.summary}</p>

          <div className="flex flex-wrap gap-2 mb-8">
            {project.tags.map((tag: string) => (
              <span key={tag} className="text-sm bg-primary/10 text-primary px-3 py-1 rounded-full">
                {tag}
              </span>
            ))}
          </div>
        </div>

        <div className="relative w-full h-64 md:h-80 mb-8 rounded-lg overflow-hidden">
          <Image src={project.imageUrl || "/placeholder.svg?height=400&width=800"} alt={project.title} fill className="object-cover" />
        </div>

        <div className="prose prose-invert prose-green max-w-none mb-8 space-y-6">
          <section>
            <h2 className="text-2xl font-semibold mb-3">Idea</h2>
            <p>{project.idea}</p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mb-3">What I Learned</h2>
            <p>{project.learned}</p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mb-3">Tools Used</h2>
            <ul className="list-disc pl-5">
              {project.tools.map((tool: string) => (
                <li key={tool}>{tool}</li>
              ))}
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mb-3">Final Thoughts</h2>
            <p>{project.thoughts}</p>
          </section>
        </div>

        <div className="flex flex-col sm:flex-row gap-4 mt-12">
          {project.link && (
            <a
              href={project.link}
              target="_blank"
              rel="noopener noreferrer"
              className="bg-primary hover:bg-primary/90 text-primary-foreground px-6 py-3 rounded-md font-medium transition-colors text-center"
            >
              View Live Project
            </a>
          )}

          {project.github && (
            <a
              href={project.github}
              target="_blank"
              rel="noopener noreferrer"
              className="bg-background hover:bg-accent text-foreground border border-border px-6 py-3 rounded-md font-medium transition-colors text-center"
            >
              View Source Code
            </a>
          )}
        </div>
      </div>
    </main>
  )
}

