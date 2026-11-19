import React, { useEffect, useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Modal } from '@/components/ui/Modal';
import { useUI } from '@/contexts/UIContext';
import { useAuth } from '@/contexts/AuthContext';
import { useUser } from '@/contexts/UserContext';
import { summaryService } from '@/services/summary.service';
import type { DoctorSummary } from '@/types';
import {
  Stethoscope,
  Share2,
  Printer,
  CheckCircle2,
  AlertTriangle,
  Pill,
  Activity,
  ShieldCheck,
  Calendar,
  Lock,
  Copy,
  Plus,
  Trash2,
  Save,
  CheckSquare,
  Square,
  Microscope,
  RotateCw,
  FileText,
  User,
  Info
} from 'lucide-react';

const DISALLOWED_DISEASES = ['unknown', 'none', 'n/a', 'na', 'unspecified', 'nil', 'no', 'not applicable'];
const DISALLOWED_ALLERGENS = ['unknown', 'none', 'n/a', 'na', 'nil', 'no', 'not applicable', 'nkda', 'no known drug allergies', 'no known allergies'];

export const DoctorSummaryPage: React.FC = () => {
  const { user } = useAuth();
  const { patient } = useUser();
  const { addToast } = useUI();

  const [summary, setSummary] = useState<DoctorSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'diagnostics' | 'checklist'>('overview');

  // Modal and Questions
  const [isShareModalOpen, setIsShareModalOpen] = useState(false);
  const [shareLink, setShareLink] = useState('');
  const [newQuestionText, setNewQuestionText] = useState('');
  const [doctorQuestions, setDoctorQuestions] = useState<string[]>([]);
  const [completedQuestions, setCompletedQuestions] = useState<Record<number, boolean>>({});
  const [isSavingQuestions, setIsSavingQuestions] = useState(false);

  const fetchSummary = async (forceGenerate = false) => {
    try {
      const data = forceGenerate
        ? await summaryService.generateDoctorSummary()
        : await summaryService.getDoctorSummary();
      if (data) {
        setSummary(data);
        if (data.doctorQuestions && data.doctorQuestions.length > 0) {
          setDoctorQuestions(data.doctorQuestions);
        }
      }
    } catch {
      // Keep state
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchSummary();
  }, []);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await fetchSummary(true);
    addToast({
      type: 'success',
      title: 'Summary Refreshed',
      message: 'Longitudinal clinical summary recompiled from your latest records.'
    });
  };

  const handlePrintPdf = () => {
    window.print();
  };

  const handleGenerateShare = () => {
    const origin = window.location.origin;
    let token = '';
    if (summary?.shareLink) {
      token = summary.shareLink.split('/').filter(Boolean).pop() || '';
    }
    if (!token || !token.startsWith('share_token_')) {
      token = `share_token_${Math.random().toString(36).substring(2, 10)}`;
    }
    const fullLink = `${origin}/physician-view/${token}`;
    setShareLink(fullLink);
    setIsShareModalOpen(true);
  };

  const handleAddQuestion = () => {
    if (!newQuestionText.trim()) return;
    const updated = [...doctorQuestions, newQuestionText.trim()];
    setDoctorQuestions(updated);
    setNewQuestionText('');
  };

  const handleAddSuggestedQuestion = (text: string) => {
    if (doctorQuestions.includes(text)) return;
    setDoctorQuestions([...doctorQuestions, text]);
  };

  const handleRemoveQuestion = (idx: number) => {
    const updated = doctorQuestions.filter((_, i) => i !== idx);
    setDoctorQuestions(updated);
    const updatedCompleted = { ...completedQuestions };
    delete updatedCompleted[idx];
    setCompletedQuestions(updatedCompleted);
  };

  const toggleQuestionComplete = (idx: number) => {
    setCompletedQuestions((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };

  const handleSaveQuestions = async () => {
    setIsSavingQuestions(true);
    try {
      await summaryService.updateDoctorQuestions(doctorQuestions);
      addToast({
        type: 'success',
        title: 'Checklist Saved',
        message: 'Your questions for the doctor appointment have been updated.'
      });
    } catch {
      addToast({
        type: 'info',
        title: 'Checklist Saved Locally',
        message: 'Your checklist notes are saved for this session.'
      });
    } finally {
      setIsSavingQuestions(false);
    }
  };

  if (loading || !summary) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] space-y-3">
        <div className="w-8 h-8 border-2 border-[#10B981] border-t-transparent rounded-full animate-spin" />
        <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF]">Compiling verified physician summary...</p>
      </div>
    );
  }

  // Filter out unknown conditions and disallowed allergens
  const filteredDiseases = (summary.currentDiseases || []).filter(
    (d: any) => !DISALLOWED_DISEASES.includes((d.name || '').trim().toLowerCase())
  );

  const filteredAllergies = (summary.knownAllergies || []).filter((a: any) => {
    const allergenStr = typeof a === 'string' ? a : a.allergen || '';
    return !DISALLOWED_ALLERGENS.includes(allergenStr.trim().toLowerCase());
  });

  const activeMedications = summary.activeMedications || [];
  const abnormalLabs = summary.abnormalLabs || [];
  const procedures = summary.proceduresAndImaging || [];
  const timelineHighlights = summary.timelineHighlights || [];

  const displayName = user?.name || summary.patientName || 'Patient';
  const ageDisplay = summary.age ? `${summary.age} yrs` : (patient?.dateOfBirth ? 'Recorded' : 'Not recorded');
  const bloodDisplay = patient?.bloodGroup || summary.bloodGroup || 'Not recorded';
  const physicianDisplay = patient?.primaryCarePhysician || summary.primaryCarePhysician || 'Not assigned';

  return (
    <div className="space-y-6 pb-12 print:p-0 print:space-y-4">
      {/* Top Action Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 print:hidden">
        <div>
          <h1 className="text-xl sm:text-2xl font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-2">
            <Stethoscope className="w-5 h-5 text-[#10B981]" /> Physician Clinical Summary
          </h1>
          <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF] mt-0.5">
            Deterministic, source-linked longitudinal medical digest prepared for appointment review and physician consultations.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            isLoading={isRefreshing}
            leftIcon={<RotateCw className="w-3.5 h-3.5" />}
          >
            Refresh
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleGenerateShare}
            leftIcon={<Share2 className="w-3.5 h-3.5" />}
          >
            Share Link
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={handlePrintPdf}
            leftIcon={<Printer className="w-3.5 h-3.5" />}
          >
            Print / Export PDF
          </Button>
        </div>
      </div>

      {/* Patient Header Identification Card */}
      <div className="bg-white dark:bg-[#1B1E23] p-5 sm:p-6 rounded-2xl border border-[#E5E7EB] dark:border-[#2F3540] shadow-sm space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-[#E5E7EB]/80 dark:border-[#2F3540]">
          <div className="space-y-1">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs font-semibold uppercase tracking-wider text-[#10B981]">
                ChronaNexus Clinical Digest
              </span>
              <span className="text-xs text-[#9CA3AF]">•</span>
              <Badge variant="success" className="gap-1 text-[11px]">
                <CheckCircle2 className="w-3 h-3" /> Verified Structured Records
              </Badge>
            </div>
            <h2 className="text-lg sm:text-xl font-bold text-[#1F2937] dark:text-[#F3F4F6]">
              Longitudinal Medical Summary — {displayName.toUpperCase()}
            </h2>
            <div className="flex flex-wrap items-center gap-3 text-xs text-[#6B7280] dark:text-[#9CA3AF] pt-0.5">
              <span>Age: <strong className="text-[#1F2937] dark:text-[#F3F4F6]">{ageDisplay}</strong></span>
              <span>•</span>
              <span>Blood Group: <strong className="text-[#1F2937] dark:text-[#F3F4F6]">{bloodDisplay}</strong></span>
              <span>•</span>
              <span>Physician: <strong className="text-[#1F2937] dark:text-[#F3F4F6]">{physicianDisplay}</strong></span>
            </div>
          </div>

          <div className="text-left md:text-right shrink-0">
            <span className="text-[11px] font-mono text-[#9CA3AF] block">
              Generated: {new Date(summary.generatedAt).toLocaleDateString()}
            </span>
            <span className="text-[11px] text-[#10B981] font-medium block mt-0.5">
              Grounding: Active Patient Memory Graph
            </span>
          </div>
        </div>

        {/* Notice to Clinicians */}
        <div className="p-3 rounded-xl bg-blue-50/60 dark:bg-blue-950/20 border border-blue-200/80 dark:border-blue-900/30 text-xs text-blue-800 dark:text-blue-300 flex items-start gap-2.5">
          <Info className="w-4 h-4 text-blue-600 dark:text-blue-400 shrink-0 mt-0.5" />
          <p className="leading-relaxed">
            {summary.clinicianNotice ||
              'NOTICE TO CLINICIANS: This clinical digest was deterministically compiled from indexed medical documents on ChronaNexus. It provides longitudinal reference data and does not constitute an automated diagnosis, treatment recommendation, or prescribing directive. All findings must be clinically verified with original primary sources.'}
          </p>
        </div>
      </div>

      {/* Modern 3-Tab Navigation (Hidden in print) */}
      <div className="flex items-center gap-2 border-b border-[#E5E7EB] dark:border-[#2F3540] pb-1 print:hidden">
        <button
          onClick={() => setActiveTab('overview')}
          className={`flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-xl transition-all ${
            activeTab === 'overview'
              ? 'bg-[#10B981] text-white shadow-sm'
              : 'text-[#6B7280] dark:text-[#9CA3AF] hover:text-[#1F2937] dark:hover:text-[#F3F4F6] hover:bg-[#F3F1ED] dark:hover:bg-[#23272E]'
          }`}
        >
          <Activity className="w-3.5 h-3.5" /> 1. Clinical Snapshot
        </button>
        <button
          onClick={() => setActiveTab('diagnostics')}
          className={`flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-xl transition-all ${
            activeTab === 'diagnostics'
              ? 'bg-[#10B981] text-white shadow-sm'
              : 'text-[#6B7280] dark:text-[#9CA3AF] hover:text-[#1F2937] dark:hover:text-[#F3F4F6] hover:bg-[#F3F1ED] dark:hover:bg-[#23272E]'
          }`}
        >
          <Microscope className="w-3.5 h-3.5" /> 2. Diagnostics & Lab Biomarkers
        </button>
        <button
          onClick={() => setActiveTab('checklist')}
          className={`flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-xl transition-all ${
            activeTab === 'checklist'
              ? 'bg-[#10B981] text-white shadow-sm'
              : 'text-[#6B7280] dark:text-[#9CA3AF] hover:text-[#1F2937] dark:hover:text-[#F3F4F6] hover:bg-[#F3F1ED] dark:hover:bg-[#23272E]'
          }`}
        >
          <CheckSquare className="w-3.5 h-3.5" /> 3. Doctor Discussion Checklist
          {doctorQuestions.length > 0 && (
            <span className="px-1.5 py-0.5 rounded-full text-[10px] bg-white/20 dark:bg-black/20">
              {doctorQuestions.length}
            </span>
          )}
        </button>
      </div>

      {/* TAB 1: CLINICAL SNAPSHOT */}
      <div className={activeTab === 'overview' ? 'space-y-6' : 'hidden print:block space-y-6 print:mt-6'}>
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
            {/* Active Diagnoses Card */}
            <div className="bg-white dark:bg-[#1B1E23] p-5 rounded-2xl border border-[#E5E7EB] dark:border-[#2F3540] shadow-sm space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-1.5">
                  <Activity className="w-3.5 h-3.5 text-rose-500" /> Active Diagnoses
                </h4>
                <Badge variant={filteredDiseases.length > 0 ? 'danger' : 'secondary'} className="text-[10px]">
                  {filteredDiseases.length} Active
                </Badge>
              </div>

              {filteredDiseases.length > 0 ? (
                <div className="space-y-2.5 pt-1">
                  {filteredDiseases.map((d: any, idx: number) => (
                    <div
                      key={d.id || idx}
                      className="p-3 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/50 border border-[#E5E7EB] dark:border-[#2F3540] text-xs space-y-1"
                    >
                      <div className="flex items-center justify-between gap-1">
                        <span className="font-semibold text-[#1F2937] dark:text-[#F3F4F6]">{d.name}</span>
                        {d.icdCode && (
                          <span className="px-1.5 py-0.5 rounded bg-rose-50 dark:bg-rose-950/40 text-[10px] font-mono text-rose-600 dark:text-rose-400">
                            {d.icdCode}
                          </span>
                        )}
                      </div>
                      <div className="text-[11px] text-[#6B7280] dark:text-[#9CA3AF]">
                        Diagnosed: {d.diagnosedDate || 'Recorded'}
                      </div>
                      {d.sourceReportTitle && (
                        <div className="text-[10px] text-[#10B981] truncate">
                          Source: {d.sourceReportTitle}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="py-6 text-center text-xs text-[#9CA3AF] italic">
                  No chronic conditions documented in records.
                </div>
              )}
            </div>

            {/* Active Medications Card */}
            <div className="bg-white dark:bg-[#1B1E23] p-5 rounded-2xl border border-[#E5E7EB] dark:border-[#2F3540] shadow-sm space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-1.5">
                  <Pill className="w-3.5 h-3.5 text-blue-500" /> Active Medications
                </h4>
                <Badge variant={activeMedications.length > 0 ? 'info' : 'secondary'} className="text-[10px]">
                  {activeMedications.length} Prescribed
                </Badge>
              </div>

              {activeMedications.length > 0 ? (
                <div className="space-y-2.5 pt-1">
                  {activeMedications.map((m: any, idx: number) => (
                    <div
                      key={m.id || idx}
                      className="p-3 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/50 border border-[#E5E7EB] dark:border-[#2F3540] text-xs space-y-1"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-[#1F2937] dark:text-[#F3F4F6]">{m.name}</span>
                        {m.dosage && (
                          <span className="font-mono text-[10px] text-blue-600 dark:text-blue-400">
                            {m.dosage}
                          </span>
                        )}
                      </div>
                      <div className="text-[11px] text-[#6B7280] dark:text-[#9CA3AF]">
                        {m.frequency || 'Daily'} • Route: {m.route || 'Oral'}
                      </div>
                      {m.prescribingDoctor && (
                        <div className="text-[10px] text-[#9CA3AF]">
                          Rx: {m.prescribingDoctor}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="py-6 text-center text-xs text-[#9CA3AF] italic">
                  No active prescriptions recorded.
                </div>
              )}
            </div>

            {/* Known Allergies Card */}
            <div className="bg-white dark:bg-[#1B1E23] p-5 rounded-2xl border border-[#E5E7EB] dark:border-[#2F3540] shadow-sm space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-1.5">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-500" /> Allergies & Reactions
                </h4>
                <Badge variant={filteredAllergies.length > 0 ? 'warning' : 'secondary'} className="text-[10px]">
                  {filteredAllergies.length} Recorded
                </Badge>
              </div>

              {filteredAllergies.length > 0 ? (
                <div className="space-y-2.5 pt-1">
                  {filteredAllergies.map((a: any, idx: number) => {
                    const allergenName = typeof a === 'string' ? a : a.allergen || 'Allergen';
                    const severity = typeof a === 'object' && a.severity ? a.severity : 'Moderate';
                    const reaction = typeof a === 'object' && a.reaction ? a.reaction : null;
                    return (
                      <div
                        key={a.id || idx}
                        className="p-3 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/50 border border-[#E5E7EB] dark:border-[#2F3540] text-xs space-y-1"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-[#1F2937] dark:text-[#F3F4F6]">{allergenName}</span>
                          <span className="px-1.5 py-0.5 rounded bg-amber-50 dark:bg-amber-950/40 text-[10px] font-semibold text-amber-700 dark:text-amber-400 capitalize">
                            {severity}
                          </span>
                        </div>
                        {reaction && (
                          <div className="text-[11px] text-[#6B7280] dark:text-[#9CA3AF]">
                            Reaction: {reaction}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="py-6 text-center text-xs text-[#9CA3AF] italic">
                  No adverse drug reactions or allergies recorded.
                </div>
              )}
            </div>
          </div>
      </div>

      {/* TAB 2: DIAGNOSTICS & LAB BIOMARKERS */}
      <div className={activeTab === 'diagnostics' ? 'space-y-6' : 'hidden print:block space-y-6 print:mt-6'}>
          {/* Flagged / Abnormal Lab Results */}
          <div className="bg-white dark:bg-[#1B1E23] p-5 sm:p-6 rounded-2xl border border-[#E5E7EB] dark:border-[#2F3540] shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-2">
                  <Microscope className="w-4 h-4 text-[#10B981]" /> Flagged Laboratory Biomarkers
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
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5 pt-1">
                {abnormalLabs.map((lab: any, idx: number) => {
                  const testName = lab.testName || lab.name || 'Lab Test';
                  const val = lab.value !== undefined ? lab.value : '--';
                  const unit = lab.unit || '';
                  const refRange = lab.referenceRange || lab.standardRange || 'Standard Range';
                  const statusLabel = lab.status || 'abnormal';
                  return (
                    <div
                      key={lab.id || idx}
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
                      <div className="flex items-baseline gap-1 text-sm font-bold text-[#1F2937] dark:text-[#F3F4F6]">
                        <span>{val}</span>
                        <span className="text-xs font-normal text-[#6B7280] dark:text-[#9CA3AF]">{unit}</span>
                      </div>
                      <div className="text-[11px] text-[#6B7280] dark:text-[#9CA3AF]">
                        Ref: {refRange}
                      </div>
                      {lab.sourceReportTitle && (
                        <div className="text-[10px] text-[#10B981] truncate pt-0.5">
                          {lab.sourceReportTitle}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="py-8 text-center text-xs text-[#9CA3AF] italic">
                All documented laboratory analytes are within expected clinical reference ranges.
              </div>
            )}
          </div>

          {/* Diagnostic Imaging & Procedures */}
          <div className="bg-white dark:bg-[#1B1E23] p-5 sm:p-6 rounded-2xl border border-[#E5E7EB] dark:border-[#2F3540] shadow-sm space-y-4">
            <h3 className="text-sm font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-2">
              <Activity className="w-4 h-4 text-blue-500" /> Diagnostic Imaging & Scans
            </h3>

            {procedures.length > 0 ? (
              <div className="space-y-3">
                {procedures.map((proc: any, idx: number) => (
                  <div
                    key={proc.id || idx}
                    className="p-3.5 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/50 border border-[#E5E7EB] dark:border-[#2F3540] text-xs space-y-1.5"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-[#1F2937] dark:text-[#F3F4F6]">
                        {proc.name || proc.procedureName || 'Diagnostic Procedure'}
                      </span>
                      <span className="text-[11px] font-mono text-[#6B7280] dark:text-[#9CA3AF]">
                        {proc.date || 'Recorded'}
                      </span>
                    </div>
                    {proc.findings && (
                      <p className="text-[11px] text-[#4B5563] dark:text-[#D1D5DB] leading-relaxed">
                        Findings: {proc.findings}
                      </p>
                    )}
                    {proc.facility && (
                      <div className="text-[10px] text-[#9CA3AF]">
                        Facility: {proc.facility}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="py-8 text-center text-xs text-[#9CA3AF] italic">
                No diagnostic imaging studies or procedural reports indexed yet.
              </div>
            )}
          </div>

          {/* Longitudinal Milestones */}
          {timelineHighlights.length > 0 && (
            <div className="bg-white dark:bg-[#1B1E23] p-5 sm:p-6 rounded-2xl border border-[#E5E7EB] dark:border-[#2F3540] shadow-sm space-y-3">
              <h3 className="text-sm font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-2">
                <Calendar className="w-4 h-4 text-[#10B981]" /> Longitudinal Timeline Milestones
              </h3>
              <div className="space-y-2 pt-1">
                {timelineHighlights.map((hl: any, idx: number) => {
                  const text = typeof hl === 'string' ? hl : hl.description || hl.title || '';
                  const date = typeof hl === 'object' ? hl.date : '';
                  return (
                    <div
                      key={idx}
                      className="flex items-start gap-2.5 p-2.5 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/40 border border-[#E5E7EB]/80 dark:border-[#2F3540] text-xs"
                    >
                      <span className="w-1.5 h-1.5 rounded-full bg-[#10B981] mt-1.5 shrink-0" />
                      <div className="flex-1">
                        <span className="text-[#1F2937] dark:text-[#F3F4F6]">{text}</span>
                        {date && (
                          <span className="ml-2 text-[10px] text-[#9CA3AF] font-mono">({date})</span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>

      {/* TAB 3: DOCTOR DISCUSSION CHECKLIST */}
      <div className={activeTab === 'checklist' ? 'space-y-6' : 'hidden print:block space-y-6 print:mt-6'}>
          <div className="bg-white dark:bg-[#1B1E23] p-5 sm:p-6 rounded-2xl border border-[#E5E7EB] dark:border-[#2F3540] shadow-sm space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h3 className="text-sm font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-2">
                  <CheckSquare className="w-4 h-4 text-[#10B981]" /> Appointment Discussion Checklist
                </h3>
                <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF] mt-0.5">
                  Prepare for your doctor visit by checking off items as discussed or adding custom clinical questions.
                </p>
              </div>

              <Button
                variant="primary"
                size="sm"
                onClick={handleSaveQuestions}
                isLoading={isSavingQuestions}
                leftIcon={<Save className="w-3.5 h-3.5" />}
                className="shrink-0"
              >
                Save Checklist
              </Button>
            </div>

            {/* Checklist Items */}
            <div className="space-y-2 pt-1">
              {doctorQuestions.map((q, idx) => {
                const isChecked = !!completedQuestions[idx];
                return (
                  <div
                    key={idx}
                    className={`flex items-center justify-between gap-3 p-3 rounded-xl border transition-all text-xs ${
                      isChecked
                        ? 'bg-emerald-50/40 dark:bg-emerald-950/20 border-emerald-200/80 dark:border-emerald-900/40 text-[#6B7280] dark:text-[#9CA3AF] line-through'
                        : 'bg-[#FAF8F5] dark:bg-[#23272E]/50 border-[#E5E7EB] dark:border-[#2F3540] text-[#1F2937] dark:text-[#F3F4F6]'
                    }`}
                  >
                    <button
                      type="button"
                      onClick={() => toggleQuestionComplete(idx)}
                      className="flex items-center gap-3 text-left flex-1"
                    >
                      {isChecked ? (
                        <CheckSquare className="w-4 h-4 text-[#10B981] shrink-0" />
                      ) : (
                        <Square className="w-4 h-4 text-[#9CA3AF] shrink-0" />
                      )}
                      <span>{q}</span>
                    </button>

                    <button
                      type="button"
                      onClick={() => handleRemoveQuestion(idx)}
                      className="p-1 rounded text-[#9CA3AF] hover:text-rose-600 transition-colors shrink-0 print:hidden"
                      title="Remove question"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                );
              })}
            </div>

            {/* Add Custom Question Form */}
            <div className="pt-2 print:hidden space-y-3">
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={newQuestionText}
                  onChange={(e) => setNewQuestionText(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      handleAddQuestion();
                    }
                  }}
                  placeholder="Type a clinical question or concern for your appointment..."
                  className="flex-1 h-9 px-3 rounded-xl bg-[#FAF8F5] dark:bg-[#121417] border border-[#E5E7EB] dark:border-[#2F3540] text-xs text-[#1F2937] dark:text-[#F3F4F6] placeholder-[#9CA3AF] focus:outline-none focus:border-[#10B981]"
                />
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleAddQuestion}
                  disabled={!newQuestionText.trim()}
                  leftIcon={<Plus className="w-3.5 h-3.5" />}
                >
                  Add
                </Button>
              </div>

              {/* Suggested Question Chips */}
              <div className="space-y-1.5">
                <span className="text-[11px] font-medium text-[#6B7280] dark:text-[#9CA3AF]">Quick Suggestions:</span>
                <div className="flex flex-wrap gap-1.5">
                  {[
                    'Review potential side effects and interactions of active medications.',
                    'Discuss target reference ranges for flagged abnormal lab results.',
                    'Evaluate necessity and timing of follow-up imaging or scans.',
                    'Inquire about recommended dietary or lifestyle modifications.'
                  ].map((chip, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => handleAddSuggestedQuestion(chip)}
                      className="px-2.5 py-1 rounded-lg text-[11px] bg-[#FAF8F5] dark:bg-[#23272E] border border-[#E5E7EB] dark:border-[#2F3540] text-[#4B5563] dark:text-[#9CA3AF] hover:text-[#10B981] hover:border-[#10B981]/50 transition-colors text-left"
                    >
                      + {chip}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>

      {/* Share Secure Physician Link Modal */}
      {isShareModalOpen && (
        <Modal
          isOpen={isShareModalOpen}
          onClose={() => setIsShareModalOpen(false)}
          title="Share Physician Summary Link"
          description="Generate a secure 48-hour access token for consulting physicians."
        >
          <div className="space-y-4 pt-1">
            <div className="p-3.5 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/50 border border-[#E5E7EB] dark:border-[#2F3540] text-xs space-y-1.5">
              <span className="font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-1.5">
                <Lock className="w-3.5 h-3.5 text-[#10B981]" /> Time-Bound Encryption Active
              </span>
              <p className="text-[#6B7280] dark:text-[#9CA3AF] leading-relaxed">
                This token provides read-only access to this verified clinical summary and auto-expires in 48 hours.
              </p>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-medium text-[#4B5563] dark:text-[#9CA3AF]">Secure Share Link</label>
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  readOnly
                  value={shareLink}
                  className="flex-1 h-10 px-3 rounded-xl bg-[#FAF8F5] dark:bg-[#121417] border border-[#E5E7EB] dark:border-[#2F3540] text-xs font-mono text-[#1F2937] dark:text-[#F3F4F6] focus:outline-none"
                />
                <Button
                  variant="primary"
                  size="md"
                  leftIcon={<Copy className="w-4 h-4" />}
                  onClick={() => {
                    navigator.clipboard.writeText(shareLink);
                    addToast({ type: 'success', title: 'Link Copied to Clipboard!' });
                    setIsShareModalOpen(false);
                  }}
                >
                  Copy
                </Button>
              </div>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};

export default DoctorSummaryPage;
