import React, { useState, useEffect } from 'react';
import { 
  Building2, 
  MapPin, 
  PhoneCall, 
  Navigation, 
  Loader2, 
  Search, 
  Crosshair, 
  AlertCircle, 
  Clock, 
  ExternalLink,
  ShieldAlert,
  Share2,
  CheckCircle2,
  Compass
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { hospitalService, type NearbyHospital, type LocationResult } from '@/services/hospital.service';

const POPULAR_CITIES = [
  { name: 'Vijayawada', lat: 16.5062, lng: 80.6480 },
  { name: 'Bhubaneswar', lat: 20.2961, lng: 85.8245 },
  { name: 'Cuttack', lat: 20.4625, lng: 85.8828 },
  { name: 'Hyderabad', lat: 17.3850, lng: 78.4867 },
  { name: 'Bengaluru', lat: 12.9716, lng: 77.5946 },
  { name: 'Delhi NCR', lat: 28.6139, lng: 77.2090 },
  { name: 'Mumbai', lat: 19.0760, lng: 72.8777 },
  { name: 'Kolkata', lat: 22.5726, lng: 88.3639 }
];

export const HospitalFinderPage: React.FC = () => {
  const [hospitals, setHospitals] = useState<NearbyHospital[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [coords, setCoords] = useState<{ lat: number; lng: number } | null>(null);
  const [locationName, setLocationName] = useState<string>('Detecting location...');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [searchResults, setSearchResults] = useState<LocationResult[]>([]);
  const [isSearchingLocation, setIsSearchingLocation] = useState<boolean>(false);
  const [activeFilter, setActiveFilter] = useState<'all' | 'emergency' | 'general'>('all');
  const [radiusKm, setRadiusKm] = useState<number>(10);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const fetchHospitals = async (lat: number, lng: number, radius: number = 10) => {
    setIsLoading(true);
    try {
      const results = await hospitalService.getNearbyHospitals(lat, lng, radius);
      setHospitals(results);
    } catch (err) {
      console.error('Error fetching hospitals:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDetectLocation = async () => {
    setIsLoading(true);
    setLocationName('Detecting location...');

    const useIpFallback = async () => {
      const ipLoc = await hospitalService.detectIpLocation();
      if (ipLoc) {
        const c = { lat: ipLoc.latitude, lng: ipLoc.longitude };
        setCoords(c);
        setLocationName(ipLoc.displayName || `${ipLoc.city}, ${ipLoc.region}`);
        fetchHospitals(c.lat, c.lng, radiusKm);
      } else {
        const fallback = { lat: 16.5062, lng: 80.6480 };
        setCoords(fallback);
        setLocationName('Vijayawada, Andhra Pradesh (Network Estimate)');
        fetchHospitals(fallback.lat, fallback.lng, radiusKm);
      }
    };

    if (!navigator.geolocation) {
      await useIpFallback();
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const c = { lat: pos.coords.latitude, lng: pos.coords.longitude };
        setCoords(c);
        setLocationName(`Current GPS (${c.lat.toFixed(3)}, ${c.lng.toFixed(3)})`);
        fetchHospitals(c.lat, c.lng, radiusKm);
      },
      async (err) => {
        console.warn('Browser GPS unavailable, engaging IP Geolocation:', err);
        await useIpFallback();
      },
      { timeout: 8000, enableHighAccuracy: true }
    );
  };

  useEffect(() => {
    handleDetectLocation();
  }, []);

  const handleSearchSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    setIsSearchingLocation(true);
    try {
      const results = await hospitalService.searchLocations(searchQuery);
      setSearchResults(results);
      if (results.length > 0) {
        const first = results[0];
        setCoords({ lat: first.latitude, lng: first.longitude });
        setLocationName(first.displayName.split(',').slice(0, 2).join(', '));
        fetchHospitals(first.latitude, first.longitude, radiusKm);
        setSearchResults([]);
      }
    } finally {
      setIsSearchingLocation(false);
    }
  };

  const handleSelectCity = (city: typeof POPULAR_CITIES[0]) => {
    setCoords({ lat: city.lat, lng: city.lng });
    setLocationName(city.name);
    setSearchQuery('');
    setSearchResults([]);
    fetchHospitals(city.lat, city.lng, radiusKm);
  };

  const handleSelectSearchResult = (res: LocationResult) => {
    setCoords({ lat: res.latitude, lng: res.longitude });
    setLocationName(res.displayName.split(',').slice(0, 2).join(', '));
    setSearchQuery('');
    setSearchResults([]);
    fetchHospitals(res.latitude, res.longitude, radiusKm);
  };

  const handleShareDirections = (hospital: NearbyHospital) => {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(hospital.directionsUrl);
      setCopiedId(hospital.id);
      setTimeout(() => setCopiedId(null), 2000);
    }
  };

  const filteredHospitals = hospitals.filter((h) => {
    if (activeFilter === 'emergency') return h.isEmergency;
    if (activeFilter === 'general') return !h.isEmergency;
    return true;
  });

  return (
    <div className="space-y-6 pb-12 max-w-7xl mx-auto px-4 sm:px-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pt-2">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold text-emerald-600 dark:text-emerald-400 uppercase tracking-wider mb-1">
            <Compass className="w-4 h-4" /> OpenStreetMap Public Registry
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#1F2937] dark:text-[#F3F4F6]">
            Hospital & Emergency Finder
          </h1>
          <p className="text-sm text-[#6B7280] dark:text-[#9CA3AF] mt-1">
            Discover verified 24/7 trauma centers, government hospitals, and casualty wards across India.
          </p>
        </div>

        {/* Current Location Badge & GPS Refresh */}
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-white dark:bg-[#1E222B] border border-[#E5E7EB] dark:border-[#2F3540] shadow-sm text-xs">
            <MapPin className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
            <span className="font-medium text-[#1F2937] dark:text-[#F3F4F6] truncate max-w-[200px]" title={locationName}>
              {locationName}
            </span>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={handleDetectLocation}
            disabled={isLoading}
            className="flex items-center gap-1.5 shadow-sm"
          >
            {isLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Crosshair className="w-3.5 h-3.5" />}
            Refresh GPS
          </Button>
        </div>
      </div>

      {/* Emergency 108 Banner */}
      <div className="relative overflow-hidden p-4 sm:p-5 rounded-2xl bg-gradient-to-r from-red-600 to-rose-700 text-white shadow-lg">
        <div className="relative z-10 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-start sm:items-center gap-3.5">
            <div className="w-12 h-12 rounded-2xl bg-white/20 backdrop-blur-md flex items-center justify-center font-black text-xl shrink-0 shadow-inner">
              108
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 rounded-full bg-white/20 text-[10px] font-bold uppercase tracking-wider">
                  National Emergency Service
                </span>
                <span className="text-xs text-red-100 flex items-center gap-1">
                  <Clock className="w-3 h-3" /> Toll-Free 24/7 Medical Trauma Response
                </span>
              </div>
              <h2 className="text-lg font-bold mt-0.5">
                Life-Threatening Emergency? Dial 108 or 112 Immediately
              </h2>
              <p className="text-xs text-red-100 max-w-xl">
                Government ambulance dispatch network across all Indian states and Union Territories.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <a
              href="tel:108"
              className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-white text-red-700 font-bold text-sm shadow-md hover:bg-red-50 transition-colors"
            >
              <PhoneCall className="w-4 h-4 animate-bounce" />
              Call 108 Now
            </a>
            <a
              href="tel:112"
              className="inline-flex items-center justify-center gap-1.5 px-4 py-2.5 rounded-xl bg-white/15 hover:bg-white/25 text-white font-semibold text-sm transition-colors"
            >
              Dial 112
            </a>
          </div>
        </div>
      </div>

      {/* Location Search & Filter Controls */}
      <div className="p-4 rounded-2xl bg-white dark:bg-[#1B1E23] border border-[#E5E7EB] dark:border-[#2F3540] shadow-sm space-y-3.5">
        <div className="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-3">
          {/* Search Box */}
          <form onSubmit={handleSearchSubmit} className="relative flex-1 max-w-xl">
            <Search className="w-4 h-4 text-[#9CA3AF] absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by city, pincode, or district (e.g., Cuttack, Vijayawada, Delhi)..."
              className="w-full pl-9 pr-24 py-2 text-sm rounded-xl bg-[#FAF8F5] dark:bg-[#23272E] border border-[#E5E7EB] dark:border-[#2F3540] text-[#1F2937] dark:text-[#F3F4F6] focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
            />
            <Button
              type="submit"
              size="sm"
              disabled={isSearchingLocation || !searchQuery.trim()}
              className="absolute right-1 top-1/2 -translate-y-1/2 h-7 px-3 text-xs"
            >
              {isSearchingLocation ? <Loader2 className="w-3 h-3 animate-spin" /> : 'Search'}
            </Button>
          </form>

          {/* Filter Pills */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 lg:pb-0">
            <button
              onClick={() => setActiveFilter('all')}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-colors ${
                activeFilter === 'all'
                  ? 'bg-emerald-600 text-white'
                  : 'bg-[#FAF8F5] dark:bg-[#23272E] text-[#6B7280] dark:text-[#9CA3AF] hover:text-[#1F2937] dark:hover:text-white'
              }`}
            >
              All Facilities ({hospitals.length})
            </button>
            <button
              onClick={() => setActiveFilter('emergency')}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-colors flex items-center gap-1 ${
                activeFilter === 'emergency'
                  ? 'bg-red-600 text-white'
                  : 'bg-[#FAF8F5] dark:bg-[#23272E] text-[#6B7280] dark:text-[#9CA3AF] hover:text-red-500'
              }`}
            >
              <ShieldAlert className="w-3 h-3" />
              24/7 Emergency ({hospitals.filter((h) => h.isEmergency).length})
            </button>
            <button
              onClick={() => setActiveFilter('general')}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-colors ${
                activeFilter === 'general'
                  ? 'bg-emerald-600 text-white'
                  : 'bg-[#FAF8F5] dark:bg-[#23272E] text-[#6B7280] dark:text-[#9CA3AF] hover:text-[#1F2937] dark:hover:text-white'
              }`}
            >
              General Hospitals ({hospitals.filter((h) => !h.isEmergency).length})
            </button>
          </div>
        </div>

        {/* Search Results Dropdown (if multiple Nominatim results) */}
        {searchResults.length > 0 && (
          <div className="p-2 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E] border border-emerald-500/30 space-y-1">
            <div className="text-[11px] font-semibold text-emerald-600 dark:text-emerald-400 px-2">
              Select Location Match:
            </div>
            {searchResults.map((res, i) => (
              <button
                key={i}
                onClick={() => handleSelectSearchResult(res)}
                className="w-full text-left px-2.5 py-1.5 rounded-lg text-xs hover:bg-emerald-500/10 text-[#1F2937] dark:text-[#F3F4F6] flex items-center justify-between"
              >
                <span className="truncate">{res.displayName}</span>
                <span className="text-[10px] text-[#9CA3AF] shrink-0 ml-2">Select</span>
              </button>
            ))}
          </div>
        )}

        {/* Quick City Pills */}
        <div className="flex items-center gap-1.5 flex-wrap pt-1 border-t border-[#E5E7EB]/70 dark:border-[#2F3540]/70">
          <span className="text-[11px] font-medium text-[#6B7280] dark:text-[#9CA3AF] mr-1">
            Quick Cities:
          </span>
          {POPULAR_CITIES.map((c) => (
            <button
              key={c.name}
              onClick={() => handleSelectCity(c)}
              className="px-2.5 py-1 rounded-lg text-xs bg-[#FAF8F5] dark:bg-[#23272E] hover:bg-emerald-500/10 hover:text-emerald-600 dark:hover:text-emerald-400 border border-[#E5E7EB] dark:border-[#2F3540] text-[#4B5563] dark:text-[#D1D5DB] transition-colors"
            >
              {c.name}
            </button>
          ))}
        </div>
      </div>

      {/* Hospital Listing Grid */}
      {isLoading ? (
        <div className="p-12 text-center rounded-2xl bg-white dark:bg-[#1B1E23] border border-[#E5E7EB] dark:border-[#2F3540]">
          <Loader2 className="w-8 h-8 text-emerald-600 animate-spin mx-auto mb-3" />
          <p className="text-sm font-medium text-[#1F2937] dark:text-[#F3F4F6]">
            Querying OpenStreetMap Registry around {locationName}...
          </p>
          <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF] mt-1">
            Retrieving verified GPS coordinates, emergency casualty status, and road directions.
          </p>
        </div>
      ) : filteredHospitals.length === 0 ? (
        <div className="p-12 text-center rounded-2xl bg-white dark:bg-[#1B1E23] border border-[#E5E7EB] dark:border-[#2F3540]">
          <AlertCircle className="w-8 h-8 text-amber-500 mx-auto mb-3" />
          <p className="text-base font-semibold text-[#1F2937] dark:text-[#F3F4F6]">
            No facilities found matching your criteria.
          </p>
          <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF] mt-1">
            Try searching a larger city, refreshing your GPS, or selecting another filter.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredHospitals.map((hospital) => (
            <div
              key={hospital.id}
              className={`p-4 rounded-2xl bg-white dark:bg-[#1B1E23] border transition-all duration-200 flex flex-col justify-between hover:shadow-md ${
                hospital.isEmergency
                  ? 'border-red-500/30 dark:border-red-500/20 hover:border-red-500/50'
                  : 'border-[#E5E7EB] dark:border-[#2F3540] hover:border-emerald-500/40'
              }`}
            >
              <div>
                {/* Header: Name + Badges */}
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1">
                    <div className="flex items-center gap-1.5 flex-wrap mb-1.5">
                      {hospital.isEmergency ? (
                        <Badge variant="danger" className="text-[10px] font-bold uppercase">
                          24/7 Casualty
                        </Badge>
                      ) : (
                        <Badge variant="secondary" className="text-[10px]">
                          {hospital.type}
                        </Badge>
                      )}
                      <span className="text-[11px] font-semibold text-emerald-600 dark:text-emerald-400">
                        {hospital.distanceKm === 0 ? 'Exact Location' : `${hospital.distanceKm} km away`}
                      </span>
                    </div>
                    <h3 className="text-sm font-bold text-[#1F2937] dark:text-[#F3F4F6] line-clamp-2">
                      {hospital.name}
                    </h3>
                  </div>

                  <div className="w-8 h-8 rounded-xl bg-emerald-500/10 dark:bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 flex items-center justify-center shrink-0">
                    <Building2 className="w-4 h-4" />
                  </div>
                </div>

                {/* Address */}
                <div className="flex items-start gap-1.5 text-xs text-[#6B7280] dark:text-[#9CA3AF] mt-3">
                  <MapPin className="w-3.5 h-3.5 text-[#9CA3AF] shrink-0 mt-0.5" />
                  <p className="line-clamp-2">{hospital.address}</p>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="pt-4 mt-3 border-t border-[#E5E7EB]/70 dark:border-[#2F3540]/70 flex items-center gap-2">
                <a
                  href={`tel:${hospital.phone || '108'}`}
                  className="flex-1 inline-flex items-center justify-center gap-1.5 py-2 px-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs transition-colors shadow-sm"
                >
                  <PhoneCall className="w-3.5 h-3.5" />
                  Call {hospital.phone || '108'}
                </a>
                <a
                  href={hospital.directionsUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center justify-center gap-1 py-2 px-3 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E] hover:bg-[#F3F4F6] dark:hover:bg-[#2F3540] text-[#1F2937] dark:text-[#F3F4F6] border border-[#E5E7EB] dark:border-[#2F3540] font-medium text-xs transition-colors"
                >
                  <Navigation className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
                  Directions
                </a>
                <button
                  onClick={() => handleShareDirections(hospital)}
                  title="Copy Directions Link"
                  className="p-2 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E] hover:bg-[#F3F4F6] dark:hover:bg-[#2F3540] text-[#6B7280] dark:text-[#9CA3AF] border border-[#E5E7EB] dark:border-[#2F3540] text-xs transition-colors"
                >
                  {copiedId === hospital.id ? (
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                  ) : (
                    <Share2 className="w-3.5 h-3.5" />
                  )}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
export default HospitalFinderPage;
