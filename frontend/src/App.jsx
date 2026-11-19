import { lazy, Suspense } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import { AppProvider } from './context/AppContext.jsx';
import AppShell from './components/layout/AppShell.jsx';

const Home = lazy(() => import('./pages/Home.jsx'));
const Compare = lazy(() => import('./pages/Compare.jsx'));
const Analytics = lazy(() => import('./pages/Analytics.jsx'));
const SavedSearches = lazy(() => import('./pages/SavedSearches.jsx'));
const VehicleListings = lazy(() => import('./pages/VehicleListings.jsx'));
const VehicleDetails = lazy(() => import('./pages/VehicleDetails.jsx'));

export default function App() {
  return (
    <AppProvider>
      <Suspense fallback={<div className="route-loading"><span className="spinner" />Loading page…</div>}>
        <Routes>
          <Route element={<AppShell />}>
            <Route index element={<Home />} />
            <Route path="compare" element={<Compare />} />
            <Route path="analytics" element={<Analytics />} />
            <Route path="saved-searches" element={<SavedSearches />} />
            <Route path="vehicles" element={<VehicleListings />} />
            <Route path="vehicles/:id" element={<VehicleDetails />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </Suspense>
    </AppProvider>
  );
}
