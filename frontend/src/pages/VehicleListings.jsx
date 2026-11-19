import { useEffect, useMemo, useState } from 'react';
import { BookmarkPlus, RotateCcw, Search, SlidersHorizontal } from 'lucide-react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAppData } from '../context/AppContext.jsx';
import { translate } from '../utils/translations.js';
import { formatCurrency } from '../utils/currency.js';
import { writeSavedSearches, readSavedSearches } from '../utils/savedSearches.js';
import VehicleCard from '../components/vehicles/VehicleCard.jsx';
import EmptyState from '../components/common/EmptyState.jsx';

const TN_CITIES = ['Chennai', 'Coimbatore', 'Salem', 'Madurai', 'Tiruchirappalli', 'Erode', 'Tirunelveli', 'Vellore', 'Thanjavur', 'Hosur', 'Kanchipuram'];
const BRAND_CATALOG = ['Maruti Suzuki', 'Hyundai', 'Tata', 'Mahindra', 'Toyota', 'Honda', 'Kia', 'Renault', 'Nissan', 'Volkswagen', 'Skoda', 'MG', 'BMW', 'Mercedes-Benz', 'Audi'];
const FUEL_CATALOG = ['Petrol', 'Diesel', 'CNG', 'Electric', 'Hybrid'];
const PAGE_SIZE = 9;

function filtersFromUrl(search) {
  const params = new URLSearchParams(search);
  return {
    search: params.get('search') || '', brand: params.get('brand') || '', model: params.get('model') || '',
    city: params.get('city') || '', fuel: params.get('fuel') || '', year: params.get('year') || '',
    maxPrice: params.get('max_price') || '', maxKm: params.get('max_km') || '',
  };
}

