const STORAGE_KEY = 'vehiclecompare-saved-searches';

export function readSavedSearches() {
  try {
    const value = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
    return Array.isArray(value) ? value : [];
  } catch {
    return [];
  }
}

export function writeSavedSearches(items) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
}
