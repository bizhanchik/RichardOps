import React from 'react';
import Card from './common/Card';

const TeamSection: React.FC = () => {
  const teamMembers = [
    {
      name: 'Alex Richards',
      role: 'Full-Stack Developer & Team Lead',
      avatar: '👨‍💻',
      skills: ['React', 'Node.js', 'Python', 'DevOps'],
      color: 'neon-purple-500',
    },
    {
      name: 'Sarah Chen',
      role: 'AI/ML Engineer',
      avatar: '👩‍🔬',
      skills: ['TensorFlow', 'PyTorch', 'NLP', 'Data Science'],
      color: 'neon-green-500',
    },
    {
      name: 'Marcus Johnson',
      role: 'Security Specialist',
      avatar: '🛡️',
      skills: ['Cybersecurity', 'SIEM', 'Threat Analysis', 'Forensics'],
      color: 'neon-purple-500',
    },
    {
      name: 'Emily Davis',
      role: 'DevOps Engineer',
      avatar: '⚙️',
      skills: ['Kubernetes', 'Docker', 'AWS', 'CI/CD'],
      color: 'neon-green-500',
    },
  ];

  return (
    <section id="team" className="py-20 bg-dark-surface">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold text-text-primary mb-6 glow-text">
            Meet Team Richards
          </h2>
          <p className="text-xl text-text-secondary max-w-3xl mx-auto">
            A diverse group of passionate developers, security experts, and innovators
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8 mb-16">
          {teamMembers.map((member, index) => (
            <Card key={index} hover={true} className="text-center group">
              <div className="text-6xl mb-4 group-hover:scale-110 transition-transform duration-300">
                {member.avatar}
              </div>
              <h3 className={`text-xl font-bold text-${member.color} mb-2 glow-text`}>
                {member.name}
              </h3>
              <p className="text-text-secondary mb-4 font-medium">
                {member.role}
              </p>
              <div className="space-y-1">
                {member.skills.map((skill, skillIndex) => (
                  <span
                    key={skillIndex}
                    className="inline-block bg-dark-bg text-text-muted px-2 py-1 rounded-lg text-sm mr-1 mb-1"
                  >
                    {skill}
                  </span>
                ))}
              </div>
            </Card>
          ))}
        </div>

        {/* Team Stats */}
        <Card className="bg-gradient-to-r from-neon-purple-900/20 to-neon-green-900/20 border-neon-purple-500">
          <h3 className="text-3xl font-bold text-text-primary mb-8 text-center">
            Team Achievements
          </h3>
          <div className="grid md:grid-cols-4 gap-8 text-center">
            <div>
              <div className="text-4xl font-bold text-neon-purple-500 mb-2">15+</div>
              <p className="text-text-muted">Years Combined Experience</p>
            </div>
            <div>
              <div className="text-4xl font-bold text-neon-green-500 mb-2">8</div>
              <p className="text-text-muted">Previous Hackathons</p>
            </div>
            <div>
              <div className="text-4xl font-bold text-neon-purple-500 mb-2">3</div>
              <p className="text-text-muted">Awards Won</p>
            </div>
            <div>
              <div className="text-4xl font-bold text-neon-green-500 mb-2">24h</div>
              <p className="text-text-muted">Development Time</p>
            </div>
          </div>
        </Card>

        {/* Team Values */}
        <div className="mt-16 grid md:grid-cols-3 gap-8">
          <Card>
            <div className="text-center">
              <div className="text-4xl mb-4">🚀</div>
              <h3 className="text-xl font-bold text-neon-purple-500 mb-4">Innovation</h3>
              <p className="text-text-muted">
                We push boundaries and explore cutting-edge technologies to solve real-world problems.
              </p>
            </div>
          </Card>
          
          <Card>
            <div className="text-center">
              <div className="text-4xl mb-4">🤝</div>
              <h3 className="text-xl font-bold text-neon-green-500 mb-4">Collaboration</h3>
              <p className="text-text-muted">
                Our diverse backgrounds and skills create a powerful synergy for building exceptional solutions.
              </p>
            </div>
          </Card>
          
          <Card>
            <div className="text-center">
              <div className="text-4xl mb-4">🎯</div>
              <h3 className="text-xl font-bold text-neon-purple-500 mb-4">Excellence</h3>
              <p className="text-text-muted">
                We strive for perfection in every line of code and every feature we deliver.
              </p>
            </div>
          </Card>
        </div>

        {/* Contact Section */}
        <div className="mt-16 text-center">
          <Card glow={true} className="max-w-2xl mx-auto">
            <h3 className="text-2xl font-bold text-text-primary mb-4">
              Get in Touch
            </h3>
            <p className="text-text-muted mb-6">
              Interested in our solution or want to collaborate? We'd love to hear from you!
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <a
                href="mailto:contact@teamrichards.dev"
                className="bg-gradient-neon text-white px-6 py-3 rounded-xl font-semibold hover:scale-105 transition-transform duration-300"
              >
                Email Us
              </a>
              <a
                href="#"
                className="bg-dark-bg text-neon-purple-500 border border-neon-purple-500 px-6 py-3 rounded-xl font-semibold hover:bg-neon-purple-500 hover:text-white transition-colors duration-300"
              >
                View GitHub
              </a>
            </div>
          </Card>
        </div>
      </div>
    </section>
  );
};

export default TeamSection;