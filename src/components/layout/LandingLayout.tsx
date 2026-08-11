import React from 'react';
import { Outlet, Link, useNavigate } from 'react-router-dom';
import { HeartPulse, ArrowRight, ShieldCheck, Github, ExternalLink } from 'lucide-react';
import { Button } from '../ui/Button';
import { useAuth } from '../../contexts/AuthContext';

export const LandingLayout: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-[#0B0F19] text-slate-900 dark:text-slate-100 font-sans flex flex-col selection:bg-blue-500 selection:text-white">
      {/* Header */}
      <header className="sticky top-0 z-50 w-full glass-panel border-b border-slate-200/80 dark:border-slate-800/80 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <Link to="/" className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-blue-600 via-blue-500 to-emerald-400 flex items-center justify-center text-white font-bold shadow-md shadow-blue-500/25">
              <HeartPulse className="w-6 h-6 animate-pulse" />
            </div>
            <span className="text-xl font-extrabold tracking-tight">
              Chrona<span className="text-blue-600 dark:text-blue-400">Nexus</span>
            </span>
          </Link>

          <nav className="hidden md:flex items-center space-x-8 text-sm font-semibold text-slate-600 dark:text-slate-300">
            <a href="#features" className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors">Features</a>
            <a href="#architecture" className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors">Architecture</a>
            <a href="#problem" className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors">Why ChronaNexus</a>
            <a href="#benefits" className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors">Benefits</a>
          </nav>

          <div className="flex items-center space-x-4">
            {isAuthenticated ? (
              <Button
                variant="primary"
                onClick={() => navigate('/dashboard')}
                rightIcon={<ArrowRight className="w-4 h-4" />}
              >
                Go to Dashboard
              </Button>
            ) : (
              <>
                <Link to="/login" className="text-sm font-semibold text-slate-700 dark:text-slate-300 hover:text-blue-600 transition-colors">
                  Sign In
                </Link>
                <Button
                  variant="primary"
                  onClick={() => navigate('/signup')}
                  rightIcon={<ArrowRight className="w-4 h-4" />}
                >
                  Launch App
                </Button>
              </>
            )}
          </div>
        </div>
      </header>

      {/* Main Landing Content */}
      <main className="flex-1">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 dark:border-slate-800/80 bg-white/50 dark:bg-[#090D16]/80 py-12 px-6">
        <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-8">
          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 rounded-xl bg-blue-600 flex items-center justify-center text-white font-bold">
                <HeartPulse className="w-5 h-5" />
              </div>
              <span className="text-lg font-bold">ChronaNexus</span>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
              Privacy-first longitudinal medical intelligence platform. Transforming medical PDFs into continuous patient understanding.
            </p>
          </div>

          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-4">Core Systems</h4>
            <ul className="space-y-2 text-xs text-slate-600 dark:text-slate-400">
              <li>Document Vault</li>
              <li>Medical Understanding Engine</li>
              <li>Patient Memory Engine</li>
              <li>Medical Timeline Engine</li>
              <li>Intelligence Search Engine</li>
              <li>Doctor Summary Engine</li>
            </ul>
          </div>

          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-4">Platform</h4>
            <ul className="space-y-2 text-xs text-slate-600 dark:text-slate-400">
              <li><Link to="/dashboard" className="hover:underline">Dashboard Overview</Link></li>
              <li><Link to="/vault" className="hover:underline">Document Vault</Link></li>
              <li><Link to="/timeline" className="hover:underline">Medical Timeline</Link></li>
              <li><Link to="/chat" className="hover:underline">AI Assistant</Link></li>
              <li><Link to="/doctor-summary" className="hover:underline">Doctor Summary Generator</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-4">Security & Privacy</h4>
            <div className="p-3 rounded-2xl bg-emerald-50/50 dark:bg-emerald-950/20 border border-emerald-200/50 dark:border-emerald-900/30 text-xs text-emerald-700 dark:text-emerald-300 space-y-2">
              <p className="font-semibold flex items-center gap-1"><ShieldCheck className="w-4 h-4 text-emerald-500" /> Patient Data Isolation</p>
              <p className="text-[11px] text-slate-500 dark:text-slate-400">Every upload creates an isolated memory graph owned exclusively by the patient.</p>
            </div>
          </div>
        </div>

        <div className="max-w-7xl mx-auto mt-12 pt-6 border-t border-slate-200 dark:border-slate-800/60 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-400 gap-4">
          <p>© 2026 ChronaNexus Inc. Capstone Project Foundation.</p>
          <div className="flex items-center space-x-6">
            <a href="#" className="hover:text-slate-200">Privacy Policy</a>
            <a href="#" className="hover:text-slate-200">Terms of Service</a>
            <a href="#" className="hover:text-slate-200">HIPAA Compliance</a>
          </div>
        </div>
      </footer>
    </div>
  );
};
