import React from 'react';
import Header from './Header';
import Hero from './Hero';
import About from './About';
import Features from './Features';
import Team from './Team';
import Footer from './Footer';

const LandingPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-white">
      <Header />
      <main>
        <Hero />
        <About />
        <Features />
        <Team />
      </main>
      <Footer />
    </div>
  );
};

export default LandingPage;