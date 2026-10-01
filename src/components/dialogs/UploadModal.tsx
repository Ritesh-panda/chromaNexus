import React, { useState } from 'react';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { useUI } from '@/contexts/UIContext';
import { reportService, type DocumentIngestionStatus } from '@/services/report.service';
import { Upload, FileText, ShieldCheck, Loader2, CheckCircle2, AlertCircle } from 'lucide-react';
import type { ReportCategory } from '@/types';

export const UploadModal: React.FC = () => {
  const { uploadModalOpen, setUploadModalOpen, addToast } = useUI();
  const [file, setFile] = useState<File | null>(null);
  const [category, setCategory] = useState<ReportCategory>('blood_report');
  const [hospital, setHospital] = useState('');
  const [doctor, setDoctor] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [ingestionStatus, setIngestionStatus] = useState<DocumentIngestionStatus | null>(null);

  if (!uploadModalOpen) return null;

  const handleFileDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
    }
  };

  const pollStatus = async (docId: string): Promise<void> => {
    const maxAttempts = 30;
    for (let i = 0; i < maxAttempts; i++) {
      await new Promise((r) => setTimeout(r, 1000));
      try {
        const status = await reportService.getIngestionStatus(docId);
        setIngestionStatus(status);
        if (status.status === 'completed' || status.status === 'failed') {
          return;
        }
      } catch {
        break;
      }
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setIsUploading(true);
    setIngestionStatus({
      document_id: 'pending',
      status: 'received',
      progress: 10,
      current_stage: 'Uploading document...',
    });

    try {
      const uploaded = await reportService.uploadReport({
        file,
        category,
        hospitalName: hospital,
        doctorName: doctor,
      });

      if (uploaded?.id) {
        setIngestionStatus({
          document_id: uploaded.id,
          status: 'processing',
          progress: 30,
          current_stage: 'Analyzing document structure & OCR...',
        });
        await pollStatus(uploaded.id);
      }

      addToast({
        type: 'success',
        title: 'Report Processed Successfully!',
        message: `${file.name} has been extracted into your longitudinal patient memory.`,
      });
      setTimeout(() => {
        setUploadModalOpen(false);
        setFile(null);
        setIngestionStatus(null);
      }, 1200);
    } catch {
      addToast({
        type: 'error',
        title: 'Upload Failed',
        message: 'Could not parse document. Please check file format.',
      });
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <Modal
      isOpen={uploadModalOpen}
      onClose={() => setUploadModalOpen(false)}
      title="Upload Medical Document"
      description="Securely ingest PDFs, Imaging, or Prescriptions into continuous patient memory."
      maxWidth="lg"
    >
      <div className="space-y-4 pt-2">
        {/* Drag & Drop Box */}
        <div
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleFileDrop}
          className="border-2 border-dashed border-blue-400/40 dark:border-blue-500/30 hover:border-blue-500 rounded-2xl p-8 flex flex-col items-center justify-center text-center bg-blue-50/30 dark:bg-blue-950/20 transition-colors cursor-pointer group"
        >
          <div className="p-4 rounded-full bg-blue-100 dark:bg-blue-900/40 text-blue-600 dark:text-blue-400 mb-3 group-hover:scale-110 transition-transform">
            <Upload className="w-8 h-8" />
          </div>
          {file ? (
            <div className="space-y-1">
              <p className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center justify-center gap-2">
                <FileText className="w-4 h-4 text-blue-500" /> {file.name}
              </p>
              <p className="text-xs text-slate-400">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  setFile(null);
                }}
                className="text-xs text-rose-500 font-semibold hover:underline mt-2 inline-block"
              >
                Remove File
              </button>
            </div>
          ) : (
            <>
              <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-200">
                Drag & drop your medical file here, or{' '}
                <label className="text-blue-600 dark:text-blue-400 hover:underline cursor-pointer">
                  browse files
                  <input
                    type="file"
                    className="hidden"
                    accept=".pdf,.png,.jpg,.jpeg,.dcm"
                    onChange={(e) => e.target.files && setFile(e.target.files[0])}
                  />
                </label>
              </h4>
              <p className="text-xs text-slate-400 mt-1">Supports PDF, PNG, JPG, DICOM (Max size: 25MB)</p>
            </>
          )}
        </div>

        {/* Category Selector */}
        <div>
          <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5 block">
            Document Category
          </label>
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value as ReportCategory)}
            className="w-full h-11 rounded-2xl bg-white dark:bg-[#0B0F19] border border-slate-200 dark:border-slate-800 px-4 text-sm text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
          >
            <option value="blood_report">Blood Report / Lab Test</option>
            <option value="prescription">Doctor Prescription</option>
            <option value="mri">MRI Scan</option>
            <option value="ct_scan">CT Scan</option>
            <option value="x_ray">X-Ray Imaging</option>
            <option value="discharge_summary">Discharge Summary</option>
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
          <div className="p-4 rounded-2xl bg-blue-50/70 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-900/60 space-y-2">
            <div className="flex items-center justify-between text-xs font-semibold text-blue-900 dark:text-blue-200">
              <span className="flex items-center gap-2">
                {ingestionStatus.status === 'completed' ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                ) : ingestionStatus.status === 'failed' ? (
                  <AlertCircle className="w-4 h-4 text-rose-500" />
                ) : (
                  <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />
                )}
                {ingestionStatus.current_stage || 'Processing document...'}
              </span>
              <span>{ingestionStatus.progress}%</span>
            </div>
            
            <div className="w-full bg-blue-200/50 dark:bg-blue-900/50 h-2 rounded-full overflow-hidden">
              <div
                className="bg-gradient-to-r from-blue-500 to-indigo-600 h-full transition-all duration-300 rounded-full"
                style={{ width: `${ingestionStatus.progress}%` }}
              />
            </div>

            {ingestionStatus.extracted_entity_counts && (
              <div className="flex flex-wrap gap-2 text-[11px] text-slate-600 dark:text-slate-400 pt-1">
                {ingestionStatus.extracted_entity_counts.lab_results ? (
                  <span className="bg-white/80 dark:bg-slate-900/80 px-2 py-0.5 rounded-md border border-slate-200 dark:border-slate-800">
                    🔬 {ingestionStatus.extracted_entity_counts.lab_results} Labs
                  </span>
                ) : null}
                {ingestionStatus.extracted_entity_counts.medications ? (
                  <span className="bg-white/80 dark:bg-slate-900/80 px-2 py-0.5 rounded-md border border-slate-200 dark:border-slate-800">
                    💊 {ingestionStatus.extracted_entity_counts.medications} Meds
                  </span>
                ) : null}
                {ingestionStatus.extracted_entity_counts.diseases ? (
                  <span className="bg-white/80 dark:bg-slate-900/80 px-2 py-0.5 rounded-md border border-slate-200 dark:border-slate-800">
                    🩺 {ingestionStatus.extracted_entity_counts.diseases} Diagnoses
                  </span>
                ) : null}
                {ingestionStatus.indexed_chunk_count ? (
                  <span className="bg-white/80 dark:bg-slate-900/80 px-2 py-0.5 rounded-md border border-slate-200 dark:border-slate-800">
                    📑 {ingestionStatus.indexed_chunk_count} Chunks Indexed
                  </span>
                ) : null}
              </div>
            )}
          </div>
        )}

        <div className="p-3 rounded-2xl bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200/60 dark:border-emerald-800/40 text-xs text-emerald-800 dark:text-emerald-300 flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 shrink-0 text-emerald-500" />
          <span>Your document will be encrypted and processed locally. Zero unencrypted third-party sharing.</span>
        </div>

        <div className="flex items-center justify-end space-x-3 pt-3 border-t border-slate-100 dark:border-slate-800">
          <Button variant="ghost" onClick={() => setUploadModalOpen(false)} disabled={isUploading}>
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
    </Modal>
  );
};
