import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { demoVehicles } from '../data/demoVehicles.js';
import { fetchVehicles, looksLikeProjectSample, normalizeVehicle } from '../services/api.js';

const AppContext = createContext(null);

export function AppProvider({ children }) {
  const [vehicles, setVehicles] = useState([]);
  const [dataState, setDataState] = useState({ loading: true, mode: 'loading', error: '' });
  const [language, setLanguageState] = useState(() => localStorage.getItem('vehiclecompare-language') || 'en');
  const [theme, setThemeState] = useState(() => localStorage.getItem('vehiclecompare-theme') === 'dark' ? 'dark' : 'light');

  const refreshVehicles = useCallback(async () => {
    setDataState((current) => ({ ...current, loading: true }));
    try {
      const rows = await fetchVehicles();
      const normalized = rows.map(normalizeVehicle);
      setVehicles(normalized);
      setDataState({
        loading: false,
        mode: normalized.length === 0 ? 'empty' : (looksLikeProjectSample(rows) ? 'project-sample' : 'api'),
        error: '',
      });
    } catch (error) {
      setVehicles(demoVehicles.map(normalizeVehicle));
      setDataState({ loading: false, mode: 'frontend-demo', error: error?.message || 'API request failed' });
    }
  }, []);

  useEffect(() => { refreshVehicles(); }, [refreshVehicles]);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    document.documentElement.style.colorScheme = theme;
    localStorage.setItem('vehiclecompare-theme', theme);
  }, [theme]);

  const setLanguage = (nextLanguage) => {
    setLanguageState(nextLanguage);
    localStorage.setItem('vehiclecompare-language', nextLanguage);
    document.documentElement.lang = nextLanguage === 'ta' ? 'ta' : 'en';
  };

  const toggleTheme = useCallback(() => setThemeState((current) => current === 'dark' ? 'light' : 'dark'), []);

  const value = useMemo(() => ({ vehicles, dataState, language, setLanguage, theme, toggleTheme, refreshVehicles }), [vehicles, dataState, language, theme, toggleTheme, refreshVehicles]);
  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useAppData() {
  const context = useContext(AppContext);
  if (!context) throw new Error('useAppData must be used inside AppProvider');
  return context;
}
