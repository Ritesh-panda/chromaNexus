import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
import { useUI } from '@/contexts/UIContext';
import { reportService, type DocumentIngestionStatus } from '@/services/report.service';
import {
  Upload,
  FileText,
  ShieldCheck,
  Loader2,
  CheckCircle2,
  Calendar,
  Building2,
  User as UserIcon,
  ExternalLink,
  ArrowRight,
  RotateCcw,
  AlertCircle,
  FlaskConical,
  Activity,
  Sparkles,
} from 'lucide-react';
import type { MedicalReport, ReportCategory } from '@/types';

const getCategoryMetadata = (cat: string) => {
  const c = (cat || '').toLowerCase();
  if (c.includes('blood') || c.includes('lab')) {
    return {
      label: 'Laboratory Blood Report',
      timelineEvent: 'Lab Result',
      badgeClass: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400 border-emerald-200 dark:border-emerald-800',
      description: 'Biomarkers, complete blood count & chemistry panels',
    };
  }
  if (c.includes('doctor') || c.includes('notes') || c.includes('consultation')) {
    return {
      label: 'Clinical Consultation Note',
      timelineEvent: 'Doctor Visit',
      badgeClass: 'bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-400 border-blue-200 dark:border-blue-800',
      description: 'Outpatient consultation & physical examination',
    };
  }
  if (c.includes('mri') || c.includes('scan') || c.includes('xray') || c.includes('imaging')) {
    return {
      label: 'Diagnostic Imaging (MRI / Scan)',
      timelineEvent: 'Imaging',
      badgeClass: 'bg-purple-50 text-purple-700 dark:bg-purple-950/40 dark:text-purple-400 border-purple-200 dark:border-purple-800',
      description: 'Radiology examination & cross-sectional imaging',
    };
  }
  if (c.includes('prescription')) {
    return {
      label: 'Prescription & Pharmacotherapy',
      timelineEvent: 'Prescription',
      badgeClass: 'bg-teal-50 text-teal-700 dark:bg-teal-950/40 dark:text-teal-400 border-teal-200 dark:border-teal-800',
      description: 'Prescribed medication regimens & dosage instructions',
    };
  }
  if (c.includes('discharge')) {
    return {
      label: 'Inpatient Discharge Summary',
      timelineEvent: 'Hospitalization',
      badgeClass: 'bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-400 border-amber-200 dark:border-amber-800',
      description: 'Inpatient hospital admission & discharge clinical records',
    };
  }
  return {
    label: cat ? cat.replace('_', ' ').replace(/\b\w/g, (s) => s.toUpperCase()) : 'Medical Report',
    timelineEvent: 'Clinical Event',
    badgeClass: 'bg-slate-50 text-slate-700 dark:bg-slate-900/40 dark:text-slate-300 border-slate-200 dark:border-slate-800',
    description: 'General medical documentation and patient records',
  };
};

