import React from 'react';

const Features: React.FC = () => {
  const features = [
    {
      title: 'Log Ingestion',
      description: 'Seamlessly collect and normalize security logs from multiple sources including servers, applications, and network devices.',
      icon: '📊'
    },
    {
      title: 'AI Threat Detection',
      description: 'Advanced machine learning algorithms analyze patterns and detect anomalies in real-time to identify potential security threats.',
      icon: '🔍'
    },
    {
      title: 'Automated Response',
      description: 'Intelligent automation system that responds to threats based on severity levels with customizable escalation procedures.',
      icon: '⚡'
    },
    {
      title: 'Natural Language Interface',
      description: 'Chat with your security system using plain English to get insights, reports, and perform security operations.',
      icon: '💬'
    }
  ];

  return (
    <section id="features" className="py-20 px-6 bg-white scroll-mt-24">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-6">
            Key Features
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Our DevSecOps AI Assistant combines cutting-edge technology with practical 
            security operations to deliver comprehensive protection.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
          {features.map((feature, index) => (
            <div 
              key={index}
              className="bg-gray-50 rounded-2xl p-6 border border-gray-200 hover:border-emerald-200 transition-all duration-300 hover:shadow-lg"
            >
              <div className="text-4xl mb-4">{feature.icon}</div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">
                {feature.title}
              </h3>
              <p className="text-gray-600 leading-relaxed">
                {feature.description}
              </p>
            </div>
          ))}
        </div>

        <div className="mt-16 text-center">
          <div className="bg-emerald-50 rounded-2xl p-8 border border-emerald-100">
            <h3 className="text-xl font-semibold text-gray-900 mb-4">
              Ready to secure your operations?
            </h3>
            <p className="text-gray-600 mb-6">
              Experience the future of DevSecOps with our AI-powered security assistant.
            </p>
            <button className="bg-emerald-600 text-white px-8 py-3 rounded-xl font-medium hover:bg-emerald-700 transition-colors">
              Get Started
            </button>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Features;