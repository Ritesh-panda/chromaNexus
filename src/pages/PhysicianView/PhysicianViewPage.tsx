import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { summaryService } from '@/services/summary.service';
import type { DoctorSummary } from '@/types';
import {
  Stethoscope,
  Printer,
  CheckCircle2,
  AlertTriangle,
  Pill,
  Activity,
  ShieldCheck,
  Calendar,
  Lock,
  Microscope,
  Info
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';

export const PhysicianViewPage: React.FC = () => {
  const { shareToken } = useParams<{ shareToken: string }>();
  const [summary, setSummary] = useState<DoctorSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    const load = async () => {
      setIsLoading(true);
      try {
        const data = await summaryService.getSharedSummary(shareToken || '');
        if (isMounted) {
          setSummary(data);
          setError(null);
        }
      } catch {
        if (isMounted) {
          setError('Unable to load clinical summary for this token or the link has expired.');
        }
      } finally {
        if (isMounted) setIsLoading(false);
      }
    };
    load();
    return () => {
      isMounted = false;
    };
  }, [shareToken]);

  const handlePrint = () => {
    window.print();
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#FAF8F5] dark:bg-[#121417] flex items-center justify-center p-6">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-[#10B981] border-t-transparent rounded-full animate-spin" />
          <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF]">
            Decentralized Patient Memory Graph â€¢ Loading Verified Physician Digest...
          </p>
        </div>
      </div>
    );
  }

  if (error || !summary) {
    return (
      <div className="min-h-screen bg-[#FAF8F5] dark:bg-[#121417] flex items-center justify-center p-6">
        <div className="max-w-md w-full bg-white dark:bg-[#1B1E23] p-6 rounded-2xl border border-[#E5E7EB] dark:border-[#2F3540] text-center space-y-4">
          <AlertTriangle className="w-10 h-10 text-rose-500 mx-auto" />
          <h2 className="text-base font-semibold text-[#1F2937] dark:text-[#F3F4F6]">
            Physician Link Expired or Invalid
          </h2>
          <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF]">
            {error || 'This clinical share link is no longer valid or has reached its security expiration window.'}
          </p>
          <Link
            to="/login"
            className="inline-block px-4 py-2 rounded-xl text-xs font-semibold bg-[#10B981] text-white hover:bg-[#059669] transition-all"
          >
            Access ChronaNexus Portal
          </Link>
        </div>
      </div>
    );
  }

  const activeDiseases = summary.currentDiseases || [];
  const activeMeds = summary.activeMedications || [];
  const abnormalLabs = summary.abnormalLabs || [];
  const questions = summary.doctorQuestions || [];

  return (
    <div className="min-h-screen bg-[#FAF8F5] dark:bg-[#121417] text-[#1F2937] dark:text-[#F3F4F6] font-sans">
      {/* Top Navigation Bar */}
      <header className="sticky top-0 z-20 bg-white/95 dark:bg-[#1B1E23]/95 backdrop-blur-md border-b border-[#E5E7EB] dark:border-[#2F3540] print:hidden">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-7 h-7 rounded-lg bg-[#10B981]/15 text-[#10B981] flex items-center justify-center font-bold text-sm">
              <Stethoscope className="w-4 h-4" />
            </div>
            <div>
              <span className="text-xs font-bold tracking-tight text-[#1F2937] dark:text-[#F3F4F6]">
                ChronaNexus
              </span>
              <span className="ml-2 text-[10px] font-medium text-[#10B981] bg-[#10B981]/10 px-2 py-0.5 rounded-full border border-[#10B981]/30">
                Physician Read-Only Portal
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="primary"
              size="sm"
              onClick={handlePrint}
              leftIcon={<Printer className="w-3.5 h-3.5" />}
            >
              Print / Save PDF
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content Container */}
      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-6 space-y-6 print:p-0 print:m-0 print:max-w-none">
        {/* Patient Header Card */}
        <div className="bg-white dark:bg-[#1B1E23] p-5 sm:p-6 rounded-2xl border border-[#E5E7EB] dark:border-[#2F3540] shadow-sm space-y-4">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-[#E5E7EB]/80 dark:border-[#2F3540]">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-bold text-[#10B981] uppercase tracking-wider">
                  Verified Longitudinal Digest
                </span>
                <span className="text-xs text-[#9CA3AF]">â€¢</span>
                <Badge variant="success" className="gap-1 text-[11px]">
                  <CheckCircle2 className="w-3 h-3" /> Source Verified
                </Badge>
              </div>
              <h1 className="text-xl sm:text-2xl font-bold text-[#1F2937] dark:text-[#F3F4F6]">
                Clinical Summary â€” {summary.patientName.toUpperCase()}
              </h1>
              <div className="flex flex-wrap items-center gap-3 text-xs text-[#6B7280] dark:text-[#9CA3AF] pt-1">
                <span>Age: <strong className="text-[#1F2937] dark:text-[#F3F4F6]">{summary.age ? `${summary.age} yrs` : 'Recorded'}</strong></span>
                <span>â€¢</span>
                <span>Blood: <strong className="text-[#1F2937] dark:text-[#F3F4F6]">{summary.bloodGroup || 'Not recorded'}</strong></span>
                <span>â€¢</span>
                <span>Primary MD: <strong className="text-[#1F2937] dark:text-[#F3F4F6]">{summary.primaryCarePhysician || 'Not assigned'}</strong></span>
              </div>
            </div>

            <div className="text-left md:text-right shrink-0">
              <span className="text-[11px] font-mono text-[#9CA3AF] block">
                Issued: {new Date(summary.generatedAt).toLocaleDateString()}
              </span>
              <span className="text-[11px] text-[#10B981] font-medium block mt-0.5">
                Grounding: Active Memory Graph
              </span>
            </div>
          </div>

          {/* Clinician Notice */}
          <div className="p-3 rounded-xl bg-blue-50/60 dark:bg-blue-950/20 border border-blue-200/80 dark:border-blue-900/30 text-xs text-blue-800 dark:text-blue-300 flex items-start gap-2.5">
            <Info className="w-4 h-4 text-blue-600 dark:text-blue-400 shrink-0 mt-0.5" />
            <p className="leading-relaxed">
              {summary.clinicianNotice ||
                'NOTICE TO CLINICIANS: This clinical digest was deterministically compiled from indexed medical documents on ChronaNexus. It provides longitudinal reference data and does not constitute an automated diagnosis, treatment recommendation, or prescribing directive. All findings must be clinically verified with original primary sources.'}
            </p>
          </div>
        </div>

        {/* Executive Clinical Briefing */}
        <div className="bg-white dark:bg-[#1B1E23] p-5 sm:p-6 rounded-2xl border border-[#E5E7EB] dark:border-[#2F3540] shadow-sm space-y-2.5">
          <h3 className="text-sm font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-[#10B981]" /> Executive Clinical Briefing
          </h3>
          <p className="text-xs text-[#4B5563] dark:text-[#D1D5DB] leading-relaxed">
            {summary.summaryOverview}
          </p>
        </div>

        {/* 3-Column Core Clinical Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {/* Active Diagnoses */}
          <div className="bg-white dark:bg-[#1B1E23] p-5 rounded-2xl border border-[#E5E7EB] dark:border-[#2F3540] shadow-sm space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-1.5">
                <Activity className="w-3.5 h-3.5 text-rose-500" /> Active Diagnoses
              </h4>
              <Badge variant="secondary">{activeDiseases.length}</Badge>
            </div>
            {activeDiseases.length > 0 ? (
              <div className="space-y-2">
                {activeDiseases.map((d: any, idx: number) => {
                  const dName = typeof d === 'string' ? d : d.name;
                  const icd = typeof d === 'object' ? d.icdCode : null;
                  const date = typeof d === 'object' ? d.diagnosedDate : null;
                  return (
                    <div
                      key={idx}
                      className="p-3 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/50 border border-[#E5E7EB] dark:border-[#2F3540] space-y-1"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-[#1F2937] dark:text-[#F3F4F6]">
                          {dName}
                        </span>
                        {icd && (
                          <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-rose-50 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400">
                            {icd}
                          </span>
                        )}
                      </div>
                      {date && (
                        <div className="text-[10px] text-[#6B7280] dark:text-[#9CA3AF]">
                          Diagnosed: {date}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="py-6 text-center text-xs text-[#9CA3AF] italic">
                No active diagnoses recorded.
              </div>
            )}
          </div>

          {/* Active Pharmacotherapy */}
          <div className="bg-white dark:bg-[#1B1E23] p-5 rounded-2xl border border-[#E5E7EB] dark:border-[#2F3540] shadow-sm space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-1.5">
                <Pill className="w-3.5 h-3.5 text-[#10B981]" /> Active Pharmacotherapy
              </h4>
              <Badge variant="success">{activeMeds.length}</Badge>
            </div>
            {activeMeds.length > 0 ? (
              <div className="space-y-2">
                {activeMeds.map((med: any, idx: number) => {
                  const medName = typeof med === 'string' ? med : med.name;
                  const dosage = typeof med === 'object' ? med.dosage : null;
                  const freq = typeof med === 'object' ? med.frequency : null;
                  return (
                    <div
                      key={idx}
                      className="p-3 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/50 border border-[#E5E7EB] dark:border-[#2F3540] space-y-1"
                    >
                      <span className="text-xs font-semibold text-[#1F2937] dark:text-[#F3F4F6] block">
                        {medName}
                      </span>
                      {dosage && (
                        <div className="text-[11px] font-mono text-[#10B981] font-semibold">
                          {dosage}
                        </div>
                      )}
                      {freq && (
                        <div className="text-[10px] text-[#6B7280] dark:text-[#9CA3AF]">
                          {freq}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="py-6 text-center text-xs text-[#9CA3AF] italic">
                No active medications recorded.
              </div>
            )}
          </div>

          {/* Known Allergies */}
          <div className="bg-white dark:bg-[#1B1E23] p-5 rounded-2xl border border-[#E5E7EB] dark:border-[#2F3540] shadow-sm space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-blue-500" /> Allergies & Reactions
              </h4>
              <Badge variant="secondary">{(summary.knownAllergies || []).length}</Badge>
            </div>
            {(summary.knownAllergies || []).length > 0 ? (
              <div className="space-y-2">
                {summary.knownAllergies.map((allergy: any, idx: number) => {
                  const substance = typeof allergy === 'string' ? allergy : allergy.substance;
                  return (
                    <div
                      key={idx}
                      className="p-3 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/50 border border-[#E5E7EB] dark:border-[#2F3540] space-y-1"
                    >
                      <span className="text-xs font-semibold text-[#1F2937] dark:text-[#F3F4F6] block">
                        {substance}
                      </span>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="py-6 text-center text-xs text-[#9CA3AF] italic">
                No adverse drug reactions or allergies recorded (NKDA).
              </div>
            )}
          </div>
        </div>

        {/* Flagged Abnormal Laboratory Analytes */}
        <div className="bg-white dark:bg-[#1B1E23] p-5 sm:p-6 rounded-2xl border border-[#E5E7EB] dark:border-[#2F3540] shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-2">
                <Microscope className="w-4 h-4 text-[#10B981]" /> Flagged Laboratory Analytes
              </h3>
              <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF] mt-0.5">
                Recent laboratory analytes measured outside standard clinical reference intervals.
              </p>
            </div>
            <Badge variant={abnormalLabs.length > 0 ? 'warning' : 'success'}>
              {abnormalLabs.length} Flagged
            </Badge>
          </div>

          {abnormalLabs.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
              {abnormalLabs.map((lab: any, idx: number) => {
                const testName = lab.testName || lab.name || 'Lab Test';
                const val = lab.value !== undefined ? lab.value : '--';
                const unit = lab.unit || '';
                const refRange = lab.referenceRange || lab.standardRange || 'Standard Range';
                const statusLabel = lab.status || 'abnormal';
                return (
                  <div
                    key={idx}
                    className="p-3.5 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/50 border border-[#E5E7EB] dark:border-[#2F3540] space-y-1.5"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-[#1F2937] dark:text-[#F3F4F6] truncate max-w-[140px]">
                        {testName}
                      </span>
                      <span className="px-1.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-rose-50 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400">
                        {statusLabel}
                      </span>
                    </div>
                    <div className="flex items-baseline gap-1.5">
                      <span className="text-lg font-bold font-mono text-[#1F2937] dark:text-[#F3F4F6]">
                        {val}
                      </span>
                      <span className="text-xs text-[#6B7280] dark:text-[#9CA3AF]">{unit}</span>
                    </div>
                    <div className="text-[10px] text-[#6B7280] dark:text-[#9CA3AF]">
                      Reference: {refRange}
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="py-6 text-center text-xs text-[#9CA3AF] italic">
              All indexed laboratory analytes are currently within standard physiological ranges.
            </div>
          )}
        </div>

        {/* Appointment Discussion Topics */}
        {questions.length > 0 && (
          <div className="bg-white dark:bg-[#1B1E23] p-5 sm:p-6 rounded-2xl border border-[#E5E7EB] dark:border-[#2F3540] shadow-sm space-y-3">
            <h3 className="text-sm font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-2">
              <Calendar className="w-4 h-4 text-[#10B981]" /> Patient-Prepared Appointment Questions
            </h3>
            <div className="space-y-2">
              {questions.map((q, idx) => (
                <div
                  key={idx}
                  className="flex items-start gap-2.5 p-3 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/50 border border-[#E5E7EB] dark:border-[#2F3540] text-xs"
                >
                  <span className="w-5 h-5 rounded-full bg-[#10B981]/15 text-[#10B981] font-bold text-[10px] flex items-center justify-center shrink-0 mt-0.5">
                    {idx + 1}
                  </span>
                  <span className="text-[#374151] dark:text-[#D1D5DB] leading-relaxed">{q}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
};
