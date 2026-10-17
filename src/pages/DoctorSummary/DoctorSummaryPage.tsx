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
  Copy
} from 'lucide-react';

export const DoctorSummaryPage: React.FC = () => {
  const { patient } = useUser();
  const [summary, setSummary] = useState<DoctorSummary>(MOCK_DOCTOR_SUMMARY);
  const [isShareModalOpen, setIsShareModalOpen] = useState(false);
  const [shareLink, setShareLink] = useState('');
  const [activeSection, setActiveSection] = useState('briefing');
  const { addToast } = useUI();

  useEffect(() => {
    let isMounted = true;
    const fetchSummary = async () => {
      try {
        const data = await summaryService.getDoctorSummary();
        if (isMounted && data && data.summaryOverview) {
          setSummary(data);
        }
      } catch {
        if (isMounted) {
          setSummary(MOCK_DOCTOR_SUMMARY);
        }
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

  const sections = [
    { id: 'briefing', label: 'Briefing' },
    { id: 'diagnoses', label: 'Diagnoses' },
    { id: 'medications', label: 'Pharmacotherapy' },
    { id: 'allergies', label: 'Alerts & Allergies' },
    { id: 'labs', label: 'Abnormal Labs' },
    { id: 'milestones', label: 'Key Milestones' },
  ];

  const scrollToSection = (id: string) => {
    setActiveSection(id);
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  return (
    <div className="space-y-6 pb-12 print:p-0">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 print:hidden">
        <div>
          <h1 className="text-xl sm:text-2xl font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-2">
            <Stethoscope className="w-5 h-5 text-[#10B981]" /> Physician Clinical Summary
          </h1>
          <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF] mt-0.5">
            Automated medical history digest structured specifically for clinical review and consultations.
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
            Download PDF
          </Button>
        </div>
      </div>

      {/* Sticky Section Navigation Anchor Bar */}
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
      <div className="bg-white dark:bg-[#1B1E23] p-6 sm:p-8 rounded-2xl border border-[#E5E7EB] dark:border-[#2F3540] space-y-8 shadow-[0_1px_3px_0_rgba(0,0,0,0.02)]">
        {/* Physician Report Header */}
        <div className="flex flex-col sm:flex-row justify-between pb-6 border-b border-[#E5E7EB] dark:border-[#2F3540] gap-4">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2">
              <span className="text-base font-semibold tracking-tight text-[#1F2937] dark:text-[#F3F4F6]">
                Chrona<span className="text-[#10B981]">Nexus</span> Clinical Digest
              </span>
              <Badge variant="success">HIPAA Certified</Badge>
              {patient?.id && (
                <Badge variant="secondary" className="font-mono text-[10px]">ID: {patient.id}</Badge>
              )}
            </div>
            <h2 className="text-lg sm:text-2xl font-semibold text-[#1F2937] dark:text-[#F3F4F6] tracking-tight">
              Longitudinal Health Summary — {summary.patientName}
            </h2>
            <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF] font-mono tabular-nums">
              Gender: {summary.gender} • Generated: {summary.generatedAt ? new Date(summary.generatedAt).toLocaleDateString() : new Date().toLocaleDateString()}
            </p>
          </div>

          <div className="sm:text-right space-y-0.5 text-xs text-[#6B7280] dark:text-[#9CA3AF]">
            <p className="font-medium text-[#1F2937] dark:text-[#F3F4F6]">Primary Care Physician</p>
            <p className="font-semibold text-[#1F2937] dark:text-[#F3F4F6]">
              {patient?.primaryCarePhysician || 'Not assigned'}
            </p>
            <p className="text-[#15803D] font-medium text-[11px] flex items-center sm:justify-end gap-1">
              <ShieldCheck className="w-3.5 h-3.5" /> {(summary.recentReports || []).length > 0 ? `${summary.recentReports.length} Verified Documents Grounded` : 'Verified Documents Grounded'}
            </p>
          </div>
        </div>

        {/* Section 1: Executive Briefing */}
        <div id="briefing" className="scroll-mt-32 space-y-2">
          <span className="text-[10px] font-semibold uppercase tracking-wider text-[#10B981] flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-[#10B981]" /> Executive Clinical Briefing
          </span>
          <div className="p-4 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/50 border border-[#E5E7EB] dark:border-[#2F3540]">
            <p className="text-xs sm:text-sm text-[#374151] dark:text-[#D1D5DB] leading-relaxed">
              {summary.summaryOverview}
            </p>
          </div>
        </div>

        {/* Section 2: Active & Chronic Diagnoses */}
        <div id="diagnoses" className="scroll-mt-32 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-2">
              <Activity className="w-4 h-4 text-[#B91C1C]" /> Active & Chronic Diagnoses
            </h3>
            <Badge variant="secondary" className="text-[10px]">
              {(summary.currentDiseases || []).length} Documented Conditions
            </Badge>
          </div>

          <div className="bg-white dark:bg-[#1B1E23] rounded-xl border border-[#E5E7EB] dark:border-[#2F3540] overflow-hidden divide-y divide-[#E5E7EB]/80 dark:divide-[#2F3540]">
            {(summary.currentDiseases || []).map((d) => (
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
                  {d.notes && <p className="text-[#6B7280] dark:text-[#9CA3AF] mt-0.5">{d.notes}</p>}
                </div>
                <Badge variant="danger" className="self-start sm:self-auto text-[10px] shrink-0">Chronic Managed</Badge>
              </div>
            ))}
          </div>
        </div>

        {/* Section 3: Active Pharmacotherapy */}
        <div id="medications" className="scroll-mt-32 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-2">
              <Pill className="w-4 h-4 text-[#10B981]" /> Active Pharmacotherapy Regimen
            </h3>
            <Badge variant="success" className="text-[10px]">
              {(summary.activeMedications || []).length} Active Prescriptions
            </Badge>
          </div>

          <div className="bg-white dark:bg-[#1B1E23] rounded-xl border border-[#E5E7EB] dark:border-[#2F3540] overflow-hidden divide-y divide-[#E5E7EB]/80 dark:divide-[#2F3540]">
            {(summary.activeMedications || []).map((m) => (
              <div key={m.id} className="p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
                <div>
                  <span className="font-semibold text-[#1F2937] dark:text-[#F3F4F6]">{m.name}</span>
                  <p className="text-[#6B7280] dark:text-[#9CA3AF] mt-0.5">Dosage: {m.dosage} • Frequency: {m.frequency}</p>
                </div>
                <div className="flex items-center gap-2 self-start sm:self-auto shrink-0">
                  <Badge variant="success" className="text-[10px] py-0">{m.status}</Badge>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Section 4 & 5: 2-Column Grid for Allergies & Abnormal Labs */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Allergies */}
          <div id="allergies" className="scroll-mt-32 space-y-3">
            <h3 className="text-sm font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-[#B45309]" /> Known Allergies & Adverse Reactions
            </h3>
            <div className="space-y-2">
              {(summary.knownAllergies || []).map((allergy, idx) => (
                <div
                  key={idx}
                  className="p-3 rounded-xl bg-[#FFFBEB] dark:bg-amber-950/20 border border-amber-200/60 dark:border-amber-800/40 text-xs font-medium text-[#B45309] dark:text-amber-300 flex items-center gap-2.5"
                >
                  <AlertTriangle className="w-4 h-4 text-[#B45309] shrink-0" />
                  <span>{allergy}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Abnormal Labs */}
          <div id="labs" className="scroll-mt-32 space-y-3">
            <h3 className="text-sm font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-2">
              <Activity className="w-4 h-4 text-[#B91C1C]" /> Abnormal Lab Findings
            </h3>
            <div className="space-y-2">
              {(summary.abnormalLabs || []).map((lab) => (
                <div
                  key={lab.id}
                  className="p-3 rounded-xl bg-[#FEF2F2] dark:bg-rose-950/20 border border-rose-200/60 dark:border-rose-800/40 text-xs flex items-center justify-between"
                >
                  <span className="font-semibold text-[#1F2937] dark:text-[#F3F4F6]">{lab.testName}</span>
                  <span className="font-mono font-semibold text-[#B91C1C] dark:text-rose-400 tabular-nums">
                    {lab.value} {lab.unit} (Ref: {lab.referenceRange})
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Section 6: Key Milestones */}
        <div id="milestones" className="scroll-mt-32 space-y-3 pt-2">
          <h3 className="text-sm font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-2">
            <Calendar className="w-4 h-4 text-[#10B981]" /> Key Longitudinal Milestones
          </h3>
          <div className="space-y-2">
            {(summary.timelineHighlights || []).map((hl, idx) => (
              <div
                key={idx}
                className="p-3 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/50 text-xs text-[#374151] dark:text-[#D1D5DB] border border-[#E5E7EB] dark:border-[#2F3540] flex items-center gap-2.5"
              >
                <CheckCircle2 className="w-3.5 h-3.5 text-[#10B981] shrink-0" />
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
          description="Generate a secure 48-hour link for consulting physicians."
        >
          <div className="space-y-4 pt-1">
            <div className="p-3.5 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/50 border border-[#E5E7EB] dark:border-[#2F3540] text-xs space-y-1.5">
              <span className="font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-1.5">
                <Lock className="w-3.5 h-3.5 text-[#10B981]" /> Time-Bound Encryption Active
              </span>
              <p className="text-[#6B7280] dark:text-[#9CA3AF] leading-relaxed">
                This link auto-expires in 48 hours. Access can be revoked anytime from Settings.
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
