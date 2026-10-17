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
    const maxAttempts = 60;
    for (let i = 0; i < maxAttempts; i++) {
      await new Promise((r) => setTimeout(r, 1000));
      try {
        const status = await reportService.getIngestionStatus(docId);
        setIngestionStatus(status);
        const st = (status.status || '').toUpperCase();
        if (st === 'COMPLETED') {
          return;
        } else if (st === 'FAILED') {
          throw new Error(status.error_message || status.error || 'Ingestion failed on server');
        }
      } catch (err: any) {
        if (err?.message?.includes('Ingestion failed') || err?.response?.status === 404) {
          throw err;
        }
      }
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setIsUploading(true);
    setIngestionStatus({
      document_id: 'pending',
      status: 'RECEIVED',
      progress_percent: 5,
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
          status: 'PROCESSING',
          progress_percent: 15,
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
      onClose={() => setUploadModalOpen(false)}
      title="Upload Medical Document"
      description="Securely ingest PDFs, Imaging, or Prescriptions into continuous patient memory."
      maxWidth="lg"
    >
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
              <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF] tabular-nums">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
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
            onChange={(e) => setCategory(e.target.value as ReportCategory)}
            className="w-full h-10 rounded-xl bg-white dark:bg-[#1B1E23] border border-[#E5E7EB] dark:border-[#2F3540] px-3.5 text-sm text-[#1F2937] dark:text-[#F3F4F6] focus:outline-none focus:ring-2 focus:ring-emerald-500/15 focus:border-[#10B981] transition-all"
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
