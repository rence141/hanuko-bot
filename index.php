<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My Portfolio</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        header {
            text-align: center;
            padding: 60px 0;
            color: white;
        }
        
        h1 {
            font-size: 3rem;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .subtitle {
            font-size: 1.2rem;
            opacity: 0.9;
        }
        
        .content {
            background: white;
            border-radius: 15px;
            padding: 40px;
            margin: 20px 0;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .section {
            margin-bottom: 40px;
        }
        
        .section h2 {
            color: #667eea;
            margin-bottom: 20px;
            font-size: 2rem;
        }
        
        .project-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .project-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #667eea;
            transition: transform 0.3s ease;
        }
        
        .project-card:hover {
            transform: translateY(-5px);
        }
        
        .project-card h3 {
            color: #333;
            margin-bottom: 10px;
        }
        
        .skills {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 20px;
        }
        
        .skill-tag {
            background: #667eea;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9rem;
        }
        
        .contact-info {
            text-align: center;
            margin-top: 40px;
        }
        
        .contact-info a {
            color: #667eea;
            text-decoration: none;
            margin: 0 10px;
        }
        
        .contact-info a:hover {
            text-decoration: underline;
        }
        
        footer {
            text-align: center;
            padding: 20px;
            color: white;
            opacity: 0.8;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Welcome to My Portfolio</h1>
            <p class="subtitle">Full-Stack Developer & Discord Bot Creator</p>
        </header>
        
        <div class="content">
            <div class="section">
                <h2>About Me</h2>
                <p>I'm a passionate developer who loves creating innovative solutions. I specialize in Discord bot development, web applications, and full-stack development. My journey in programming has led me to create various projects that showcase my skills and creativity.</p>
            </div>
            
            <div class="section">
                <h2>Featured Projects</h2>
                <div class="project-grid">
                    <div class="project-card">
                        <h3>Discord Bot - Hanuko</h3>
                        <p>A comprehensive Discord bot with features including AFK system, daily/weekly streaks, polls, auto-moderation, and an SCP containment game.</p>
                        <div class="skills">
                            <span class="skill-tag">Python</span>
                            <span class="skill-tag">Discord.py</span>
                            <span class="skill-tag">JSON</span>
                        </div>
                    </div>
                    
                    <div class="project-card">
                        <h3>Web Portfolio</h3>
                        <p>A modern, responsive portfolio website built with PHP and CSS, featuring clean design and smooth animations.</p>
                        <div class="skills">
                            <span class="skill-tag">PHP</span>
                            <span class="skill-tag">HTML</span>
                            <span class="skill-tag">CSS</span>
                        </div>
                    </div>
                    
                    <div class="project-card">
                        <h3>Future Projects</h3>
                        <p>Always working on new ideas and learning new technologies. Stay tuned for more exciting projects!</p>
                        <div class="skills">
                            <span class="skill-tag">React</span>
                            <span class="skill-tag">Node.js</span>
                            <span class="skill-tag">SQL</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>Skills & Technologies</h2>
                <div class="skills">
                    <span class="skill-tag">Python</span>
                    <span class="skill-tag">PHP</span>
                    <span class="skill-tag">JavaScript</span>
                    <span class="skill-tag">HTML/CSS</span>
                    <span class="skill-tag">Discord.py</span>
                    <span class="skill-tag">Git</span>
                    <span class="skill-tag">Docker</span>
                    <span class="skill-tag">Render</span>
                </div>
            </div>
            
            <div class="contact-info">
                <h2>Get In Touch</h2>
                <p>I'm always interested in new opportunities and collaborations!</p>
                <a href="mailto:your.email@example.com">Email</a>
                <a href="https://github.com/yourusername">GitHub</a>
                <a href="https://linkedin.com/in/yourusername">LinkedIn</a>
            </div>
        </div>
    </div>
    
    <footer>
        <p>&copy; <?php echo date('Y'); ?> My Portfolio. Built with ❤️ and PHP.</p>
    </footer>
</body>
</html> 