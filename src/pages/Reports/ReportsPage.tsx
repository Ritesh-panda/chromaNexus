import React, { useEffect, useState } from 'react';
import { Table } from '@/components/ui/Table';
import type { Column } from '@/components/ui/Table';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Search } from '@/components/ui/Search';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';
import { Input } from '@/components/ui/Input';
import { reportService } from '@/services/report.service';
import { useAuth } from '@/contexts/AuthContext';
import { useUI } from '@/contexts/UIContext';
import { MOCK_REPORTS } from '@/constants/mockData';
import type { MedicalReport } from '@/types';
import {
  FileCheck,
  Eye,
  Download,
  ShieldCheck,
  FileText,
  Calendar,
  Edit3,
  Trash2,
  ExternalLink,
  CheckCircle2,
} from 'lucide-react';

export const ReportsPage: React.FC = () => {
  const { user } = useAuth();
  const { addToast } = useUI();
  const [reports, setReports] = useState<MedicalReport[]>([]);
  const [search, setSearch] = useState('');
  const [hospitalFilter, setHospitalFilter] = useState('all');
  const [selectedReport, setSelectedReport] = useState<MedicalReport | null>(null);

  // Edit Modal State
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editTitle, setEditTitle] = useState('');
  const [editCategory, setEditCategory] = useState('');
  const [editDate, setEditDate] = useState('');
  const [editHospital, setEditHospital] = useState('');
  const [editDoctor, setEditDoctor] = useState('');
  const [isUpdating, setIsUpdating] = useState(false);

  // Delete Modal State
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const fetchReports = async () => {
    try {
      const data = await reportService.getReports(
        hospitalFilter === 'all' ? undefined : hospitalFilter,
        search || undefined
      );
      const isDemo = user?.email === 'alex.vance@example.com';
      const res = isDemo ? (data && data.length > 0 ? data : MOCK_REPORTS) : (data || []);
      setReports(res);
      setSelectedReport((prev) => {
        if (!prev) return res.length > 0 ? res[0] : null;
        return res.find((r) => r.id === prev.id) || (res.length > 0 ? res[0] : null);
      });
    } catch {
      const isDemo = user?.email === 'alex.vance@example.com';
      const res = isDemo ? MOCK_REPORTS : [];
      setReports(res);
      setSelectedReport((prev) => prev ?? (res.length > 0 ? res[0] : null));
    }
  };

  useEffect(() => {
    fetchReports();
  }, [hospitalFilter, search]);

  const handleOpenEdit = (r: MedicalReport) => {
    setEditTitle(r.title);
    setEditCategory(r.category);
    setEditDate(r.reportDate);
    setEditHospital(r.hospitalName);
    setEditDoctor(r.doctorName || '');
    setIsEditModalOpen(true);
  };

  const handleSaveEdit = async () => {
    if (!selectedReport) return;
    setIsUpdating(true);
    try {
      const updated = await reportService.updateReport(selectedReport.id, {
        title: editTitle,
        category: editCategory as any,
        reportDate: editDate,
        hospitalName: editHospital,
        doctorName: editDoctor,
      });
      addToast({
        type: 'success',
        title: 'Report Updated',
        message: 'Clinical record details have been saved successfully.',
      });
      setIsEditModalOpen(false);
      setSelectedReport(updated);
      fetchReports();
    } catch {
      addToast({
        type: 'error',
        title: 'Update Failed',
        message: 'Could not update report details.',
      });
    } finally {
      setIsUpdating(false);
    }
  };

  const handleConfirmDelete = async () => {
    if (!selectedReport) return;
    setIsDeleting(true);
    try {
      await reportService.deleteReport(selectedReport.id);
      addToast({
        type: 'success',
        title: 'Report Deleted',
        message: 'Medical document removed from vault.',
      });
      setIsDeleteModalOpen(false);
      setSelectedReport(null);
      fetchReports();
    } catch {
      addToast({
        type: 'error',
        title: 'Deletion Failed',
        message: 'Unable to delete the report.',
      });
    } finally {
      setIsDeleting(false);
    }
  };

  const hospitals = Array.from(new Set(reports.map((r) => r.hospitalName).filter(Boolean)));

  const filteredReports = reports.filter((r) => {
    const matchesSearch =
      r.title.toLowerCase().includes(search.toLowerCase()) ||
      r.hospitalName.toLowerCase().includes(search.toLowerCase());
    const matchesHospital = hospitalFilter === 'all' || r.hospitalName === hospitalFilter;
    return matchesSearch && matchesHospital;
  });

  const columns: Column<MedicalReport>[] = [
    {
      header: 'Report Title',
      accessor: (r) => (
        <div>
          <span className="font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-2">
            <FileText className="w-3.5 h-3.5 text-[#10B981]" /> {r.title}
          </span>
          <span className="text-[11px] font-mono text-[#9CA3AF] tabular-nums">{r.fileName}</span>
        </div>
      ),
    },
    {
      header: 'Category',
      accessor: (r) => <Badge variant="secondary">{r.category.replace('_', ' ')}</Badge>,
    },
    {
      header: 'Hospital / Facility',
      accessor: (r) => <span className="text-xs text-[#6B7280] dark:text-[#9CA3AF]">{r.hospitalName}</span>,
    },
    {
      header: 'Report Date',
      accessor: (r) => (
        <span className="text-xs font-mono tabular-nums text-[#6B7280] dark:text-[#9CA3AF]">{r.reportDate}</span>
      ),
    },
    {
      header: 'Status',
      accessor: (r) => <Badge variant={r.status === 'completed' ? 'success' : 'warning'}>{r.status}</Badge>,
    },
    {
      header: 'Action',
      accessor: (r) => (
        <div className="flex items-center gap-1.5">
          <Button
            variant={selectedReport?.id === r.id ? 'secondary' : 'ghost'}
            size="sm"
            onClick={() => setSelectedReport(r)}
            leftIcon={<Eye className="w-3.5 h-3.5" />}
          >
            Inspect
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6 pb-12">
      <div>
        <h1 className="text-xl sm:text-2xl font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-2">
          <FileCheck className="w-5 h-5 text-[#10B981]" /> Medical Reports Directory
        </h1>
        <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF] mt-0.5">
          Browse, filter, and inspect structured data extractions across all medical documentation.
        </p>
      </div>

      {/* Filter Row */}
      <div className="bg-white dark:bg-[#1B1E23] p-3.5 sm:p-4 rounded-2xl border border-[#E5E7EB] dark:border-[#2F3540] flex flex-col md:flex-row items-center justify-between gap-3.5 shadow-[0_1px_2px_0_rgba(0,0,0,0.02)]">
        <div className="w-full md:w-80">
          <Search
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onClear={() => setSearch('')}
            placeholder="Search report title or facility..."
          />
        </div>

        <div className="flex items-center space-x-2.5 w-full md:w-auto">
          <label className="text-xs font-medium text-[#6B7280] dark:text-[#9CA3AF] shrink-0">Facility:</label>
          <select
            value={hospitalFilter}
            onChange={(e) => setHospitalFilter(e.target.value)}
            className="h-9 px-3 rounded-xl bg-white dark:bg-[#1B1E23] border border-[#E5E7EB] dark:border-[#2F3540] text-xs text-[#1F2937] dark:text-[#F3F4F6] focus:outline-none focus:ring-2 focus:ring-emerald-500/15 focus:border-[#10B981]"
          >
            <option value="all">All Healthcare Facilities</option>
            {hospitals.map((h) => (
              <option key={h} value={h}>
                {h}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Grid: Master Table + Side Detail Preview */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <Table
            columns={columns}
            data={filteredReports}
            keyExtractor={(r) => r.id}
            onRowClick={(r) => setSelectedReport(r)}
          />
        </div>

        {/* Selected Report Inspection Card */}
        {selectedReport && (
          <Card className="p-5 sm:p-6 border-[#E5E7EB] dark:border-[#2F3540] space-y-4 h-fit bg-white dark:bg-[#1B1E23]">
            <div className="flex items-start justify-between pb-3.5 border-b border-[#E5E7EB]/80 dark:border-[#2F3540] gap-2">
              <div>
                <Badge variant="default" className="mb-1 text-[10px]">
                  {selectedReport.category.replace('_', ' ')}
                </Badge>
                <h3 className="text-sm sm:text-base font-semibold text-[#1F2937] dark:text-[#F3F4F6]">
                  {selectedReport.title}
                </h3>
                <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF] mt-0.5">{selectedReport.hospitalName}</p>
                <p className="text-[11px] text-[#9CA3AF] font-mono tabular-nums flex items-center gap-1 mt-0.5">
                  <Calendar className="w-3 h-3" /> {selectedReport.reportDate}
                </p>
              </div>
              <span className="text-[11px] font-mono font-medium text-[#15803D] dark:text-emerald-400 flex items-center gap-1 shrink-0">
                <ShieldCheck className="w-3.5 h-3.5" /> 98% Verified
              </span>
            </div>

            <div className="space-y-1.5">
              <span className="text-[10px] font-semibold text-[#6B7280] dark:text-[#9CA3AF] uppercase tracking-wider">
                Clinical Summary
              </span>
              <p className="text-xs text-[#4B5563] dark:text-[#D1D5DB] leading-relaxed bg-[#FAF8F5] dark:bg-[#23272E]/50 border border-[#E5E7EB]/70 dark:border-[#2F3540] p-3 rounded-xl">
                {selectedReport.summary}
              </p>
            </div>

            <div className="space-y-1.5">
              <span className="text-[10px] font-semibold text-[#6B7280] dark:text-[#9CA3AF] uppercase tracking-wider">
                Extracted Structured Entities
              </span>
              <div className="space-y-1.5 max-h-44 overflow-y-auto">
                {(() => {
                  const dedupedMap = new Map<string, (typeof selectedReport.extractedEntities)[0]>();
                  for (const ent of selectedReport.extractedEntities || []) {
                    let normName = ent.name.trim().toLowerCase();
                    if (normName.includes('type 2 diabetes') || normName === 'diabetes') {
                      normName = 'type 2 diabetes mellitus';
                    }
                    const key = `${ent.category || ''}_${normName}`;
                    const existing = dedupedMap.get(key);
                    if (!existing) {
                      dedupedMap.set(key, ent);
                    } else {
                      if (!existing.value && ent.value) {
                        dedupedMap.set(key, ent);
                      } else if (existing.value && ent.value && ent.value.length > existing.value.length) {
                        dedupedMap.set(key, ent);
                      }
                    }
                  }
                  return Array.from(dedupedMap.values()).map((ent, i) => (
                    <div
                      key={i}
                      className="p-2 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/60 border border-[#E5E7EB] dark:border-[#2F3540] flex items-center justify-between text-xs"
                    >
                      <span className="font-medium text-[#1F2937] dark:text-[#F3F4F6]">{ent.name}</span>
                      {ent.value && (
                        <span className="font-mono text-[#10B981] font-semibold tabular-nums text-right ml-2">
                          {ent.value} {ent.unit || ''}
                        </span>
                      )}
                    </div>
                  ));
                })()}
              </div>
            </div>

            {/* Document Controls */}
            <div className="space-y-2 pt-2 border-t border-[#E5E7EB]/80 dark:border-[#2F3540]">
              <div className="grid grid-cols-2 gap-2">
                <Button
                  variant="primary"
                  size="sm"
                  className="w-full"
                  leftIcon={<Eye className="w-3.5 h-3.5" />}
                  onClick={() => reportService.openDocument(selectedReport.id)}
                >
                  View PDF
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  className="w-full"
                  leftIcon={<Download className="w-3.5 h-3.5" />}
                  onClick={() => reportService.downloadDocument(selectedReport.id, selectedReport.fileName)}
                >
                  Download
                </Button>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full text-xs text-[#4B5563] dark:text-[#9CA3AF] hover:bg-[#FAF8F5] dark:hover:bg-[#23272E]"
                  leftIcon={<Edit3 className="w-3.5 h-3.5" />}
                  onClick={() => handleOpenEdit(selectedReport)}
                >
                  Edit Details
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full text-xs text-[#DC2626] hover:bg-red-50 dark:hover:bg-red-950/30"
                  leftIcon={<Trash2 className="w-3.5 h-3.5 text-[#DC2626]" />}
                  onClick={() => setIsDeleteModalOpen(true)}
                >
                  Delete
                </Button>
              </div>
            </div>
          </Card>
        )}
      </div>

      {/* EDIT REPORT MODAL */}
      <Modal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        title="Edit Medical Report Details"
        description="Update the clinical metadata, consultation date, and healthcare facility."
      >
        <div className="space-y-3.5 pt-1 text-xs">
          <Input
            label="Report Title"
            value={editTitle}
            onChange={(e) => setEditTitle(e.target.value)}
          />

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-medium text-[#4B5563] dark:text-[#9CA3AF] mb-1 block">
                Category
              </label>
              <select
                value={editCategory}
                onChange={(e) => setEditCategory(e.target.value)}
                className="w-full h-9 rounded-xl bg-white dark:bg-[#1B1E23] border border-[#E5E7EB] dark:border-[#2F3540] px-3 text-xs text-[#1F2937] dark:text-[#F3F4F6] focus:outline-none focus:ring-2 focus:ring-emerald-500/15 focus:border-[#10B981]"
              >
                <option value="prescription">Prescription (Rx)</option>
                <option value="blood_report">Blood Report / Lab Test</option>
                <option value="mri">MRI / Scan</option>
                <option value="x_ray">X-Ray</option>
                <option value="discharge_summary">Discharge Summary</option>
                <option value="doctor_notes">Doctor Consultation Note</option>
              </select>
            </div>

            <Input
              label="Clinical Date (YYYY-MM-DD)"
              value={editDate}
              onChange={(e) => setEditDate(e.target.value)}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Hospital / Facility Name"
              value={editHospital}
              onChange={(e) => setEditHospital(e.target.value)}
            />
            <Input
              label="Doctor / Physician"
              value={editDoctor}
              onChange={(e) => setEditDoctor(e.target.value)}
            />
          </div>

          <div className="flex items-center justify-end space-x-2 pt-3 border-t border-[#E5E7EB]/80 dark:border-[#2F3540]">
            <Button variant="ghost" size="sm" onClick={() => setIsEditModalOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              isLoading={isUpdating}
              onClick={handleSaveEdit}
            >
              Save Changes
            </Button>
          </div>
        </div>
      </Modal>

      {/* DELETE CONFIRMATION MODAL */}
      <Modal
        isOpen={isDeleteModalOpen}
        onClose={() => setIsDeleteModalOpen(false)}
        title="Delete Medical Record?"
        description="Are you sure you want to permanently delete this report from your vault? This will also remove associated timeline events."
      >
        <div className="space-y-4 pt-1">
          <div className="p-3.5 rounded-xl bg-red-50 dark:bg-rose-950/30 border border-red-200/80 dark:border-rose-900/40 text-xs text-[#B91C1C] dark:text-rose-400">
            Document: <strong>{selectedReport?.title}</strong> ({selectedReport?.fileName})
          </div>

          <div className="flex items-center justify-end space-x-2 pt-2">
            <Button variant="ghost" size="sm" onClick={() => setIsDeleteModalOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="danger"
              size="sm"
              isLoading={isDeleting}
              onClick={handleConfirmDelete}
            >
              Permanently Delete
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
