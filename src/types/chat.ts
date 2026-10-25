export interface Citation {
  reportId: string;
  reportTitle: string;
  excerpt: string;
  date: string;
  confidenceScore: number;
  pageNumber?: number;
  facility?: string;
  analyte?: string;
  value?: string;
  unit?: string;
}

export interface MeasurementPoint {
  id: string;
  test_name: string;
  canonical_name?: string;
  value: string;
  numeric_value?: number;
  unit: string;
  test_date: string;
  facility: string;
  source_report_id?: string;
  source_report_title?: string;
  reference_range?: string;
  status?: string;
  page_number?: number;
}

export interface MultiAnalyteItem {
  analyte: string;
  previous_value: string;
  previous_date: string;
  latest_value: string;
  latest_date: string;
  change: string;
}

export interface StructuredTrendData {
  query_type: string;
  analyte_name: string;
  canonical_name: string;
  loinc_code?: string;
  latest_measurement?: MeasurementPoint;
  previous_measurement?: MeasurementPoint;
  all_measurements: MeasurementPoint[];
  trend_direction: 'increasing' | 'decreasing' | 'stable' | 'insufficient_data' | 'conflicting' | 'incompatible_units' | 'not_found';
  absolute_change?: number;
  percentage_change?: number;
  unit?: string;
  reference_range?: string;
  reference_range_status?: 'normal' | 'elevated' | 'low' | 'unavailable';
  conflicting_measurements: MeasurementPoint[];
  incompatible_units_detected: boolean;
  has_sufficient_data: boolean;
  time_window_applied?: string;
  narrative_summary: string;
  citations: Citation[];
  multi_analyte_items?: MultiAnalyteItem[];
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'ai';
  text: string;
  timestamp: string;
  citations?: Citation[];
  reasoningType?: 'fact' | 'inference';
  structuredTrend?: StructuredTrendData;
  isTyping?: boolean;
}

export interface ConversationThread {
  id: string;
  title: string;
  lastMessageDate: string;
  messageCount: number;
}
