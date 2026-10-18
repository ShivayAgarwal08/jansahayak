import React from 'react';
import { Link } from 'react-router-dom';
import { Shield, Lock, FileText, ExternalLink, HeartHandshake } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-navy-950 text-white pt-14 pb-10 border-t border-navy-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-10 pb-12 border-b border-navy-800">
          
          {/* Col 1: Brand & Mission */}
          <div className="md:col-span-1 space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-leaf-700 flex items-center justify-center text-white font-black text-lg">
                जन
              </div>
              <span className="text-xl font-bold tracking-tight text-white">JanSahayak</span>
            </div>
            <p className="text-sm text-navy-200/70 leading-relaxed">
              Empowering Indian citizens with verified welfare information, deterministic eligibility rules, and guided application preparation in your own language.
            </p>
            <div className="flex items-center gap-2 text-xs text-saffron-500 font-semibold pt-1">
              <Shield className="w-4 h-4" />
              <span>Zero-Aadhaar Data Collection</span>
            </div>
          </div>

          {/* Col 2: Citizen Services */}
          <div>
            <h4 className="text-sm font-bold uppercase tracking-wider text-saffron-500 mb-4">
              Citizen Services
            </h4>
            <ul className="space-y-2.5 text-sm text-navy-200/80">
              <li>
                <Link to="/schemes" className="hover:text-white transition-colors">
                  Scheme Discovery
                </Link>
              </li>
              <li>
                <Link to="/eligibility" className="hover:text-white transition-colors">
                  Deterministic Eligibility Engine
                </Link>
              </li>
              <li>
                <Link to="/assistant" className="hover:text-white transition-colors">
                  Multilingual Voice Assistant
                </Link>
              </li>
              <li>
                <Link to="/applications" className="hover:text-white transition-colors">
                  Application Preparation
                </Link>
              </li>
              <li>
                <Link to="/compare" className="hover:text-white transition-colors">
                  Scheme Comparison
                </Link>
              </li>
            </ul>
          </div>

          {/* Col 3: Legal & Grievances */}
          <div>
            <h4 className="text-sm font-bold uppercase tracking-wider text-saffron-500 mb-4">
              Transparency & Rights
            </h4>
            <ul className="space-y-2.5 text-sm text-navy-200/80">
              <li>
                <Link to="/rti" className="hover:text-white transition-colors">
                  RTI Application Drafter (Sec 6(1))
                </Link>
              </li>
              <li>
                <Link to="/grievances" className="hover:text-white transition-colors">
                  Public Grievance Drafter (CPGRAMS)
                </Link>
              </li>
              <li>
                <a
                  href="https://pgportal.gov.in"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 hover:text-white transition-colors"
                >
                  <span>Official CPGRAMS Portal</span>
                  <ExternalLink className="w-3.5 h-3.5 opacity-70" />
                </a>
              </li>
              <li>
                <a
                  href="https://rtionline.gov.in"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 hover:text-white transition-colors"
                >
                  <span>Official RTI Online Portal</span>
                  <ExternalLink className="w-3.5 h-3.5 opacity-70" />
                </a>
              </li>
            </ul>
          </div>

          {/* Col 4: Trust & Privacy */}
          <div>
            <h4 className="text-sm font-bold uppercase tracking-wider text-saffron-500 mb-4">
              Security & Privacy
            </h4>
            <ul className="space-y-2.5 text-sm text-navy-200/80">
              <li>
                <Link to="/privacy" className="hover:text-white transition-colors">
                  Privacy Charter & Data Rights
                </Link>
              </li>
              <li>
                <Link to="/privacy#rights" className="hover:text-white transition-colors">
                  Account & Data Deletion
                </Link>
              </li>
              <li>
                <a
                  href="https://www.india.gov.in"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 hover:text-white transition-colors"
                >
                  <span>National Portal of India</span>
                  <ExternalLink className="w-3.5 h-3.5 opacity-70" />
                </a>
              </li>
            </ul>
          </div>

        </div>

        {/* Bottom Bar & Disclaimer */}
        <div className="pt-8 flex flex-col md:flex-row items-center justify-between gap-4 text-xs text-navy-200/60 text-center md:text-left">
          <p>
            © {new Date().getFullYear()} JanSahayak (जनसहायक). Designed for public welfare and digital empowerment across India.
          </p>
          <div className="flex items-center gap-6">
            <Link to="/privacy" className="hover:text-white transition-colors">
              Privacy Policy
            </Link>
            <Link to="/schemes" className="hover:text-white transition-colors">
              Verified Portals
            </Link>
            <span className="text-saffron-500 font-semibold">
              🇮🇳 Made for Every Indian Citizen
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
};
