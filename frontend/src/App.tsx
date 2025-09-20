import Header from "./components/Header";
import Hero from "./components/Hero";
import About from "./components/About";
import Features from "./components/Features";
import Team from "./components/Team";
import Footer from "./components/Footer";

// Main App component for Team Richards landing page
function App() {
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
}

export default App;
