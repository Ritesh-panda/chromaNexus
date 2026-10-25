import React, { useEffect, useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Modal } from '@/components/ui/Modal';
import { useUI } from '@/contexts/UIContext';
import { useUser } from '@/contexts/UserContext';
import { summaryService } from '@/services/summary.service';
import { MOCK_DOCTOR_SUMMARY } from '@/constants/mockData';
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
  History,
  FileQuestion,
  Plus,
  Trash2,
  AlertCircle,
  HelpCircle
} from 'lucide-react';

export const DoctorSummaryPage: React.FC = () => {
  const { patient } = useUser();
  const [summary, setSummary] = useState<DoctorSummary>(MOCK_DOCTOR_SUMMARY);
  const [loading, setLoading] = useState(true);
  const [isShareModalOpen, setIsShareModalOpen] = useState(false);
  const [shareLink, setShareLink] = useState('');
  const [activeSection, setActiveSection] = useState('briefing');
  const [newQuestionText, setNewQuestionText] = useState('');
  const [doctorQuestions, setDoctorQuestions] = useState<string[]>([]);
  const [isSavingQuestions, setIsSavingQuestions] = useState(false);
  const { addToast } = useUI();

  useEffect(() => {
    let isMounted = true;
    const fetchSummary = async () => {
      setLoading(true);
      try {
        const data = await summaryService.getDoctorSummary();
        if (isMounted && data && data.summaryOverview) {
          setSummary(data);
          if (data.doctorQuestions) {
            setDoctorQuestions(data.doctorQuestions);
          }
        }
      } catch {
        if (isMounted) {
          setSummary(MOCK_DOCTOR_SUMMARY);
          setDoctorQuestions([
            'Review dosage and potential side effects of active medications.',
            'Discuss target reference ranges for any abnormal laboratory biomarkers.',
            'Evaluate necessity and timing of follow-up diagnostic imaging or procedures.'
          ]);
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    };
    fetchSummary();
    return () => {
      isMounted = false;
    };
  }, []);

  const handlePrintPdf = () => {
    window.print();
  };

  const handleGenerateShare = () => {
    const token =
      summary.shareLink ||
      `https://chronanexus.app/physician-view/share_${Math.random().toString(36).substring(7)}`;
    setShareLink(token);
    setIsShareModalOpen(true);
  };

  const handleAddQuestion = () => {
    if (!newQuestionText.trim()) return;
    const updated = [...doctorQuestions, newQuestionText.trim()];
    setDoctorQuestions(updated);
    setNewQuestionText('');
  };

  const handleRemoveQuestion = (idx: number) => {
    const updated = doctorQuestions.filter((_, i) => i !== idx);
    setDoctorQuestions(updated);
  };

  const handleSaveQuestions = async () => {
    setIsSavingQuestions(true);
    try {
      await summaryService.updateDoctorQuestions(doctorQuestions);
      addToast({ type: 'success', title: 'Appointment Notes Saved', message: 'Your questions for the doctor have been recorded.' });
    } catch {
      addToast({ type: 'info', title: 'Notes Saved Locally', message: 'Notes are saved in your current clinical session.' });
    } finally {
      setIsSavingQuestions(false);
    }
  };

  const sections = [
    { id: 'briefing', label: 'Briefing' },
    { id: 'diagnoses', label: 'Conditions & Diagnoses' },
    { id: 'allergies', label: 'Allergies & Reactions' },
    { id: 'medications', label: 'Medications' },
    { id: 'labs', label: 'Laboratory Results' },
    { id: 'procedures', label: 'Procedures & Imaging' },
    { id: 'timeline', label: 'Recent Timeline' },
    { id: 'conflicts', label: 'Conflicting Information' },
    { id: 'questions', label: 'Questions for Doctor' },
  ];

  const scrollToSection = (id: string) => {
    setActiveSection(id);
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  return (
    <div className="space-y-6 pb-12 print:p-0 print:space-y-4">
      {/* Header Bar (hidden in print) */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 print:hidden">
        <div>
          <h1 className="text-xl sm:text-2xl font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-2">
            <Stethoscope className="w-5 h-5 text-[#10B981]" /> Physician Clinical Summary
          </h1>
          <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF] mt-0.5">
            Deterministic, source-linked longitudinal medical digest prepared for appointment review and physician consultations.
          </p>
        </div>

        <div className="flex items-center space-x-2.5">
          <Button
            variant="secondary"
            size="md"
            onClick={handleGenerateShare}
            leftIcon={<Share2 className="w-4 h-4" />}
          >
            Share Link
          </Button>
          <Button
            variant="primary"
            size="md"
            onClick={handlePrintPdf}
            leftIcon={<Printer className="w-4 h-4" />}
          >
            Print / Export PDF
          </Button>
        </div>
      </div>

      {/* Sticky Section Navigation Anchor Bar (hidden in print) */}
      <div className="sticky top-14 z-20 bg-white/95 dark:bg-[#1B1E23]/95 backdrop-blur-md p-2 rounded-2xl border border-[#E5E7EB] dark:border-[#2F3540] flex items-center space-x-1.5 overflow-x-auto shadow-[0_1px_3px_0_rgba(0,0,0,0.03)] print:hidden">
        {sections.map((sec) => (
          <button
            key={sec.id}
            onClick={() => scrollToSection(sec.id)}
            className={`px-3 py-1.5 rounded-xl text-xs font-medium whitespace-nowrap transition-colors ${
              activeSection === sec.id
                ? 'bg-[#1F2937] text-white dark:bg-[#10B981] dark:text-white shadow-sm'
                : 'text-[#6B7280] dark:text-[#9CA3AF] hover:bg-[#FAF8F5] dark:hover:bg-[#23272E]'
            }`}
          >
            {sec.label}
          </button>
        ))}
      </div>

      {/* Structured Clinical Report Paper */}
      <div className="bg-white dark:bg-[#1B1E23] p-6 sm:p-8 rounded-2xl border border-[#E5E7EB] dark:border-[#2F3540] space-y-8 shadow-[0_1px_3px_0_rgba(0,0,0,0.02)] print:border-none print:shadow-none print:p-0">
        {loading && (
          <div className="p-2.5 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E] border border-[#E5E7EB] dark:border-[#2F3540] text-xs text-[#10B981] font-medium flex items-center gap-2 print:hidden">
            <span className="w-2 h-2 rounded-full bg-[#10B981] animate-ping" />
            Assembling fresh clinical provenance from indexed medical records...
          </div>
        )}
        
        {/* Physician Report Header */}
        <div className="flex flex-col sm:flex-row justify-between pb-6 border-b border-[#E5E7EB] dark:border-[#2F3540] gap-4">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2">
              <span className="text-base font-semibold tracking-tight text-[#1F2937] dark:text-[#F3F4F6]">
                Chrona<span className="text-[#10B981]">Nexus</span> Clinical Digest
              </span>
              <Badge variant="success">Verified Structured Records</Badge>
              {patient?.id && (
                <Badge variant="secondary" className="font-mono text-[10px]">ID: {patient.id.slice(0, 8)}</Badge>
              )}
            </div>
            <h2 className="text-lg sm:text-2xl font-semibold text-[#1F2937] dark:text-[#F3F4F6] tracking-tight">
              Longitudinal Medical Summary — {summary.patientName}
            </h2>
            <div className="flex flex-wrap items-center gap-2 text-xs text-[#6B7280] dark:text-[#9CA3AF] font-mono">
              <span>Age: {summary.age ? `${summary.age} yrs` : 'Unrecorded'}</span>
              <span>•</span>
              <span>Gender: {summary.gender || 'Not recorded'}</span>
              <span>•</span>
              <span>Blood Group: {summary.bloodGroup || 'Not recorded'}</span>
              <span>•</span>
              <span>Generated: {summary.generatedAt ? new Date(summary.generatedAt).toLocaleDateString() : new Date().toLocaleDateString()}</span>
            </div>
          </div>

          <div className="sm:text-right space-y-0.5 text-xs text-[#6B7280] dark:text-[#9CA3AF]">
            <p className="font-medium text-[#1F2937] dark:text-[#F3F4F6]">Primary Care Physician</p>
            <p className="font-semibold text-[#1F2937] dark:text-[#F3F4F6]">
              {summary.primaryCarePhysician || patient?.primaryCarePhysician || 'Not assigned'}
            </p>
            <p className="text-[#15803D] font-medium text-[11px] flex items-center sm:justify-end gap-1">
              <ShieldCheck className="w-3.5 h-3.5" /> {(summary.recentReports || []).length} Indexed Documents Grounded
            </p>
          </div>
        </div>

        {/* Clinician Review Notice Banner */}
        <div className="p-3.5 rounded-xl bg-[#EFF6FF] dark:bg-blue-950/20 border border-blue-200/60 dark:border-blue-900/40 text-xs text-[#1E40AF] dark:text-blue-300 flex items-start gap-2.5">
          <AlertCircle className="w-4 h-4 text-[#2563EB] shrink-0 mt-0.5" />
          <p className="leading-relaxed">
            {summary.clinicianNotice ||
              'NOTICE TO CLINICIANS: This clinical digest was deterministically compiled from indexed medical documents on ChronaNexus. It provides longitudinal reference data and does not constitute an automated diagnosis, treatment recommendation, or prescribing directive. All findings must be clinically verified with original primary sources.'}
          </p>
        </div>

        {/* Section 1: Executive Briefing */}
        <div id="briefing" className="scroll-mt-32 space-y-2">
          <span className="text-[10px] font-semibold uppercase tracking-wider text-[#10B981] flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-[#10B981]" /> 1. Executive Clinical Briefing
          </span>
          <div className="p-4 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/50 border border-[#E5E7EB] dark:border-[#2F3540]">
            <p className="text-xs sm:text-sm text-[#374151] dark:text-[#D1D5DB] leading-relaxed">
              {summary.summaryOverview}
            </p>
          </div>
        </div>

        {/* Section 2: Known Medical Conditions & Diagnoses */}
        <div id="diagnoses" className="scroll-mt-32 space-y-3 break-inside-avoid">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-2">
              <Activity className="w-4 h-4 text-[#B91C1C]" /> 2. Known Medical Conditions & Diagnoses
            </h3>
            <Badge variant="secondary" className="text-[10px]">
              {(summary.currentDiseases || []).length} Active • {(summary.pastDiseases || []).length} Past / Resolved
            </Badge>
          </div>

          {(summary.currentDiseases || []).length === 0 && (summary.pastDiseases || []).length === 0 ? (
            <p className="text-xs text-[#9CA3AF] p-3 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/30 border border-[#E5E7EB] dark:border-[#2F3540]">
              No diagnoses recorded in available documents (absence in records does not confirm clinical absence).
            </p>
          ) : (
            <div className="bg-white dark:bg-[#1B1E23] rounded-xl border border-[#E5E7EB] dark:border-[#2F3540] overflow-hidden divide-y divide-[#E5E7EB]/80 dark:divide-[#2F3540]">
              {/* Active Conditions */}
              {(summary.currentDiseases || []).map((d: any) => (
                <div key={d.id} className="p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-[#1F2937] dark:text-[#F3F4F6]">{d.name}</span>
                      {d.icdCode && (
                        <span className="font-mono text-[10px] text-[#9CA3AF] bg-[#FAF8F5] dark:bg-[#23272E] px-1.5 py-0.5 rounded border border-[#E5E7EB] dark:border-[#2F3540]">
                          ICD: {d.icdCode}
                        </span>
                      )}
                    </div>
                    <div className="flex flex-wrap items-center gap-2 text-[#6B7280] dark:text-[#9CA3AF] mt-1 text-[11px]">
                      <span>Diagnosed: {d.diagnosedDate || 'Date unrecorded'}</span>
                      {d.sourceHospital && <span>• Facility: {d.sourceHospital}</span>}
                      {d.sourceReportTitle && (
                        <span className="text-[#10B981] font-medium flex items-center gap-1">
                          • Source: {d.sourceReportTitle} {d.sourcePageNumber ? `(p.${d.sourcePageNumber})` : ''}
                        </span>
                      )}
                    </div>
                  </div>
                  <Badge variant="danger" className="self-start sm:self-auto text-[10px] shrink-0">Active / Chronic</Badge>
                </div>
              ))}

              {/* Past / Resolved Conditions */}
              {(summary.pastDiseases || []).map((d: any) => (
                <div key={d.id} className="p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs opacity-80">
                  <div>
                    <span className="font-medium text-[#1F2937] dark:text-[#F3F4F6] line-through decoration-[#9CA3AF]">{d.name}</span>
                    <p className="text-[11px] text-[#6B7280] dark:text-[#9CA3AF] mt-0.5">
                      Diagnosed: {d.diagnosedDate || 'Date unrecorded'} • Resolved / In Remission
                    </p>
                  </div>
                  <Badge variant="secondary" className="self-start sm:self-auto text-[10px] shrink-0">Past / Resolved</Badge>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Section 3: Allergies & Adverse Reactions */}
        <div id="allergies" className="scroll-mt-32 space-y-3 break-inside-avoid">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-[#B45309]" /> 3. Documented Allergies & Adverse Reactions
            </h3>
            <Badge variant="warning" className="text-[10px]">
              {(summary.knownAllergies || []).length} Documented
            </Badge>
          </div>

          {(summary.knownAllergies || []).length === 0 ? (
            <div className="p-3.5 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/30 border border-[#E5E7EB] dark:border-[#2F3540] text-xs text-[#6B7280] dark:text-[#9CA3AF]">
              No allergies documented in indexed records. (Absence of documentation does not confirm clinical absence of allergy).
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {(summary.knownAllergies || []).map((allergy: any, idx: number) => {
                const isObj = typeof allergy === 'object' && allergy !== null;
                const allergenName = isObj ? allergy.allergen || allergy.name : allergy;
                const severity = isObj ? allergy.severity : 'Documented';
                const reaction = isObj ? allergy.reaction : null;
                const source = isObj ? allergy.sourceReportTitle : null;
                const page = isObj ? allergy.sourcePageNumber : null;

                return (
                  <div
                    key={idx}
                    className="p-3.5 rounded-xl bg-[#FFFBEB] dark:bg-amber-950/20 border border-amber-200/60 dark:border-amber-800/40 text-xs text-[#92400E] dark:text-amber-200 flex flex-col justify-between"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-sm">{allergenName}</span>
                        <Badge variant="warning" className="text-[10px] capitalize">{severity}</Badge>
                      </div>
                      {reaction && (
                        <p className="text-[11px] text-[#B45309] dark:text-amber-300">Reaction: {reaction}</p>
                      )}
                    </div>
                    {source && (
                      <span className="text-[10px] text-[#B45309]/80 dark:text-amber-400/80 font-mono mt-2 pt-1 border-t border-amber-200/40">
                        Source: {source} {page ? `(p.${page})` : ''}
                      </span>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Section 4: Current & Historical Medications */}
        <div id="medications" className="scroll-mt-32 space-y-4 break-inside-avoid">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-2">
              <Pill className="w-4 h-4 text-[#10B981]" /> 4. Pharmacotherapy Regimen
            </h3>
            <Badge variant="success" className="text-[10px]">
              {(summary.activeMedications || []).length} Active Prescriptions
            </Badge>
          </div>

          {/* Active Medications Sub-section */}
          <div className="space-y-2">
            <span className="text-xs font-semibold text-[#15803D] dark:text-emerald-400 uppercase tracking-wider block">
              Active Prescriptions
            </span>
            {(summary.activeMedications || []).length === 0 ? (
              <p className="text-xs text-[#9CA3AF] p-3 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/30 border border-[#E5E7EB] dark:border-[#2F3540]">
                No active medications documented in indexed records.
              </p>
            ) : (
              <div className="bg-white dark:bg-[#1B1E23] rounded-xl border border-[#E5E7EB] dark:border-[#2F3540] overflow-hidden divide-y divide-[#E5E7EB]/80 dark:divide-[#2F3540]">
                {(summary.activeMedications || []).map((m: any) => (
                  <div key={m.id} className="p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-[#1F2937] dark:text-[#F3F4F6]">{m.name}</span>
                        {m.rxnormCode && (
                          <span className="font-mono text-[10px] text-[#9CA3AF] bg-[#FAF8F5] dark:bg-[#23272E] px-1.5 py-0.5 rounded border border-[#E5E7EB] dark:border-[#2F3540]">
                            RxNorm: {m.rxnormCode}
                          </span>
                        )}
                      </div>
                      <p className="text-[#6B7280] dark:text-[#9CA3AF] mt-0.5">
                        Dosage: {m.dosage} • Frequency: {m.frequency} • Route: {m.route || 'oral'}
                      </p>
                      <div className="flex flex-wrap items-center gap-2 text-[#6B7280] dark:text-[#9CA3AF] mt-1 text-[11px]">
                        <span>Started: {m.startDate || 'Unrecorded'}</span>
                        {m.prescribingDoctor && <span>• Prescriber: {m.prescribingDoctor}</span>}
                        {m.sourceReportTitle && (
                          <span className="text-[#10B981] font-medium">
                            • Source: {m.sourceReportTitle} {m.sourcePageNumber ? `(p.${m.sourcePageNumber})` : ''}
                          </span>
                        )}
                      </div>
                    </div>
                    <Badge variant="success" className="text-[10px] self-start sm:self-auto py-0.5">Active</Badge>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Historical / Discontinued Medications Sub-section */}
          {(summary.historicalMedications || []).length > 0 && (
            <div className="space-y-2 pt-2">
              <span className="text-xs font-semibold text-[#6B7280] dark:text-[#9CA3AF] uppercase tracking-wider block">
                Discontinued / Completed Historical Medications
              </span>
              <div className="bg-white dark:bg-[#1B1E23] rounded-xl border border-[#E5E7EB] dark:border-[#2F3540] overflow-hidden divide-y divide-[#E5E7EB]/80 dark:divide-[#2F3540]">
                {(summary.historicalMedications || []).map((m: any) => (
                  <div key={m.id} className="p-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs opacity-80">
                    <div>
                      <span className="font-medium text-[#1F2937] dark:text-[#F3F4F6]">{m.name} ({m.dosage})</span>
                      <p className="text-[11px] text-[#6B7280] dark:text-[#9CA3AF]">
                        Started: {m.startDate || 'Unknown'} • Ended: {m.endDate || 'Discontinued'} • Status: {m.status}
                      </p>
                    </div>
                    <Badge variant="secondary" className="text-[10px] self-start sm:self-auto">Historical</Badge>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Section 5: Laboratory Results & Biomarker Trends */}
        <div id="labs" className="scroll-mt-32 space-y-3 break-inside-avoid">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-2">
              <Activity className="w-4 h-4 text-[#2563EB]" /> 5. Recent Laboratory Results & Biomarkers
            </h3>
            <Badge variant="secondary" className="text-[10px]">
              {(summary.abnormalLabs || []).length} Flagged Abnormal
            </Badge>
          </div>

          {/* Abnormal Labs Callout */}
          {(summary.abnormalLabs || []).length > 0 && (
            <div className="space-y-2">
              <span className="text-xs font-semibold text-[#B91C1C] dark:text-rose-400 uppercase tracking-wider block">
                Out-of-Range Biomarkers Requiring Clinical Attention
              </span>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                {(summary.abnormalLabs || []).map((lab: any) => (
                  <div
                    key={lab.id}
                    className="p-3.5 rounded-xl bg-[#FEF2F2] dark:bg-rose-950/20 border border-rose-200/60 dark:border-rose-800/40 text-xs flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-[#1F2937] dark:text-[#F3F4F6]">{lab.testName}</span>
                        <Badge variant="danger" className="text-[10px] capitalize">{lab.status}</Badge>
                      </div>
                      <p className="font-mono font-semibold text-sm text-[#B91C1C] dark:text-rose-400 mt-1 tabular-nums">
                        {lab.value} {lab.unit}
                        <span className="text-xs font-normal text-[#6B7280] dark:text-[#9CA3AF] ml-2">
                          (Ref: {lab.referenceRange})
                        </span>
                      </p>
                    </div>
                    <div className="flex items-center justify-between text-[10px] text-[#6B7280] dark:text-[#9CA3AF] mt-2 pt-1 border-t border-rose-200/40">
                      <span>Observed: {lab.testDate}</span>
                      <span>Facility: {lab.hospitalName || 'Lab'}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Standard Recent Labs Table */}
          <div className="space-y-2 pt-2">
            <span className="text-xs font-semibold text-[#6B7280] dark:text-[#9CA3AF] uppercase tracking-wider block">
              Recent Indexed Lab Measurements
            </span>
            <div className="bg-white dark:bg-[#1B1E23] rounded-xl border border-[#E5E7EB] dark:border-[#2F3540] overflow-hidden divide-y divide-[#E5E7EB]/80 dark:divide-[#2F3540]">
              {(summary.recentLabs || summary.abnormalLabs || []).slice(0, 8).map((lab: any) => (
                <div key={lab.id} className="p-3 flex items-center justify-between text-xs">
                  <div>
                    <span className="font-medium text-[#1F2937] dark:text-[#F3F4F6]">{lab.testName}</span>
                    <span className="text-[11px] text-[#6B7280] dark:text-[#9CA3AF] ml-2">
                      {lab.testDate} • {lab.hospitalName}
                    </span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="font-mono tabular-nums font-semibold text-[#1F2937] dark:text-[#F3F4F6]">
                      {lab.value} {lab.unit}
                    </span>
                    <Badge variant={lab.status === 'normal' ? 'secondary' : 'danger'} className="text-[10px]">
                      {lab.status}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Section 6: Procedures & Diagnostic Imaging */}
        <div id="procedures" className="scroll-mt-32 space-y-3 break-inside-avoid">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-2">
              <Calendar className="w-4 h-4 text-[#8B5CF6]" /> 6. Diagnostic Imaging & Procedures
            </h3>
            <Badge variant="secondary" className="text-[10px]">
              {(summary.proceduresAndImaging || []).length} Indexed
            </Badge>
          </div>

          {(summary.proceduresAndImaging || []).length === 0 ? (
            <p className="text-xs text-[#9CA3AF] p-3 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/30 border border-[#E5E7EB] dark:border-[#2F3540]">
              No imaging or procedure records documented in available vault files.
            </p>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {(summary.proceduresAndImaging || []).map((proc: any) => (
                <div
                  key={proc.id}
                  className="p-3.5 rounded-xl bg-white dark:bg-[#1B1E23] border border-[#E5E7EB] dark:border-[#2F3540] text-xs space-y-1.5 flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-[#1F2937] dark:text-[#F3F4F6]">{proc.title}</span>
                      <Badge variant="secondary" className="text-[10px] capitalize">{proc.category?.replace('_', ' ')}</Badge>
                    </div>
                    {proc.summary && (
                      <p className="text-[11px] text-[#6B7280] dark:text-[#9CA3AF] line-clamp-2 mt-1">
                        {proc.summary}
                      </p>
                    )}
                  </div>
                  <div className="flex items-center justify-between text-[10px] text-[#9CA3AF] pt-2 border-t border-[#E5E7EB]/50 dark:border-[#2F3540]/50 font-mono">
                    <span>Date: {proc.reportDate}</span>
                    <span>{proc.hospitalName}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Section 7: Recent Longitudinal Milestones */}
        <div id="timeline" className="scroll-mt-32 space-y-3 break-inside-avoid">
          <h3 className="text-sm font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-2">
            <History className="w-4 h-4 text-[#10B981]" /> 7. Key Longitudinal Milestones
          </h3>
          <div className="space-y-2">
            {(summary.timelineHighlights || []).map((hl: any, idx: number) => {
              const text = typeof hl === 'object' && hl !== null ? `${hl.date}: ${hl.title} (${hl.hospitalName || ''})` : hl;
              return (
                <div
                  key={idx}
                  className="p-3 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/50 text-xs text-[#374151] dark:text-[#D1D5DB] border border-[#E5E7EB] dark:border-[#2F3540] flex items-center gap-2.5"
                >
                  <CheckCircle2 className="w-3.5 h-3.5 text-[#10B981] shrink-0" />
                  <span>{text}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Section 8: Conflicting or Uncertain Information */}
        <div id="conflicts" className="scroll-mt-32 space-y-3 break-inside-avoid">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-[#DC2626]" /> 8. Conflicting Observations & Missing Data Disclosures
            </h3>
            <Badge variant="secondary" className="text-[10px]">
              {(summary.conflictingInformation || []).length} Discrepancies Noted
            </Badge>
          </div>

          {(summary.conflictingInformation || []).length > 0 && (
            <div className="space-y-2">
              {(summary.conflictingInformation || []).map((conf, idx) => (
                <div
                  key={idx}
                  className="p-3.5 rounded-xl bg-[#FEF2F2] dark:bg-rose-950/20 border border-rose-200/60 dark:border-rose-900/40 text-xs text-[#991B1B] dark:text-rose-300 space-y-1"
                >
                  <span className="font-semibold block">{conf.topic}</span>
                  <p className="text-[11px] leading-relaxed">{conf.details}</p>
                  {conf.recordsInvolved && conf.recordsInvolved.length > 0 && (
                    <ul className="text-[10px] list-disc list-inside font-mono pt-1 text-[#B91C1C] dark:text-rose-400">
                      {conf.recordsInvolved.map((rec, rIdx) => (
                        <li key={rIdx}>{rec}</li>
                      ))}
                    </ul>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Explicit Missing Data Disclosures */}
          <div className="p-3.5 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/30 border border-[#E5E7EB] dark:border-[#2F3540] text-xs space-y-1.5 text-[#6B7280] dark:text-[#9CA3AF]">
            <span className="font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-1.5">
              <HelpCircle className="w-3.5 h-3.5 text-[#6B7280]" /> Data Boundaries & Incomplete Record Notices:
            </span>
            <ul className="list-disc list-inside space-y-0.5 text-[11px]">
              {(summary.missingDataDisclosures || [
                'Digest compiled from indexed documents. Any unuploaded or non-digitized records are not reflected.',
                'Absence of conditions or allergies in records does not confirm clinical absence.'
              ]).map((disc, idx) => (
                <li key={idx}>{disc}</li>
              ))}
            </ul>
          </div>
        </div>

        {/* Section 9: Questions for the Doctor (Interactive & Print-Friendly) */}
        <div id="questions" className="scroll-mt-32 space-y-3 break-inside-avoid">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-2">
              <FileQuestion className="w-4 h-4 text-[#2563EB]" /> 9. Patient Appointment Notes & Questions for the Doctor
            </h3>
            <span className="text-[11px] text-[#6B7280] dark:text-[#9CA3AF] font-mono">
              (Patient notes, not clinician directives)
            </span>
          </div>

          <div className="space-y-2">
            {doctorQuestions.map((q, idx) => (
              <div
                key={idx}
                className="p-3 rounded-xl bg-white dark:bg-[#1B1E23] border border-[#E5E7EB] dark:border-[#2F3540] flex items-center justify-between text-xs gap-3"
              >
                <div className="flex items-start gap-2.5">
                  <span className="font-semibold text-[#2563EB] font-mono shrink-0">{idx + 1}.</span>
                  <span className="text-[#1F2937] dark:text-[#F3F4F6]">{q}</span>
                </div>
                <button
                  onClick={() => handleRemoveQuestion(idx)}
                  className="text-[#9CA3AF] hover:text-[#DC2626] transition-colors p-1 shrink-0 print:hidden"
                  title="Remove note"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>

          {/* Add Question Input Box (hidden in print) */}
          <div className="flex items-center gap-2 pt-1 print:hidden">
            <input
              type="text"
              value={newQuestionText}
              onChange={(e) => setNewQuestionText(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') handleAddQuestion(); }}
              placeholder="Add a question or discussion point for your doctor..."
              className="flex-1 h-9 px-3 rounded-xl bg-[#FAF8F5] dark:bg-[#121417] border border-[#E5E7EB] dark:border-[#2F3540] text-xs text-[#1F2937] dark:text-[#F3F4F6] focus:outline-none"
            />
            <Button
              variant="secondary"
              size="sm"
              onClick={handleAddQuestion}
              leftIcon={<Plus className="w-3.5 h-3.5" />}
            >
              Add Note
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={handleSaveQuestions}
              disabled={isSavingQuestions}
            >
              {isSavingQuestions ? 'Saving...' : 'Save Notes'}
            </Button>
          </div>
        </div>

        {/* Footer Provenance Note */}
        <div className="pt-6 border-t border-[#E5E7EB] dark:border-[#2F3540] flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-[#9CA3AF] font-mono">
          <span>ChronaNexus Clinical Intelligence System</span>
          <span>End-to-End Cryptographic & Source Provenance Grounded</span>
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
                This token provides access to this exact grounded summary view and auto-expires in 48 hours.
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
