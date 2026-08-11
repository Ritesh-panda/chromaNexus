import React, { useState } from 'react';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Badge } from '../../components/ui/Badge';
import { Search } from '../../components/ui/Search';
import { ReportCard } from '../../components/cards/ReportCard';
import { Modal } from '../../components/ui/Modal';
import { useUI } from '../../contexts/UIContext';
import { MOCK_REPORTS } from '../../constants/mockData';
import { MedicalReport, ReportCategory } from '../../types';
import {
  FolderLock,
  Upload,
  Grid,
  List as ListIcon,
  Filter,
  FileText,
  Building2,
  Calendar,
  User,
  ShieldCheck,
  CheckCircle2,
  Trash2,
  Download
} from 'lucide-react';
import { motion } from 'framer-motion';

export const VaultPage: React.FC = () => {
  const { setUploadModalOpen, addToast } = useUI();
  const [reports, setReports] = useState<MedicalReport[]>(MOCK_REPORTS);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [inspectReport, setInspectReport] = useState<MedicalReport | null>(null);

  const categories = [
    { id: 'all', label: 'All Documents' },
    { id: 'blood_report', label: 'Blood Reports' },
    { id: 'prescription', label: 'Prescriptions' },
    { id: 'mri', label: 'MRI Scans' },
    { id: 'discharge_summary', label: 'Discharge Summaries' },
  ];

  const filteredReports = reports.filter((r) => {
    const matchesCategory = selectedCategory === 'all' || r.category === selectedCategory;
    const matchesSearch =
      r.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.hospitalName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (r.summary && r.summary.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesCategory && matchesSearch;
  });

  const handleDelete = (id: string) => {
    setReports((prev) => prev.filter((r) => r.id !== id));
    setInspectReport(null);
    addToast({
      type: 'info',
      title: 'Report Removed',
      message: 'Medical document was deleted from vault.',
    });
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <FolderLock className="w-6 h-6 text-blue-500" /> Medical Vault
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Encrypted storage & structured entity extraction of all your healthcare records.
          </p>
        </div>

        <Button
          variant="primary"
          onClick={() => setUploadModalOpen(true)}
          leftIcon={<Upload className="w-4 h-4" />}
        >
          Upload New Document
        </Button>
      </div>

      {/* Controls Bar: Search + Category Filters + Grid/List View Toggle */}
      <div className="glass-card p-4 rounded-2xl border border-slate-200 dark:border-slate-800 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="w-full md:w-80">
          <Search
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onClear={() => setSearchQuery('')}
            placeholder="Filter files by name or hospital..."
          />
        </div>

        {/* Category Pills */}
        <div className="flex items-center space-x-1 overflow-x-auto w-full md:w-auto pb-1 md:pb-0">
          {categories.map((cat) => (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(cat.id)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-colors ${
                selectedCategory === cat.id
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200'
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>

        {/* View Toggle */}
        <div className="flex items-center space-x-1 bg-slate-100 dark:bg-slate-800 p-1 rounded-xl shrink-0">
          <button
            onClick={() => setViewMode('grid')}
            className={`p-1.5 rounded-lg transition-colors ${
              viewMode === 'grid' ? 'bg-white dark:bg-slate-900 text-blue-600 shadow-sm' : 'text-slate-400'
            }`}
            title="Grid View"
          >
            <Grid className="w-4 h-4" />
          </button>
          <button
            onClick={() => setViewMode('list')}
            className={`p-1.5 rounded-lg transition-colors ${
              viewMode === 'list' ? 'bg-white dark:bg-slate-900 text-blue-600 shadow-sm' : 'text-slate-400'
            }`}
            title="List View"
          >
            <ListIcon className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Grid or List View */}
      {viewMode === 'grid' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredReports.map((report) => (
            <ReportCard key={report.id} report={report} onSelect={(r) => setInspectReport(r)} />
          ))}
        </div>
      ) : (
        <div className="glass-card rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden divide-y divide-slate-100 dark:divide-slate-800">
          {filteredReports.map((r) => (
            <div
              key={r.id}
              onClick={() => setInspectReport(r)}
              className="p-4 flex items-center justify-between hover:bg-slate-50 dark:hover:bg-slate-800/50 cursor-pointer transition-colors"
            >
              <div className="flex items-center space-x-4">
                <div className="p-3 rounded-xl bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400">
                  <FileText className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100">{r.title}</h4>
                  <p className="text-xs text-slate-400 font-mono">{r.fileName} • {r.hospitalName} • {r.reportDate}</p>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <Badge variant={r.status === 'completed' ? 'success' : 'warning'}>{r.status}</Badge>
                <Button variant="ghost" size="sm">Inspect ➔</Button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Document Detail Inspection Drawer / Modal */}
      {inspectReport && (
        <Modal
          isOpen={!!inspectReport}
          onClose={() => setInspectReport(null)}
          title={inspectReport.title}
          description={`${inspectReport.hospitalName} • Date: ${inspectReport.reportDate}`}
          maxWidth="xl"
        >
          <div className="space-y-4 pt-2">
            <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-800 space-y-2">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">AI Executive Summary</span>
              <p className="text-xs text-slate-700 dark:text-slate-200 leading-relaxed">{inspectReport.summary}</p>
            </div>

            {/* Extracted Clinical Entities Breakdown */}
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
                Extracted Structured Entities ({inspectReport.extractedEntities.length})
              </h4>
              <div className="space-y-2">
                {inspectReport.extractedEntities.map((ent, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-xl bg-white dark:bg-[#0B0F19] border border-slate-200 dark:border-slate-800 flex items-center justify-between text-xs"
                  >
                    <div className="flex items-center space-x-2">
                      <Badge variant="default">{ent.category.replace('_', ' ')}</Badge>
                      <span className="font-bold text-slate-800 dark:text-slate-100">{ent.name}</span>
                      {ent.value && <span className="font-mono text-blue-600 font-bold">{ent.value} {ent.unit}</span>}
                    </div>
                    <span className="text-[11px] text-emerald-600 font-semibold flex items-center gap-1">
                      <ShieldCheck className="w-3.5 h-3.5" /> {(ent.confidence * 100).toFixed(0)}% Match
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Raw OCR Text Snippet */}
            {inspectReport.rawText && (
              <div className="space-y-1">
                <span className="text-[11px] font-bold text-slate-400 uppercase">OCR Raw Extracted Text</span>
                <div className="p-3 rounded-xl bg-slate-900 text-slate-200 font-mono text-[11px] max-h-32 overflow-y-auto">
                  {inspectReport.rawText}
                </div>
              </div>
            )}

            <div className="flex items-center justify-between pt-4 border-t border-slate-100 dark:border-slate-800">
              <Button
                variant="danger"
                size="sm"
                leftIcon={<Trash2 className="w-4 h-4" />}
                onClick={() => handleDelete(inspectReport.id)}
              >
                Delete Document
              </Button>
              <div className="flex items-center space-x-2">
                <Button variant="outline" size="sm" leftIcon={<Download className="w-4 h-4" />}>
                  Download File
                </Button>
                <Button variant="primary" size="sm" onClick={() => setInspectReport(null)}>
                  Close Inspection
                </Button>
              </div>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
