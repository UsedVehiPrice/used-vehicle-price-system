const INR = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 0,
});

const INDIAN_NUMBER = new Intl.NumberFormat('en-IN', { maximumFractionDigits: 0 });

export function formatCurrency(value) {
  const amount = Number(value);
  return Number.isFinite(amount) ? INR.format(amount) : '—';
}

export function formatCurrencyCompact(value) {
  const amount = Number(value);
  if (!Number.isFinite(amount)) return '—';
  if (amount >= 10_000_000) return `₹${(amount / 10_000_000).toLocaleString('en-IN', { maximumFractionDigits: 1 })} Cr`;
  if (amount >= 100_000) return `₹${(amount / 100_000).toLocaleString('en-IN', { maximumFractionDigits: 1 })} L`;
  return INR.format(amount);
}

export function formatNumber(value) {
  const amount = Number(value);
  return Number.isFinite(amount) ? INDIAN_NUMBER.format(amount) : '—';
}
