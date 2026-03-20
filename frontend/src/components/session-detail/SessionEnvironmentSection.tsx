import {
  Cloud,
  CloudRain,
  CloudSnow,
  Droplets,
  Haze,
  MapPin,
  Moon,
  ShieldCheck,
  Sun,
  SunDim,
  Sunrise,
  Sunset,
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
  surface: Record<string, number> | null;
  daytimeTag: string | null;
  daytimeLabel: string | null;
  sunrise: string | null;
  sunset: string | null;
}

function weatherIcon(code: number) {
  if (code === 0 || code === 1) return <Sun className="w-4 h-4" />;
  if (code >= 95) return <Zap className="w-4 h-4" />;
  if (code >= 71 && code <= 86) return <CloudSnow className="w-4 h-4" />;
  if (code >= 51 && code <= 67) return <CloudRain className="w-4 h-4" />;
  if (code >= 80 && code <= 82) return <CloudRain className="w-4 h-4" />;
  return <Cloud className="w-4 h-4" />;
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

function daytimeIcon(tag: string) {
  switch (tag) {
    case 'dawn':
      return <Sunrise className="w-4 h-4" />;
    case 'dusk':
      return <Sunset className="w-4 h-4" />;
    case 'night':
      return <Moon className="w-4 h-4" />;
    default:
      return <Sun className="w-4 h-4" />;
  }
}

function formatTime(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' });
  } catch {
    return iso;
  }
}

const SURFACE_COLORS = [
  'var(--color-secondary-1-400)',
  'var(--color-primary-1-400)',
  'var(--color-primary-2-400)',
  'var(--color-secondary-2-400)',
  'var(--color-secondary-1-600)',
];

function SurfaceBar({ surface }: { surface: Record<string, number> }) {
  const entries = Object.entries(surface);
  return (
    <div>
      <div className="text-xs text-[var(--color-text-muted)] mb-1.5">Untergrund</div>
      <div className="flex gap-0.5 h-2.5 rounded-[var(--radius-sm)] overflow-hidden">
        {entries.map(([label, pct], i) => (
          <div
            key={label}
            style={{ width: `${pct}%`, backgroundColor: SURFACE_COLORS[i % SURFACE_COLORS.length] }}
            title={`${label} ${pct}%`}
          />
        ))}
      </div>
      <div className="flex flex-wrap gap-x-3 gap-y-0.5 mt-1.5">
        {entries.map(([label, pct], i) => (
          <span
            key={label}
            className="flex items-center gap-1 text-[10px] text-[var(--color-text-muted)]"
          >
            <span
              className="inline-block w-2 h-2 rounded-full"
              style={{ backgroundColor: SURFACE_COLORS[i % SURFACE_COLORS.length] }}
            />
            {label} {pct.toFixed(0)}%
          </span>
        ))}
      </div>
    </div>
  );
}

function EnvironmentMetricsGrid({
  weather,
  airQuality,
  sunrise,
  sunset,
}: {
  weather: WeatherData | null;
  airQuality: AirQualityData | null;
  sunrise: string | null;
  sunset: string | null;
}) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
      {weather && (
        <>
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
        </>
      )}
      {airQuality && (
        <>
          <MetricItem
            icon={<ShieldCheck className="w-4 h-4" />}
            label="Luftqualität"
            value={`AQI ${airQuality.european_aqi} — ${airQuality.aqi_label}`}
          />
          <MetricItem
            icon={<SunDim className="w-4 h-4" />}
            label="UV-Index"
            value={`${airQuality.uv_index.toFixed(1)} — ${airQuality.uv_label}`}
          />
          <MetricItem
            icon={<Haze className="w-4 h-4" />}
            label="PM2.5"
            value={`${airQuality.pm2_5.toFixed(1)} µg/m³`}
          />
          <MetricItem
            icon={<Haze className="w-4 h-4" />}
            label="PM10"
            value={`${airQuality.pm10.toFixed(1)} µg/m³`}
          />
        </>
      )}
      {sunrise && (
        <MetricItem
          icon={<Sunrise className="w-4 h-4" />}
          label="Sonnenaufgang"
          value={formatTime(sunrise)}
        />
      )}
      {sunset && (
        <MetricItem
          icon={<Sunset className="w-4 h-4" />}
          label="Sonnenuntergang"
          value={formatTime(sunset)}
        />
      )}
    </div>
  );
}

export function SessionEnvironmentSection({
  weather,
  airQuality,
  locationName,
  surface,
  daytimeTag,
  daytimeLabel,
  sunrise,
  sunset,
}: SessionEnvironmentSectionProps) {
  if (!weather && !airQuality && !locationName && !surface && !daytimeTag) return null;

  return (
    <Card elevation="raised">
      <CardHeader>
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-[var(--color-text-base)]">
            Umgebungsbedingungen
          </h2>
          {daytimeTag && daytimeLabel && (
            <Badge variant="neutral" size="sm">
              <span className="flex items-center gap-1">
                {daytimeIcon(daytimeTag)}
                {daytimeLabel}
              </span>
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardBody>
        <div className="space-y-4">
          {locationName && (
            <div className="flex items-center gap-2 text-sm text-[var(--color-text-muted)]">
              <MapPin className="w-4 h-4 shrink-0" />
              <span>{locationName}</span>
            </div>
          )}
          <EnvironmentMetricsGrid
            weather={weather}
            airQuality={airQuality}
            sunrise={sunrise}
            sunset={sunset}
          />
          {surface && Object.keys(surface).length > 0 && <SurfaceBar surface={surface} />}
        </div>
      </CardBody>
    </Card>
  );
}
