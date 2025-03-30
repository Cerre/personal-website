import Link from "next/link"
import Image from "next/image"
import { ArrowLeft } from "lucide-react"

// Sample project data - you would replace this with your actual projects
const projects = {
  "project-1": {
    id: "project-1",
    title: "Portfolio Website",
    summary: "A responsive portfolio website built with Next.js and Tailwind CSS.",
    description: `
      This portfolio website showcases my skills and projects in a clean, modern interface. 
      
      I built this website using Next.js for server-side rendering and routing, and Tailwind CSS for styling. The site features a responsive design that works well on all devices, from mobile phones to desktop computers.
      
      Key features include:
      - Dark mode with custom green theme
      - Responsive layout
      - Fast page transitions
      - SEO optimization
      - Contact form with validation
      
      The biggest challenge was creating a design that effectively communicates my personal brand while maintaining excellent performance metrics. I'm particularly proud of the animations and transitions that make the site feel polished and professional.
    `,
    tags: ["Next.js", "React", "Tailwind CSS"],
    link: "https://example.com",
    github: "https://github.com/yourusername/portfolio",
  },
  "project-2": {
    id: "project-2",
    title: "E-commerce Platform",
    summary: "A full-stack e-commerce solution with payment processing and inventory management.",
    description: `
      This e-commerce platform provides a complete solution for online stores, from product listings to checkout and order management.
      
      Built with TypeScript, Node.js, and MongoDB, this application offers a robust backend API that handles product management, user authentication, shopping cart functionality, and payment processing through Stripe.
      
      Key features include:
      - User authentication and profiles
      - Product catalog with categories and search
      - Shopping cart and wishlist
      - Secure checkout with Stripe
      - Order history and tracking
      - Admin dashboard for inventory management
      
      The most challenging aspect was implementing a secure and seamless payment process while ensuring the inventory updates correctly after each purchase. I learned a lot about transaction management and error handling in distributed systems.
    `,
    tags: ["TypeScript", "Node.js", "MongoDB"],
    link: "https://example-store.com",
    github: "https://github.com/yourusername/ecommerce",
  },
  "project-3": {
    id: "project-3",
    title: "Mobile Fitness App",
    summary: "A cross-platform mobile application for tracking workouts and nutrition.",
    description: `
      This fitness application helps users track their workouts, nutrition, and progress toward their health goals.
      
      Developed with React Native and Firebase, the app works on both iOS and Android devices. It features real-time data synchronization, offline support, and personalized workout recommendations.
      
      Key features include:
      - Workout tracking with custom routines
      - Nutrition logging and calorie counting
      - Progress charts and statistics
      - Social sharing and challenges
      - Personalized recommendations
      - Offline mode for workouts without internet
      
      The biggest technical challenge was implementing accurate calorie and nutrient calculations while maintaining a simple, intuitive user interface. I'm particularly proud of the custom animation system that makes tracking workouts more engaging.
    `,
    tags: ["React Native", "Firebase", "Redux"],
    link: "https://play.google.com/store/apps/details?id=com.example.fitnessapp",
    github: "https://github.com/yourusername/fitness-app",
  },
  "project-4": {
    id: "project-4",
    title: "AI Content Generator",
    summary: "An AI-powered tool that generates marketing copy and social media content.",
    description: `
      This AI content generator helps marketers and content creators produce high-quality marketing copy and social media posts quickly.
      
      Built with Python and TensorFlow, the application uses natural language processing to understand the user's intent and generate relevant, engaging content tailored to their brand voice.
      
      Key features include:
      - Marketing copy generation for various platforms
      - Social media post creation with hashtag suggestions
      - Brand voice customization
      - Content optimization for SEO
      - Batch generation for content calendars
      - Analytics on content performance
      
      The most significant challenge was fine-tuning the language model to produce content that feels authentic and aligns with different brand voices. This project taught me a lot about the practical applications of NLP and the importance of user feedback in refining AI systems.
    `,
    tags: ["Python", "TensorFlow", "NLP"],
    link: "https://ai-content-generator.example.com",
    github: "https://github.com/yourusername/ai-content-generator",
  },
}

export default function ProjectPage({ params }: { params: { slug: string } }) {
  const project = projects[params.slug]

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
            {project.tags.map((tag) => (
              <span key={tag} className="text-sm bg-primary/10 text-primary px-3 py-1 rounded-full">
                {tag}
              </span>
            ))}
          </div>
        </div>

        <div className="relative w-full h-64 md:h-80 mb-8 rounded-lg overflow-hidden">
          <Image src="/placeholder.svg?height=400&width=800" alt={project.title} fill className="object-cover" />
        </div>

        <div className="prose prose-invert prose-green max-w-none mb-8">
          {project.description.split("\n\n").map((paragraph, index) => (
            <p key={index}>{paragraph}</p>
          ))}
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

