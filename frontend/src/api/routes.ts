import { apiClient } from './client';

// --- Types ---

export interface Waypoint {
  lat: number;
  lng: number;
  alt?: number | null;
  km_marker?: number | null;
}

export interface RouteSegment {
  segment_type: string;
  start_km: number;
  end_km: number;
  target_pace_min?: string | null;
  target_pace_max?: string | null;
  target_hr_min?: number | null;
  target_hr_max?: number | null;
  elevation_gain_m?: number | null;
  elevation_loss_m?: number | null;
  surface?: string | null;
  notes?: string | null;
}

export interface TrainingRouteResponse {
  id: number;
  name: string;
  description: string | null;
  distance_km: number;
  elevation_gain_m: number;
  elevation_loss_m: number;
  location_name: string | null;
  surface: Record<string, number> | null;
  waypoints: Waypoint[];
  route_segments: RouteSegment[] | null;
  pacing_strategy: string | null;
  linked_session_template_id: number | null;
  tags: string[] | null;
  is_favorite: boolean;
  created_at: string;
  updated_at: string;
}

export interface TrainingRouteSummary {
  id: number;
  name: string;
  distance_km: number;
  elevation_gain_m: number;
  location_name: string | null;
  pacing_strategy: string | null;
  tags: string[] | null;
  is_favorite: boolean;
  waypoint_count: number;
  segment_count: number;
  created_at: string;
  updated_at: string;
}

export interface TrainingRouteListResponse {
  routes: TrainingRouteSummary[];
  total: number;
}

export interface TrainingRouteCreateParams {
  name: string;
  description?: string;
  distance_km: number;
  elevation_gain_m?: number;
  elevation_loss_m?: number;
  location_name?: string;
  surface?: Record<string, number>;
  waypoints: Waypoint[];
  route_segments?: RouteSegment[];
  pacing_strategy?: string;
  tags?: string[];
  is_favorite?: boolean;
}

export interface TrainingRouteUpdateParams {
  name?: string;
  description?: string;
  distance_km?: number;
  waypoints?: Waypoint[];
  route_segments?: RouteSegment[];
  is_favorite?: boolean;
  tags?: string[];
}

export interface RouteSnapResponse {
  points: Waypoint[];
  distance_km: number;
  duration_s: number;
  snapped_waypoints: Waypoint[];
}

export interface RoundTripOption {
  points: Waypoint[];
  distance_km: number;
  duration_s: number;
  target_distance_km: number;
  deviation_percent: number;
  direction_deg: number;
}

export interface RoundTripResponse {
  options: RoundTripOption[];
}

// --- Pacing Types (#548) ---

export interface RoutePacingRequest {
  target_time_seconds: number;
  strategy: 'even' | 'negative' | 'effort_based';
  temperature_celsius?: number | null;
  wind_speed_kmh?: number | null;
  humidity_percent?: number | null;
}

export interface SegmentPacing {
  segment_index: number;
  segment_type: string;
  start_km: number;
  end_km: number;
  distance_km: number;
  elevation_gain_m: number;
  elevation_loss_m: number;
  target_pace_min: string;
  target_pace_max: string;
  target_time_seconds: number;
  target_time_formatted: string;
  avg_pace_sec_per_km: number;
  notes: string | null;
}

export interface RoutePacingResponse {
  strategy: string;
  strategy_label: string;
  distance_km: number;
  target_time_seconds: number;
  target_time_formatted: string;
  avg_pace_sec_per_km: number;
  avg_pace_formatted: string;
  segment_pacing: SegmentPacing[];
  weather_notes: string | null;
  general_notes: string[];
}

// --- API Functions ---

export async function listRoutes(params?: {
  is_favorite?: boolean;
  tag?: string;
  search?: string;
}): Promise<TrainingRouteListResponse> {
  const searchParams = new URLSearchParams();
  if (params?.is_favorite !== undefined)
    searchParams.set('is_favorite', String(params.is_favorite));
  if (params?.tag) searchParams.set('tag', params.tag);
  if (params?.search) searchParams.set('search', params.search);

  const url = searchParams.toString()
    ? `/api/v1/routes?${searchParams.toString()}`
    : '/api/v1/routes';

  const response = await apiClient.get<TrainingRouteListResponse>(url);
  return response.data;
}

export async function getRoute(routeId: number): Promise<TrainingRouteResponse> {
  const response = await apiClient.get<TrainingRouteResponse>(`/api/v1/routes/${routeId}`);
  return response.data;
}

export async function createRoute(
  params: TrainingRouteCreateParams,
): Promise<TrainingRouteResponse> {
  const response = await apiClient.post<TrainingRouteResponse>('/api/v1/routes', params);
  return response.data;
}

export async function updateRoute(
  routeId: number,
  params: TrainingRouteUpdateParams,
): Promise<TrainingRouteResponse> {
  const response = await apiClient.patch<TrainingRouteResponse>(
    `/api/v1/routes/${routeId}`,
    params,
  );
  return response.data;
}

export async function deleteRoute(routeId: number): Promise<void> {
  await apiClient.delete(`/api/v1/routes/${routeId}`);
}

export async function snapRoute(waypoints: Waypoint[]): Promise<RouteSnapResponse> {
  const response = await apiClient.post<RouteSnapResponse>('/api/v1/routes/snap', { waypoints });
  return response.data;
}

export async function generateRoundTrip(params: {
  start_lat: number;
  start_lng: number;
  target_distance_km: number;
  num_alternatives?: number;
}): Promise<RoundTripResponse> {
  const response = await apiClient.post<RoundTripResponse>(
    '/api/v1/routes/generate-round-trip',
    params,
  );
  return response.data;
}

export async function calculateRoutePacing(
  routeId: number,
  params: RoutePacingRequest,
): Promise<RoutePacingResponse> {
  const response = await apiClient.post<RoutePacingResponse>(
    `/api/v1/routes/${routeId}/pacing`,
    params,
  );
  return response.data;
}

// --- Route from Template ---

export interface RouteFromTemplateRequest {
  start_lat: number;
  start_lng: number;
  num_alternatives?: number;
}

export interface RouteFromTemplatePreview {
  name: string;
  distance_km: number;
  waypoints: Waypoint[];
  route_segments: RouteSegment[];
  linked_session_template_id: number;
  pacing_strategy: string;
}

export async function routeFromTemplate(
  templateId: number,
  params: RouteFromTemplateRequest,
): Promise<RouteFromTemplatePreview> {
  const response = await apiClient.post<RouteFromTemplatePreview>(
    `/api/v1/routes/from-template/${templateId}`,
    params,
  );
  return response.data;
}

export async function exportRouteGpx(routeId: number, routeName: string): Promise<void> {
  const response = await apiClient.get(`/api/v1/routes/${routeId}/export/gpx`, {
    responseType: 'blob',
  });
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  const safeName = routeName.replace(/\s+/g, '_').replace(/[^\w\-äöüÄÖÜß]/g, '') || 'route';
  link.setAttribute('download', `${safeName}.gpx`);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}
