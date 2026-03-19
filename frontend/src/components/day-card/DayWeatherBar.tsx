import { Cloud, CloudRain, CloudSnow, Sun, Zap, Wind, AlertTriangle } from 'lucide-react';
import { Tooltip } from '@nordlig/components';
import type { DayWeatherForecast } from '@/api/weekly-plan';

function weatherIcon(code: number) {
  const cls = 'w-3 h-3';
  if (code === 0 || code === 1) return <Sun className={cls} />;
  if (code >= 95) return <Zap className={cls} />;
  if (code >= 71 && code <= 86) return <CloudSnow className={cls} />;
  if ((code >= 51 && code <= 67) || (code >= 80 && code <= 82))
    return <CloudRain className={cls} />;
  return <Cloud className={cls} />;
}

function hasWarning(w: DayWeatherForecast): string | null {
  const warnings: string[] = [];
  if (w.temperature_max >= 30) warnings.push(`Hitze ${w.temperature_max.toFixed(0)}°C`);
  if (w.temperature_min <= 0) warnings.push(`Frost ${w.temperature_min.toFixed(0)}°C`);
  if (w.wind_speed_max_kmh >= 40) warnings.push(`Sturm ${w.wind_speed_max_kmh.toFixed(0)} km/h`);
  if (w.aqi != null && w.aqi > 60) warnings.push(`Schlechte Luft (AQI ${w.aqi})`);
  return warnings.length > 0 ? warnings.join(', ') : null;
}

export function DayWeatherBar({ weather }: { weather: DayWeatherForecast }) {
  const warning = hasWarning(weather);
  const tooltipText = [
    weather.weather_label,
    `${weather.temperature_min.toFixed(0)}–${weather.temperature_max.toFixed(0)}°C`,
    weather.precipitation_mm > 0 ? `${weather.precipitation_mm.toFixed(1)} mm Niederschlag` : null,
    `Wind bis ${weather.wind_speed_max_kmh.toFixed(0)} km/h`,
    weather.aqi_label ? `Luft: ${weather.aqi_label}` : null,
  ]
    .filter(Boolean)
    .join(' · ');

  return (
    <Tooltip content={tooltipText} side="top">
      <div className="px-[var(--spacing-sm)] pb-1 flex items-center gap-1.5 text-[10px] text-[var(--color-text-muted)] cursor-default">
        {weatherIcon(weather.weather_code)}
        <span>
          {weather.temperature_min.toFixed(0)}–{weather.temperature_max.toFixed(0)}°C
        </span>
        {weather.precipitation_mm > 0 && (
          <span className="flex items-center gap-0.5">
            <CloudRain className="w-2.5 h-2.5" />
            {weather.precipitation_mm.toFixed(0)}mm
          </span>
        )}
        {weather.wind_speed_max_kmh >= 25 && (
          <span className="flex items-center gap-0.5">
            <Wind className="w-2.5 h-2.5" />
            {weather.wind_speed_max_kmh.toFixed(0)}
          </span>
        )}
        {warning && <AlertTriangle className="w-3 h-3 text-[var(--color-text-warning)]" />}
      </div>
    </Tooltip>
  );
}
