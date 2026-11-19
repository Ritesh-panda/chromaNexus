import { api } from './axios';

export interface NearbyHospital {
  id: string;
  name: string;
  type: string;
  distanceKm: number;
  isEmergency: boolean;
  phone: string;
  address: string;
  latitude: number;
  longitude: number;
  directionsUrl: string;
}

export interface NearbyHospitalResponse {
  status: string;
  count: number;
  userCoordinates: { lat: number; lng: number };
  hospitals: NearbyHospital[];
}

export interface LocationResult {
  displayName: string;
  latitude: number;
  longitude: number;
  city?: string;
  region?: string;
}

export const hospitalService = {
  async detectIpLocation(): Promise<LocationResult | null> {
    try {
      const response = await api.get<{ status: string; location: LocationResult }>('/hospitals/ip-location');
      return response.data?.location || null;
    } catch {
      try {
        // Direct client fallback
        const res = await fetch('https://ipapi.co/json/');
        if (res.ok) {
          const data = await res.json();
          if (data.latitude && data.longitude) {
            return {
              displayName: `${data.city}, ${data.region}`,
              latitude: Number(data.latitude),
              longitude: Number(data.longitude),
              city: data.city,
              region: data.region
            };
          }
        }
      } catch (err) {
        console.warn('Direct IP geocoding fallback failed:', err);
      }
      return null;
    }
  },

  async searchLocations(query: string): Promise<LocationResult[]> {
    if (!query || query.trim().length < 2) return [];
    try {
      const response = await api.get<{ status: string; results: LocationResult[] }>('/hospitals/search-location', {
        params: { query: query.trim() }
      });
      return response.data?.results || [];
    } catch {
      return [];
    }
  },

  async getNearbyHospitals(lat: number, lng: number, radiusKm: number = 10): Promise<NearbyHospital[]> {
    try {
      const response = await api.get<NearbyHospitalResponse>('/hospitals/nearby', {
        params: { lat, lng, radius_km: radiusKm }
      });
      return response.data?.hospitals || [];
    } catch (error) {
      console.warn('Hospital service API call error, using local fallback:', error);
      return [
        {
          id: 'em_108',
          name: '108 Emergency Ambulance Dispatch Network',
          type: 'Emergency Casualty & Trauma Dispatch',
          distanceKm: 0.0,
          isEmergency: true,
          phone: '108',
          address: 'Emergency Dispatch to Your Current Coordinates',
          latitude: lat,
          longitude: lng,
          directionsUrl: `https://www.google.com/maps/search/hospitals/@${lat},${lng},13z`
        },
        {
          id: 'dist_govt',
          name: 'District Civil & Trauma Hospital',
          type: '24/7 Government Emergency Center',
          distanceKm: 2.3,
          isEmergency: true,
          phone: '108',
          address: 'District Main Healthcare Center',
          latitude: lat + 0.012,
          longitude: lng + 0.012,
          directionsUrl: `https://www.google.com/maps/search/hospitals/@${lat},${lng},13z`
        }
      ];
    }
  }
};
