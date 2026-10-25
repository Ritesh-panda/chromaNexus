import React, { useState } from 'react';
import type { StructuredTrendData, MeasurementPoint } from '@/types';
import { ClinicalTrendChart } from '@/components/charts/ClinicalTrendChart';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';
import {
  TrendingUp,
  TrendingDown,
  Activity,
  AlertTriangle,
  AlertCircle,
  Clock,
  Building,
  CheckCircle2,
  Table as TableIcon,
  LineChart as ChartIcon,
  FileText,
  Calendar,
  Layers,
} from 'lucide-react';

interface ClinicalTrendCardProps {
  trend: StructuredTrendData;
  onCitationClick?: (reportId: string) => void;
}

export const ClinicalTrendCard: React.FC<ClinicalTrendCardProps> = ({
  trend,
  onCitationClick,
}) => {
  const [viewMode, setViewMode] = useState<'chart' | 'table'>('chart');
  const [inspectedPoint, setInspectedPoint] = useState<MeasurementPoint | null>(null);

  const {
    canonical_name,
    loinc_code,
    latest_measurement,
    previous_measurement,
    all_measurements,
    trend_direction,
    absolute_change,
    percentage_change,
    unit,
    reference_range,
    reference_range_status,
    conflicting_measurements,
    incompatible_units_detected,
    time_window_applied,
    multi_analyte_items,
  } = trend;

  // Direction badge styling
  const renderTrendBadge = () => {
    switch (trend_direction) {
      case 'increasing':
        return (
          <Badge variant="default" className="bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400 border border-emerald-200/60 dark:border-emerald-800/40 text-[10px] py-0.5 px-2">
            <TrendingUp className="w-3 h-3 mr-1" /> Increasing
          </Badge>
        );
      case 'decreasing':
        return (
          <Badge variant="default" className="bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-400 border border-blue-200/60 dark:border-blue-800/40 text-[10px] py-0.5 px-2">
            <TrendingDown className="w-3 h-3 mr-1" /> Decreasing
          </Badge>
        );
      case 'stable':
        return (
          <Badge variant="default" className="bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 text-[10px] py-0.5 px-2">
            <Activity className="w-3 h-3 mr-1" /> Stable
          </Badge>
        );
      case 'insufficient_data':
        return (
          <Badge variant="secondary" className="text-[10px] py-0.5 px-2 text-slate-500">
            Baseline Only
          </Badge>
        );
      default:
        return null;
    }
  };

  const renderRefStatusBadge = () => {
    if (!reference_range_status || reference_range_status === 'unavailable') return null;
    if (reference_range_status === 'normal') {
      return (
        <span className="text-[10px] text-emerald-600 dark:text-emerald-400 font-medium flex items-center">
          <CheckCircle2 className="w-3 h-3 mr-1" /> In Range
        </span>
      );
    }
    if (reference_range_status === 'elevated') {
      return (
        <span className="text-[10px] text-amber-600 dark:text-amber-400 font-medium flex items-center">
          <AlertCircle className="w-3 h-3 mr-1" /> High
        </span>
      );
    }
    if (reference_range_status === 'low') {
      return (
        <span className="text-[10px] text-blue-600 dark:text-blue-400 font-medium flex items-center">
          <AlertCircle className="w-3 h-3 mr-1" /> Low
        </span>
      );
    }
    return null;
  };

  return (
    <div className="w-full rounded-2xl bg-white dark:bg-[#1B1E23] border border-[#E5E7EB] dark:border-[#2F3540] p-4 sm:p-5 space-y-4 shadow-sm">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 pb-2 border-b border-slate-100 dark:border-slate-800">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200/60 dark:border-emerald-800/40 flex items-center justify-center text-[#10B981]">
            <Activity className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-sm sm:text-base font-semibold text-slate-900 dark:text-white leading-tight">
              {canonical_name}
            </h4>
            {loinc_code && (
              <span className="text-[9px] text-[#6B7280] dark:text-[#9CA3AF] tracking-wide font-mono">
                LOINC: {loinc_code}
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {time_window_applied && (
            <span className="text-[10px] px-2 py-0.5 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 flex items-center font-medium">
              <Clock className="w-3 h-3 mr-1 text-slate-400" /> {time_window_applied}
            </span>
          )}
          {renderTrendBadge()}

          {/* View toggle (Chart vs Table) */}
          {all_measurements && all_measurements.length > 0 && (
            <div className="flex items-center rounded-lg border border-slate-200 dark:border-slate-700 p-0.5 bg-slate-50 dark:bg-slate-800/50">
              <button
                type="button"
                onClick={() => setViewMode('chart')}
                className={`p-1 rounded text-xs transition-colors ${
                  viewMode === 'chart'
                    ? 'bg-white dark:bg-slate-700 text-[#10B981] shadow-xs'
                    : 'text-slate-400 hover:text-slate-600'
                }`}
                title="Line Chart View"
              >
                <ChartIcon className="w-3.5 h-3.5" />
              </button>
              <button
                type="button"
                onClick={() => setViewMode('table')}
                className={`p-1 rounded text-xs transition-colors ${
                  viewMode === 'table'
                    ? 'bg-white dark:bg-slate-700 text-[#10B981] shadow-xs'
                    : 'text-slate-400 hover:text-slate-600'
                }`}
                title="Tabular Data View"
              >
                <TableIcon className="w-3.5 h-3.5" />
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Multi-analyte list display */}
      {multi_analyte_items && multi_analyte_items.length > 0 && (
        <div className="space-y-2 bg-slate-50 dark:bg-[#23272E] p-3 rounded-xl border border-slate-200/80 dark:border-slate-800">
          <div className="text-[10px] font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-[#10B981]" />
            Identified Longitudinal Biomarker Changes
          </div>
          <div className="divide-y divide-slate-200/60 dark:divide-slate-800">
            {multi_analyte_items.map((item, idx) => (
              <div key={idx} className="py-2 flex items-center justify-between text-xs">
                <div>
                  <span className="font-medium text-slate-800 dark:text-slate-200">{item.analyte}</span>
                  <div className="text-[10px] text-slate-500 font-mono">
                    {item.previous_value} ({item.previous_date}) &rarr; {item.latest_value} ({item.latest_date})
                  </div>
                </div>
                <Badge variant="default" className="text-[10px] py-0 px-2 font-mono">
                  {item.change}
                </Badge>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Metrics Row (for single analyte) */}
      {latest_measurement && (
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
          {/* Latest Tile */}
          <div className="p-3 rounded-xl bg-slate-50 dark:bg-[#23272E] border border-slate-200/70 dark:border-slate-800 space-y-1">
            <div className="text-[10px] font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Latest Result</div>
            <div className="flex items-baseline space-x-1.5">
              <span className="text-xl font-bold font-mono text-slate-900 dark:text-white">
                {latest_measurement.value}
              </span>
              <span className="text-xs font-medium text-slate-500">{latest_measurement.unit}</span>
            </div>
            <div className="flex items-center justify-between text-[10px] pt-0.5">
              <span className="text-slate-500 font-mono">{latest_measurement.test_date}</span>
              {renderRefStatusBadge()}
            </div>
          </div>

          {/* Previous Tile */}
          {previous_measurement ? (
            <div className="p-3 rounded-xl bg-slate-50 dark:bg-[#23272E] border border-slate-200/70 dark:border-slate-800 space-y-1">
              <div className="text-[10px] font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Previous Result</div>
              <div className="flex items-baseline space-x-1.5">
                <span className="text-xl font-bold font-mono text-slate-700 dark:text-slate-300">
                  {previous_measurement.value}
                </span>
                <span className="text-xs font-medium text-slate-500">{previous_measurement.unit}</span>
              </div>
              <div className="text-[10px] text-slate-500 font-mono pt-0.5">
                {previous_measurement.test_date}
              </div>
            </div>
          ) : (
            <div className="p-3 rounded-xl bg-slate-50/60 dark:bg-[#23272E]/60 border border-slate-200/50 dark:border-slate-800/50 flex flex-col justify-center">
              <span className="text-xs text-slate-400 italic">No Prior Observation</span>
            </div>
          )}

          {/* Change Tile */}
          {absolute_change !== null && absolute_change !== undefined && (
            <div className="col-span-2 sm:col-span-1 p-3 rounded-xl bg-slate-50 dark:bg-[#23272E] border border-slate-200/70 dark:border-slate-800 space-y-1">
              <div className="text-[10px] font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Measured Delta</div>
              <div className="flex items-baseline space-x-1.5 font-mono">
                <span
                  className={`text-xl font-bold ${
                    absolute_change > 0 ? 'text-emerald-600 dark:text-emerald-400' : absolute_change < 0 ? 'text-blue-600 dark:text-blue-400' : 'text-slate-600'
                  }`}
                >
                  {absolute_change > 0 ? `+${absolute_change}` : absolute_change}
                </span>
                <span className="text-xs text-slate-500">{unit}</span>
              </div>
              {percentage_change !== null && percentage_change !== undefined && (
                <div className="text-[10px] font-mono text-slate-500">
                  {percentage_change > 0 ? `+${percentage_change}%` : `${percentage_change}%`}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Conflicting measurements callout */}
      {conflicting_measurements && conflicting_measurements.length > 0 && (
        <div className="p-3 rounded-xl bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800/50 text-xs text-amber-900 dark:text-amber-200 space-y-1.5">
          <div className="font-semibold flex items-center gap-1.5">
            <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
            Conflicting Multi-Facility Findings Recorded
          </div>
          <p className="text-[11px] leading-relaxed">
            Differing measurements were documented on the same date across separate healthcare facilities. Both are shown without synthetic reconciliation:
          </p>
          <div className="space-y-1 pl-3 text-[11px] font-mono">
            {conflicting_measurements.map((c, i) => (
              <div key={i} className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
                <span>{c.value} {c.unit} on {c.test_date} at <strong>{c.facility}</strong></span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Incompatible units warning */}
      {incompatible_units_detected && (
        <div className="p-3 rounded-xl bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-800/50 text-xs text-rose-800 dark:text-rose-200 flex items-start gap-2">
          <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
          <div className="space-y-0.5">
            <span className="font-semibold block">Incompatible Units Across Records</span>
            <p className="text-[11px]">Reports utilized differing measurement units. Mathematical delta cannot be computed without a validated conversion formula.</p>
          </div>
        </div>
      )}

      {/* Main Visualization: Chart View or Table View */}
      {all_measurements && all_measurements.length > 0 && (
        <div className="pt-1">
          {viewMode === 'chart' ? (
            <div className="space-y-1">
              <div className="flex items-center justify-between text-[11px] text-slate-500 font-medium px-1">
                <span>Chronological Trend ({all_measurements.length} observation{all_measurements.length > 1 ? 's' : ''})</span>
                {reference_range && <span className="font-mono">Reference Range: {reference_range}</span>}
              </div>
              <ClinicalTrendChart
                measurements={all_measurements}
                unit={unit}
                referenceRange={reference_range}
                onSelectPoint={(pt) => setInspectedPoint(pt)}
                selectedPointId={inspectedPoint?.id}
              />
            </div>
          ) : (
            /* Table Alternative */
            <div className="space-y-2">
              <div className="text-[11px] font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider px-1">
                Historical Measurements List ({all_measurements.length})
              </div>
              <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 dark:bg-[#23272E] text-[10px] text-slate-500 uppercase font-semibold">
                    <tr>
                      <th className="py-2.5 px-3">Date</th>
                      <th className="py-2.5 px-3">Value</th>
                      <th className="py-2.5 px-3">Status</th>
                      <th className="py-2.5 px-3">Facility</th>
                      <th className="py-2.5 px-3">Source Record</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800 font-mono">
                    {all_measurements.map((m) => (
                      <tr
                        key={m.id}
                        onClick={() => setInspectedPoint(m)}
                        className="hover:bg-slate-50/80 dark:hover:bg-[#23272E]/50 cursor-pointer transition-colors"
                      >
                        <td className="py-2 px-3 text-slate-900 dark:text-slate-200">{m.test_date}</td>
                        <td className="py-2 px-3 font-semibold text-slate-900 dark:text-white">
                          {m.value} <span className="text-[10px] font-normal text-slate-500">{m.unit}</span>
                        </td>
                        <td className="py-2 px-3">
                          <span
                            className={`px-1.5 py-0.5 rounded text-[10px] font-sans capitalize ${
                              m.status === 'high' || m.status === 'critical'
                                ? 'bg-amber-100 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300'
                                : m.status === 'low'
                                ? 'bg-blue-100 dark:bg-blue-950/40 text-blue-800 dark:text-blue-300'
                                : 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-300'
                            }`}
                          >
                            {m.status || 'normal'}
                          </span>
                        </td>
                        <td className="py-2 px-3 text-slate-600 dark:text-slate-400 font-sans">{m.facility}</td>
                        <td className="py-2 px-3 font-sans">
                          {m.source_report_id ? (
                            <button
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation();
                                if (onCitationClick) onCitationClick(m.source_report_id!);
                              }}
                              className="text-[#10B981] hover:underline flex items-center gap-1 text-[11px]"
                            >
                              <FileText className="w-3 h-3" /> {m.source_report_title || 'Report'}
                            </button>
                          ) : (
                            <span className="text-slate-400">Verified Lab</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Point Detail Modal */}
      {inspectedPoint && (
        <Modal
          isOpen={!!inspectedPoint}
          onClose={() => setInspectedPoint(null)}
          title={`Observation: ${canonical_name}`}
          description={`Recorded on ${inspectedPoint.test_date} at ${inspectedPoint.facility}`}
        >
          <div className="space-y-4 pt-1 text-xs">
            <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-[#23272E]/60 border border-slate-200 dark:border-slate-800 space-y-2">
              <div className="flex items-baseline justify-between">
                <div>
                  <span className="text-[10px] text-slate-500 uppercase tracking-wider block">Recorded Measurement</span>
                  <span className="text-2xl font-bold font-mono text-slate-900 dark:text-white">
                    {inspectedPoint.value} {inspectedPoint.unit}
                  </span>
                </div>
                <Badge variant={inspectedPoint.status === 'high' || inspectedPoint.status === 'low' ? 'warning' : 'success'}>
                  {inspectedPoint.status || 'normal'}
                </Badge>
              </div>

              {inspectedPoint.reference_range && (
                <div className="text-[11px] text-slate-600 dark:text-slate-300 pt-1 border-t border-slate-200/80 dark:border-slate-700">
                  Applicable Reference Range: <strong className="font-mono">{inspectedPoint.reference_range}</strong>
                </div>
              )}
            </div>

            <div className="space-y-2">
              <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block">Clinical Provenance</span>
              <div className="p-3 rounded-xl bg-white dark:bg-[#1B1E23] border border-slate-200 dark:border-slate-800 space-y-1.5">
                <div className="flex items-center gap-1.5 text-slate-800 dark:text-slate-200">
                  <Building className="w-3.5 h-3.5 text-[#10B981]" />
                  <span>Facility: <strong>{inspectedPoint.facility}</strong></span>
                </div>
                <div className="flex items-center gap-1.5 text-slate-800 dark:text-slate-200">
                  <Calendar className="w-3.5 h-3.5 text-[#10B981]" />
                  <span>Collection Date: <strong>{inspectedPoint.test_date}</strong></span>
                </div>
                {inspectedPoint.source_report_title && (
                  <div className="flex items-center gap-1.5 text-[#10B981]">
                    <FileText className="w-3.5 h-3.5" />
                    <span>Source Report: <strong>{inspectedPoint.source_report_title}</strong></span>
                  </div>
                )}
              </div>
            </div>

            {inspectedPoint.source_report_id && onCitationClick && (
              <Button
                variant="secondary"
                size="sm"
                className="w-full"
                onClick={() => {
                  const rId = inspectedPoint.source_report_id!;
                  setInspectedPoint(null);
                  onCitationClick(rId);
                }}
              >
                Inspect Source Document
              </Button>
            )}

            <Button variant="primary" size="sm" className="w-full" onClick={() => setInspectedPoint(null)}>
              Close
            </Button>
          </div>
        </Modal>
      )}

      {/* Facility & Report Provenance Footer */}
      {latest_measurement && (
        <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-slate-100 dark:border-slate-800 text-[11px] text-slate-500 dark:text-slate-400">
          <span className="flex items-center gap-1">
            <Building className="w-3.5 h-3.5 text-slate-400" /> {latest_measurement.facility}
          </span>
          {latest_measurement.source_report_id && (
            <button
              type="button"
              onClick={() => onCitationClick && onCitationClick(latest_measurement.source_report_id!)}
              className="text-[#10B981] hover:underline flex items-center gap-1"
            >
              <FileText className="w-3 h-3" /> {latest_measurement.source_report_title || 'Source Report'}
            </button>
          )}
        </div>
      )}
    </div>
  );
};
