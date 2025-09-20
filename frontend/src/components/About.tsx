import React from 'react';

const About: React.FC = () => {
  return (
    <section id="about" className="py-20 px-6 bg-gray-50 scroll-mt-24">
      <div className="max-w-4xl mx-auto text-center">
        <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-6">
          About Our Hackathon Case
        </h2>
        <p className="text-lg text-gray-600 mb-8 max-w-3xl mx-auto">
          Our DevSecOps AI Assistant represents a breakthrough in automated security operations. 
          Built for the hackathon challenge, this platform combines machine learning with 
          DevSecOps best practices to create an intelligent security monitoring solution.
        </p>
        
        <div className="bg-white rounded-2xl p-8 border border-gray-200 shadow-sm">
          <h3 className="text-xl font-semibold text-gray-900 mb-4">
            What makes our solution unique?
          </h3>
          <div className="grid md:grid-cols-2 gap-6 text-left">
            <div>
              <h4 className="font-semibold text-gray-900 mb-2">Intelligent Log Analysis</h4>
              <p className="text-gray-600">
                AI-powered parsing and analysis of security logs from multiple sources 
                with real-time threat detection capabilities.
              </p>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 mb-2">Automated Response</h4>
              <p className="text-gray-600">
                Immediate automated actions based on threat severity, from alerting 
                to containment and remediation suggestions.
              </p>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 mb-2">Natural Language Interface</h4>
              <p className="text-gray-600">
                Query security status and get insights using plain English, 
                making security accessible to all team members.
              </p>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 mb-2">Predictive Analytics</h4>
              <p className="text-gray-600">
                Machine learning models that learn from patterns to predict 
                and prevent future security incidents.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default About;