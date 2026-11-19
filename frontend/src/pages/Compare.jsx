import { useEffect, useMemo, useState } from 'react';
import { ArrowLeftRight, Check, Plus, X } from 'lucide-react';
import { useLocation, useNavigate } from 'react-router-dom';
import { fetchSourceComparison } from '../services/api.js';
import { useAppData } from '../context/AppContext.jsx';
import { formatCurrency } from '../utils/currency.js';
import { formatKilometres } from '../utils/distance.js';
import { translate } from '../utils/translations.js';
import EmptyState from '../components/common/EmptyState.jsx';

const comparisonRows = [
  ['yearLabel', (vehicle) => vehicle.year || '—'],
  ['fuel', (vehicle) => vehicle.fuel_type || '—'],
  ['kmsDriven', (vehicle) => formatKilometres(vehicle.km_driven)],
  ['transmission', (vehicle) => vehicle.transmission || vehicle.transmission_type || 'Not provided'],
  ['location', (vehicle) => vehicle.location || '—'],
  ['source', (vehicle) => vehicle.source || '—'],
  ['owner', (vehicle) => vehicle.seller_type || '—'],
];

export default function Compare() {
  const { vehicles, language } = useAppData();
  const t = (key) => translate(language, key);
  const location = useLocation();
  const navigate = useNavigate();
  const params = useMemo(() => new URLSearchParams(location.search), [location.search]);
  const [selectedIds, setSelectedIds] = useState(() => params.get('vehicle') ? [params.get('vehicle')] : []);
  const [candidate, setCandidate] = useState('');
  const [sourceRows, setSourceRows] = useState([]);
  const [sourceLoading, setSourceLoading] = useState(false);
  const selected = selectedIds.map((id) => vehicles.find((vehicle) => String(vehicle.id) === String(id))).filter(Boolean);
  const lowest = Math.min(...selected.map((vehicle) => vehicle.price));
  const available = vehicles.filter((vehicle) => !selectedIds.includes(String(vehicle.id)));
  const selectedKey = selected[0] ? `${selected[0].model}:${selected[0].year}` : '';

  useEffect(() => {
    const id = params.get('vehicle');
    if (id && vehicles.some((vehicle) => String(vehicle.id) === id)) setSelectedIds((current) => current.includes(id) ? current : [id, ...current].slice(0, 4));
  }, [params, vehicles]);

  useEffect(() => {
    let active = true;
    if (!selected[0]) { setSourceRows([]); return undefined; }
    setSourceLoading(true);
    fetchSourceComparison(selected[0].model, selected[0].year).then((rows) => {
      if (active) setSourceRows(rows);
    }).catch(() => {
      if (active) setSourceRows([]);
    }).finally(() => {
      if (active) setSourceLoading(false);
    });
    return () => { active = false; };
  }, [selectedKey]);

  function addVehicle() {
    if (!candidate || selectedIds.length >= 4) return;
    setSelectedIds((current) => [...current, candidate]);
    setCandidate('');
  }

  function removeVehicle(id) {
    setSelectedIds((current) => current.filter((selectedId) => selectedId !== id));
    const next = new URLSearchParams(location.search);
    if (next.get('vehicle') === id) next.delete('vehicle');
    navigate({ pathname: '/compare', search: next.toString() }, { replace: true });
  }

  return (
    <div className="compare-page page-enter">
      <div className="page-heading-row"><div><div className="eyebrow">{t('sideBySide').toUpperCase()}</div><h1>{t('compareTitle')}</h1><p>{t('compareSub')}</p></div></div>
      <section className="compare-picker-panel">
        <div className="compare-picker-copy"><span className="compare-picker-icon"><ArrowLeftRight size={19} /></span><div><strong>{t('chooseVehicle')}</strong><p>{selectedIds.length} {t('selected')} · {t('selectHint')}</p></div></div>
        <div className="compare-picker-actions"><select value={candidate} onChange={(event) => setCandidate(event.target.value)} aria-label={t('chooseVehicle')}><option value="">{t('chooseVehicle')}</option>{available.map((vehicle) => <option key={vehicle.id} value={vehicle.id}>{vehicle.brand} {vehicle.model} · {vehicle.year || '—'} · {formatCurrency(vehicle.price)}</option>)}</select><button className="primary-button" disabled={!candidate || selectedIds.length >= 4} onClick={addVehicle}><Plus size={17} />{t('addVehicle')}</button></div>
      </section>

      {selected.length === 0 ? <EmptyState title={t('selectHint')} description={t('emptyDataHint')} /> : (
        <>
          <div className={`comparison-grid comparison-count-${selected.length}`}>
            <div className="comparison-label-column"><div className="comparison-label-top">{t('vehicle')}</div><div className="comparison-price-label">{t('askingPrice')}</div>{comparisonRows.map(([key]) => <div key={key} className="comparison-row-label">{t(key)}</div>)}</div>
            {selected.map((vehicle) => {
              const isLowest = vehicle.price === lowest;
              const difference = vehicle.price - lowest;
              return <article className={`comparison-vehicle-column ${isLowest ? 'comparison-winner' : ''}`} key={vehicle.id}>
                <button className="comparison-remove icon-button" onClick={() => removeVehicle(String(vehicle.id))} aria-label={`${t('remove')} ${vehicle.brand} ${vehicle.model}`}><X size={17} /></button>
                <div className="comparison-vehicle-head"><span className="comparison-car-badge"><ArrowLeftRight size={18} /></span><h2>{vehicle.brand}</h2><p>{vehicle.model}</p>{isLowest && <span className="best-price-badge"><Check size={13} />{t('lowestPrice')}</span>}</div>
                <div className="comparison-price-cell"><strong>{formatCurrency(vehicle.price)}</strong><span>{t('difference')}: {difference === 0 ? '—' : formatCurrency(difference)}</span></div>
                {comparisonRows.map(([key, value]) => <div className="comparison-data-cell" key={key}>{value(vehicle)}</div>)}
              </article>;
            })}
          </div>
          {selected[0] && sourceRows.length > 0 && <section className="source-comparison-card"><div className="section-heading-row"><div><h2>{t('marketSources')}</h2><p className="section-subtitle">{selected[0].brand} {selected[0].model} · {selected[0].year || '—'}</p></div><span className="source-data-badge">{t('apiSource')}</span></div><div className="source-price-grid">{sourceRows.map((row) => <div className="source-price-item" key={row.source}><span>{row.source}</span><strong>{formatCurrency(row.avg_price)}</strong><small>{row.listings} listings · {formatCurrency(row.min_price)}–{formatCurrency(row.max_price)}</small></div>)}</div></section>}
          {sourceLoading && <div className="loading-row"><span className="spinner" /> {t('loadingSourceComparison')}</div>}
        </>
      )}
    </div>
  );
}
