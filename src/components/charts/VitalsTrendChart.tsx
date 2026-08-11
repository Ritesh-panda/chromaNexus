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
    <div className="w-full h-72 pt-4">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="colorHbA1c" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#2563EB" stopOpacity={0.4} />
              <stop offset="95%" stopColor="#2563EB" stopOpacity={0.0} />
            </linearGradient>
            <linearGradient id="colorCholesterol" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#10B981" stopOpacity={0.4} />
              <stop offset="95%" stopColor="#10B981" stopOpacity={0.0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" opacity={0.15} vertical={false} />
          <XAxis dataKey="year" stroke="#94A3B8" fontSize={12} tickLine={false} />
          <YAxis stroke="#94A3B8" fontSize={12} tickLine={false} />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1E293B',
              borderColor: '#334155',
              borderRadius: '12px',
              color: '#F8FAFC',
              fontSize: '12px',
            }}
          />
          <Area
            type="monotone"
            dataKey="hba1c"
            name="HbA1c (%)"
            stroke="#2563EB"
            strokeWidth={2.5}
            fillOpacity={1}
            fill="url(#colorHbA1c)"
          />
          <Area
            type="monotone"
            dataKey="cholesterol"
            name="Total Cholesterol (mg/dL)"
            stroke="#10B981"
            strokeWidth={2.5}
            fillOpacity={1}
            fill="url(#colorCholesterol)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};
