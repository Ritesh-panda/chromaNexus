import React, { useState } from 'react';
import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { useUI } from '../../contexts/UIContext';
import { reportService } from '../../services/report.service';
import { Upload, FileText, CheckCircle2, AlertCircle, X, ShieldCheck } from 'lucide-react';
import type { ReportCategory } from '../../types';

export const UploadModal: React.FC = () => {
  const { uploadModalOpen, setUploadModalOpen, addToast } = useUI();
  const [file, setFile] = useState<File | null>(null);
  const [category, setCategory] = useState<ReportCategory>('blood_report');
  const [hospital, setHospital] = useState('');
  const [doctor, setDoctor] = useState('');
  const [isUploading, setIsUploading] = useState(false);

  if (!uploadModalOpen) return null;

  const handleFileDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setIsUploading(true);
    try {
      await reportService.uploadReport({
        file,
        category,
        hospitalName: hospital,
        doctorName: doctor,
      });
      addToast({
        type: 'success',
        title: 'Report Processed Successfully!',
        message: `${file.name} has been extracted into your longitudinal patient memory.`,
      });
      setUploadModalOpen(false);
      setFile(null);
    } catch (err) {
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

        <div className="p-3 rounded-2xl bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200/60 dark:border-emerald-800/40 text-xs text-emerald-800 dark:text-emerald-300 flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 shrink-0 text-emerald-500" />
          <span>Your document will be encrypted and processed locally. Zero unencrypted third-party sharing.</span>
        </div>

        <div className="flex items-center justify-end space-x-3 pt-3 border-t border-slate-100 dark:border-slate-800">
          <Button variant="ghost" onClick={() => setUploadModalOpen(false)}>
            Cancel
          </Button>
          <Button
            variant="primary"
            isLoading={isUploading}
            disabled={!file}
            onClick={handleUpload}
            leftIcon={<Upload className="w-4 h-4" />}
          >
            Process Document
          </Button>
        </div>
      </div>
    </Modal>
  );
};