export default function VehicleListings() {
  const { vehicles, dataState, language } = useAppData();
  const t = (key) => translate(language, key);
  const location = useLocation();
  const navigate = useNavigate();
  const [filters, setFilters] = useState(() => filtersFromUrl(location.search));
  const [sort, setSort] = useState('price-asc');
  const [page, setPage] = useState(1);
  const [savedMessage, setSavedMessage] = useState('');

  useEffect(() => {
    setFilters(filtersFromUrl(location.search));
    setPage(1);
  }, [location.search]);

  const brands = useMemo(() => [...new Set([...BRAND_CATALOG, ...vehicles.map((vehicle) => vehicle.brand).filter(Boolean)])], [vehicles]);
  const models = useMemo(() => [...new Set(vehicles.filter((vehicle) => !filters.brand || vehicle.brand === filters.brand).map((vehicle) => vehicle.model).filter(Boolean))].sort(), [vehicles, filters.brand]);
  const fuelTypes = useMemo(() => [...new Set([...FUEL_CATALOG, ...vehicles.map((vehicle) => vehicle.fuel_type).filter(Boolean)])], [vehicles]);
  const years = useMemo(() => [...new Set(vehicles.map((vehicle) => vehicle.year).filter(Boolean))].sort((a, b) => b - a), [vehicles]);
  const locations = useMemo(() => {
    const present = new Set(vehicles.map((vehicle) => vehicle.location).filter(Boolean));
    return [...TN_CITIES, ...[...present].filter((city) => !TN_CITIES.includes(city)).sort()];
  }, [vehicles]);

  const filteredVehicles = useMemo(() => {
    const query = filters.search.trim().toLowerCase();
    const filtered = vehicles.filter((vehicle) => {
      const searchable = [vehicle.brand, vehicle.model, vehicle.location, vehicle.fuel_type].join(' ').toLowerCase();
      return (!query || searchable.includes(query))
        && (!filters.brand || vehicle.brand === filters.brand)
        && (!filters.model || vehicle.model === filters.model)
        && (!filters.city || vehicle.location === filters.city)
        && (!filters.fuel || vehicle.fuel_type.toLowerCase() === filters.fuel.toLowerCase())
        && (!filters.year || String(vehicle.year) === filters.year)
        && (!filters.maxPrice || vehicle.price <= Number(filters.maxPrice))
        && (!filters.maxKm || vehicle.km_driven == null || vehicle.km_driven <= Number(filters.maxKm));
    });
    return filtered.sort((a, b) => {
      if (sort === 'price-desc') return b.price - a.price;
      if (sort === 'year-desc') return (b.year || 0) - (a.year || 0);
      if (sort === 'km-asc') return (a.km_driven ?? Infinity) - (b.km_driven ?? Infinity);
      return a.price - b.price;
    });
  }, [vehicles, filters, sort]);

  const pageCount = Math.max(1, Math.ceil(filteredVehicles.length / PAGE_SIZE));
  const pageVehicles = filteredVehicles.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  function setFilter(key, value) {
    setFilters((current) => ({ ...current, [key]: value }));
    setPage(1);
  }

  function clearFilters() {
    setFilters({ search: '', brand: '', model: '', city: '', fuel: '', year: '', maxPrice: '', maxKm: '' });
    setPage(1);
    navigate('/vehicles', { replace: true });
  }

  function saveSearch() {
    const label = [filters.brand, filters.model, filters.city, filters.fuel].filter(Boolean).join(' · ') || filters.search || 'All available vehicles';
    const current = readSavedSearches();
    const saved = { id: `search-${Date.now()}`, label, filters, count: filteredVehicles.length, createdAt: new Date().toISOString() };
    writeSavedSearches([saved, ...current]);
    setSavedMessage(t('savedMessage'));
    window.setTimeout(() => setSavedMessage(''), 2800);
  }

  const queryTitle = filters.brand || filters.search;
  return (
    <div className="listings-page page-enter">
      <div className="page-heading-row">
        <div><div className="eyebrow">{t('tnIndia').toUpperCase()}</div><h1>{queryTitle ? `${t('listingsFor')} ${queryTitle}` : t('listings')}</h1><p>{t('listingsSub')}</p></div>
        <button className="secondary-button" onClick={saveSearch}><BookmarkPlus size={17} />{t('saveSearch')}</button>
      </div>
      {savedMessage && <div className="toast-message" role="status">{savedMessage}</div>}

      <section className="filter-panel">
        <div className="filter-panel-title"><SlidersHorizontal size={17} /><strong>{t('filters')}</strong><span className="filter-count">{filteredVehicles.length} {t('results')}</span></div>
        <div className="filter-grid">
          <label className="filter-control filter-search-control"><span>{t('searchVehicles')}</span><div className="input-with-icon"><Search size={16} /><input value={filters.search} onChange={(event) => setFilter('search', event.target.value)} placeholder={t('searchPlaceholder')} /></div></label>
          <label className="filter-control"><span>{t('brand')}</span><select value={filters.brand} onChange={(event) => { setFilter('brand', event.target.value); setFilters((current) => ({ ...current, model: '' })); }}><option value="">{t('allBrands')}</option>{brands.map((brand) => <option key={brand}>{brand}</option>)}</select></label>
          <label className="filter-control"><span>{t('model')}</span><select value={filters.model} onChange={(event) => setFilter('model', event.target.value)}><option value="">{t('allModels')}</option>{models.map((model) => <option key={model}>{model}</option>)}</select></label>
          <label className="filter-control"><span>{t('city')}</span><select value={filters.city} onChange={(event) => setFilter('city', event.target.value)}><option value="">{t('allCities')}</option>{locations.map((city) => <option key={city}>{city}</option>)}</select></label>
          <label className="filter-control"><span>{t('fuel')}</span><select value={filters.fuel} onChange={(event) => setFilter('fuel', event.target.value)}><option value="">{t('allFuels')}</option>{fuelTypes.map((fuel) => <option key={fuel}>{fuel}</option>)}</select></label>
          <label className="filter-control"><span>{t('year')}</span><select value={filters.year} onChange={(event) => setFilter('year', event.target.value)}><option value="">{t('anyYear')}</option>{years.map((year) => <option key={year}>{year}</option>)}</select></label>
          <label className="filter-control"><span>{t('maxPrice')}</span><select value={filters.maxPrice} onChange={(event) => setFilter('maxPrice', event.target.value)}><option value="">{t('anyPrice')}</option>{[500000, 800000, 1200000, 2000000, 3000000].map((price) => <option key={price} value={price}>{formatCurrency(price)}</option>)}</select></label>
          <label className="filter-control"><span>{t('maxKm')}</span><select value={filters.maxKm} onChange={(event) => setFilter('maxKm', event.target.value)}><option value="">{t('anyDistance')}</option>{[25000, 50000, 75000, 100000, 150000].map((km) => <option key={km} value={km}>{new Intl.NumberFormat('en-IN').format(km)} km</option>)}</select></label>
        </div>
        <div className="filter-panel-footer"><button className="quiet-button" onClick={clearFilters}><RotateCcw size={14} />{t('clearFilters')}</button><span className="price-note">{t('dataNote')}</span></div>
      </section>

      <div className="results-toolbar"><span><strong>{filteredVehicles.length}</strong> {t('results')}{dataState.loading && <span className="inline-loading"><i />Updating</span>}</span><label className="sort-select"><span>{t('sortBy')}</span><select value={sort} onChange={(event) => { setSort(event.target.value); setPage(1); }}><option value="price-asc">{t('priceLow')}</option><option value="price-desc">{t('priceHigh')}</option><option value="year-desc">{t('newest')}</option><option value="km-asc">{t('lowestKm')}</option></select></label></div>

      {pageVehicles.length ? <div className="vehicle-card-grid">{pageVehicles.map((vehicle) => <VehicleCard key={vehicle.id} vehicle={vehicle} onCompare={(item) => navigate(`/compare?vehicle=${encodeURIComponent(item.id)}`)} />)}</div> : <EmptyState title={t('noMatch')} description={dataState.mode === 'empty' ? t('emptyDataHint') : t('noMatchHint')} />}

      {filteredVehicles.length > PAGE_SIZE && <div className="pagination"><button className="secondary-button" disabled={page <= 1} onClick={() => setPage((current) => current - 1)}>{t('previous')}</button><span>{t('page')} <strong>{page}</strong> {t('of')} {pageCount}</span><button className="secondary-button" disabled={page >= pageCount} onClick={() => setPage((current) => current + 1)}>{t('next')}</button></div>}
    </div>
  );
}
