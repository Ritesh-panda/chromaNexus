import React, { useState } from 'react';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { SummaryCard } from '../../components/cards/SummaryCard';
import { Modal } from '../../components/ui/Modal';
import { useUI } from '../../contexts/UIContext';
import { MOCK_DOCTOR_SUMMARY } from '../../constants/mockData';
import {
  Stethoscope,
  Download,
  Share2,
  Printer,
  CheckCircle2,
  AlertTriangle,
  Pill,
  Activity,
  FileText,
  ShieldCheck,
  User,
  Calendar,
  Lock
} from 'lucide-react';

export const DoctorSummaryPage: React.FC = () => {
  const [summary] = useState(MOCK_DOCTOR_SUMMARY);
  const [isShareModalOpen, setIsShareModalOpen] = useState(false);
  const [shareLink, setShareLink] = useState('');
  const { addToast } = useUI();

  const handlePrintPdf = () => {
    window.print();
  };

  const handleGenerateShare = () => {
    const link = `https://chronanexus.app/physician-view/share_${Math.random().toString(36).substring(7)}`;
    setShareLink(link);
    setIsShareModalOpen(true);
  };

  return (
    <div className="space-y-6 pb-12 print:p-0">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 print:hidden">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <Stethoscope className="w-6 h-6 text-rose-500" /> One-Click Physician Clinical Summary
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Automated 60-second medical history digest formatted specifically for attending physicians.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <Button
            variant="outline"
            size="md"
            onClick={handleGenerateShare}
            leftIcon={<Share2 className="w-4 h-4" />}
          >
            Share Physician Link
          </Button>
          <Button
            variant="primary"
            size="md"
            onClick={handlePrintPdf}
            leftIcon={<Printer className="w-4 h-4" />}
          >
            Download PDF Report
          </Button>
        </div>
      </div>

      {/* Structured Clinical Report Paper Shell */}
      <div className="glass-card p-8 rounded-3xl border border-slate-200 dark:border-slate-800 space-y-6 bg-white dark:bg-[#111726]">
        {/* Physician Report Header */}
        <div className="flex flex-col sm:flex-row justify-between pb-6 border-b border-slate-200 dark:border-slate-800 gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-lg font-black tracking-tight text-slate-900 dark:text-slate-100">ChronaNexus</span>
              <Badge variant="success">HIPAA Certified Digest</Badge>
            </div>
            <h2 className="text-xl font-extrabold text-slate-800 dark:text-slate-100">
              Longitudinal Clinical Summary — {summary.patientName}
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 font-mono">
              Demographics: {summary.gender} • Generated: {new Date(summary.generatedAt).toLocaleString()}
            </p>
          </div>

          <div className="text-right space-y-1 text-xs text-slate-500 dark:text-slate-400">
            <p className="font-semibold text-slate-800 dark:text-slate-200">Primary Care Physician</p>
            <p>Dr. Sarah Jenkins, MD</p>
            <p className="text-emerald-600 font-bold">8 Sources Grounded</p>
          </div>
        </div>

        {/* Executive Clinical Overview Box */}
        <div className="p-4 rounded-2xl bg-blue-50/60 dark:bg-blue-950/30 border border-blue-200/80 dark:border-blue-800/40 space-y-2">
          <span className="text-xs font-bold uppercase tracking-wider text-blue-700 dark:text-blue-400 flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-blue-500" /> Executive Clinical Briefing
          </span>
          <p className="text-xs sm:text-sm text-slate-800 dark:text-slate-200 leading-relaxed font-sans">
            {summary.summaryOverview}
          </p>
        </div>

        {/* 2-Column Clinical Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Active Diseases */}
          <SummaryCard
            title="Active & Chronic Diagnoses"
            icon={<Activity className="w-4 h-4 text-rose-500" />}
            badgeText={`${summary.currentDiseases.length} Active`}
          >
            <div className="space-y-2.5">
              {summary.currentDiseases.map((d) => (
                <div key={d.id} className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-800 text-xs space-y-1">
                  <div className="flex items-center justify-between font-bold text-slate-900 dark:text-slate-100">
                    <span>{d.name}</span>
                    {d.icdCode && <span className="font-mono text-[10px] text-slate-400">ICD: {d.icdCode}</span>}
                  </div>
                  {d.notes && <p className="text-slate-600 dark:text-slate-400">{d.notes}</p>}
                </div>
              ))}
            </div>
          </SummaryCard>

          {/* Active Medications */}
          <SummaryCard
            title="Active Pharmacotherapy"
            icon={<Pill className="w-4 h-4 text-emerald-500" />}
            badgeText={`${summary.activeMedications.length} Prescriptions`}
          >
            <div className="space-y-2.5">
              {summary.activeMedications.map((m) => (
                <div key={m.id} className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-800 text-xs space-y-1">
                  <div className="flex items-center justify-between font-bold text-slate-900 dark:text-slate-100">
                    <span>{m.name} ({m.dosage})</span>
                    <Badge variant="success">{m.status}</Badge>
                  </div>
                  <p className="text-slate-600 dark:text-slate-400">Sig: {m.frequency}</p>
                </div>
              ))}
            </div>
          </SummaryCard>

          {/* Known Allergies */}
          <SummaryCard
            title="Known Allergies & Adverse Reactions"
            icon={<AlertTriangle className="w-4 h-4 text-amber-500" />}
          >
            <div className="space-y-2">
              {summary.knownAllergies.map((allergy, idx) => (
                <div key={idx} className="p-2.5 rounded-xl bg-amber-50/50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900/40 text-xs font-semibold text-amber-800 dark:text-amber-300 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0" />
                  <span>{allergy}</span>
                </div>
              ))}
            </div>
          </SummaryCard>

          {/* Abnormal Lab Findings */}
          <SummaryCard
            title="Abnormal Lab Results & Risk Factors"
            icon={<Activity className="w-4 h-4 text-purple-500" />}
          >
            <div className="space-y-2">
              {summary.abnormalLabs.map((lab) => (
                <div key={lab.id} className="p-2.5 rounded-xl bg-rose-50/50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900/40 text-xs flex items-center justify-between">
                  <span className="font-bold text-slate-800 dark:text-slate-200">{lab.testName}</span>
                  <span className="font-mono font-extrabold text-rose-600 dark:text-rose-400">{lab.value} {lab.unit} (Ref: {lab.referenceRange})</span>
                </div>
              ))}
            </div>
          </SummaryCard>
        </div>

        {/* Timeline Highlights */}
        <div className="space-y-3 pt-2">
          <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <Calendar className="w-4 h-4 text-purple-500" /> Key Longitudinal Chronology
          </h3>
          <div className="space-y-2">
            {summary.timelineHighlights.map((hl, idx) => (
              <div key={idx} className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/40 text-xs text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-800/80 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                <span>{hl}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Share Secure Physician Link Modal */}
      {isShareModalOpen && (
        <Modal
          isOpen={isShareModalOpen}
          onClose={() => setIsShareModalOpen(false)}
          title="Share Physician Summary Link"
          description="Generate a 48-hour password-protected link for consulting physicians."
        >
          <div className="space-y-4 pt-2">
            <div className="p-3 rounded-2xl bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-800/40 text-xs space-y-2">
              <span className="font-bold text-blue-700 dark:text-blue-300 flex items-center gap-1">
                <Lock className="w-4 h-4" /> Time-Bound Encryption Active
              </span>
              <p className="text-slate-600 dark:text-slate-300">
                The link auto-expires in 48 hours. Access can be revoked anytime from Settings.
              </p>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">Secure Share Link</label>
              <input
                type="text"
                readOnly
                value={shareLink}
                className="w-full h-11 px-3 rounded-xl bg-slate-100 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 text-xs font-mono text-slate-800 dark:text-slate-200"
              />
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <Button
                variant="primary"
                onClick={() => {
                  navigator.clipboard.writeText(shareLink);
                  addToast({ type: 'success', title: 'Link Copied to Clipboard!' });
                  setIsShareModalOpen(false);
                }}
              >
                Copy Link
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
