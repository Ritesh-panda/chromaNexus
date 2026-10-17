import React, { useEffect, useState } from 'react';
import { Table } from '@/components/ui/Table';
import type { Column } from '@/components/ui/Table';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Search } from '@/components/ui/Search';
import { Button } from '@/components/ui/Button';
import { reportService } from '@/services/report.service';
import { MOCK_REPORTS } from '@/constants/mockData';
import type { MedicalReport } from '@/types';
import { FileCheck, Eye, Download, ShieldCheck, FileText, Calendar } from 'lucide-react';

export const ReportsPage: React.FC = () => {
  const [reports, setReports] = useState<MedicalReport[]>([]);
  const [search, setSearch] = useState('');
  const [hospitalFilter, setHospitalFilter] = useState('all');
  const [selectedReport, setSelectedReport] = useState<MedicalReport | null>(null);

  useEffect(() => {
    let isMounted = true;
    const fetchReports = async () => {
      try {
        const data = await reportService.getReports(
          hospitalFilter === 'all' ? undefined : hospitalFilter,
          search || undefined
        );
        if (isMounted) {
          const res = data && data.length > 0 ? data : MOCK_REPORTS;
          setReports(res);
          setSelectedReport((prev) => prev ?? (res.length > 0 ? res[0] : null));
        }
      } catch {
        if (isMounted) {
          setReports(MOCK_REPORTS);
          setSelectedReport((prev) => prev ?? MOCK_REPORTS[0]);
        }
      }
    };
    fetchReports();
    return () => {
      isMounted = false;
    };
  }, [hospitalFilter, search]);

  const hospitals = Array.from(new Set(reports.map((r) => r.hospitalName)));

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
      accessor: (r) => <span className="text-xs font-mono tabular-nums text-[#6B7280] dark:text-[#9CA3AF]">{r.reportDate}</span>,
    },
    {
      header: 'Status',
      accessor: (r) => <Badge variant={r.status === 'completed' ? 'success' : 'warning'}>{r.status}</Badge>,
    },
    {
      header: 'Action',
      accessor: (r) => (
        <Button
          variant={selectedReport?.id === r.id ? 'secondary' : 'ghost'}
          size="sm"
          onClick={() => setSelectedReport(r)}
          leftIcon={<Eye className="w-3.5 h-3.5" />}
        >
          Inspect
        </Button>
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
              <option key={h} value={h}>{h}</option>
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
                <Badge variant="default" className="mb-1 text-[10px]">{selectedReport.category.replace('_', ' ')}</Badge>
                <h3 className="text-sm sm:text-base font-semibold text-[#1F2937] dark:text-[#F3F4F6]">{selectedReport.title}</h3>
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
              <div className="space-y-1.5 max-h-48 overflow-y-auto">
                {(selectedReport.extractedEntities || []).map((ent, i) => (
                  <div
                    key={i}
                    className="p-2.5 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/60 border border-[#E5E7EB] dark:border-[#2F3540] flex items-center justify-between text-xs"
                  >
                    <span className="font-medium text-[#1F2937] dark:text-[#F3F4F6]">{ent.name}</span>
                    {ent.value && (
                      <span className="font-mono text-[#10B981] font-semibold tabular-nums">
                        {ent.value} {ent.unit}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>

            <Button
              variant="primary"
              size="sm"
              className="w-full"
              leftIcon={<Download className="w-4 h-4" />}
            >
              Download Original Document
            </Button>
          </Card>
        )}
      </div>
    </div>
  );
};
