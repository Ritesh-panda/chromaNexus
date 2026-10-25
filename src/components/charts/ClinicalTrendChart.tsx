import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine,
} from 'recharts';
import type { MeasurementPoint } from '@/types';
import { AlertCircle, Building2, Calendar, FileText } from 'lucide-react';

interface ClinicalTrendChartProps {
  measurements: MeasurementPoint[];
  unit?: string;
  referenceRange?: string;
  onSelectPoint?: (point: MeasurementPoint) => void;
  selectedPointId?: string;
}

export const ClinicalTrendChart: React.FC<ClinicalTrendChartProps> = ({
  measurements,
  unit,
  referenceRange,
  onSelectPoint,
  selectedPointId,
}) => {
  if (!measurements || measurements.length === 0) {
    return (
      <div className="w-full py-8 text-center text-xs text-[#6B7280] dark:text-[#9CA3AF] bg-[#FAF8F5] dark:bg-[#23272E]/40 rounded-xl border border-dashed border-[#E5E7EB] dark:border-[#2F3540]">
        No longitudinal measurements available for visualization.
      </div>
    );
  }

  // Safety Check: Incompatible Units
  const distinctUnits = Array.from(new Set(measurements.map((m) => (m.unit || '').trim().toLowerCase()))).filter(Boolean);
  if (distinctUnits.length > 1) {
    return (
      <div className="p-4 rounded-xl bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 text-xs text-amber-900 dark:text-amber-200 flex items-start gap-2.5">
        <AlertCircle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <span className="font-semibold block">Incompatible Measurement Units Detected</span>
          <p className="text-[11px] leading-relaxed">
            Records for this biomarker contain differing units ({distinctUnits.join(', ')}). A unified trend curve cannot be rendered without a verified clinical conversion to preserve data safety.
          </p>
        </div>
      </div>
    );
  }

  // Parse reference range boundaries if present
  let refLow: number | null = null;
  let refHigh: number | null = null;
  if (referenceRange) {
    const rangeMatch = referenceRange.match(/([0-9]+(?:\.[0-9]+)?)\s*(?:-|to)\s*([0-9]+(?:\.[0-9]+)?)/i);
    if (rangeMatch) {
      refLow = parseFloat(rangeMatch[1]);
      refHigh = parseFloat(rangeMatch[2]);
    } else {
      const ltMatch = referenceRange.match(/<\s*=?\s*([0-9]+(?:\.[0-9]+)?)/);
      if (ltMatch) refHigh = parseFloat(ltMatch[1]);
      const gtMatch = referenceRange.match(/>\s*=?\s*([0-9]+(?:\.[0-9]+)?)/);
      if (gtMatch) refLow = parseFloat(gtMatch[1]);
    }
  }

  // Format data sorted chronologically
  const sorted = [...measurements].sort((a, b) => a.test_date.localeCompare(b.test_date));

  // Single-measurement dataset handling
  if (sorted.length === 1) {
    const single = sorted[0];
    const val = single.numeric_value !== undefined ? single.numeric_value : parseFloat(single.value) || 0;
    return (
      <div className="p-4 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/50 border border-[#E5E7EB] dark:border-[#2F3540] space-y-2">
        <div className="flex items-center justify-between text-xs">
          <span className="font-medium text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5 text-[#10B981]" /> Baseline Observation: {single.test_date}
          </span>
          <span className="text-[11px] text-[#6B7280] dark:text-[#9CA3AF] flex items-center gap-1">
            <Building2 className="w-3 h-3" /> {single.facility || 'Verified Lab'}
          </span>
        </div>
        <div className="flex items-baseline gap-2 pt-1">
          <span className="text-2xl font-bold font-mono text-[#1F2937] dark:text-white">{val}</span>
          <span className="text-xs text-[#6B7280] dark:text-[#9CA3AF]">{single.unit || unit}</span>
          {referenceRange && (
            <span className="text-xs text-[#6B7280] dark:text-[#9CA3AF] pl-2 border-l border-[#E5E7EB] dark:border-[#2F3540]">
              Ref: {referenceRange}
            </span>
          )}
        </div>
        <p className="text-[11px] text-[#6B7280] dark:text-[#9CA3AF] italic">
          Single baseline measurement recorded. At least two chronological observations are required to calculate trend direction.
        </p>
      </div>
    );
  }

  const data = sorted.map((m) => {
    const numeric = m.numeric_value !== undefined ? m.numeric_value : parseFloat(m.value) || 0;
    return {
      id: m.id,
      date: m.test_date,
      value: numeric,
      unit: m.unit || unit,
      facility: m.facility,
      status: m.status || 'normal',
      sourceReportTitle: m.source_report_title,
      raw: m,
    };
  });

  const values = data.map((d) => d.value);
  if (refLow !== null) values.push(refLow);
  if (refHigh !== null) values.push(refHigh);

  const minVal = Math.min(...values);
  const maxVal = Math.max(...values);
  const padding = (maxVal - minVal) * 0.18 || 1.0;
  const yDomain = [Math.max(0, Math.floor(minVal - padding)), Math.ceil(maxVal + padding)];

  return (
    <div className="w-full pt-2">
      <div className="w-full h-48 sm:h-56">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={data}
            margin={{ top: 12, right: 16, left: -20, bottom: 4 }}
            onClick={(state: any) => {
              const s = state as any;
              if (s && s.activePayload && s.activePayload[0] && onSelectPoint) {
                const payload = s.activePayload[0].payload;
                if (payload && payload.raw) {
                  onSelectPoint(payload.raw);
                }
              }
            }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" opacity={0.5} vertical={false} />
            <XAxis
              dataKey="date"
              stroke="#9CA3AF"
              fontSize={10}
              tickLine={false}
              axisLine={false}
              tickFormatter={(val: string) => {
                try {
                  const parts = val.split('-');
                  return `${parts[1]}/${parts[2] || parts[0]}`;
                } catch {
                  return val;
                }
              }}
            />
            <YAxis
              stroke="#9CA3AF"
              fontSize={10}
              tickLine={false}
              axisLine={false}
              domain={yDomain}
            />
            <Tooltip
              formatter={(val: any, _name: any, item: any) => [
                `${val} ${item?.payload?.unit || ''} • Status: ${item?.payload?.status || 'normal'}`,
                'Measurement',
              ]}
              labelFormatter={(label: any) => `Collection Date: ${label}`}
              contentStyle={{
                backgroundColor: '#FFFFFF',
                borderColor: '#E5E7EB',
                borderRadius: '12px',
                color: '#1F2937',
                fontSize: '11px',
                boxShadow: '0 4px 16px rgba(0, 0, 0, 0.08)',
              }}
            />
            {refLow !== null && (
              <ReferenceLine
                y={refLow}
                stroke="#9CA3AF"
                strokeDasharray="4 4"
                label={{ value: `Low (${refLow})`, position: 'insideBottomLeft', fill: '#9CA3AF', fontSize: 9 }}
              />
            )}
            {refHigh !== null && (
              <ReferenceLine
                y={refHigh}
                stroke="#F59E0B"
                strokeDasharray="4 4"
                label={{ value: `High (${refHigh})`, position: 'insideTopLeft', fill: '#D97706', fontSize: 9 }}
              />
            )}
            <Line
              type="monotone"
              dataKey="value"
              stroke="#10B981"
              strokeWidth={2.5}
              cursor="pointer"
              dot={(props: any) => {
                const { cx, cy, payload } = props;
                const isSelected = selectedPointId && payload.id === selectedPointId;
                const isAbnormal = payload.status === 'high' || payload.status === 'critical' || payload.status === 'low';
                const fillColor = isAbnormal ? '#F59E0B' : '#10B981';
                return (
                  <circle
                    key={payload.id}
                    cx={cx}
                    cy={cy}
                    r={isSelected ? 6 : 4}
                    fill={fillColor}
                    stroke="#FFFFFF"
                    strokeWidth={isSelected ? 3 : 2}
                    className="transition-all hover:scale-125 cursor-pointer"
                    onClick={(e) => {
                      e.stopPropagation();
                      if (onSelectPoint && payload.raw) {
                        onSelectPoint(payload.raw);
                      }
                    }}
                  />
                );
              }}
              activeDot={{ fill: '#059669', stroke: '#FFFFFF', strokeWidth: 2, r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="text-[10px] text-[#6B7280] dark:text-[#9CA3AF] flex items-center justify-between px-1 pt-1">
        <span>Click any observation point to view clinical report context</span>
        {referenceRange && <span className="font-mono">Reference Range: {referenceRange}</span>}
      </div>
    </div>
  );
};
