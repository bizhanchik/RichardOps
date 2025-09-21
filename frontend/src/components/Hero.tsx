import React from 'react';
import { useNavigate } from 'react-router-dom';

const Hero: React.FC = () => {
  const navigate = useNavigate();
  return (
    <section className="pt-6 pb-8 px-6">
      <div className="max-w-4xl mx-auto text-center">
        {/* Hero Title */}
        <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6">
          <span className="block">Team Richards</span>
          <span className="block text-emerald-600">Securing Tomorrow with AI</span>
        </h1>
        
        {/* Subtitle */}
        <p className="text-xl md:text-2xl text-gray-600 mb-6 max-w-3xl mx-auto">
          We're building an AI-powered assistant that revolutionizes security monitoring 
          and automated response for modern development teams.
        </p>

        {/* CTA Button */}
        <div className="mb-6">
          <button 
            onClick={() => navigate('/solution')}
            className="bg-emerald-600 text-white px-8 py-4 rounded-xl text-lg font-semibold hover:bg-emerald-700 transition-colors shadow-lg hover:shadow-xl"
          >
            Explore Solution
          </button>
        </div>

        {/* Visual element */}
        <div className="relative max-w-2xl mx-auto">
          <div className="bg-gradient-to-r from-emerald-50 to-blue-50 rounded-2xl p-8 border border-gray-200">
            <div className="space-y-4">
              <div className="flex items-center justify-between text-sm text-gray-600">
                <span>Security Status</span>
                <span className="text-emerald-600 font-semibold">✓ All systems secure</span>
              </div>
              <div className="bg-white rounded-lg p-4 border border-gray-100">
                <div className="flex items-center space-x-3">
                  <div className="w-3 h-3 bg-emerald-500 rounded-full animate-pulse"></div>
                  <span className="text-gray-700">AI monitoring 247 endpoints...</span>
                </div>
              </div>
              <div className="grid grid-cols-3 gap-4 text-center">
                <div className="bg-white rounded-lg p-3 border border-gray-100">
                  <div className="text-2xl font-bold text-emerald-600">0</div>
                  <div className="text-xs text-gray-600">Threats</div>
                </div>
                <div className="bg-white rounded-lg p-3 border border-gray-100">
                  <div className="text-2xl font-bold text-blue-600">98.5%</div>
                  <div className="text-xs text-gray-600">Uptime</div>
                </div>
                <div className="bg-white rounded-lg p-3 border border-gray-100">
                  <div className="text-2xl font-bold text-gray-900">12ms</div>
                  <div className="text-xs text-gray-600">Response</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Hero;