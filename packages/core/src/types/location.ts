export interface PhysicalLocation {
  latitude?: number;
  longitude?: number;
  city?: string;
  state?: string;
  country?: string;
  zip?: string;
  address?: string;
  timezone?: string;
  ip?: string;
  provider?: string;
  accuracy?: number;
  source?: string;
  lastUpdated?: Date;
}
