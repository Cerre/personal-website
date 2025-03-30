import Link from "next/link"

interface Project {
  id: string
  title: string
  summary: string
  tags: string[]
}

interface ProjectCardProps {
  project: Project
}

export function ProjectCard({ project }: ProjectCardProps) {
  return (
    <Link href={`/projects/${project.id}`} className="block">
      <div className="h-full bg-card hover:bg-card/80 border border-border rounded-lg p-6 transition-colors hover:border-primary/50 hover:shadow-md hover:shadow-primary/5">
        <h3 className="text-xl font-semibold mb-2 text-card-foreground">{project.title}</h3>
        <p className="text-muted-foreground mb-4">{project.summary}</p>
        <div className="flex flex-wrap gap-2 mt-auto">
          {project.tags.map((tag) => (
            <span key={tag} className="text-xs bg-primary/10 text-primary px-2 py-1 rounded-full">
              {tag}
            </span>
          ))}
        </div>
      </div>
    </Link>
  )
}

