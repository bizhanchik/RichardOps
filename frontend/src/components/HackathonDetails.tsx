import React from 'react';
import Card from './common/Card';

const HackathonDetails: React.FC = () => {
  return (
    <section className="py-20 bg-dark-bg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold text-text-primary mb-6 glow-text">
            Hackathon 2025
          </h2>
          <p className="text-xl text-text-secondary max-w-3xl mx-auto">
            Our journey in the DevSecOps AI Assistant Challenge
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8 mb-16">
          <Card glow={true}>
            <h3 className="text-2xl font-bold text-text-primary mb-6">
              🏆 Competition Details
            </h3>
            <div className="space-y-4 text-text-muted">
              <div className="flex justify-between">
                <span>Event:</span>
                <span className="text-neon-purple-500 font-semibold">DevSecOps AI Hackathon 2025</span>
              </div>
              <div className="flex justify-between">
                <span>Duration:</span>
                <span className="text-neon-green-500 font-semibold">48 Hours</span>
              </div>
              <div className="flex justify-between">
                <span>Track:</span>
                <span className="text-neon-purple-500 font-semibold">AI-Powered Security</span>
              </div>
              <div className="flex justify-between">
                <span>Team Size:</span>
                <span className="text-neon-green-500 font-semibold">4 Developers</span>
              </div>
            </div>
          </Card>

          <Card>
            <h3 className="text-2xl font-bold text-text-primary mb-6">
              🎯 Our Approach
            </h3>
            <ul className="space-y-3 text-text-muted">
              <li className="flex items-start">
                <span className="text-neon-purple-500 mr-3">•</span>
                Rapid prototyping with modern tech stack
              </li>
              <li className="flex items-start">
                <span className="text-neon-green-500 mr-3">•</span>
                AI-first architecture design
              </li>
              <li className="flex items-start">
                <span className="text-neon-purple-500 mr-3">•</span>
                Focus on real-world security challenges
              </li>
              <li className="flex items-start">
                <span className="text-neon-green-500 mr-3">•</span>
                Scalable and production-ready solution
              </li>
            </ul>
          </Card>
        </div>

        {/* Timeline */}
        <Card className="mb-16">
          <h3 className="text-3xl font-bold text-text-primary mb-8 text-center">
            Development Timeline
          </h3>
          <div className="grid md:grid-cols-4 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-gradient-purple rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-white font-bold text-xl">1</span>
              </div>
              <h4 className="text-lg font-bold text-neon-purple-500 mb-2">Planning</h4>
              <p className="text-text-muted text-sm">Architecture design & tech stack selection</p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-gradient-green rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-white font-bold text-xl">2</span>
              </div>
              <h4 className="text-lg font-bold text-neon-green-500 mb-2">Development</h4>
              <p className="text-text-muted text-sm">Core features & AI model implementation</p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-gradient-purple rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-white font-bold text-xl">3</span>
              </div>
              <h4 className="text-lg font-bold text-neon-purple-500 mb-2">Integration</h4>
              <p className="text-text-muted text-sm">System integration & testing</p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-gradient-green rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-white font-bold text-xl">4</span>
              </div>
              <h4 className="text-lg font-bold text-neon-green-500 mb-2">Presentation</h4>
              <p className="text-text-muted text-sm">Demo preparation & final pitch</p>
            </div>
          </div>
        </Card>

        {/* Technologies Used */}
        <Card className="bg-gradient-to-r from-dark-card to-dark-surface">
          <h3 className="text-3xl font-bold text-text-primary mb-8 text-center">
            Technologies & Tools
          </h3>
          <div className="grid md:grid-cols-3 gap-8">
            <div>
              <h4 className="text-xl font-bold text-neon-purple-500 mb-4">Backend</h4>
              <ul className="space-y-2 text-text-muted">
                <li>• Python & FastAPI</li>
                <li>• TensorFlow & PyTorch</li>
                <li>• Apache Kafka</li>
                <li>• Elasticsearch</li>
              </ul>
            </div>
            <div>
              <h4 className="text-xl font-bold text-neon-green-500 mb-4">Frontend</h4>
              <ul className="space-y-2 text-text-muted">
                <li>• React & TypeScript</li>
                <li>• Tailwind CSS</li>
                <li>• D3.js for visualizations</li>
                <li>• WebSocket for real-time</li>
              </ul>
            </div>
            <div>
              <h4 className="text-xl font-bold text-neon-purple-500 mb-4">Infrastructure</h4>
              <ul className="space-y-2 text-text-muted">
                <li>• Docker & Kubernetes</li>
                <li>• AWS/Azure Cloud</li>
                <li>• Redis for caching</li>
                <li>• PostgreSQL</li>
              </ul>
            </div>
          </div>
        </Card>
      </div>
    </section>
  );
};

export default HackathonDetails;