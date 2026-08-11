import React from 'react';
import { Outlet, Link } from 'react-router-dom';
import { HeartPulse, Shield, Sparkles, CheckCircle2 } from 'lucide-react';
import { ToastContainer } from '../ui/Toast';

export const AuthLayout: React.FC = () => {
  return (
    <div className="min-h-screen w-full flex bg-slate-50 dark:bg-[#0B0F19] text-slate-900 dark:text-slate-100 font-sans">
      {/* Left Healthcare Hero Graphic Banner */}
      <div className="hidden lg:flex lg:w-1/2 hero-gradient border-r border-slate-200/80 dark:border-slate-800/80 p-12 flex-col justify-between relative overflow-hidden">
        <div className="flex items-center space-x-3 z-10">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-blue-600 to-emerald-400 flex items-center justify-center text-white font-bold shadow-lg shadow-blue-500/25">
            <HeartPulse className="w-6 h-6 animate-pulse" />
          </div>
          <span className="text-xl font-extrabold tracking-tight text-slate-900 dark:text-slate-100">
            Chrona<span className="text-blue-600 dark:text-blue-400">Nexus</span>
          </span>
        </div>

        {/* Feature Cards Showcase */}
        <div className="my-auto z-10 space-y-6 max-w-lg">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-100 dark:bg-blue-950/80 text-blue-700 dark:text-blue-300 text-xs font-bold border border-blue-200 dark:border-blue-800/50">
            <Sparkles className="w-3.5 h-3.5" /> Longitudinal Medical Memory Engine
          </div>
          <h1 className="text-4xl font-extrabold leading-tight text-slate-900 dark:text-slate-100">
            Transforming Fragmented Records into Unified Clinical Intelligence.
          </h1>
          <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
            ChronaNexus connects years of blood tests, MRI scans, and prescriptions into a continuous, machine-understandable memory with zero privacy compromise.
          </p>

          <div className="space-y-3 pt-2">
            {[
              'End-to-End Encrypted Zero-Trust Vault',
              'Automated Clinical Entity Extraction & Reasoning',
              'Instant 60-Second Physician Summary Reports',
            ].map((feat, idx) => (
              <div key={idx} className="flex items-center space-x-3 text-xs font-semibold text-slate-700 dark:text-slate-200">
                <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                <span>{feat}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="flex items-center justify-between text-xs text-slate-400 z-10 border-t border-slate-200/60 dark:border-slate-800/60 pt-4">
          <span className="flex items-center gap-1.5"><Shield className="w-4 h-4 text-emerald-500" /> HIPAA & GDPR Compliant Architecture</span>
          <span>v1.0 Capstone Edition</span>
        </div>
      </div>

      {/* Right Form Container */}
      <div className="flex-1 flex flex-col justify-between p-6 sm:p-12 md:p-16">
        <div className="flex items-center justify-between lg:hidden">
          <Link to="/" className="flex items-center space-x-2">
            <div className="w-8 h-8 rounded-xl bg-blue-600 flex items-center justify-center text-white font-bold">
              <HeartPulse className="w-5 h-5" />
            </div>
            <span className="text-lg font-bold">ChronaNexus</span>
          </Link>
        </div>

        <div className="w-full max-w-md mx-auto my-auto py-8">
          <Outlet />
        </div>

        <div className="text-center text-xs text-slate-400">
          © 2026 ChronaNexus Inc. Privacy First Medical Intelligence.
        </div>
      </div>

      <ToastContainer />
    </div>
  );
};
