/**
 * Map tile style configuration.
 * Separated from RouteMap to keep react-refresh happy
 * (files exporting components should only export components).
 */

export type MapTileStyle = 'streets' | 'satellite' | 'terrain' | 'outdoor' | 'dark';

export const MAP_TILE_LABELS: Record<MapTileStyle, string> = {
  streets: 'Standard',
  satellite: 'Satellit',
  terrain: 'Terrain',
  outdoor: 'Outdoor',
  dark: 'Dunkel',
};

export const TILES: Record<MapTileStyle, { url: string; attribution: string; maxZoom?: number }> = {
  streets: {
    url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
  },
  satellite: {
    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attribution: '&copy; <a href="https://www.esri.com/">Esri</a>',
    maxZoom: 18,
  },
  terrain: {
    url: 'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://opentopomap.org/">OpenTopoMap</a>',
    maxZoom: 17,
  },
  outdoor: {
    url: 'https://{s}.tile-cyclosm.openstreetmap.fr/cyclosm/{z}/{x}/{y}.png',
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://www.cyclosm.org/">CyclOSM</a>',
    maxZoom: 20,
  },
  dark: {
    url: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/">CARTO</a>',
  },
};
