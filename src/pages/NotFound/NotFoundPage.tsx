import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/Button';
import { HeartPulse, ArrowLeft, Home } from 'lucide-react';

export const NotFoundPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-6 bg-slate-50 dark:bg-[#0B0F19] text-center space-y-6">
      <div className="w-16 h-16 rounded-3xl bg-blue-100 dark:bg-blue-900/40 text-blue-600 dark:text-blue-400 flex items-center justify-center shadow-xl">
        <HeartPulse className="w-8 h-8 animate-pulse" />
      </div>

      <div className="space-y-2 max-w-md">
        <span className="text-xs font-mono font-bold text-blue-600 dark:text-blue-400 uppercase tracking-widest">
          Error 404 • Endpoint Not Found
        </span>
        <h1 className="text-3xl font-extrabold text-slate-900 dark:text-slate-100">
          Medical Memory Node Missing
        </h1>
        <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
          The requested route or medical record link does not exist within your patient memory graph.
        </p>
      </div>

      <div className="flex items-center space-x-3 pt-2">
        <Button variant="outline" onClick={() => navigate(-1)} leftIcon={<ArrowLeft className="w-4 h-4" />}>
          Go Back
        </Button>
        <Button variant="primary" onClick={() => navigate('/dashboard')} leftIcon={<Home className="w-4 h-4" />}>
          Return to Dashboard
        </Button>
      </div>
    </div>
  );
};
