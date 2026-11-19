import axios from 'axios';

const baseURL = import.meta.env.VITE_API_BASE_URL || '/api';

export const api = axios.create({
  baseURL,
  timeout: 10000,
  headers: { Accept: 'application/json' },
});

export async function fetchVehicles(params = {}) {
  const response = await api.get('/vehicles', { params: { limit: 500, sort: 'price', ...params } });
  return Array.isArray(response.data) ? response.data : [];
}

export async function fetchMarketStats() {
  const response = await api.get('/stats');
  return Array.isArray(response.data) ? response.data : [];
}

export async function fetchSourceComparison(model, year) {
  const response = await api.get('/compare', { params: { model, year } });
  return Array.isArray(response.data) ? response.data : [];
}

export function looksLikeProjectSample(rows) {
  return rows.some((row) => /^site-[a-z0-9]+$/i.test(row.source || '') || /example\.com/i.test(row.url || ''));
}

export function normalizeVehicle(row, index = 0) {
  return {
    ...row,
    id: row.id ?? `${row.brand || 'vehicle'}-${row.model || 'listing'}-${row.year || 'year'}-${row.km_driven ?? index}-${index}`,
    brand: row.brand || 'Other',
    model: row.model || 'Model not listed',
    year: Number(row.year) || null,
    fuel_type: row.fuel_type || '',
    km_driven: Number.isFinite(Number(row.km_driven)) ? Number(row.km_driven) : null,
    price: Number(row.price) || 0,
    location: row.location || '',
    source: row.source || '',
    seller_type: row.seller_type || '',
    url: row.url || '',
    image_url: row.image_url || row.imageUrl || row.photo_url || row.thumbnail_url || '',
    image_alt: row.image_alt || row.imageAlt || '',
  };
}
