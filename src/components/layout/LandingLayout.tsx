import React from 'react';
import { Outlet, Link, useNavigate } from 'react-router-dom';
import { ArrowRight, Activity, ShieldCheck } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { useAuth } from '@/contexts/AuthContext';

export const LandingLayout: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-[#FAF8F5] dark:bg-[#121417] text-[#1F2937] dark:text-[#F3F4F6] font-sans flex flex-col selection:bg-emerald-500/20 selection:text-[#10B981]">
      {/* Header */}
      <header className="sticky top-0 z-50 w-full bg-[#FAF8F5]/90 dark:bg-[#121417]/90 backdrop-blur-md border-b border-[#E5E7EB] dark:border-[#2F3540] px-6 py-3.5">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <Link to="/" className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-xl bg-[#ECFDF5] dark:bg-emerald-950/40 border border-emerald-200/60 dark:border-emerald-800/40 flex items-center justify-center text-[#10B981] font-semibold">
              <Activity className="w-4 h-4" />
            </div>
            <span className="text-base font-semibold tracking-tight text-[#1F2937] dark:text-[#F3F4F6]">
              Chrona<span className="text-[#10B981]">Nexus</span>
            </span>
          </Link>

          <nav className="hidden md:flex items-center space-x-7 text-xs font-medium text-[#6B7280] dark:text-[#9CA3AF]">
            <a href="#features" className="hover:text-[#1F2937] dark:hover:text-[#F3F4F6] transition-colors">Features</a>
            <a href="#architecture" className="hover:text-[#1F2937] dark:hover:text-[#F3F4F6] transition-colors">Architecture</a>
            <a href="#problem" className="hover:text-[#1F2937] dark:hover:text-[#F3F4F6] transition-colors">Why ChronaNexus</a>
          </nav>

          <div className="flex items-center space-x-3">
            {isAuthenticated ? (
              <Button
                variant="primary"
                size="sm"
                onClick={() => navigate('/dashboard')}
                rightIcon={<ArrowRight className="w-3.5 h-3.5" />}
              >
                Go to Dashboard
              </Button>
            ) : (
              <>
                <Link to="/login" className="text-xs font-medium text-[#6B7280] dark:text-[#9CA3AF] hover:text-[#1F2937] dark:hover:text-[#F3F4F6] transition-colors">
                  Sign In
                </Link>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => navigate('/signup')}
                  rightIcon={<ArrowRight className="w-3.5 h-3.5" />}
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
      <footer className="border-t border-[#E5E7EB] dark:border-[#2F3540] bg-white dark:bg-[#1B1E23] py-12 px-6">
        <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-8">
          <div className="space-y-3">
            <div className="flex items-center space-x-2">
              <div className="w-7 h-7 rounded-lg bg-[#ECFDF5] border border-emerald-200 text-[#10B981] flex items-center justify-center font-bold">
                <Activity className="w-3.5 h-3.5" />
              </div>
              <span className="text-sm font-semibold">ChronaNexus</span>
            </div>
            <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF] leading-relaxed">
              Privacy-first longitudinal medical intelligence platform. Transforming medical PDFs into continuous patient understanding.
            </p>
          </div>

          <div>
            <h4 className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF] mb-3">Core Engines</h4>
            <ul className="space-y-1.5 text-xs text-[#6B7280] dark:text-[#9CA3AF]">
              <li>Document Vault</li>
              <li>Medical Understanding Engine</li>
              <li>Patient Memory Graph</li>
              <li>Longitudinal Timeline</li>
              <li>Doctor Summary Engine</li>
            </ul>
          </div>

          <div>
            <h4 className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF] mb-3">Platform Navigation</h4>
            <ul className="space-y-1.5 text-xs text-[#6B7280] dark:text-[#9CA3AF]">
              <li><Link to="/dashboard" className="hover:underline">Dashboard Overview</Link></li>
              <li><Link to="/vault" className="hover:underline">Document Vault</Link></li>
              <li><Link to="/timeline" className="hover:underline">Medical Timeline</Link></li>
              <li><Link to="/chat" className="hover:underline">Clinical Assistant</Link></li>
              <li><Link to="/doctor-summary" className="hover:underline">Physician Summary</Link></li>
            </ul>
          </div>

          <div className="space-y-2 text-xs text-[#6B7280] dark:text-[#9CA3AF]">
            <h4 className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF] mb-3">Security & Privacy</h4>
            <p className="flex items-center gap-1.5 font-medium text-[#1F2937] dark:text-[#F3F4F6]">
              <ShieldCheck className="w-4 h-4 text-[#10B981]" /> Zero-Knowledge Local AI
            </p>
            <p className="text-[11px] leading-relaxed">
              Patient data is isolated by user identifier and never stored unencrypted.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};
