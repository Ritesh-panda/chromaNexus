import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { ReportCard } from '@/components/cards/ReportCard';
import { MedicalCard } from '@/components/cards/MedicalCard';
import { TimelineCard } from '@/components/cards/TimelineCard';
import { VitalsTrendChart } from '@/components/charts/VitalsTrendChart';
import { useUI } from '@/contexts/UIContext';
import {
  MOCK_REPORTS,
  MOCK_DISEASES,
  MOCK_MEDICATIONS,
  MOCK_TIMELINE_EVENTS,
  MOCK_CHAT_MESSAGES
} from '@/constants/mockData';
import {
  FileText,
  Activity,
  Pill,
  GitCommit,
  Bot,
  Upload,
  Stethoscope,
  ArrowRight,
  Sparkles,
  TrendingUp,
  Zap
} from 'lucide-react';
import { motion } from 'framer-motion';

export const DashboardPage: React.FC = () => {
  const { setUploadModalOpen, setSearchOpen } = useUI();
  const navigate = useNavigate();

  const activeDiseases = MOCK_DISEASES.filter(d => d.status === 'active' || d.status === 'chronic');
  const activeMeds = MOCK_MEDICATIONS.filter(m => m.status === 'active');
  const recentReports = MOCK_REPORTS.slice(0, 3);
  const recentTimeline = MOCK_TIMELINE_EVENTS.slice(0, 3);

  return (
    <div className="space-y-8 pb-12">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 glass-card p-6 rounded-3xl border border-blue-200/60 dark:border-blue-900/40 hero-gradient">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wider text-blue-600 dark:text-blue-400">
              Longitudinal Intelligence Active
            </span>
            <Badge variant="success">Patient Memory In-Sync</Badge>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-slate-100">
            Welcome back, Alex Vance
          </h1>
          <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400">
            Your patient memory contains <strong className="text-slate-800 dark:text-slate-200">{MOCK_REPORTS.length} medical documents</strong> across 7 years (2019 - 2026).
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="md"
            onClick={() => navigate('/chat')}
            leftIcon={<Bot className="w-4 h-4 text-emerald-500" />}
          >
            Ask AI Assistant
          </Button>
          <Button
            variant="primary"
            size="md"
            onClick={() => setUploadModalOpen(true)}
            leftIcon={<Upload className="w-4 h-4" />}
          >
            Upload Record
          </Button>
        </div>
      </div>

      {/* Overview KPI Grid Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          {
            title: 'Medical Documents',
            value: MOCK_REPORTS.length.toString(),
            subtitle: '100% Extracted & Verified',
            icon: <FileText className="w-5 h-5 text-blue-500" />,
            badge: 'Vault',
          },
          {
            title: 'Active Diagnoses',
            value: activeDiseases.length.toString(),
            subtitle: 'Type 2 Diabetes & Hypertension',
            icon: <Activity className="w-5 h-5 text-rose-500" />,
            badge: 'Chronic',
          },
          {
            title: 'Ongoing Medications',
            value: activeMeds.length.toString(),
            subtitle: 'Metformin, Lisinopril, Statin',
            icon: <Pill className="w-5 h-5 text-emerald-500" />,
            badge: 'Rx',
          },
          {
            title: 'Timeline Milestones',
            value: MOCK_TIMELINE_EVENTS.length.toString(),
            subtitle: 'Spans 2019 to Present',
            icon: <GitCommit className="w-5 h-5 text-purple-500" />,
            badge: 'Timeline',
          },
        ].map((kpi, idx) => (
          <motion.div
            key={idx}
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: idx * 0.05 }}
          >
            <Card hoverEffect className="p-5 border-slate-200 dark:border-slate-800 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">{kpi.title}</span>
                <div className="p-2 rounded-xl bg-slate-100 dark:bg-slate-800/80">{kpi.icon}</div>
              </div>
              <p className="text-3xl font-extrabold text-slate-900 dark:text-slate-100">{kpi.value}</p>
              <p className="text-xs text-slate-500 dark:text-slate-400 flex items-center justify-between">
                <span>{kpi.subtitle}</span>
                <Badge variant="secondary" className="text-[10px]">{kpi.badge}</Badge>
              </p>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Main Charts & Quick Actions Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Vital Trends Chart */}
        <Card className="lg:col-span-2 p-6 border-slate-200 dark:border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-blue-500" /> Longitudinal Vital & Lab Trends
              </CardTitle>
              <CardDescription>HbA1c (%) vs Total Cholesterol (mg/dL) trajectory over 5 years</CardDescription>
            </div>
            <Badge variant="success">Normal HbA1c Target Reached</Badge>
          </div>
          <VitalsTrendChart />
        </Card>

        {/* Quick Actions & AI Conversation Preview */}
        <Card className="p-6 border-slate-200 dark:border-slate-800 space-y-5 flex flex-col justify-between">
          <div className="space-y-3">
            <CardTitle className="flex items-center gap-2">
              <Zap className="w-5 h-5 text-amber-500" /> Quick Clinical Actions
            </CardTitle>
            <CardDescription>Perform actions on your patient memory</CardDescription>

            <div className="space-y-2 pt-2">
              <button
                onClick={() => navigate('/doctor-summary')}
                className="w-full flex items-center justify-between p-3.5 rounded-2xl bg-blue-50 dark:bg-blue-950/40 hover:bg-blue-100 border border-blue-200 dark:border-blue-800/50 text-blue-700 dark:text-blue-300 text-xs font-bold transition-all"
              >
                <span className="flex items-center gap-2">
                  <Stethoscope className="w-4 h-4" /> Doctor Summary Generator
                </span>
                <ArrowRight className="w-4 h-4" />
              </button>

              <button
                onClick={() => setUploadModalOpen(true)}
                className="w-full flex items-center justify-between p-3.5 rounded-2xl bg-slate-100 dark:bg-slate-800/60 hover:bg-slate-200 text-slate-800 dark:text-slate-200 text-xs font-bold transition-all"
              >
                <span className="flex items-center gap-2">
                  <Upload className="w-4 h-4 text-emerald-500" /> Upload New Medical PDF
                </span>
                <ArrowRight className="w-4 h-4 text-slate-400" />
              </button>

              <button
                onClick={() => setSearchOpen(true)}
                className="w-full flex items-center justify-between p-3.5 rounded-2xl bg-slate-100 dark:bg-slate-800/60 hover:bg-slate-200 text-slate-800 dark:text-slate-200 text-xs font-bold transition-all"
              >
                <span className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-purple-500" /> Global Memory Search
                </span>
                <kbd className="px-2 py-0.5 text-[10px] font-mono bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded">⌘K</kbd>
              </button>
            </div>
          </div>

          <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 space-y-2">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1">
              <Bot className="w-3.5 h-3.5 text-blue-500" /> Recent AI Query
            </span>
            <p className="text-xs text-slate-700 dark:text-slate-300 italic">
              "{MOCK_CHAT_MESSAGES[0]?.text}"
            </p>
            <Button variant="ghost" size="sm" onClick={() => navigate('/chat')} className="p-0 h-auto text-xs text-blue-600 font-bold">
              Continue Conversation ➔
            </Button>
          </div>
        </Card>
      </div>

      {/* Grid Row: Active Diseases & Medications */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Active Medical Conditions */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
              <Activity className="w-5 h-5 text-rose-500" /> Active Medical Conditions
            </h3>
            <Button variant="ghost" size="sm" onClick={() => navigate('/timeline')}>
              View Timeline
            </Button>
          </div>
          <div className="space-y-3">
            {activeDiseases.map((d) => (
              <MedicalCard key={d.id} item={d} type="disease" />
            ))}
          </div>
        </div>

        {/* Current Active Medications */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
              <Pill className="w-5 h-5 text-emerald-500" /> Current Active Medications
            </h3>
            <Button variant="ghost" size="sm" onClick={() => navigate('/vault')}>
              View Prescriptions
            </Button>
          </div>
          <div className="space-y-3">
            {activeMeds.map((m) => (
              <MedicalCard key={m.id} item={m} type="medication" />
            ))}
          </div>
        </div>
      </div>

      {/* Grid Row: Recent Uploads & Timeline Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Uploaded Reports */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
              <FileText className="w-5 h-5 text-blue-500" /> Recent Uploaded Reports
            </h3>
            <Button variant="ghost" size="sm" onClick={() => navigate('/reports')}>
              View All ({MOCK_REPORTS.length})
            </Button>
          </div>
          <div className="space-y-3">
            {recentReports.map((r) => (
              <ReportCard key={r.id} report={r} onSelect={() => navigate('/reports')} />
            ))}
          </div>
        </div>

        {/* Recent Timeline Activity */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
              <GitCommit className="w-5 h-5 text-purple-500" /> Longitudinal Timeline Feed
            </h3>
            <Button variant="ghost" size="sm" onClick={() => navigate('/timeline')}>
              Full Interactive Timeline
            </Button>
          </div>
          <div className="space-y-3">
            {recentTimeline.map((e) => (
              <TimelineCard key={e.id} event={e} onSelect={() => navigate('/timeline')} />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
