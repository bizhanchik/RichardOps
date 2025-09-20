import React from 'react';
import Card from './common/Card';

const SystemArchitecture: React.FC = () => {
  const architectureSteps = [
    {
      title: 'Data Sources',
      description: 'Firewalls, IDS/IPS, SIEM, Cloud Logs',
      icon: '🗄️',
      color: 'neon-purple-500',
    },
    {
      title: 'Ingestion Layer',
      description: 'Real-time log collection & normalization',
      icon: '📥',
      color: 'neon-green-500',
    },
    {
      title: 'Processing Engine',
      description: 'Data parsing, enrichment & correlation',
      icon: '⚙️',
      color: 'neon-purple-500',
    },
    {
      title: 'AI Analysis',
      description: 'ML models for threat detection & prediction',
      icon: '🧠',
      color: 'neon-green-500',
    },
    {
      title: 'Response System',
      description: 'Automated actions & alerting',
      icon: '🛡️',
      color: 'neon-purple-500',
    },
  ];

  return (
    <section id="architecture" className="py-20 bg-dark-surface">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold text-text-primary mb-6 glow-text">
            System Architecture
          </h2>
          <p className="text-xl text-text-secondary max-w-3xl mx-auto">
            A scalable, intelligent security platform built for the future
          </p>
        </div>

        {/* Architecture Flow */}
        <div className="mb-16">
          <div className="flex flex-col lg:flex-row items-center justify-between space-y-8 lg:space-y-0 lg:space-x-4">
            {architectureSteps.map((step, index) => (
              <div key={index} className="flex flex-col lg:flex-row items-center">
                <Card hover={true} className="w-64 text-center group">
                  <div className="text-4xl mb-4 group-hover:scale-110 transition-transform duration-300">
                    {step.icon}
                  </div>
                  <h3 className={`text-lg font-bold text-${step.color} mb-2 glow-text`}>
                    {step.title}
                  </h3>
                  <p className="text-text-muted text-sm">
                    {step.description}
                  </p>
                </Card>
                
                {index < architectureSteps.length - 1 && (
                  <div className="lg:mx-4 my-4 lg:my-0">
                    <svg 
                      className="w-8 h-8 text-neon-purple-500 rotate-90 lg:rotate-0" 
                      fill="none" 
                      stroke="currentColor" 
                      viewBox="0 0 24 24"
                    >
                      <path 
                        strokeLinecap="round" 
                        strokeLinejoin="round" 
                        strokeWidth={2} 
                        d="M13 7l5 5m0 0l-5 5m5-5H6" 
                      />
                    </svg>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Technical Details */}
        <div className="grid md:grid-cols-2 gap-8">
          <Card glow={true}>
            <h3 className="text-2xl font-bold text-text-primary mb-6">
              📊 Data Processing Pipeline
            </h3>
            <ul className="space-y-3 text-text-muted">
              <li className="flex items-start">
                <span className="text-neon-purple-500 mr-3">•</span>
                High-throughput log ingestion (1M+ events/sec)
              </li>
              <li className="flex items-start">
                <span className="text-neon-purple-500 mr-3">•</span>
                Real-time stream processing with Apache Kafka
              </li>
              <li className="flex items-start">
                <span className="text-neon-purple-500 mr-3">•</span>
                Elasticsearch for fast querying and indexing
              </li>
              <li className="flex items-start">
                <span className="text-neon-purple-500 mr-3">•</span>
                Microservices architecture for scalability
              </li>
            </ul>
          </Card>

          <Card>
            <h3 className="text-2xl font-bold text-text-primary mb-6">
              🤖 AI & Machine Learning
            </h3>
            <ul className="space-y-3 text-text-muted">
              <li className="flex items-start">
                <span className="text-neon-green-500 mr-3">•</span>
                Anomaly detection using unsupervised learning
              </li>
              <li className="flex items-start">
                <span className="text-neon-green-500 mr-3">•</span>
                NLP models for log text analysis
              </li>
              <li className="flex items-start">
                <span className="text-neon-green-500 mr-3">•</span>
                Reinforcement learning for response optimization
              </li>
              <li className="flex items-start">
                <span className="text-neon-green-500 mr-3">•</span>
                Continuous model training and improvement
              </li>
            </ul>
          </Card>
        </div>

        {/* Performance Metrics */}
        <div className="mt-16">
          <Card className="bg-gradient-to-r from-neon-purple-900/20 to-neon-green-900/20 border-neon-purple-500">
            <h3 className="text-3xl font-bold text-text-primary mb-8 text-center">
              Performance Benchmarks
            </h3>
            <div className="grid md:grid-cols-4 gap-8 text-center">
              <div>
                <div className="text-4xl font-bold text-neon-purple-500 mb-2">99.9%</div>
                <p className="text-text-muted">Uptime</p>
              </div>
              <div>
                <div className="text-4xl font-bold text-neon-green-500 mb-2">&lt;100ms</div>
                <p className="text-text-muted">Response Time</p>
              </div>
              <div>
                <div className="text-4xl font-bold text-neon-purple-500 mb-2">1M+</div>
                <p className="text-text-muted">Events/Second</p>
              </div>
              <div>
                <div className="text-4xl font-bold text-neon-green-500 mb-2">98%</div>
                <p className="text-text-muted">Accuracy</p>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </section>
  );
};

export default SystemArchitecture;