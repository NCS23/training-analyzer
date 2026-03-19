import {
  Cloud,
  CloudRain,
  CloudSnow,
  Droplets,
  Haze,
  MapPin,
  ShieldCheck,
  Sun,
  SunDim,
  Thermometer,
  Wind,
  Zap,
} from 'lucide-react';
import { Card, CardHeader, CardBody } from '@nordlig/components';
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

          {/* Alle Metriken in einheitlichem Grid */}
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
          </div>
        </div>
      </CardBody>
    </Card>
  );
}
