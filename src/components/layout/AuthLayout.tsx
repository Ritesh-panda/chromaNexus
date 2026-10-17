import React from 'react';
import { Outlet, Link } from 'react-router-dom';
import { ShieldCheck, CheckCircle2, Activity, Sun, Moon } from 'lucide-react';
import { ToastContainer } from '@/components/ui/Toast';
import { useTheme } from '@/contexts/ThemeContext';

export const AuthLayout: React.FC = () => {
  const { theme, setTheme } = useTheme();

  return (
    <div className="min-h-screen w-full flex bg-[#FAF8F5] dark:bg-[#121417] text-[#1F2937] dark:text-[#F3F4F6] font-sans">
      {/* Left Healthcare Feature Banner */}
      <div className="hidden lg:flex lg:w-1/2 bg-white dark:bg-[#1B1E23] border-r border-[#E5E7EB] dark:border-[#2F3540] p-12 flex-col justify-between relative overflow-hidden">
        <div className="flex items-center space-x-2.5 z-10">
          <div className="w-9 h-9 rounded-xl bg-[#ECFDF5] dark:bg-emerald-950/40 border border-emerald-200/60 dark:border-emerald-800/40 flex items-center justify-center text-[#10B981] font-semibold shrink-0">
            <Activity className="w-4 h-4" />
          </div>
          <span className="text-base font-semibold tracking-tight text-[#1F2937] dark:text-[#F3F4F6]">
            Chrona<span className="text-[#10B981]">Nexus</span>
          </span>
        </div>

        {/* Feature Narrative */}
        <div className="my-auto z-10 space-y-5 max-w-lg">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#ECFDF5] dark:bg-emerald-950/40 text-[#15803D] dark:text-emerald-300 text-xs font-medium border border-emerald-200/60 dark:border-emerald-800/40">
            <ShieldCheck className="w-3.5 h-3.5" /> Longitudinal Medical Intelligence
          </div>
          <h1 className="text-3xl sm:text-4xl font-semibold leading-tight text-[#1F2937] dark:text-[#F3F4F6] tracking-tight">
            Transforming fragmented medical records into continuous patient understanding.
          </h1>
          <p className="text-xs sm:text-sm text-[#6B7280] dark:text-[#9CA3AF] leading-relaxed">
            ChronaNexus connects years of blood tests, MRI scans, and prescriptions into a unified, machine-understandable memory with zero privacy compromise.
          </p>

          <div className="space-y-2.5 pt-2">
            {[
              'End-to-End Encrypted Patient Vault',
              'Automated Clinical Entity & Numerical Extraction',
              'Instant 60-Second Physician Summary Digests',
            ].map((feat, idx) => (
              <div key={idx} className="flex items-center space-x-2.5 text-xs font-medium text-[#4B5563] dark:text-[#D1D5DB]">
                <CheckCircle2 className="w-4 h-4 text-[#10B981] shrink-0" />
                <span>{feat}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="flex items-center justify-between text-xs text-[#9CA3AF] z-10 border-t border-[#E5E7EB]/80 dark:border-[#2F3540] pt-4">
          <span className="flex items-center gap-1.5 font-medium text-[#6B7280] dark:text-[#9CA3AF]">
            <ShieldCheck className="w-3.5 h-3.5 text-[#10B981]" /> HIPAA Compliant Architecture
          </span>
          <span>v1.0 Capstone</span>
        </div>
      </div>

      {/* Right Form Container */}
      <div className="flex-1 flex flex-col justify-between p-6 sm:p-12 md:p-16">
        <div className="flex items-center justify-between pb-4">
          <div className="lg:hidden">
            <Link to="/" className="flex items-center space-x-2">
              <div className="w-8 h-8 rounded-xl bg-[#ECFDF5] border border-emerald-200 text-[#10B981] flex items-center justify-center font-bold">
                <Activity className="w-4 h-4" />
              </div>
              <span className="text-base font-semibold">ChronaNexus</span>
            </Link>
          </div>
          <div className="ml-auto">
            <button
              onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
              className="p-2 rounded-xl text-[#6B7280] hover:text-[#1F2937] hover:bg-[#F3F1ED] dark:text-[#9CA3AF] dark:hover:text-[#F3F4F6] dark:hover:bg-[#23272E] transition-colors"
              aria-label="Toggle theme"
            >
              {theme === 'dark' ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4" />}
            </button>
          </div>
        </div>

        <div className="w-full max-w-md mx-auto my-auto py-6">
          <div className="bg-white dark:bg-[#1B1E23] p-6 sm:p-8 rounded-2xl border border-[#E5E7EB] dark:border-[#2F3540] shadow-[0_1px_3px_0_rgba(0,0,0,0.02)]">
            <Outlet />
          </div>
        </div>

        <div className="text-center text-xs text-[#9CA3AF] pt-4">
          © 2026 ChronaNexus. Privacy-first longitudinal medical intelligence.
        </div>
      </div>

      <ToastContainer />
    </div>
  );
};
