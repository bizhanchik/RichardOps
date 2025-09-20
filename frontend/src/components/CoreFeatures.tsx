import React from 'react';
import Card from './common/Card';

const CoreFeatures: React.FC = () => {
  const features = [
    {
      icon: '📊',
      title: 'Multi-Source Log Ingestion',
      description: 'Seamlessly collect and normalize security logs from firewalls, IDS/IPS, SIEM systems, and cloud platforms.',
      color: 'neon-purple-500',
    },
    {
      icon: '🤖',
      title: 'AI-Powered Threat Detection',
      description: 'Advanced machine learning algorithms identify patterns and anomalies to detect sophisticated threats.',
      color: 'neon-green-500',
    },
    {
      icon: '⚡',
      title: 'Automated Response',
      description: 'Instant automated reactions to detected threats including quarantine, blocking, and alert escalation.',
      color: 'neon-purple-500',
    },
    {
      icon: '🔮',
      title: 'Predictive Analytics',
      description: 'Forecast potential security issues and vulnerabilities before they become critical threats.',
      color: 'neon-green-500',
    },
    {
      icon: '💬',
      title: 'Natural Language Interface',
      description: 'Query security data and get insights using natural language commands and conversational AI.',
      color: 'neon-purple-500',
    },
    {
      icon: '📈',
      title: 'Real-time Dashboard',
      description: 'Comprehensive visualization of security metrics, threat landscape, and system health.',
      color: 'neon-green-500',
    },
  ];

  return (
    <section id="features" className="py-20 bg-dark-bg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold text-text-primary mb-6 glow-text">
            Core Features
          </h2>
          <p className="text-xl text-text-secondary max-w-3xl mx-auto">
            Cutting-edge capabilities that redefine cybersecurity operations
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <Card key={index} hover={true} className="group">
              <div className="text-center">
                <div className="text-4xl mb-4 group-hover:scale-110 transition-transform duration-300">
                  {feature.icon}
                </div>
                <h3 className={`text-xl font-bold text-${feature.color} mb-4 glow-text`}>
                  {feature.title}
                </h3>
                <p className="text-text-muted leading-relaxed">
                  {feature.description}
                </p>
              </div>
            </Card>
          ))}
        </div>

        {/* Technical Stack */}
        <div className="mt-20">
          <div className="text-center mb-12">
            <h3 className="text-3xl font-bold text-text-primary mb-4">
              Powered by Advanced Technology
            </h3>
          </div>
          
          <Card className="bg-gradient-to-r from-dark-card to-dark-surface">
            <div className="grid md:grid-cols-4 gap-8 text-center">
              <div>
                <div className="text-neon-purple-500 font-bold text-lg mb-2">Machine Learning</div>
                <p className="text-text-muted text-sm">TensorFlow, PyTorch</p>
              </div>
              <div>
                <div className="text-neon-green-500 font-bold text-lg mb-2">Data Processing</div>
                <p className="text-text-muted text-sm">Apache Kafka, Elasticsearch</p>
              </div>
              <div>
                <div className="text-neon-purple-500 font-bold text-lg mb-2">AI Models</div>
                <p className="text-text-muted text-sm">BERT, Transformer Networks</p>
              </div>
              <div>
                <div className="text-neon-green-500 font-bold text-lg mb-2">Infrastructure</div>
                <p className="text-text-muted text-sm">Kubernetes, Docker</p>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </section>
  );
};

export default CoreFeatures;