# Personal Portfolio Website

A clean, responsive personal portfolio website to showcase your projects and social links.

## Features

- Responsive design that works on all devices
- Clean, modern UI
- Sections for about me, social links, and projects
- Easy to customize with your own content
- Smooth animations
- No complex frameworks or dependencies

## How to Customize

### Basic Information

1. Open `index.html` and replace:
   - "Your Name" with your actual name
   - The tagline with your profession/interests
   - The "About Me" text with your own introduction
   - Update social media links with your own profiles
   - Add your projects with descriptions and links

### Adding More Projects

To add more projects, simply copy one of the existing project card divs and customize it:

```html
<div class="project-card">
    <h3>Your Project Name</h3>
    <p>Description of your project.</p>
    <div class="project-links">
        <a href="#" target="_blank">View Project</a>
        <a href="#" target="_blank">Source Code</a>
    </div>
</div>
```

### Customizing Colors

To change the color scheme, modify the CSS variables in `css/style.css`:

```css
:root {
    --primary-color: #2563eb;
    --secondary-color: #3b82f6;
    /* Other color variables */
}
```

## Deployment Options

### 1. GitHub Pages (Free)

1. Create a GitHub repository
2. Push your website files to the repository
3. Go to repository Settings > Pages
4. Choose the branch (usually `main`) and save
5. Your site will be published at `https://yourusername.github.io/repositoryname/`

### 2. Netlify (Free)

1. Sign up on [Netlify](https://www.netlify.com/)
2. Drag and drop your website folder to Netlify's upload area
3. Or connect your GitHub repository for continuous deployment
4. Your site will be published with a Netlify subdomain
5. You can add a custom domain if desired

### 3. Vercel (Free)

1. Sign up on [Vercel](https://vercel.com/)
2. Connect your GitHub repository
3. Configure the deployment settings
4. Your site will be published with a Vercel subdomain
5. You can add a custom domain if desired

## Using a Custom Domain

If you already own a domain name, you can point it to any of the above hosting services. Each service provides instructions for adding custom domains in their documentation.

## Local Development

To preview your site locally, simply open the `index.html` file in a web browser. No server is required for this static website.

## License

Feel free to use this template for your personal website. 