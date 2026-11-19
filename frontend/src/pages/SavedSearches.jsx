import { useState } from 'react';
import { ArrowRight, Bookmark, Clock3, Trash2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { readSavedSearches, writeSavedSearches } from '../utils/savedSearches.js';
import { translate } from '../utils/translations.js';
import { useAppData } from '../context/AppContext.jsx';
import { formatNumber } from '../utils/currency.js';
import EmptyState from '../components/common/EmptyState.jsx';

function buildQuery(filters = {}) {
  const params = new URLSearchParams();
  Object.entries({ search: filters.search, brand: filters.brand, model: filters.model, city: filters.city, fuel: filters.fuel, year: filters.year, max_price: filters.maxPrice, max_km: filters.maxKm }).forEach(([key, value]) => { if (value) params.set(key, value); });
  return params.toString();
}

export default function SavedSearches() {
  const { language } = useAppData();
  const t = (key) => translate(language, key);
  const navigate = useNavigate();
  const [items, setItems] = useState(() => readSavedSearches());

  function removeItem(id) {
    const next = items.filter((item) => item.id !== id);
    setItems(next);
    writeSavedSearches(next);
  }

  return (
    <div className="saved-page page-enter">
      <div className="page-heading-row"><div><div className="eyebrow">{t('onThisDevice').toUpperCase()}</div><h1>{t('savedTitle')}</h1><p>{t('savedSub')}</p></div><span className="local-storage-chip"><Bookmark size={15} /> {t('savedLocally')}</span></div>
      {items.length ? <div className="saved-search-list">{items.map((item) => <article className="saved-search-card" key={item.id}><span className="saved-search-icon"><Bookmark size={18} /></span><div className="saved-search-main"><h2>{item.label}</h2><div className="saved-search-meta"><span><Clock3 size={13} />{new Date(item.createdAt).toLocaleDateString(language === 'ta' ? 'ta-IN' : 'en-IN')}</span><span>{formatNumber(item.count || 0)} {t('results')}</span></div></div><div className="saved-search-actions"><button className="secondary-button" onClick={() => navigate(`/vehicles?${buildQuery(item.filters)}`)}>{t('openResults')} <ArrowRight size={16} /></button><button className="icon-button danger-action" onClick={() => removeItem(item.id)} aria-label={`${t('delete')} ${item.label}`}><Trash2 size={17} /></button></div></article>)}</div> : <EmptyState title={t('noSaved')} description={t('noSavedHint')} action={<button className="primary-button" onClick={() => navigate('/vehicles')}>{t('listings')} <ArrowRight size={16} /></button>} />}
    </div>
  );
}
