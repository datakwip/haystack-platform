/**
 * API client for communicating with the simulator FastAPI backend
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';

export interface HealthResponse {
  status: string;
  uptime_seconds: number;
  version: string;
}

export interface StatusResponse {
  status: string;
  last_run: string | null;
  points_generated_total: number | null;
  error_message: string | null;
}

export interface StateResponse {
  status: string;
  last_run_timestamp: string | null;
  totalizers: Record<string, any> | null;
  config: Record<string, any> | null;
  error_message: string | null;
  updated_at: string | null;
}

export interface ControlResponse {
  message: string;
  status: string;
}

export interface ActivityEvent {
  id: number;
  timestamp: string;
  event_type: string;
  message: string;
  details: Record<string, any> | null;
}

export interface ActivityResponse {
  events: ActivityEvent[];
  limit: number;
  offset: number;
  count: number;
}

export interface MetricsResponse {
  total_points_generated: number;
  total_entities: number;
  generation_rate_per_min: number | null;
  last_interval_duration_ms: number | null;
  error_count_24h: number;
  uptime_seconds: number;
}

/**
 * Fetch wrapper with error handling
 */
async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${endpoint}`;

  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(error.detail || `HTTP ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`API Error (${endpoint}):`, error);
    throw error;
  }
}

// Health & Status

export async function getHealth(): Promise<HealthResponse> {
  return fetchAPI<HealthResponse>('/api/health');
}

export async function getStatus(): Promise<StatusResponse> {
  return fetchAPI<StatusResponse>('/api/status');
}

export async function getState(): Promise<StateResponse> {
  return fetchAPI<StateResponse>('/api/state');
}

export async function getMetrics(): Promise<MetricsResponse> {
  return fetchAPI<MetricsResponse>('/api/metrics');
}

// Control Actions

export async function startSimulator(): Promise<ControlResponse> {
  return fetchAPI<ControlResponse>('/api/control/start', {
    method: 'POST',
  });
}

export async function stopSimulator(): Promise<ControlResponse> {
  return fetchAPI<ControlResponse>('/api/control/stop', {
    method: 'POST',
  });
}

export async function resetSimulator(clearData: boolean = false): Promise<ControlResponse> {
  return fetchAPI<ControlResponse>(`/api/control/reset?clear_data=${clearData}`, {
    method: 'POST',
  });
}

// Configuration

export async function getConfig(): Promise<Record<string, any>> {
  return fetchAPI<Record<string, any>>('/api/config');
}

export async function updateConfig(config: Record<string, any>): Promise<ControlResponse> {
  return fetchAPI<ControlResponse>('/api/config', {
    method: 'PUT',
    body: JSON.stringify({ config }),
  });
}

// Activity Log

export async function getActivity(
  limit: number = 100,
  offset: number = 0,
  eventType?: string
): Promise<ActivityResponse> {
  const params = new URLSearchParams({
    limit: limit.toString(),
    offset: offset.toString(),
  });

  if (eventType) {
    params.append('event_type', eventType);
  }

  return fetchAPI<ActivityResponse>(`/api/activity?${params.toString()}`);
}
