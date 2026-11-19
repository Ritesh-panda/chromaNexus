import React, { useState, useEffect } from 'react';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { hospitalService, type NearbyHospital } from '@/services/hospital.service';
import { 
  Building2, 
  MapPin, 
  PhoneCall, 
  Navigation, 
  Loader2, 
  AlertTriangle, 
  Compass, 
  Search,
  ExternalLink 
} from 'lucide-react';

export interface HospitalLocatorModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialQuery?: string;
}

export const HospitalLocatorModal: React.FC<HospitalLocatorModalProps> = ({
  isOpen,
  onClose,
  initialQuery = ''
}) => {
  const [hospitals, setHospitals] = useState<NearbyHospital[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [coords, setCoords] = useState<{ lat: number; lng: number } | null>(null);
  const [locationName, setLocationName] = useState<string>('Detecting Current GPS Location...');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fetchHospitalsForCoords = async (lat: number, lng: number) => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const results = await hospitalService.getNearbyHospitals(lat, lng, 12);
      setHospitals(results);
    } catch (err) {
      setErrorMsg('Could not query OpenStreetMap. Using emergency fallback.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDetectLocation = async () => {
    setIsLoading(true);
    setErrorMsg(null);

    const useIpFallback = async () => {
      const ipLoc = await hospitalService.detectIpLocation();
      if (ipLoc) {
        setCoords({ lat: ipLoc.latitude, lng: ipLoc.longitude });
        setLocationName(`${ipLoc.displayName || ipLoc.city || 'Detected Location'} (Network IP)`);
        fetchHospitalsForCoords(ipLoc.latitude, ipLoc.longitude);
      } else {
        const fallback = { lat: 16.5062, lng: 80.6480 };
        setCoords(fallback);
        setLocationName('Current Location (Fallback)');
        fetchHospitalsForCoords(fallback.lat, fallback.lng);
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
        setLocationName(`Current GPS: ${c.lat.toFixed(4)}, ${c.lng.toFixed(4)}`);
        fetchHospitalsForCoords(c.lat, c.lng);
      },
      async (err) => {
        console.warn('Geolocation denied or unavailable:', err);
        await useIpFallback();
      },
      { timeout: 7000 }
    );
  };

  useEffect(() => {
    if (isOpen) {
      handleDetectLocation();
    }
  }, [isOpen]);

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Nearby Hospitals & Emergency Facilities"
    >
      <div className="space-y-4">
        {/* Emergency Hotline Header */}
        <div className="p-3.5 rounded-2xl bg-red-500/10 border border-red-500/20 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-red-600 text-white flex items-center justify-center font-bold text-sm shrink-0 shadow-sm animate-pulse">
              108
            </div>
            <div>
              <div className="text-xs font-bold text-red-600 dark:text-red-400 uppercase tracking-wider">
                National Ambulance Dispatch
              </div>
              <div className="text-[11px] text-[#4B5563] dark:text-[#9CA3AF]">
                Toll-free 24/7 medical trauma response across India
              </div>
            </div>
          </div>
          <a
            href="tel:108"
            className="px-3 py-1.5 rounded-xl bg-red-600 text-white font-semibold text-xs hover:bg-red-700 transition flex items-center gap-1.5 shadow-sm"
          >
            <PhoneCall className="w-3.5 h-3.5" /> Call 108
          </a>
        </div>

        {/* Location Status Bar */}
        <div className="flex items-center justify-between text-xs px-1 text-[#6B7280] dark:text-[#9CA3AF]">
          <div className="flex items-center gap-1.5 truncate max-w-[320px]">
            <MapPin className="w-3.5 h-3.5 text-[#10B981] shrink-0" />
            <span className="truncate font-medium">{locationName}</span>
          </div>
          <button
            onClick={handleDetectLocation}
            disabled={isLoading}
            className="text-[#10B981] hover:underline text-xs flex items-center gap-1 font-medium shrink-0"
          >
            <Compass className="w-3 h-3" /> Refresh GPS
          </button>
        </div>

        {/* Hospital Cards List */}
        {isLoading ? (
          <div className="py-12 flex flex-col items-center justify-center space-y-2 text-xs text-[#9CA3AF]">
            <Loader2 className="w-6 h-6 animate-spin text-[#10B981]" />
            <span>Scanning OpenStreetMap for verified clinics & casualty wards...</span>
          </div>
        ) : hospitals.length === 0 ? (
          <div className="py-8 text-center text-xs text-[#9CA3AF]">
            No hospital records found in this perimeter. Try expanding GPS radius.
          </div>
        ) : (
          <div className="max-h-[380px] overflow-y-auto space-y-2.5 pr-1">
            {hospitals.map((hosp) => (
              <div
                key={hosp.id}
                className="p-3.5 rounded-xl border border-[#E5E7EB] dark:border-[#2F3540] bg-[#FAF8F5]/50 dark:bg-[#23272E]/40 hover:border-emerald-500/50 transition-colors flex items-start justify-between gap-3"
              >
                <div className="space-y-1 min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-xs text-[#1F2937] dark:text-[#F3F4F6] truncate">
                      {hosp.name}
                    </span>
                    {hosp.isEmergency && (
                      <span className="px-1.5 py-0.5 rounded text-[10px] bg-red-100 text-red-600 dark:bg-red-950/60 dark:text-red-400 font-bold shrink-0">
                        24/7 Casualty
                      </span>
                    )}
                  </div>
                  <div className="text-[11px] text-[#6B7280] dark:text-[#9CA3AF] flex items-center gap-2">
                    <span>{hosp.type}</span>
                    <span>•</span>
                    <span className="font-semibold text-[#10B981]">{hosp.distanceKm} km away</span>
                  </div>
                  <p className="text-[11px] text-[#4B5563] dark:text-[#9CA3AF] truncate">
                    {hosp.address}
                  </p>
                </div>

                <div className="flex flex-col gap-1.5 shrink-0">
                  <a
                    href={hosp.directionsUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="px-2.5 py-1.5 rounded-lg bg-white dark:bg-[#1B1E23] border border-[#E5E7EB] dark:border-[#2F3540] hover:border-emerald-500 text-xs font-medium text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-1 transition"
                  >
                    <Navigation className="w-3 h-3 text-[#10B981]" /> Directions
                  </a>
                  {hosp.phone && (
                    <a
                      href={`tel:${hosp.phone}`}
                      className="px-2.5 py-1.5 rounded-lg bg-[#ECFDF5] dark:bg-emerald-950/50 text-[#10B981] hover:bg-emerald-100 dark:hover:bg-emerald-900/40 text-xs font-semibold flex items-center justify-center gap-1 transition"
                    >
                      <PhoneCall className="w-3 h-3" /> Call
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="pt-2 border-t border-[#E5E7EB] dark:border-[#2F3540] flex items-center justify-between text-[10px] text-[#9CA3AF]">
          <span>Data source: OpenStreetMap (OSM) public registry. Free & open-source.</span>
          <Button variant="secondary" size="sm" onClick={onClose}>
            Close
          </Button>
        </div>
      </div>
    </Modal>
  );
};
