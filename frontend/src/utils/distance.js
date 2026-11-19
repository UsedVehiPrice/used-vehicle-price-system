import { formatNumber } from './currency.js';

export function formatKilometres(value) {
  const amount = Number(value);
  return Number.isFinite(amount) ? `${formatNumber(amount)} km` : '—';
}
