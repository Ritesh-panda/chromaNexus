import React from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';

const data = [
  { year: '2021', hba1c: 5.6, glucose: 95, cholesterol: 242 },
  { year: '2022', hba1c: 5.8, glucose: 102, cholesterol: 228 },
  { year: '2023', hba1c: 7.2, glucose: 142, cholesterol: 210 },
  { year: '2024', hba1c: 6.9, glucose: 130, cholesterol: 205 },
  { year: '2025', hba1c: 6.8, glucose: 125, cholesterol: 195 },
  { year: '2026', hba1c: 6.7, glucose: 128, cholesterol: 198 },
];

export const VitalsTrendChart: React.FC = () => {
  return (
    <div className="w-full pt-2 space-y-2">
      <div className="w-full h-64 sm:h-72">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="colorHbA1c" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10B981" stopOpacity={0.25} />
                <stop offset="95%" stopColor="#10B981" stopOpacity={0.0} />
              </linearGradient>
              <linearGradient id="colorCholesterol" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#2563EB" stopOpacity={0.2} />
                <stop offset="95%" stopColor="#2563EB" stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" opacity={0.6} vertical={false} />
            <XAxis dataKey="year" stroke="#9CA3AF" fontSize={11} tickLine={false} axisLine={false} />
            <YAxis stroke="#9CA3AF" fontSize={11} tickLine={false} axisLine={false} />
            <Tooltip
              formatter={(value: any, name: any) => [`${value} (Demo / Sample)`, name]}
              contentStyle={{
                backgroundColor: '#FFFFFF',
                borderColor: '#E5E7EB',
                borderRadius: '12px',
                color: '#1F2937',
                fontSize: '12px',
                boxShadow: '0 4px 12px rgba(0, 0, 0, 0.05)',
              }}
            />
            <Area
              type="monotone"
              dataKey="hba1c"
              name="HbA1c (%)"
              stroke="#10B981"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorHbA1c)"
            />
            <Area
              type="monotone"
              dataKey="cholesterol"
              name="Total Cholesterol (mg/dL)"
              stroke="#2563EB"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorCholesterol)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
      <div className="flex items-center justify-between text-[11px] text-[#6B7280] dark:text-[#9CA3AF] px-1 pt-2 border-t border-[#E5E7EB]/70 dark:border-[#2F3540]">
        <span className="flex items-center gap-1.5 font-medium">
          <span className="inline-block w-1.5 h-1.5 rounded-full bg-amber-500 shrink-0" />
          Sample / Demo Laboratory Data — Not verified clinical history
        </span>
        <span className="font-mono text-[10px] text-[#9CA3AF]">Illustrative Model</span>
      </div>
    </div>
  );
};
