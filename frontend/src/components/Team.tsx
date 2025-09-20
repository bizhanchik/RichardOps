import React from 'react';

const Team: React.FC = () => {
  const teamMembers = [
    {
      name: 'Dauren',
      role: 'Genius',
      description: 'The brains of the operation — architect of ideas, breaker of limits.',
      avatar: 'D'
    },
    {
      name: 'Bizhan',
      role: 'Millionaire',
      description: 'Knows how to turn caffeine and code into pure gold. Probably funding our afterparty.',
      avatar: 'B'
    },
    {
      name: 'Fatikh',
      role: 'Philanthropist',
      description: 'Always building for the greater good — automates, secures, and shares the love.',
      avatar: 'F'
    }
  ];

  return (
    <section id="team" className="py-20 px-6 bg-gray-50 scroll-mt-24">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-6">
            Meet Team Richards
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Our diverse team brings together expertise in security, AI, and software 
            development to create innovative DevSecOps solutions.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8 mb-16 justify-center">
          {teamMembers.map((member, index) => (
            <div 
              key={index}
              className="bg-white rounded-2xl p-6 border border-gray-200 text-center hover:shadow-lg transition-all duration-300 max-w-sm mx-auto"
            >
              <div className="w-20 h-20 bg-emerald-600 rounded-full flex items-center justify-center text-white font-bold text-xl mx-auto mb-4">
                {member.avatar}
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                {member.name}
              </h3>
              <p className="text-emerald-600 font-medium mb-3">
                {member.role}
              </p>
              <p className="text-gray-600 text-sm leading-relaxed">
                {member.description}
              </p>
            </div>
          ))}
        </div>

        <div className="bg-white rounded-2xl p-8 border border-gray-200 text-center">
          <h3 className="text-2xl font-semibold text-gray-900 mb-4">
            Get in Touch
          </h3>
          <p className="text-gray-600 mb-6">
            Interested in our DevSecOps AI Assistant? Let's discuss how we can help 
            secure your operations.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a 
              href="https://mail.google.com/mail/?view=cm&fs=1&to=aidyn.fatikh@gmail.com"
              target="_blank"
              rel="noopener noreferrer"
              className="bg-emerald-600 text-white px-6 py-3 rounded-xl font-medium hover:bg-emerald-700 transition-colors"
            >
              Email Us
            </a>
            <a 
              href="#"
              className="border border-gray-300 text-gray-700 px-6 py-3 rounded-xl font-medium hover:border-gray-400 transition-colors"
            >
              View Demo
            </a>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Team;