import React, { useState } from 'react';
import { Table } from '@/components/ui/Table';
import type { Column } from '@/components/ui/Table';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Search } from '@/components/ui/Search';
import { Button } from '@/components/ui/Button';
import { MOCK_REPORTS } from '@/constants/mockData';
import type { MedicalReport } from '@/types';
import { FileCheck, Eye, Download, ShieldCheck } from 'lucide-react';

export const ReportsPage: React.FC = () => {
  const [reports] = useState<MedicalReport[]>(MOCK_REPORTS);
  const [search, setSearch] = useState('');
  const [hospitalFilter, setHospitalFilter] = useState('all');
  const [selectedReport, setSelectedReport] = useState<MedicalReport | null>(reports[0]);

  const hospitals = Array.from(new Set(reports.map((r) => r.hospitalName)));

  const filteredReports = reports.filter((r) => {
    const matchesSearch = r.title.toLowerCase().includes(search.toLowerCase()) || r.hospitalName.toLowerCase().includes(search.toLowerCase());
    const matchesHospital = hospitalFilter === 'all' || r.hospitalName === hospitalFilter;
    return matchesSearch && matchesHospital;
  });

  const columns: Column<MedicalReport>[] = [
    {
      header: 'Report Title',
      accessor: (r) => (
        <div>
          <span className="font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <FileCheck className="w-4 h-4 text-blue-500" /> {r.title}
          </span>
          <span className="text-[11px] font-mono text-slate-400">{r.fileName}</span>
        </div>
      ),
    },
    {
      header: 'Category',
      accessor: (r) => <Badge variant="secondary">{r.category.replace('_', ' ')}</Badge>,
    },
    {
      header: 'Hospital / Clinic',
      accessor: (r) => <span className="text-xs font-medium">{r.hospitalName}</span>,
    },
    {
      header: 'Report Date',
      accessor: (r) => <span className="text-xs font-mono">{r.reportDate}</span>,
    },
    {
      header: 'Status',
      accessor: (r) => <Badge variant={r.status === 'completed' ? 'success' : 'warning'}>{r.status}</Badge>,
    },
    {
      header: 'Action',
      accessor: (r) => (
        <Button variant="ghost" size="sm" onClick={() => setSelectedReport(r)} leftIcon={<Eye className="w-3.5 h-3.5" />}>
          Preview
        </Button>
      ),
    },
  ];

  return (
    <div className="space-y-6 pb-12">
      <div>
        <h1 className="text-2xl font-extrabold text-slate-900 dark:text-slate-100 flex items-center gap-2">
          <FileCheck className="w-6 h-6 text-blue-500" /> Medical Reports Directory
        </h1>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          Browse, filter, and inspect structured data extractions across all medical documentation.
        </p>
      </div>

      {/* Filter Row */}
      <div className="glass-card p-4 rounded-2xl border border-slate-200 dark:border-slate-800 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="w-full md:w-80">
          <Search value={search} onChange={(e) => setSearch(e.target.value)} onClear={() => setSearch('')} />
        </div>

        <div className="flex items-center space-x-3 w-full md:w-auto">
          <label className="text-xs font-semibold text-slate-500">Facility:</label>
          <select
            value={hospitalFilter}
            onChange={(e) => setHospitalFilter(e.target.value)}
            className="h-10 px-3 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs text-slate-900 dark:text-slate-100 focus:outline-none"
          >
            <option value="all">All Healthcare Facilities</option>
            {hospitals.map((h) => (
              <option key={h} value={h}>{h}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Grid: Table + Side Preview Panel */}
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
          <Card className="p-6 border-slate-200 dark:border-slate-800 space-y-4 h-fit">
            <div className="flex items-start justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
              <div>
                <Badge variant="default" className="mb-1">{selectedReport.category.replace('_', ' ')}</Badge>
                <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">{selectedReport.title}</h3>
                <p className="text-xs text-slate-400 font-mono mt-0.5">{selectedReport.hospitalName}</p>
              </div>
              <span className="text-xs font-mono font-semibold text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5" /> 98% AI Match
              </span>
            </div>

            <div className="space-y-2">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Clinical Summary</span>
              <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed bg-slate-50 dark:bg-slate-800/40 p-3 rounded-xl">
                {selectedReport.summary}
              </p>
            </div>

            <div className="space-y-2">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Extracted Entities</span>
              <div className="space-y-1.5">
                {selectedReport.extractedEntities.map((ent, i) => (
                  <div key={i} className="p-2.5 rounded-xl bg-slate-100/70 dark:bg-slate-800/60 flex items-center justify-between text-xs">
                    <span className="font-semibold">{ent.name}</span>
                    {ent.value && <span className="font-mono text-blue-600 font-bold">{ent.value} {ent.unit}</span>}
                  </div>
                ))}
              </div>
            </div>

            <Button variant="primary" size="sm" className="w-full" leftIcon={<Download className="w-4 h-4" />}>
              Download Original PDF
            </Button>
          </Card>
        )}
      </div>
    </div>
  );
};
