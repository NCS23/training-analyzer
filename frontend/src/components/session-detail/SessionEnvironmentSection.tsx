import {
  Cloud,
  CloudRain,
  CloudSnow,
  Droplets,
  MapPin,
  Sun,
  Thermometer,
  Wind,
  Zap,
} from 'lucide-react';
import { Card, CardHeader, CardBody, Badge } from '@nordlig/components';
import type { WeatherData, AirQualityData } from '@/api/training';

interface SessionEnvironmentSectionProps {
  weather: WeatherData | null;
  airQuality: AirQualityData | null;
  locationName: string | null;
}

function weatherIcon(code: number) {
  if (code === 0 || code === 1) return <Sun className="w-4 h-4" />;
  if (code >= 95) return <Zap className="w-4 h-4" />;
  if (code >= 71 && code <= 86) return <CloudSnow className="w-4 h-4" />;
  if (code >= 51 && code <= 67) return <CloudRain className="w-4 h-4" />;
  if (code >= 80 && code <= 82) return <CloudRain className="w-4 h-4" />;
  return <Cloud className="w-4 h-4" />;
}

function aqiBadgeVariant(aqi: number): 'success' | 'warning' | 'error' | 'neutral' {
  if (aqi <= 40) return 'success';
  if (aqi <= 60) return 'warning';
  return 'error';
}

function uvBadgeVariant(uv: number): 'success' | 'warning' | 'error' | 'neutral' {
  if (uv <= 2) return 'success';
  if (uv <= 5) return 'neutral';
  if (uv <= 7) return 'warning';
  return 'error';
}

function MetricItem({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-[var(--color-text-muted)]">{icon}</span>
      <div>
        <div className="text-xs text-[var(--color-text-muted)]">{label}</div>
        <div className="text-sm font-medium text-[var(--color-text-base)]">{value}</div>
      </div>
    </div>
  );
}

export function SessionEnvironmentSection({
  weather,
  airQuality,
  locationName,
}: SessionEnvironmentSectionProps) {
  if (!weather && !airQuality && !locationName) return null;

  return (
    <Card elevation="raised">
      <CardHeader>
        <h2 className="text-sm font-semibold text-[var(--color-text-base)]">
          Umgebungsbedingungen
        </h2>
      </CardHeader>
      <CardBody>
        <div className="space-y-4">
          {/* Location */}
          {locationName && (
            <div className="flex items-center gap-2 text-sm text-[var(--color-text-muted)]">
              <MapPin className="w-4 h-4 shrink-0" />
              <span>{locationName}</span>
            </div>
          )}

          {/* Wetter */}
          {weather && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <MetricItem
                icon={weatherIcon(weather.weather_code)}
                label="Wetter"
                value={weather.weather_label}
              />
              <MetricItem
                icon={<Thermometer className="w-4 h-4" />}
                label="Temperatur"
                value={`${weather.temperature_c.toFixed(1)} °C`}
              />
              <MetricItem
                icon={<Wind className="w-4 h-4" />}
                label="Wind"
                value={`${weather.wind_speed_kmh.toFixed(0)} km/h`}
              />
              <MetricItem
                icon={<Droplets className="w-4 h-4" />}
                label="Luftfeuchtigkeit"
                value={`${weather.humidity_pct.toFixed(0)} %`}
              />
            </div>
          )}

          {/* Luftqualität + UV */}
          {airQuality && (
            <div className="flex flex-wrap gap-3">
              <div className="flex items-center gap-2">
                <span className="text-xs text-[var(--color-text-muted)]">Luftqualität</span>
                <Badge variant={aqiBadgeVariant(airQuality.european_aqi)}>
                  AQI {airQuality.european_aqi} — {airQuality.aqi_label}
                </Badge>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-[var(--color-text-muted)]">UV-Index</span>
                <Badge variant={uvBadgeVariant(airQuality.uv_index)}>
                  UV {airQuality.uv_index.toFixed(1)} — {airQuality.uv_label}
                </Badge>
              </div>
            </div>
          )}
        </div>
      </CardBody>
    </Card>
  );
}
