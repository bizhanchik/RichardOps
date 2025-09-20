import React from 'react';
import Card from './common/Card';

const AboutCase: React.FC = () => {
  return (
    <section id="about" className="py-20 bg-gray-800/50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-6 glow-text">
            The Challenge
          </h2>
          <p className="text-xl text-gray-300 max-w-3xl mx-auto">
            DevSecOps AI Assistant: Transforming Security Operations
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8 items-center">
          <div>
            <Card glow={true}>
              <h3 className="text-2xl font-bold text-white mb-4">The Problem</h3>
              <ul className="space-y-3 text-gray-300">
                <li className="flex items-start">
                  <span className="text-purple-500 mr-3">•</span>
                  Security teams are overwhelmed by massive volumes of logs from multiple sources
                </li>
                <li className="flex items-start">
                  <span className="text-purple-500 mr-3">•</span>
                  Manual threat detection is slow and error-prone
                </li>
                <li className="flex items-start">
                  <span className="text-purple-500 mr-3">•</span>
                  Response times to security incidents are too slow
                </li>
                <li className="flex items-start">
                  <span className="text-purple-500 mr-3">•</span>
                  Lack of predictive insights for proactive security
                </li>
              </ul>
            </Card>
          </div>

          <div>
            <Card>
              <h3 className="text-2xl font-bold text-white mb-4">Our Solution</h3>
              <ul className="space-y-3 text-gray-300">
                <li className="flex items-start">
                  <span className="text-green-500 mr-3">✓</span>
                  AI-powered log ingestion from multiple security tools
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-3">✓</span>
                  Machine learning models for intelligent threat detection
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-3">✓</span>
                  Automated response systems for immediate action
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-3">✓</span>
                  Predictive analytics for proactive security measures
                </li>
              </ul>
            </Card>
          </div>
        </div>

        <div className="mt-16 text-center">
          <Card className="max-w-4xl mx-auto">
            <h3 className="text-3xl font-bold text-white mb-6">Impact & Innovation</h3>
            <div className="grid md:grid-cols-3 gap-8">
              <div>
                <div className="text-3xl font-bold text-purple-500 mb-2">95%</div>
                <p className="text-gray-300">Faster Threat Detection</p>
              </div>
              <div>
                <div className="text-3xl font-bold text-green-500 mb-2">80%</div>
                <p className="text-gray-300">Reduction in False Positives</p>
              </div>
              <div>
                <div className="text-3xl font-bold text-purple-500 mb-2">24/7</div>
                <p className="text-gray-300">Automated Monitoring</p>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </section>
  );
};

export default AboutCase;