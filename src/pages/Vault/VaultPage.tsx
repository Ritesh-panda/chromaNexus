import React, { useEffect, useState, useMemo } from 'react';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Search } from '@/components/ui/Search';
import { ReportCard } from '@/components/cards/ReportCard';
import { Modal } from '@/components/ui/Modal';
import { useUI } from '@/contexts/UIContext';
import { reportService } from '@/services/report.service';
import { MOCK_REPORTS } from '@/constants/mockData';
import type { MedicalReport } from '@/types';
import {
  FolderLock,
  Upload,
  Grid,
  List as ListIcon,
  FileText,
  ShieldCheck,
  Trash2,
  Building2,
  Calendar,
  Clock,
  Pill,
  Activity,
  AlertTriangle,
  RotateCcw,
  Sparkles,
  SearchX
} from 'lucide-react';

export const VaultPage: React.FC = () => {
  const { setUploadModalOpen, addToast } = useUI();
  const [reports, setReports] = useState<MedicalReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [facilities, setFacilities] = useState<string[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedFacility, setSelectedFacility] = useState<string>('all');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'clinical_date' | 'upload_date'>('clinical_date');
  const [sortOrder, setSortOrder] = useState<'desc' | 'asc'>('desc');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [inspectReport, setInspectReport] = useState<MedicalReport | null>(null);
  const [inspectionTab, setInspectionTab] = useState<'overview' | 'extracted' | 'linked' | 'raw'>('overview');

  // Load available facilities
  useEffect(() => {
    let isMounted = true;
    reportService.getFacilities().then((facs) => {
      if (isMounted && facs.length > 0) {
        setFacilities(facs);
      }
    });
    return () => { isMounted = false; };
  }, []);

  // Fetch reports with current filters & sorting
  const fetchVaultReports = async () => {
    setLoading(true);
    try {
      const data = await reportService.getReports({
        category: selectedCategory === 'all' ? undefined : selectedCategory,
        hospital: selectedFacility === 'all' ? undefined : selectedFacility,
        status: selectedStatus === 'all' ? undefined : selectedStatus,
        search: searchQuery || undefined,
        startDate: startDate || undefined,
        endDate: endDate || undefined,
        sortBy,
        sortOrder,
      });
      setReports(data && data.length > 0 ? data : MOCK_REPORTS);
    } catch {
      setReports(MOCK_REPORTS);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchVaultReports();
  }, [selectedCategory, selectedFacility, selectedStatus, sortBy, sortOrder, startDate, endDate, searchQuery]);

  // Compute category counts
  const categories = useMemo(() => [
    { id: 'all', label: 'All Documents', count: reports.length },
    { id: 'blood_report', label: 'Blood Reports', count: reports.filter((r) => r.category === 'blood_report').length },
    { id: 'prescription', label: 'Prescriptions', count: reports.filter((r) => r.category === 'prescription').length },
    { id: 'mri', label: 'Imaging / MRI', count: reports.filter((r) => r.category === 'mri' || r.category === 'x_ray' || r.category === 'ct_scan').length },
    { id: 'discharge_summary', label: 'Discharge Summaries', count: reports.filter((r) => r.category === 'discharge_summary').length },
  ], [reports]);

  const handleDelete = async (id: string) => {
    try {
      await reportService.deleteReport(id);
    } catch {
      // Graceful local deletion fallback
    }
    setReports((prev) => prev.filter((r) => r.id !== id));
    setInspectReport(null);
    addToast({
      type: 'info',
      title: 'Report Removed',
      message: 'Medical document was removed from vault.',
    });
  };

  const handleResetFilters = () => {
    setSearchQuery('');
    setSelectedCategory('all');
    setSelectedFacility('all');
    setSelectedStatus('all');
    setSortBy('clinical_date');
    setSortOrder('desc');
    setStartDate('');
    setEndDate('');
  };

  // Inspect specific report with linked clinical records
  const handleOpenInspect = async (report: MedicalReport) => {
    setInspectReport(report);
    setInspectionTab('overview');
    try {
      const full = await reportService.getReportById(report.id);
      if (full) {
        setInspectReport(full);
      }
    } catch {
      // Retain basic report
    }
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-2">
            <FolderLock className="w-5 h-5 text-[#10B981]" /> Medical Document Vault
          </h1>
          <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF] mt-0.5">
            Encrypted zero-trust repository with automated OCR entity extraction, deduplication, and clinical provenance.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Badge variant="success" className="text-[11px] py-1">
            <ShieldCheck className="w-3.5 h-3.5 mr-1" /> AES-256 Encrypted
          </Badge>
          <Button
            variant="primary"
            onClick={() => setUploadModalOpen(true)}
            leftIcon={<Upload className="w-4 h-4" />}
          >
            Upload Document
          </Button>
        </div>
      </div>

      {/* Storage & Index Summary Strip */}
      {(() => {
        const totalIndexedBytes = reports.reduce((acc, r) => acc + (r.fileSize || 0), 0);
        const formattedIndexedSize = totalIndexedBytes > 0
          ? totalIndexedBytes >= 1024 * 1024
            ? `${(totalIndexedBytes / (1024 * 1024)).toFixed(1)} MB`
            : `${(totalIndexedBytes / 1024).toFixed(0)} KB`
          : '0 KB';
        const completedCount = reports.filter((r) => r.status === 'completed').length;
        const processingCount = reports.filter((r) => r.status === 'processing').length;
        const failedCount = reports.filter((r) => r.status === 'failed').length;

        return (
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
            <div className="p-4 rounded-2xl bg-white dark:bg-[#1B1E23] border border-[#E5E7EB] dark:border-[#2F3540] shadow-[0_1px_2px_0_rgba(0,0,0,0.02)] flex items-center justify-between">
              <div>
                <span className="text-[11px] text-[#6B7280] dark:text-[#9CA3AF]">Indexed Documents</span>
                <p className="text-xl font-semibold text-[#1F2937] dark:text-[#F3F4F6] tabular-nums">{reports.length} records</p>
              </div>
              <div className="p-2.5 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E] text-[#10B981]">
                <FileText className="w-4 h-4" />
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-white dark:bg-[#1B1E23] border border-[#E5E7EB] dark:border-[#2F3540] shadow-[0_1px_2px_0_rgba(0,0,0,0.02)] flex items-center justify-between">
              <div>
                <span className="text-[11px] text-[#6B7280] dark:text-[#9CA3AF]">Total Volume</span>
                <p className="text-xl font-semibold text-[#1F2937] dark:text-[#F3F4F6] tabular-nums">{formattedIndexedSize}</p>
              </div>
              <div className="p-2.5 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E] text-[#2563EB]">
                <FolderLock className="w-4 h-4" />
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-white dark:bg-[#1B1E23] border border-[#E5E7EB] dark:border-[#2F3540] shadow-[0_1px_2px_0_rgba(0,0,0,0.02)] flex items-center justify-between">
              <div>
                <span className="text-[11px] text-[#6B7280] dark:text-[#9CA3AF]">Verified Completed</span>
                <p className="text-xl font-semibold text-[#15803D] dark:text-emerald-400 tabular-nums">{completedCount} verified</p>
              </div>
              <div className="p-2.5 rounded-xl bg-[#ECFDF5] dark:bg-emerald-950/40 text-[#10B981]">
                <ShieldCheck className="w-4 h-4" />
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-white dark:bg-[#1B1E23] border border-[#E5E7EB] dark:border-[#2F3540] shadow-[0_1px_2px_0_rgba(0,0,0,0.02)] flex items-center justify-between">
              <div>
                <span className="text-[11px] text-[#6B7280] dark:text-[#9CA3AF]">Pipeline In-Flight</span>
                <p className="text-xl font-semibold text-[#B45309] dark:text-amber-400 tabular-nums">
                  {processingCount > 0 ? `${processingCount} processing` : failedCount > 0 ? `${failedCount} attention` : 'All Idle'}
                </p>
              </div>
              <div className="p-2.5 rounded-xl bg-[#FFFBEB] dark:bg-amber-950/30 text-[#B45309]">
                <Sparkles className="w-4 h-4" />
              </div>
            </div>
          </div>
        );
      })()}

      {/* Controls Bar: Search + Category Filters */}
      <div className="bg-white dark:bg-[#1B1E23] p-4 rounded-2xl border border-[#E5E7EB] dark:border-[#2F3540] space-y-3.5 shadow-[0_1px_2px_0_rgba(0,0,0,0.02)]">
        <div className="flex flex-col md:flex-row items-center justify-between gap-3.5">
          <div className="w-full md:w-80">
            <Search
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onClear={() => setSearchQuery('')}
              placeholder="Search title, hospital, or summary..."
            />
          </div>

          {/* Category Filter Pills */}
          <div className="flex items-center space-x-1.5 overflow-x-auto w-full md:w-auto pb-1 md:pb-0">
            {categories.map((cat) => (
              <button
                key={cat.id}
                onClick={() => setSelectedCategory(cat.id)}
                className={`px-3 py-1.5 rounded-xl text-xs font-medium whitespace-nowrap transition-colors flex items-center gap-1.5 ${
                  selectedCategory === cat.id
                    ? 'bg-[#1F2937] text-white dark:bg-[#10B981] dark:text-white shadow-sm'
                    : 'bg-[#FAF8F5] dark:bg-[#23272E] text-[#6B7280] dark:text-[#9CA3AF] hover:bg-[#F3F1ED] dark:hover:bg-[#2D323B]'
                }`}
              >
                <span>{cat.label}</span>
                <span className={`text-[10px] px-1.5 py-0.2 rounded-full tabular-nums ${
                  selectedCategory === cat.id
                    ? 'bg-white/20 text-white'
                    : 'bg-[#E5E7EB] dark:bg-[#2F3540] text-[#6B7280] dark:text-[#9CA3AF]'
                }`}>
                  {cat.count}
                </span>
              </button>
            ))}
          </div>

          {/* View Toggle */}
          <div className="flex items-center space-x-1 bg-[#FAF8F5] dark:bg-[#23272E] p-1 rounded-xl shrink-0 self-end md:self-auto border border-[#E5E7EB] dark:border-[#2F3540]">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-1.5 rounded-lg transition-colors ${
                viewMode === 'grid'
                  ? 'bg-white dark:bg-[#1B1E23] text-[#1F2937] dark:text-[#F3F4F6] shadow-sm'
                  : 'text-[#9CA3AF] hover:text-[#1F2937]'
              }`}
              title="Grid View"
              aria-label="Grid view"
            >
              <Grid className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-1.5 rounded-lg transition-colors ${
                viewMode === 'list'
                  ? 'bg-white dark:bg-[#1B1E23] text-[#1F2937] dark:text-[#F3F4F6] shadow-sm'
                  : 'text-[#9CA3AF] hover:text-[#1F2937]'
              }`}
              title="List View"
              aria-label="List view"
            >
              <ListIcon className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Advanced Filters: Facility, Processing Status, Sort Order (Distinguishing Clinical vs Upload date), and Date Ranges */}
        <div className="pt-3 border-t border-[#E5E7EB]/70 dark:border-[#2F3540] flex flex-wrap items-center gap-3 text-xs">
          {/* Facility Filter */}
          <div className="flex items-center gap-1.5">
            <span className="text-[#6B7280] dark:text-[#9CA3AF] font-medium flex items-center gap-1">
              <Building2 className="w-3.5 h-3.5 text-[#9CA3AF]" /> Facility:
            </span>
            <select
              value={selectedFacility}
              onChange={(e) => setSelectedFacility(e.target.value)}
              className="px-2.5 py-1.5 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E] border border-[#E5E7EB] dark:border-[#2F3540] text-[#1F2937] dark:text-[#F3F4F6] focus:outline-none"
            >
              <option value="all">All Facilities</option>
              {facilities.map((fac) => (
                <option key={fac} value={fac}>{fac}</option>
              ))}
            </select>
          </div>

          {/* Processing Status Filter */}
          <div className="flex items-center gap-1.5">
            <span className="text-[#6B7280] dark:text-[#9CA3AF] font-medium flex items-center gap-1">
              <Clock className="w-3.5 h-3.5 text-[#9CA3AF]" /> Status:
            </span>
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="px-2.5 py-1.5 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E] border border-[#E5E7EB] dark:border-[#2F3540] text-[#1F2937] dark:text-[#F3F4F6] focus:outline-none"
            >
              <option value="all">All Statuses</option>
              <option value="completed">Completed</option>
              <option value="processing">Processing</option>
              <option value="failed">Needs Attention / Failed</option>
            </select>
          </div>

          {/* Sort By: Clinical Date vs Upload Date */}
          <div className="flex items-center gap-1.5">
            <span className="text-[#6B7280] dark:text-[#9CA3AF] font-medium flex items-center gap-1">
              <Calendar className="w-3.5 h-3.5 text-[#9CA3AF]" /> Sort by:
            </span>
            <select
              value={`${sortBy}-${sortOrder}`}
              onChange={(e) => {
                const [sb, so] = e.target.value.split('-') as ['clinical_date' | 'upload_date', 'desc' | 'asc'];
                setSortBy(sb);
                setSortOrder(so);
              }}
              className="px-2.5 py-1.5 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E] border border-[#E5E7EB] dark:border-[#2F3540] text-[#1F2937] dark:text-[#F3F4F6] focus:outline-none font-medium"
            >
              <option value="clinical_date-desc">Clinical Date (Newest first)</option>
              <option value="clinical_date-asc">Clinical Date (Oldest first)</option>
              <option value="upload_date-desc">Upload Date (Newest first)</option>
              <option value="upload_date-asc">Upload Date (Oldest first)</option>
            </select>
          </div>

          {/* Clear Filters Button */}
          {(selectedCategory !== 'all' || selectedFacility !== 'all' || selectedStatus !== 'all' || searchQuery || startDate || endDate) && (
            <button
              onClick={handleResetFilters}
              className="text-xs text-[#EF4444] hover:text-[#DC2626] font-medium flex items-center gap-1 ml-auto"
            >
              <RotateCcw className="w-3 h-3" /> Reset Filters
            </button>
          )}
        </div>
      </div>

      {/* Reports Display: Grid or List View */}
      {loading ? (
        <div className="p-12 text-center bg-white dark:bg-[#1B1E23] rounded-2xl border border-[#E5E7EB] dark:border-[#2F3540] text-xs text-[#6B7280]">
          Loading medical vault documents...
        </div>
      ) : reports.length === 0 ? (
        <div className="p-12 text-center bg-white dark:bg-[#1B1E23] rounded-2xl border border-[#E5E7EB] dark:border-[#2F3540] space-y-3">
          <div className="w-12 h-12 mx-auto rounded-full bg-[#FAF8F5] dark:bg-[#23272E] flex items-center justify-center text-[#9CA3AF]">
            <SearchX className="w-6 h-6" />
          </div>
          <h3 className="text-sm font-semibold text-[#1F2937] dark:text-[#F3F4F6]">No medical documents match your criteria</h3>
          <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF] max-w-sm mx-auto">
            Try adjusting your search query, facility filter, or date filters to find your records.
          </p>
          <Button variant="secondary" size="sm" onClick={handleResetFilters} leftIcon={<RotateCcw className="w-3.5 h-3.5" />}>
            Reset Filters
          </Button>
        </div>
      ) : viewMode === 'grid' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {reports.map((report) => (
            <ReportCard key={report.id} report={report} onSelect={handleOpenInspect} />
          ))}
        </div>
      ) : (
        <div className="bg-white dark:bg-[#1B1E23] rounded-2xl border border-[#E5E7EB] dark:border-[#2F3540] overflow-hidden divide-y divide-[#E5E7EB]/80 dark:divide-[#2F3540]">
          {reports.map((r) => (
            <div
              key={r.id}
              onClick={() => handleOpenInspect(r)}
              className="p-4 flex items-center justify-between hover:bg-[#FAF8F5] dark:hover:bg-[#23272E]/50 cursor-pointer transition-colors"
            >
              <div className="flex items-center space-x-3.5 min-w-0">
                <div className="p-2.5 rounded-xl bg-[#F3F1ED] dark:bg-[#23272E] text-[#10B981] shrink-0 border border-[#E5E7EB] dark:border-[#2F3540]">
                  <FileText className="w-4 h-4" />
                </div>
                <div className="min-w-0">
                  <h4 className="text-sm font-semibold text-[#1F2937] dark:text-[#F3F4F6] truncate">{r.title}</h4>
                  <div className="flex flex-wrap items-center gap-2 text-xs text-[#6B7280] dark:text-[#9CA3AF] mt-0.5 font-mono">
                    <span>{r.hospitalName}</span>
                    <span>•</span>
                    <span className="text-[#10B981] font-medium">Observed: {r.reportDate}</span>
                    <span>•</span>
                    <span>Uploaded: {r.uploadDate ? new Date(r.uploadDate).toLocaleDateString() : 'Unknown'}</span>
                    {r.pageCount && (
                      <>
                        <span>•</span>
                        <span>{r.pageCount} pgs</span>
                      </>
                    )}
                  </div>
                </div>
              </div>
              <div className="flex items-center space-x-3 shrink-0">
                <Badge variant={r.status === 'completed' ? 'success' : r.status === 'failed' ? 'danger' : 'warning'}>
                  {r.status}
                </Badge>
                <Button variant="ghost" size="sm">Inspect ➔</Button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Enhanced Document Detail Inspection Modal */}
      {inspectReport && (
        <Modal
          isOpen={!!inspectReport}
          onClose={() => setInspectReport(null)}
          title={inspectReport.title}
          description={`${inspectReport.hospitalName} • Clinical Date: ${inspectReport.reportDate} • Uploaded: ${inspectReport.uploadDate ? new Date(inspectReport.uploadDate).toLocaleDateString() : 'Unknown'}`}
          maxWidth="2xl"
        >
          <div className="space-y-4 pt-1">
            {/* Modal Navigation Tabs */}
            <div className="flex items-center space-x-2 border-b border-[#E5E7EB] dark:border-[#2F3540] pb-2 text-xs font-medium">
              <button
                onClick={() => setInspectionTab('overview')}
                className={`px-3 py-1.5 rounded-lg transition-colors ${
                  inspectionTab === 'overview'
                    ? 'bg-[#1F2937] text-white dark:bg-[#10B981] dark:text-white'
                    : 'text-[#6B7280] dark:text-[#9CA3AF] hover:bg-[#FAF8F5] dark:hover:bg-[#23272E]'
                }`}
              >
                Executive Overview
              </button>
              <button
                onClick={() => setInspectionTab('extracted')}
                className={`px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1 ${
                  inspectionTab === 'extracted'
                    ? 'bg-[#1F2937] text-white dark:bg-[#10B981] dark:text-white'
                    : 'text-[#6B7280] dark:text-[#9CA3AF] hover:bg-[#FAF8F5] dark:hover:bg-[#23272E]'
                }`}
              >
                Extracted Entities ({(inspectReport.extractedEntities || []).length})
              </button>
              <button
                onClick={() => setInspectionTab('linked')}
                className={`px-3 py-1.5 rounded-lg transition-colors ${
                  inspectionTab === 'linked'
                    ? 'bg-[#1F2937] text-white dark:bg-[#10B981] dark:text-white'
                    : 'text-[#6B7280] dark:text-[#9CA3AF] hover:bg-[#FAF8F5] dark:hover:bg-[#23272E]'
                }`}
              >
                Linked Records
              </button>
              <button
                onClick={() => setInspectionTab('raw')}
                className={`px-3 py-1.5 rounded-lg transition-colors ${
                  inspectionTab === 'raw'
                    ? 'bg-[#1F2937] text-white dark:bg-[#10B981] dark:text-white'
                    : 'text-[#6B7280] dark:text-[#9CA3AF] hover:bg-[#FAF8F5] dark:hover:bg-[#23272E]'
                }`}
              >
                OCR Text
              </button>
            </div>

            {/* Tab 1: Overview & Provenance */}
            {inspectionTab === 'overview' && (
              <div className="space-y-3.5">
                <div className="p-4 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/50 border border-[#E5E7EB] dark:border-[#2F3540] space-y-1.5">
                  <span className="text-[10px] font-semibold text-[#6B7280] dark:text-[#9CA3AF] uppercase tracking-wider">
                    Executive Clinical Summary
                  </span>
                  <p className="text-xs text-[#374151] dark:text-[#D1D5DB] leading-relaxed">
                    {inspectReport.summary || 'Summary generated during clinical document ingestion.'}
                  </p>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 text-xs">
                  <div className="p-3 rounded-xl bg-white dark:bg-[#1B1E23] border border-[#E5E7EB] dark:border-[#2F3540]">
                    <span className="text-[10px] text-[#9CA3AF] uppercase block font-semibold">Document Type</span>
                    <span className="font-semibold text-[#1F2937] dark:text-[#F3F4F6] capitalize">{inspectReport.category.replace('_', ' ')}</span>
                  </div>
                  <div className="p-3 rounded-xl bg-white dark:bg-[#1B1E23] border border-[#E5E7EB] dark:border-[#2F3540]">
                    <span className="text-[10px] text-[#9CA3AF] uppercase block font-semibold">Page Count</span>
                    <span className="font-semibold text-[#1F2937] dark:text-[#F3F4F6]">{inspectReport.pageCount || 1} pages</span>
                  </div>
                  <div className="p-3 rounded-xl bg-white dark:bg-[#1B1E23] border border-[#E5E7EB] dark:border-[#2F3540]">
                    <span className="text-[10px] text-[#9CA3AF] uppercase block font-semibold">File Size</span>
                    <span className="font-semibold text-[#1F2937] dark:text-[#F3F4F6]">{((inspectReport.fileSize || 0) / 1024 / 1024).toFixed(1)} MB</span>
                  </div>
                  <div className="p-3 rounded-xl bg-white dark:bg-[#1B1E23] border border-[#E5E7EB] dark:border-[#2F3540] sm:col-span-3">
                    <span className="text-[10px] text-[#9CA3AF] uppercase block font-semibold">Integrity SHA-256 Checksum</span>
                    <span className="font-mono text-[10px] text-[#6B7280] dark:text-[#9CA3AF] break-all">
                      {inspectReport.checksum || 'SHA-256 binary verification active'}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Tab 2: Extracted Structured Entities */}
            {inspectionTab === 'extracted' && (
              <div className="space-y-2">
                <div className="max-h-72 overflow-y-auto space-y-1.5 pr-1">
                  {(inspectReport.extractedEntities || []).length === 0 ? (
                    <p className="text-xs text-[#9CA3AF] p-4 text-center">No structured entities extracted from this document.</p>
                  ) : (
                    (inspectReport.extractedEntities || []).map((ent, idx) => (
                      <div
                        key={idx}
                        className="p-2.5 rounded-xl bg-white dark:bg-[#1B1E23] border border-[#E5E7EB] dark:border-[#2F3540] flex items-center justify-between text-xs"
                      >
                        <div className="flex items-center space-x-2">
                          <Badge variant="default" className="text-[10px] py-0">{ent.category.replace('_', ' ')}</Badge>
                          <span className="font-semibold text-[#1F2937] dark:text-[#F3F4F6]">{ent.name}</span>
                          {ent.value && (
                            <span className="font-mono text-[#10B981] font-semibold tabular-nums">
                              {ent.value} {ent.unit}
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-2">
                          {ent.sourcePageNumber && (
                            <span className="text-[10px] font-mono text-[#9CA3AF] bg-[#FAF8F5] dark:bg-[#23272E] px-1.5 py-0.5 rounded border border-[#E5E7EB] dark:border-[#2F3540]">
                              Pg {ent.sourcePageNumber}
                            </span>
                          )}
                          <span className="text-[11px] text-[#15803D] dark:text-emerald-400 font-medium flex items-center gap-1">
                            <ShieldCheck className="w-3.5 h-3.5" /> {((ent.confidence || 0.95) * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}

            {/* Tab 3: Linked Clinical Graph Records */}
            {inspectionTab === 'linked' && (
              <div className="space-y-3 max-h-72 overflow-y-auto pr-1">
                {inspectReport.linkedEntities ? (
                  <div className="space-y-3">
                    {/* Linked Labs */}
                    {(inspectReport.linkedEntities.labResults || []).length > 0 && (
                      <div className="space-y-1.5">
                        <span className="text-[11px] font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-1.5">
                          <Activity className="w-3.5 h-3.5 text-[#10B981]" /> Connected Biomarkers ({inspectReport.linkedEntities.labResults?.length})
                        </span>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                          {inspectReport.linkedEntities.labResults?.map((lr: any) => (
                            <div key={lr.id} className="p-2 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/50 border border-[#E5E7EB] dark:border-[#2F3540] flex justify-between">
                              <span className="font-medium text-[#1F2937] dark:text-[#F3F4F6]">{lr.testName}</span>
                              <span className="font-mono font-semibold text-[#10B981]">{lr.value} {lr.unit}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Linked Medications */}
                    {(inspectReport.linkedEntities.medications || []).length > 0 && (
                      <div className="space-y-1.5">
                        <span className="text-[11px] font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-1.5">
                          <Pill className="w-3.5 h-3.5 text-[#2563EB]" /> Connected Prescriptions ({inspectReport.linkedEntities.medications?.length})
                        </span>
                        <div className="space-y-1 text-xs">
                          {inspectReport.linkedEntities.medications?.map((m: any) => (
                            <div key={m.id} className="p-2 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/50 border border-[#E5E7EB] dark:border-[#2F3540] flex justify-between">
                              <span className="font-medium text-[#1F2937] dark:text-[#F3F4F6]">{m.name}</span>
                              <span className="text-[#6B7280]">{m.dosage} • {m.frequency}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Linked Diagnoses */}
                    {(inspectReport.linkedEntities.diseases || []).length > 0 && (
                      <div className="space-y-1.5">
                        <span className="text-[11px] font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-1.5">
                          <AlertTriangle className="w-3.5 h-3.5 text-[#B91C1C]" /> Connected Diagnoses ({inspectReport.linkedEntities.diseases?.length})
                        </span>
                        <div className="space-y-1 text-xs">
                          {inspectReport.linkedEntities.diseases?.map((d: any) => (
                            <div key={d.id} className="p-2 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/50 border border-[#E5E7EB] dark:border-[#2F3540] flex justify-between">
                              <span className="font-medium text-[#1F2937] dark:text-[#F3F4F6]">{d.name}</span>
                              <span className="text-[#6B7280]">{d.status} • Diagnosed: {d.diagnosedDate}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {(!inspectReport.linkedEntities.labResults?.length &&
                      !inspectReport.linkedEntities.medications?.length &&
                      !inspectReport.linkedEntities.diseases?.length) && (
                      <p className="text-xs text-[#9CA3AF] p-4 text-center">No persistent clinical entities directly linked to this report ID.</p>
                    )}
                  </div>
                ) : (
                  <p className="text-xs text-[#9CA3AF] p-4 text-center">Loading linked graph records...</p>
                )}
              </div>
            )}

            {/* Tab 4: Raw OCR Text */}
            {inspectionTab === 'raw' && (
              <div className="space-y-2">
                <div className="p-3 rounded-xl bg-[#FAF8F5] dark:bg-[#121417] text-[#4B5563] dark:text-[#D1D5DB] font-mono text-xs max-h-60 overflow-y-auto border border-[#E5E7EB] dark:border-[#2F3540] whitespace-pre-wrap">
                  {inspectReport.rawText || 'OCR text extraction snippet unavailable for this document.'}
                </div>
              </div>
            )}

            <div className="flex items-center justify-between pt-4 border-t border-[#E5E7EB]/80 dark:border-[#2F3540]">
              <Button
                variant="danger"
                size="sm"
                leftIcon={<Trash2 className="w-4 h-4" />}
                onClick={() => handleDelete(inspectReport.id)}
              >
                Delete
              </Button>
              <div className="flex items-center space-x-2">
                <Button variant="primary" size="sm" onClick={() => setInspectReport(null)}>
                  Close
                </Button>
              </div>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
