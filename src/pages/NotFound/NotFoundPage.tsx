import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/Button';
import { ArrowLeft, Home, Activity } from 'lucide-react';

export const NotFoundPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-6 bg-[#FAF8F5] dark:bg-[#121417] text-center space-y-5 font-sans">
      <div className="w-12 h-12 rounded-2xl bg-[#ECFDF5] dark:bg-emerald-950/40 border border-emerald-200/60 dark:border-emerald-800/40 text-[#10B981] flex items-center justify-center shadow-sm">
        <Activity className="w-6 h-6" />
      </div>

      <div className="space-y-1.5 max-w-sm">
        <span className="text-[11px] font-mono font-medium text-[#10B981] dark:text-emerald-400 uppercase tracking-wider">
          Error 404 • Page Not Found
        </span>
        <h1 className="text-2xl font-semibold text-[#1F2937] dark:text-[#F3F4F6] tracking-tight">
          Page Not Available
        </h1>
        <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF] leading-relaxed">
          The requested route or medical record link does not exist within your patient memory graph.
        </p>
      </div>

      <div className="flex items-center space-x-2.5 pt-2">
        <Button variant="secondary" onClick={() => navigate(-1)} leftIcon={<ArrowLeft className="w-4 h-4" />}>
          Go Back
        </Button>
        <Button variant="primary" onClick={() => navigate('/dashboard')} leftIcon={<Home className="w-4 h-4" />}>
          Return to Dashboard
        </Button>
      </div>
    </div>
  );
};
