import React, { useEffect, useState, useMemo } from 'react';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Modal } from '@/components/ui/Modal';
import { timelineService } from '@/services/timeline.service';
import { patientService } from '@/services/patient.service';
import { ClinicalTrendCard } from '@/components/cards/ClinicalTrendCard';
import type { TimelineEvent, AnalyteSummary, StructuredTrendData } from '@/types';
import {
  GitCommit,
  Filter,
  FileText,
  Building2,
  Activity,
  Pill,
  ChevronRight,
  Stethoscope,
  Calendar,
  AlertTriangle,
  Upload,
  Clock,
  Layers,
  Search,
  RefreshCw,
  SlidersHorizontal,
  TrendingUp,
} from 'lucide-react';

export const TimelinePage: React.FC = () => {
  // Navigation tab: 'timeline' | 'trends'
  const [activeTab, setActiveTab] = useState<'timeline' | 'trends'>('timeline');

  // Timeline state
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [facilities, setFacilities] = useState<string[]>([]);
  const [selectedType, setSelectedType] = useState<string>('all');
  const [selectedYear, setSelectedYear] = useState<string>('all');
  const [selectedFacility, setSelectedFacility] = useState<string>('all');
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');
  const [sortOrder, setSortOrder] = useState<'desc' | 'asc'>('desc');
  const [selectedEvent, setSelectedEvent] = useState<TimelineEvent | null>(null);
  const [isLoadingEvents, setIsLoadingEvents] = useState<boolean>(true);
  const [timelineError, setTimelineError] = useState<string | null>(null);

  // Lab trends state
  const [analytes, setAnalytes] = useState<AnalyteSummary[]>([]);
  const [selectedAnalyte, setSelectedAnalyte] = useState<string>('');
  const [analyteSearch, setAnalyteSearch] = useState<string>('');
  const [timeWindow, setTimeWindow] = useState<string>('all');
  const [trendData, setTrendData] = useState<StructuredTrendData | null>(null);
  const [isLoadingTrend, setIsLoadingTrend] = useState<boolean>(false);
  const [trendError, setTrendError] = useState<string | null>(null);

  // Load timeline events & facilities
  const fetchTimeline = async () => {
    setIsLoadingEvents(true);
    setTimelineError(null);
    try {
      const [eventsData, facData] = await Promise.all([
        timelineService.getTimelineEvents({
          filterType: selectedType,
          facility: selectedFacility,
          startDate: startDate || undefined,
          endDate: endDate || undefined,
          year: selectedYear !== 'all' ? parseInt(selectedYear, 10) : undefined,
          order: sortOrder,
        }),
        timelineService.getTimelineFacilities(),
      ]);
      setEvents(eventsData || []);
      setFacilities(facData || []);
    } catch (err) {
      console.error('Error fetching timeline:', err);
      setTimelineError('Failed to load clinical timeline records. Please try again.');
    } finally {
      setIsLoadingEvents(false);
    }
  };

  useEffect(() => {
    fetchTimeline();
  }, [selectedType, selectedFacility, selectedYear, startDate, endDate, sortOrder]);

  // Load analytes list
  useEffect(() => {
    let isMounted = true;
    const fetchAnalytes = async () => {
      try {
        const list = await patientService.getAnalytes();
        if (isMounted && list && list.length > 0) {
          setAnalytes(list);
          if (!selectedAnalyte) {
            setSelectedAnalyte(list[0].canonicalName || list[0].testName);
          }
        }
      } catch (err) {
        console.error('Error fetching analytes:', err);
      }
    };
    fetchAnalytes();
    return () => {
      isMounted = false;
    };
  }, []);

  // Fetch trend when selected analyte or time window changes
  useEffect(() => {
    if (!selectedAnalyte) return;
    let isMounted = true;
    const fetchTrend = async () => {
      setIsLoadingTrend(true);
      setTrendError(null);
      try {
        const data = await patientService.getLabTrend(selectedAnalyte, timeWindow);
        if (isMounted) {
          setTrendData(data);
        }
      } catch (err) {
        if (isMounted) {
          console.error('Error fetching lab trend:', err);
          setTrendError(`Failed to retrieve laboratory trend for ${selectedAnalyte}.`);
        }
      } finally {
        if (isMounted) setIsLoadingTrend(false);
      }
    };
    fetchTrend();
    return () => {
      isMounted = false;
    };
  }, [selectedAnalyte, timeWindow]);

  const eventTypes = [
    { id: 'all', label: 'All Records' },
    { id: 'diagnosis', label: 'Diagnoses' },
    { id: 'medication_start', label: 'Medications' },
    { id: 'lab_test', label: 'Lab Tests' },
    { id: 'imaging', label: 'Imaging / MRI' },
    { id: 'medical_report', label: 'Reports & Uploads' },
    { id: 'hospital_visit', label: 'Consultations' },
  ];

  // Distinct years for filter
  const distinctYears = useMemo(() => {
    const yrs = new Set<number>();
    events.forEach((e) => {
      if (e.year && e.year > 0) yrs.add(e.year);
    });
    return Array.from(yrs).sort((a, b) => b - a);
  }, [events]);

  // Group events by year
  const groupedEvents = useMemo(() => {
    const validEvents = events.filter((e) => !e.isUnknownDate);
    const unknownEvents = events.filter((e) => e.isUnknownDate);

    const map = new Map<number, TimelineEvent[]>();
    validEvents.forEach((e) => {
      const yr = e.year || 0;
      if (!map.has(yr)) map.set(yr, []);
      map.get(yr)!.push(e);
    });

    const sortedYears = Array.from(map.keys()).sort((a, b) => (sortOrder === 'desc' ? b - a : a - b));
    return {
      years: sortedYears,
      map,
      unknownEvents,
    };
  }, [events, sortOrder]);

  const getEventIcon = (type: TimelineEvent['type']) => {
    switch (type) {
      case 'diagnosis':
        return <Activity className="w-4 h-4 text-[#B91C1C]" />;
      case 'medication_start':
      case 'medication_stop':
        return <Pill className="w-4 h-4 text-[#10B981]" />;
      case 'lab_test':
        return <FileText className="w-4 h-4 text-[#2563EB]" />;
      case 'imaging':
        return <Stethoscope className="w-4 h-4 text-[#4B5563]" />;
      case 'hospital_visit':
        return <Building2 className="w-4 h-4 text-[#B45309]" />;
      case 'medical_report':
        return <Layers className="w-4 h-4 text-[#059669]" />;
      default:
        return <Calendar className="w-4 h-4 text-[#1F2937]" />;
    }
  };

  const filteredAnalytes = useMemo(() => {
    if (!analyteSearch.trim()) return analytes;
    const q = analyteSearch.toLowerCase().trim();
    return analytes.filter(
      (a) =>
        a.testName.toLowerCase().includes(q) ||
        a.canonicalName.toLowerCase().includes(q) ||
        (a.loincCode && a.loincCode.toLowerCase().includes(q))
    );
  }, [analytes, analyteSearch]);

  const resetTimelineFilters = () => {
    setSelectedType('all');
    setSelectedYear('all');
    setSelectedFacility('all');
    setStartDate('');
    setEndDate('');
    setSortOrder('desc');
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-[#1F2937] dark:text-[#F3F4F6]">
            Clinical History & Longitudinal Trends
          </h1>
          <p className="text-xs sm:text-sm text-[#6B7280] dark:text-[#9CA3AF] mt-0.5">
            Verified chronology of medical records, diagnoses, medications, and laboratory biomarker trends.
          </p>
        </div>

        {/* Tab Navigation Switch */}
        <div className="flex items-center p-1 rounded-xl bg-[#FAF8F5] dark:bg-[#1B1E23] border border-[#E5E7EB] dark:border-[#2F3540] self-start sm:self-auto">
          <button
            type="button"
            onClick={() => setActiveTab('timeline')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
              activeTab === 'timeline'
                ? 'bg-white dark:bg-[#23272E] text-[#1F2937] dark:text-[#F3F4F6] shadow-xs'
                : 'text-[#6B7280] dark:text-[#9CA3AF] hover:text-[#1F2937] dark:hover:text-[#F3F4F6]'
            }`}
          >
            <GitCommit className="w-3.5 h-3.5 text-[#10B981]" />
            Clinical Timeline
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('trends')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
              activeTab === 'trends'
                ? 'bg-white dark:bg-[#23272E] text-[#1F2937] dark:text-[#F3F4F6] shadow-xs'
                : 'text-[#6B7280] dark:text-[#9CA3AF] hover:text-[#1F2937] dark:hover:text-[#F3F4F6]'
            }`}
          >
            <TrendingUp className="w-3.5 h-3.5 text-[#10B981]" />
            Biomarker Trends
          </button>
        </div>
      </div>

      {/* TAB 1: CLINICAL TIMELINE */}
      {activeTab === 'timeline' && (
        <div className="space-y-6">
          {/* Filter Bar */}
          <div className="p-4 rounded-2xl bg-white dark:bg-[#1B1E23] border border-[#E5E7EB] dark:border-[#2F3540] space-y-3.5 shadow-xs">
            <div className="flex items-center justify-between gap-2 flex-wrap pb-2 border-b border-[#E5E7EB]/70 dark:border-[#2F3540]">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-[#1F2937] dark:text-[#F3F4F6]">
                <Filter className="w-3.5 h-3.5 text-[#10B981]" />
                <span>Filter Clinical Records</span>
                <span className="text-[10px] font-normal text-[#6B7280] dark:text-[#9CA3AF]">
                  ({events.length} event{events.length !== 1 ? 's' : ''})
                </span>
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc')}
                  className="text-[11px] text-[#6B7280] dark:text-[#9CA3AF] hover:text-[#10B981] font-medium flex items-center gap-1 transition-colors"
                >
                  <SlidersHorizontal className="w-3 h-3" />
                  {sortOrder === 'desc' ? 'Newest First' : 'Oldest First'}
                </button>
                <Button variant="ghost" size="sm" onClick={resetTimelineFilters} className="text-xs h-7 px-2">
                  Reset
                </Button>
              </div>
            </div>

            {/* Category Chips */}
            <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none">
              {eventTypes.map((t) => (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => setSelectedType(t.id)}
                  className={`px-3 py-1.5 rounded-xl text-xs font-medium whitespace-nowrap transition-colors ${
                    selectedType === t.id
                      ? 'bg-[#1F2937] text-white dark:bg-[#10B981] dark:text-white shadow-xs'
                      : 'text-[#6B7280] dark:text-[#9CA3AF] hover:bg-[#FAF8F5] dark:hover:bg-[#23272E]'
                  }`}
                >
                  {t.label}
                </button>
              ))}
            </div>

            {/* Secondary Controls: Year, Facility, Date Inputs */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 pt-1 text-xs">
              {/* Year Selector */}
              <div>
                <label className="text-[10px] font-medium text-[#6B7280] dark:text-[#9CA3AF] uppercase tracking-wider block mb-1">
                  Encounter Year
                </label>
                <select
                  value={selectedYear}
                  onChange={(e) => setSelectedYear(e.target.value)}
                  className="w-full h-8 px-2.5 rounded-lg border border-[#E5E7EB] dark:border-[#2F3540] bg-white dark:bg-[#23272E] text-xs text-[#1F2937] dark:text-[#F3F4F6] focus:outline-hidden focus:ring-1 focus:ring-[#10B981]"
                >
                  <option value="all">All Available Years</option>
                  {distinctYears.map((yr) => (
                    <option key={yr} value={String(yr)}>
                      Year {yr}
                    </option>
                  ))}
                </select>
              </div>

              {/* Facility Selector */}
              <div>
                <label className="text-[10px] font-medium text-[#6B7280] dark:text-[#9CA3AF] uppercase tracking-wider block mb-1">
                  Healthcare Facility
                </label>
                <select
                  value={selectedFacility}
                  onChange={(e) => setSelectedFacility(e.target.value)}
                  className="w-full h-8 px-2.5 rounded-lg border border-[#E5E7EB] dark:border-[#2F3540] bg-white dark:bg-[#23272E] text-xs text-[#1F2937] dark:text-[#F3F4F6] focus:outline-hidden focus:ring-1 focus:ring-[#10B981]"
                >
                  <option value="all">All Facilities</option>
                  {facilities.map((fac) => (
                    <option key={fac} value={fac}>
                      {fac}
                    </option>
                  ))}
                </select>
              </div>

              {/* Date Range Inputs */}
              <div>
                <label className="text-[10px] font-medium text-[#6B7280] dark:text-[#9CA3AF] uppercase tracking-wider block mb-1">
                  Date Window
                </label>
                <div className="flex items-center gap-1.5">
                  <input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    placeholder="From"
                    className="w-full h-8 px-2 rounded-lg border border-[#E5E7EB] dark:border-[#2F3540] bg-white dark:bg-[#23272E] text-[11px] text-[#1F2937] dark:text-[#F3F4F6] focus:outline-hidden"
                  />
                  <span className="text-slate-400">&ndash;</span>
                  <input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    placeholder="To"
                    className="w-full h-8 px-2 rounded-lg border border-[#E5E7EB] dark:border-[#2F3540] bg-white dark:bg-[#23272E] text-[11px] text-[#1F2937] dark:text-[#F3F4F6] focus:outline-hidden"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Error State */}
          {timelineError && (
            <div className="p-4 rounded-2xl bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-800 text-xs text-rose-800 dark:text-rose-200 flex items-center justify-between">
              <span>{timelineError}</span>
              <Button variant="secondary" size="sm" onClick={fetchTimeline} className="h-7 text-xs">
                Retry
              </Button>
            </div>
          )}

          {/* Loading Skeleton */}
          {isLoadingEvents && (
            <div className="space-y-4 p-8 text-center bg-white dark:bg-[#1B1E23] rounded-2xl border border-[#E5E7EB] dark:border-[#2F3540]">
              <RefreshCw className="w-6 h-6 text-[#10B981] animate-spin mx-auto opacity-75" />
              <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF]">
                Retrieving patient records and synchronizing clinical chronology...
              </p>
            </div>
          )}

          {/* Empty State */}
          {!isLoadingEvents && events.length === 0 && (
            <div className="p-12 text-center bg-white dark:bg-[#1B1E23] rounded-2xl border border-[#E5E7EB] dark:border-[#2F3540] space-y-3">
              <GitCommit className="w-8 h-8 text-[#9CA3AF] mx-auto opacity-50" />
              <h3 className="text-base font-semibold text-[#1F2937] dark:text-[#F3F4F6]">No Clinical Milestones Found</h3>
              <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF] max-w-sm mx-auto leading-relaxed">
                No clinical records matched the selected filters. Reset your filters to view all recorded encounters.
              </p>
              <Button variant="secondary" size="sm" onClick={resetTimelineFilters}>
                Reset All Filters
              </Button>
            </div>
          )}

          {/* Timeline Stream */}
          {!isLoadingEvents && events.length > 0 && (
            <div className="relative pl-6 sm:pl-10 space-y-12 border-l-2 border-[#E5E7EB] dark:border-[#2F3540] ml-4 sm:ml-6">
              {groupedEvents.years.map((yr) => {
                const eventsInYr = groupedEvents.map.get(yr) || [];
                return (
                  <div key={yr} className="space-y-4 relative">
                    {/* Year Marker */}
                    <div className="absolute -left-[31px] sm:-left-[47px] top-0 flex items-center space-x-3">
                      <div className="w-8 h-8 sm:w-9 sm:h-9 rounded-full bg-white dark:bg-[#1B1E23] border-2 border-[#10B981] text-[#1F2937] dark:text-[#F3F4F6] font-semibold text-xs sm:text-sm flex items-center justify-center shadow-xs tabular-nums ring-4 ring-[#FAF8F5] dark:ring-[#121417]">
                        {yr > 0 ? yr : '??'}
                      </div>
                    </div>

                    <div className="pt-1 pl-3 sm:pl-4 space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-[11px] font-semibold text-[#6B7280] dark:text-[#9CA3AF] tracking-wider uppercase tabular-nums">
                          {yr > 0 ? `${yr} Clinical Records` : 'Undated Records'} ({eventsInYr.length})
                        </span>
                      </div>

                      <div className="space-y-3">
                        {eventsInYr.map((event) => (
                          <div
                            key={event.id}
                            onClick={() => setSelectedEvent(event)}
                            className="p-4 sm:p-5 rounded-2xl bg-white dark:bg-[#1B1E23] border border-[#E5E7EB] dark:border-[#2F3540] hover:border-[#10B981]/50 cursor-pointer transition-all shadow-xs group flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                          >
                            <div className="flex items-start gap-3.5 min-w-0">
                              <div className="p-2.5 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E] border border-[#E5E7EB] dark:border-[#2F3540] shrink-0 mt-0.5">
                                {getEventIcon(event.type)}
                              </div>
                              <div className="min-w-0 space-y-1">
                                <div className="flex items-center gap-2 flex-wrap">
                                  <span className="text-xs font-mono font-semibold text-[#10B981] tabular-nums flex items-center gap-1">
                                    <Calendar className="w-3 h-3 text-[#10B981]" />
                                    {event.isUnknownDate ? 'Date Unrecorded' : event.date}
                                  </span>
                                  <Badge variant="secondary" className="text-[10px] py-0 capitalize">
                                    {event.type.replace('_', ' ')}
                                  </Badge>
                                  {event.facility && (
                                    <span className="text-[11px] text-[#6B7280] dark:text-[#9CA3AF] flex items-center gap-1">
                                      <Building2 className="w-3 h-3" /> {event.facility}
                                    </span>
                                  )}
                                  {event.hasConflict && (
                                    <span className="text-[10px] px-1.5 py-0.2 rounded bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-400 border border-amber-200/60 flex items-center gap-1">
                                      <AlertTriangle className="w-2.5 h-2.5" /> Conflict
                                    </span>
                                  )}
                                </div>
                                <h4 className="text-sm font-semibold text-[#1F2937] dark:text-[#F3F4F6] group-hover:text-[#10B981] transition-colors">
                                  {event.title}
                                </h4>
                                <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF] leading-relaxed line-clamp-2">
                                  {event.description}
                                </p>
                                {event.uploadDate && (
                                  <div className="text-[10px] text-slate-400 flex items-center gap-1 pt-0.5">
                                    <Upload className="w-2.5 h-2.5" />
                                    <span>Uploaded: {event.uploadDate.split('T')[0]}</span>
                                  </div>
                                )}
                              </div>
                            </div>

                            <div className="flex items-center gap-2 shrink-0 self-end sm:self-center">
                              <span className="text-xs text-[#10B981] font-medium hidden sm:inline-flex items-center gap-1 group-hover:translate-x-0.5 transition-transform">
                                Inspect Record <ChevronRight className="w-3.5 h-3.5" />
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                );
              })}

              {/* Undated / Incomplete Date Events */}
              {groupedEvents.unknownEvents.length > 0 && (
                <div className="space-y-4 relative">
                  <div className="absolute -left-[31px] sm:-left-[47px] top-0 flex items-center space-x-3">
                    <div className="w-8 h-8 sm:w-9 sm:h-9 rounded-full bg-amber-50 dark:bg-amber-950/40 border-2 border-amber-500 text-amber-700 font-semibold text-xs flex items-center justify-center shadow-xs">
                      ?
                    </div>
                  </div>
                  <div className="pt-1 pl-3 sm:pl-4 space-y-3">
                    <span className="text-[11px] font-semibold text-amber-700 dark:text-amber-400 tracking-wider uppercase">
                      Incomplete or Undated Records ({groupedEvents.unknownEvents.length})
                    </span>
                    <div className="space-y-3">
                      {groupedEvents.unknownEvents.map((event) => (
                        <div
                          key={event.id}
                          onClick={() => setSelectedEvent(event)}
                          className="p-4 rounded-2xl bg-white dark:bg-[#1B1E23] border border-amber-200/80 dark:border-amber-900/40 cursor-pointer shadow-xs"
                        >
                          <div className="flex items-center gap-2 text-xs text-amber-700">
                            <AlertTriangle className="w-3.5 h-3.5" />
                            <span className="font-semibold">{event.title}</span>
                          </div>
                          <p className="text-xs text-slate-600 dark:text-slate-400 mt-1 leading-relaxed">
                            {event.description}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Event Inspection Modal */}
          {selectedEvent && (
            <Modal
              isOpen={!!selectedEvent}
              onClose={() => setSelectedEvent(null)}
              title={selectedEvent.title}
              description={`Clinical Date: ${selectedEvent.isUnknownDate ? 'Unrecorded' : selectedEvent.date} • Facility: ${
                selectedEvent.facility || 'Verified Health Record'
              }`}
            >
              <div className="space-y-4 pt-1">
                {selectedEvent.hasConflict && (
                  <div className="p-3 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 text-xs text-amber-900 dark:text-amber-200 space-y-1">
                    <div className="font-semibold flex items-center gap-1.5">
                      <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                      Multi-Facility Discrepancy Note
                    </div>
                    <p className="text-[11px] leading-relaxed">
                      {selectedEvent.conflictDetails ||
                        'Multiple healthcare entries were recorded across differing facilities on this date.'}
                    </p>
                  </div>
                )}

                <div className="p-4 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/50 border border-[#E5E7EB] dark:border-[#2F3540] space-y-1.5">
                  <span className="text-[10px] font-semibold text-[#6B7280] dark:text-[#9CA3AF] uppercase tracking-wider">
                    Clinical Context & Documentation
                  </span>
                  <p className="text-xs text-[#4B5563] dark:text-[#D1D5DB] leading-relaxed">
                    {selectedEvent.description}
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="p-3 rounded-xl bg-slate-50 dark:bg-[#23272E]/40 border border-slate-200 dark:border-slate-800 space-y-0.5">
                    <span className="text-[10px] text-slate-500 uppercase tracking-wider block">Clinical Encounter</span>
                    <span className="font-mono font-semibold text-slate-800 dark:text-slate-200">
                      {selectedEvent.isUnknownDate ? 'Date Unknown' : selectedEvent.date}
                    </span>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-50 dark:bg-[#23272E]/40 border border-slate-200 dark:border-slate-800 space-y-0.5">
                    <span className="text-[10px] text-slate-500 uppercase tracking-wider block">System Upload Date</span>
                    <span className="font-mono font-semibold text-slate-800 dark:text-slate-200">
                      {selectedEvent.uploadDate ? selectedEvent.uploadDate.split('T')[0] : 'N/A'}
                    </span>
                  </div>
                </div>

                {selectedEvent.doctorName && (
                  <div className="text-xs text-slate-600 dark:text-slate-300 flex items-center gap-1.5">
                    <Stethoscope className="w-3.5 h-3.5 text-[#10B981]" />
                    <span>Attending Physician: <strong>{selectedEvent.doctorName}</strong></span>
                  </div>
                )}

                {selectedEvent.connectedEntities && (
                  <div className="space-y-2">
                    <span className="text-[10px] font-semibold uppercase tracking-wider text-[#6B7280] dark:text-[#9CA3AF]">
                      Connected Clinical Entities
                    </span>
                    {selectedEvent.connectedEntities.diseases && selectedEvent.connectedEntities.diseases.length > 0 && (
                      <div className="flex flex-wrap gap-1.5">
                        {selectedEvent.connectedEntities.diseases.map((d, idx) => (
                          <Badge key={idx} variant="danger">
                            Condition: {d}
                          </Badge>
                        ))}
                      </div>
                    )}
                    {selectedEvent.connectedEntities.medications && selectedEvent.connectedEntities.medications.length > 0 && (
                      <div className="flex flex-wrap gap-1.5">
                        {selectedEvent.connectedEntities.medications.map((m, idx) => (
                          <Badge key={idx} variant="success">
                            Rx: {m}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {selectedEvent.sourceReportTitle && (
                  <div className="p-3 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/60 border border-[#E5E7EB] dark:border-[#2F3540] flex items-center justify-between text-xs">
                    <span className="font-medium text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-1.5">
                      <FileText className="w-3.5 h-3.5 text-[#10B981]" /> {selectedEvent.sourceReportTitle}
                    </span>
                    <span className="text-[#10B981] font-medium text-[11px]">Primary Source</span>
                  </div>
                )}

                <Button variant="primary" className="w-full mt-2" onClick={() => setSelectedEvent(null)}>
                  Close
                </Button>
              </div>
            </Modal>
          )}
        </div>
      )}

      {/* TAB 2: LABORATORY TRENDS & BIOMARKERS */}
      {activeTab === 'trends' && (
        <div className="space-y-6">
          {/* Analyte Selection Controls */}
          <div className="p-4 rounded-2xl bg-white dark:bg-[#1B1E23] border border-[#E5E7EB] dark:border-[#2F3540] space-y-3.5 shadow-xs">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h3 className="text-sm font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-1.5">
                  <Activity className="w-4 h-4 text-[#10B981]" />
                  Select Laboratory Analyte
                </h3>
                <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF]">
                  Choose any recorded biomarker to inspect historical measurements and source reports.
                </p>
              </div>

              {/* Time Window Buttons */}
              <div className="flex items-center gap-1 bg-[#FAF8F5] dark:bg-[#23272E] p-1 rounded-xl border border-[#E5E7EB] dark:border-[#2F3540]">
                {[
                  { id: 'all', label: 'All Time' },
                  { id: '1y', label: '1 Year' },
                  { id: '6m', label: '6 Months' },
                  { id: '3m', label: '3 Months' },
                ].map((tw) => (
                  <button
                    key={tw.id}
                    type="button"
                    onClick={() => setTimeWindow(tw.id)}
                    className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-colors ${
                      timeWindow === tw.id
                        ? 'bg-white dark:bg-[#1B1E23] text-[#10B981] shadow-xs'
                        : 'text-[#6B7280] dark:text-[#9CA3AF] hover:text-[#1F2937]'
                    }`}
                  >
                    {tw.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Analyte Search & Dropdown */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
              <div className="relative">
                <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
                <input
                  type="text"
                  value={analyteSearch}
                  onChange={(e) => setAnalyteSearch(e.target.value)}
                  placeholder="Search analyte (e.g. Potassium, Glucose, HbA1c)..."
                  className="w-full h-8 pl-8 pr-3 rounded-xl border border-[#E5E7EB] dark:border-[#2F3540] bg-white dark:bg-[#23272E] text-xs text-[#1F2937] dark:text-[#F3F4F6] focus:outline-hidden focus:ring-1 focus:ring-[#10B981]"
                />
              </div>

              <div>
                <select
                  value={selectedAnalyte}
                  onChange={(e) => setSelectedAnalyte(e.target.value)}
                  className="w-full h-8 px-3 rounded-xl border border-[#E5E7EB] dark:border-[#2F3540] bg-white dark:bg-[#23272E] text-xs font-medium text-[#1F2937] dark:text-[#F3F4F6] focus:outline-hidden focus:ring-1 focus:ring-[#10B981]"
                >
                  {filteredAnalytes.map((a) => (
                    <option key={a.canonicalName} value={a.canonicalName}>
                      {a.canonicalName} ({a.count} observation{a.count > 1 ? 's' : ''} &bull; Latest: {a.latestValue} {a.unit || ''})
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Trend Error */}
          {trendError && (
            <div className="p-4 rounded-2xl bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-800 text-xs text-rose-800 dark:text-rose-200">
              {trendError}
            </div>
          )}

          {/* Trend Loading Skeleton */}
          {isLoadingTrend && (
            <div className="p-8 text-center bg-white dark:bg-[#1B1E23] rounded-2xl border border-[#E5E7EB] dark:border-[#2F3540] space-y-3">
              <RefreshCw className="w-6 h-6 text-[#10B981] animate-spin mx-auto opacity-75" />
              <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF]">
                Analyzing longitudinal measurements for {selectedAnalyte}...
              </p>
            </div>
          )}

          {/* Render Trend Card */}
          {!isLoadingTrend && trendData && (
            <div className="space-y-4">
              <ClinicalTrendCard trend={trendData} />
            </div>
          )}

          {/* Empty state if no data */}
          {!isLoadingTrend && !trendData && (
            <div className="p-12 text-center bg-white dark:bg-[#1B1E23] rounded-2xl border border-[#E5E7EB] dark:border-[#2F3540] space-y-2">
              <Activity className="w-8 h-8 text-slate-300 mx-auto" />
              <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300">No Biomarker Selected</h4>
              <p className="text-xs text-slate-500 max-w-sm mx-auto">
                Select an analyte from your verified laboratory records above to inspect its longitudinal trend.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