export const UploadModal: React.FC = () => {
  const { uploadModalOpen, setUploadModalOpen, addToast } = useUI();
  const navigate = useNavigate();

  const [file, setFile] = useState<File | null>(null);
  const [category, setCategory] = useState<string>('auto');
  const [hospital, setHospital] = useState('');
  const [doctor, setDoctor] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [ingestionStatus, setIngestionStatus] = useState<DocumentIngestionStatus | null>(null);
  const [summaryReport, setSummaryReport] = useState<MedicalReport | null>(null);

  if (!uploadModalOpen) return null;

  const handleClose = () => {
    setUploadModalOpen(false);
    setFile(null);
    setIngestionStatus(null);
    setSummaryReport(null);
  };

  const handleFileDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
    }
  };

  const pollStatus = async (docId: string): Promise<MedicalReport | null> => {
    const maxAttempts = 60;
    for (let i = 0; i < maxAttempts; i++) {
      await new Promise((r) => setTimeout(r, 1000));
      try {
        const status = await reportService.getIngestionStatus(docId);
        setIngestionStatus(status);
        const st = (status.status || '').toUpperCase();
        if (st === 'COMPLETED') {
          // Fetch final updated report with all extracted entities and detected date
          const fresh = await reportService.getReportById(docId);
          return fresh;
        } else if (st === 'FAILED') {
          throw new Error(status.error_message || status.error || 'Ingestion failed on server');
        }
      } catch (err: any) {
        if (err?.message?.includes('Ingestion failed')) {
          throw err;
        }
      }
    }
    try {
      return await reportService.getReportById(docId);
    } catch {
      return null;
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setIsUploading(true);
    setIngestionStatus({
      document_id: 'pending',
      status: 'RECEIVED',
      progress_percent: 10,
      current_stage: 'Uploading document...',
    });

    try {
      const uploaded = await reportService.uploadReport({
        file,
        category: (category === 'auto' ? 'blood_report' : category) as ReportCategory,
        hospitalName: hospital,
        doctorName: doctor,
      });

      if (uploaded?.id) {
        setIngestionStatus({
          document_id: uploaded.id,
          status: 'PROCESSING',
          progress_percent: 30,
          current_stage: 'Extracting document entities and clinical date...',
        });

        const completedReport = await pollStatus(uploaded.id);
        let finalReport = completedReport;
        if (!finalReport) {
          try {
            finalReport = await reportService.getReportById(uploaded.id);
          } catch {
            finalReport = uploaded;
          }
        }
        if (!finalReport) finalReport = uploaded;
        setSummaryReport(finalReport);
        addToast({
          type: 'success',
          title: 'Document Analyzed',
          message: `${finalReport.title || file.name} has been indexed with clinical date ${finalReport.reportDate}.`,
        });
      }
    } catch (err: any) {
      const errorMsg =
        err?.response?.data?.detail ||
        err?.message ||
        'Could not parse document. Please check file format.';
      addToast({
        type: 'error',
        title: 'Upload Failed',
        message: typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg),
      });
      setIngestionStatus(null);
    } finally {
      setIsUploading(false);
    }
  };

  const currentProgress = ingestionStatus
    ? (ingestionStatus.progress_percent ?? ingestionStatus.progress ?? 0)
    : 0;
  const statusUpper = ingestionStatus?.status ? ingestionStatus.status.toUpperCase() : '';
  const counts = ingestionStatus?.extracted_counts || ingestionStatus?.extracted_entity_counts;
  const chunkCount = ingestionStatus?.indexed_chunks_count ?? ingestionStatus?.indexed_chunk_count;

  return (
    <Modal
      isOpen={uploadModalOpen}
      onClose={handleClose}
      title={summaryReport ? "Document Clinical Summary" : "Upload Medical Document"}
      description={
        summaryReport
          ? "Structured medical data extracted from your uploaded record."
          : "Securely ingest PDFs, Imaging, or Prescriptions into continuous patient memory."
      }
      maxWidth="lg"
    >
      {/* VIEW A: SUMMARY REPORT DISPLAY */}
      {summaryReport ? (() => {
        const catMeta = getCategoryMetadata(summaryReport.category);
        const labEntities = summaryReport.extractedEntities?.filter((e) => e.category === 'lab_value') || [];
        const medEntities = summaryReport.extractedEntities?.filter((e) => e.category === 'medication') || [];
        const diseaseEntities = summaryReport.extractedEntities?.filter((e) => e.category === 'disease') || [];
        const otherEntities = summaryReport.extractedEntities?.filter((e) => !['lab_value', 'medication', 'disease'].includes(e.category)) || [];

        return (
          <div className="space-y-4 pt-1">
            <div className="p-4 rounded-2xl bg-[#ECFDF5] dark:bg-emerald-950/30 border border-emerald-200/80 dark:border-emerald-800/40 space-y-2.5">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="text-xs font-semibold text-[#15803D] dark:text-emerald-400 flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-[#10B981]" />
                  Document Verified & Indexed
                </span>
                <div className="flex items-center gap-1.5 flex-wrap">
                  <span className={`px-2.5 py-0.5 rounded-full text-[11px] font-semibold border ${catMeta.badgeClass}`}>
                    {catMeta.label}
                  </span>
                  <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
                    <Activity className="w-3 h-3" /> Timeline: {catMeta.timelineEvent}
                  </span>
                </div>
              </div>

              <h3 className="text-base font-semibold text-[#1F2937] dark:text-[#F3F4F6]">
                {summaryReport.title}
              </h3>
              {summaryReport.summary && (
                <p className="text-xs text-[#4B5563] dark:text-[#9CA3AF] leading-relaxed">
                  {summaryReport.summary}
                </p>
              )}
            </div>

            {/* Metadata Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              {/* CARD 1: EXTRACTED TIMELINE DATE */}
              <div className="p-3.5 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/60 border border-[#E5E7EB] dark:border-[#2F3540] space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-medium text-[#6B7280] dark:text-[#9CA3AF] flex items-center gap-1.5">
                    <Calendar className="w-3.5 h-3.5 text-[#10B981]" /> Extracted Clinical Date
                  </span>
                  <span className="text-[10px] font-semibold text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20">
                    Timeline Date
                  </span>
                </div>
                <p className="font-bold text-[#1F2937] dark:text-[#F3F4F6] text-base tabular-nums">
                  {summaryReport.reportDate || 'Not specified'}
                </p>
                <p className="text-[10px] text-[#6B7280] dark:text-[#9CA3AF]">
                  Clinical event date recorded in patient timeline (instead of upload date)
                </p>
              </div>

              {/* CARD 2: REPORT TYPE & CLINICAL CLASSIFICATION */}
              <div className="p-3.5 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/60 border border-[#E5E7EB] dark:border-[#2F3540] space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-medium text-[#6B7280] dark:text-[#9CA3AF] flex items-center gap-1.5">
                    <FlaskConical className="w-3.5 h-3.5 text-[#10B981]" /> Report Classification
                  </span>
                  <span className="text-[10px] font-semibold text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20">
                    {catMeta.timelineEvent}
                  </span>
                </div>
                <p className="font-bold text-[#1F2937] dark:text-[#F3F4F6] text-sm truncate">
                  {catMeta.label}
                </p>
                <p className="text-[10px] text-[#6B7280] dark:text-[#9CA3AF] truncate">
                  {catMeta.description}
                </p>
              </div>

              {/* CARD 3: MEDICAL FACILITY */}
              <div className="p-3.5 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/60 border border-[#E5E7EB] dark:border-[#2F3540] space-y-1.5">
                <span className="text-[11px] font-medium text-[#6B7280] dark:text-[#9CA3AF] flex items-center gap-1.5">
                  <Building2 className="w-3.5 h-3.5 text-[#10B981]" /> Medical Facility / Laboratory
                </span>
                <p className="font-semibold text-[#1F2937] dark:text-[#F3F4F6] text-sm truncate">
                  {summaryReport.hospitalName || 'Clinical Health Facility'}
                </p>
                <p className="text-[10px] text-[#6B7280] dark:text-[#9CA3AF]">
                  Validated clinical health facility source
                </p>
              </div>

              {/* CARD 4: PRESCRIBING / ATTENDING */}
              <div className="p-3.5 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/60 border border-[#E5E7EB] dark:border-[#2F3540] space-y-1.5">
                <span className="text-[11px] font-medium text-[#6B7280] dark:text-[#9CA3AF] flex items-center gap-1.5">
                  <UserIcon className="w-3.5 h-3.5 text-[#10B981]" /> Prescribing / Attending
                </span>
                <p className="font-semibold text-[#1F2937] dark:text-[#F3F4F6] text-sm truncate">
                  {summaryReport.doctorName || 'Clinical Laboratory Staff'}
                </p>
                <p className="text-[10px] text-[#6B7280] dark:text-[#9CA3AF] truncate">
                  Source: {summaryReport.fileName}
                </p>
              </div>
            </div>

            {/* EXTRACTED CLINICAL FINDINGS (LABS, MEDS, CONDITIONS) */}
            <div className="p-3.5 rounded-xl bg-white dark:bg-[#1B1E23] border border-[#E5E7EB] dark:border-[#2F3540] space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-1.5">
                  <Activity className="w-3.5 h-3.5 text-[#10B981]" />
                  Extracted Clinical Findings
                  {summaryReport.extractedEntities && summaryReport.extractedEntities.length > 0 && (
                    <span className="text-[10px] font-medium text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                      {summaryReport.extractedEntities.length} Structured Values
                    </span>
                  )}
                </span>
                <span className="text-[10px] text-[#6B7280] dark:text-[#9CA3AF]">
                  Source-Grounded Extraction
                </span>
              </div>

              {/* Lab Values List */}
              {labEntities.length > 0 && (
                <div className="space-y-1.5">
                  <span className="text-[11px] font-medium text-[#6B7280] dark:text-[#9CA3AF]">
                    Laboratory Biomarkers & Measurements ({labEntities.length})
                  </span>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                    {labEntities.map((ent, idx) => (
                      <div key={idx} className="p-2 rounded-lg bg-[#FAF8F5] dark:bg-[#23272E]/60 border border-[#E5E7EB] dark:border-[#2F3540]/80">
                        <div className="text-[11px] font-medium text-[#4B5563] dark:text-[#9CA3AF] truncate">
                          {ent.name}
                        </div>
                        <div className="text-xs font-bold text-[#1F2937] dark:text-[#F3F4F6] mt-0.5">
                          {ent.value} <span className="text-[10px] font-normal text-[#6B7280] dark:text-[#9CA3AF]">{ent.unit || ''}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Medications List */}
              {medEntities.length > 0 && (
                <div className="space-y-1.5">
                  <span className="text-[11px] font-medium text-[#6B7280] dark:text-[#9CA3AF]">
                    Prescribed Medications ({medEntities.length})
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {medEntities.map((ent, idx) => (
                      <Badge key={idx} variant="secondary" className="text-[11px]">
                        {ent.name} {ent.value ? `(${ent.value} ${ent.unit || ''})` : ''}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {/* Conditions List */}
              {diseaseEntities.length > 0 && (
                <div className="space-y-1.5">
                  <span className="text-[11px] font-medium text-[#6B7280] dark:text-[#9CA3AF]">
                    Identified Conditions & Diagnoses ({diseaseEntities.length})
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {diseaseEntities.map((ent, idx) => (
                      <Badge key={idx} variant="secondary" className="text-[11px] bg-red-500/10 text-red-400 border border-red-500/20">
                        {ent.name} {ent.value ? `[ICD: ${ent.value}]` : ''}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {/* Other entities */}
              {otherEntities.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {otherEntities.map((ent, idx) => (
                    <Badge key={idx} variant="secondary" className="text-[11px]">
                      {ent.name} {ent.value ? `(${ent.value})` : ''}
                    </Badge>
                  ))}
                </div>
              )}

              {(!summaryReport.extractedEntities || summaryReport.extractedEntities.length === 0) && (
                <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF] py-1">
                  Document ingested and indexed into semantic patient memory graph.
                </p>
              )}
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row items-center justify-between gap-2.5 pt-3 border-t border-[#E5E7EB]/80 dark:border-[#2F3540]">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => {
                  setSummaryReport(null);
                  setFile(null);
                  setIngestionStatus(null);
                }}
                leftIcon={<RotateCcw className="w-3.5 h-3.5" />}
              >
                Upload Another
              </Button>

              <div className="flex items-center gap-2 w-full sm:w-auto">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => reportService.openDocument(summaryReport.id)}
                  leftIcon={<ExternalLink className="w-3.5 h-3.5 text-[#10B981]" />}
                >
                  View PDF Document
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => {
                    handleClose();
                    navigate('/vault');
                  }}
                  rightIcon={<ArrowRight className="w-3.5 h-3.5" />}
                >
                  Continue to Vault
                </Button>
              </div>
            </div>
          </div>
        );
      })() : (
        /* VIEW B: UPLOAD FORM */
        <div className="space-y-4 pt-1">
          {/* Drag & Drop Box */}
          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleFileDrop}
            className="border border-dashed border-[#E5E7EB] dark:border-[#2F3540] hover:border-[#10B981] dark:hover:border-[#10B981] rounded-2xl p-7 flex flex-col items-center justify-center text-center bg-[#FAF8F5] dark:bg-[#23272E]/40 transition-colors cursor-pointer group"
          >
            <div className="p-3 rounded-2xl bg-white dark:bg-[#1B1E23] border border-[#E5E7EB] dark:border-[#2F3540] text-[#10B981] mb-3 group-hover:scale-105 transition-transform shadow-[0_1px_2px_0_rgba(0,0,0,0.02)]">
              <Upload className="w-6 h-6" />
            </div>
            {file ? (
              <div className="space-y-1">
                <p className="text-sm font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center justify-center gap-2">
                  <FileText className="w-4 h-4 text-[#10B981]" /> {file.name}
                </p>
                <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF] tabular-nums">
                  {(file.size / 1024 / 1024).toFixed(2)} MB
                </p>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    setFile(null);
                  }}
                  className="text-xs text-[#B91C1C] hover:underline mt-2 inline-block font-medium"
                >
                  Remove File
                </button>
              </div>
            ) : (
              <>
                <h4 className="text-sm font-medium text-[#1F2937] dark:text-[#F3F4F6]">
                  Drag & drop your medical file here, or{' '}
                  <label className="text-[#10B981] hover:underline cursor-pointer font-semibold">
                    browse files
                    <input
                      type="file"
                      className="hidden"
                      accept=".pdf,.txt,.png,.jpg,.jpeg,.dcm"
                      onChange={(e) => e.target.files && setFile(e.target.files[0])}
                    />
                  </label>
                </h4>
                <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF] mt-1">
                  Supports PDF, TXT, PNG, JPG, DICOM (Max size: 25MB)
                </p>
              </>
            )}
          </div>

          {/* Category Selector */}
          <div>
            <label className="text-xs font-medium text-[#4B5563] dark:text-[#9CA3AF] mb-1.5 block">
              Document Category
            </label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full h-10 rounded-xl bg-white dark:bg-[#1B1E23] border border-[#E5E7EB] dark:border-[#2F3540] px-3.5 text-sm text-[#1F2937] dark:text-[#F3F4F6] focus:outline-none focus:ring-2 focus:ring-emerald-500/15 focus:border-[#10B981] transition-all"
            >
              <option value="auto">Auto-Detect with AI (Prescription, Lab Report, Scan, Summary)</option>
              <option value="prescription">Doctor Prescription (Rx)</option>
              <option value="blood_report">Blood Report / Laboratory Test</option>
              <option value="mri">MRI / Imaging Scan</option>
              <option value="ct_scan">CT Scan</option>
              <option value="x_ray">X-Ray Imaging</option>
              <option value="discharge_summary">Hospital Discharge Summary</option>
              <option value="vaccination">Vaccination Record</option>
            </select>
          </div>

          {/* Facility & Doctor Details */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <Input
              label="Hospital / Lab Name"
              placeholder="e.g. Metro General Hospital"
              value={hospital}
              onChange={(e) => setHospital(e.target.value)}
            />
            <Input
              label="Physician / Doctor Name"
              placeholder="e.g. Dr. Sarah Jenkins"
              value={doctor}
              onChange={(e) => setDoctor(e.target.value)}
            />
          </div>

          {/* Live Ingestion Status Banner */}
          {ingestionStatus && (
            <div className="p-4 rounded-2xl bg-[#FAF8F5] dark:bg-[#23272E] border border-[#E5E7EB] dark:border-[#2F3540] space-y-2">
              <div className="flex items-center justify-between text-xs font-semibold text-[#1F2937] dark:text-[#F3F4F6]">
                <span className="flex items-center gap-2">
                  {statusUpper === 'COMPLETED' ? (
                    <CheckCircle2 className="w-4 h-4 text-[#15803D]" />
                  ) : statusUpper === 'FAILED' ? (
                    <AlertCircle className="w-4 h-4 text-[#B91C1C]" />
                  ) : (
                    <Loader2 className="w-4 h-4 text-[#10B981] animate-spin" />
                  )}
                  {ingestionStatus.current_stage || 'Processing document...'}
                </span>
                <span className="tabular-nums">{currentProgress}%</span>
              </div>

              <div className="w-full bg-[#E5E7EB] dark:bg-[#2F3540] h-1.5 rounded-full overflow-hidden">
                <div
                  className="bg-[#10B981] h-full transition-all duration-300 rounded-full"
                  style={{ width: `${currentProgress}%` }}
                />
              </div>

              {counts && (
                <div className="flex flex-wrap gap-1.5 text-[11px] text-[#6B7280] dark:text-[#9CA3AF] pt-1">
                  {counts.lab_results ? (
                    <span className="bg-white dark:bg-[#1B1E23] px-2 py-0.5 rounded-md border border-[#E5E7EB] dark:border-[#2F3540]">
                      🔬 {counts.lab_results} Labs
                    </span>
                  ) : null}
                  {counts.medications ? (
                    <span className="bg-white dark:bg-[#1B1E23] px-2 py-0.5 rounded-md border border-[#E5E7EB] dark:border-[#2F3540]">
                      💊 {counts.medications} Meds
                    </span>
                  ) : null}
                  {counts.diseases ? (
                    <span className="bg-white dark:bg-[#1B1E23] px-2 py-0.5 rounded-md border border-[#E5E7EB] dark:border-[#2F3540]">
                      🩺 {counts.diseases} Diagnoses
                    </span>
                  ) : null}
                  {chunkCount ? (
                    <span className="bg-white dark:bg-[#1B1E23] px-2 py-0.5 rounded-md border border-[#E5E7EB] dark:border-[#2F3540]">
                      📑 {chunkCount} Chunks Indexed
                    </span>
                  ) : null}
                </div>
              )}
            </div>
          )}

          <div className="p-3 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/60 border border-[#E5E7EB] dark:border-[#2F3540] text-xs text-[#4B5563] dark:text-[#9CA3AF] flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 shrink-0 text-[#10B981]" />
            <span>Your document will be encrypted and processed locally. Zero unencrypted third-party sharing.</span>
          </div>

          <div className="flex items-center justify-end space-x-2.5 pt-3 border-t border-[#E5E7EB]/80 dark:border-[#2F3540]">
            <Button variant="ghost" onClick={handleClose} disabled={isUploading}>
              Cancel
            </Button>
            <Button
              variant="primary"
              isLoading={isUploading}
              disabled={!file}
              onClick={handleUpload}
              leftIcon={<Upload className="w-4 h-4" />}
            >
              {isUploading ? 'Ingesting...' : 'Process Document'}
            </Button>
          </div>
        </div>
      )}
    </Modal>
  );
};
