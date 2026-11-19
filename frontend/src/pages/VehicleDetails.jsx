import { ArrowLeft, ArrowLeftRight, ExternalLink, Fuel, Gauge, MapPin, CalendarDays, UserRound } from 'lucide-react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { useAppData } from '../context/AppContext.jsx';
import { formatCurrency } from '../utils/currency.js';
import { formatKilometres } from '../utils/distance.js';
import { translate } from '../utils/translations.js';
import { getVehicleImage, localVehicleFallback } from '../utils/vehicleImages.js';
import EmptyState from '../components/common/EmptyState.jsx';

export default function VehicleDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { vehicles, dataState, language } = useAppData();
  const t = (key) => translate(language, key);
  const vehicle = vehicles.find((item) => String(item.id) === decodeURIComponent(id || ''));
  if (!vehicle && dataState.loading) return <div className="loading-row"><span className="spinner" />{t('loadingVehicle')}</div>;
  if (!vehicle) return <div className="page-enter"><EmptyState title={t('noDetails')} action={<Link className="primary-button" to="/vehicles">{t('backToListings')}</Link>} /></div>;
  const originalUrlAvailable = vehicle.url && !/example\.com/i.test(vehicle.url) && vehicle.source !== 'Frontend demo';
  const demo = vehicle.source === 'Frontend demo' || dataState.mode === 'project-sample';
  const photo = getVehicleImage(vehicle);
  const photoAlt = photo.representative
    ? `${vehicle.brand} ${vehicle.model} representative photo`
    : vehicle.image_alt || vehicle.imageAlt || `${vehicle.brand} ${vehicle.model} listing photo`;

  return (
    <div className="vehicle-detail-page page-enter">
      <button className="back-link" onClick={() => navigate(-1)}><ArrowLeft size={16} />{t('backToListings')}</button>
      <div className="detail-layout">
        <section className="detail-visual"><img className="detail-photo" src={photo.url} alt={photoAlt} onError={(event) => { event.currentTarget.onerror = null; event.currentTarget.src = localVehicleFallback; }} />{(demo || photo.representative) && <span className={`vehicle-image-tag detail-demo-tag ${photo.representative ? 'vehicle-image-tag-photo' : ''}`}>{photo.representative ? t('representativePhoto') : t('sampleLabel')}</span>}</section>
        <section className="detail-information"><div className="eyebrow">{t('detailTitle').toUpperCase()}</div><h1>{vehicle.brand} {vehicle.model}</h1><div className="detail-price">{formatCurrency(vehicle.price)}</div><p className="detail-price-caption">{t('askingPrice')}</p>
          <div className="detail-facts-grid"><div><CalendarDays size={17} /><span>{t('yearLabel')}</span><strong>{vehicle.year || '—'}</strong></div><div><Fuel size={17} /><span>{t('fuel')}</span><strong>{vehicle.fuel_type || '—'}</strong></div><div><Gauge size={17} /><span>{t('kmsDriven')}</span><strong>{formatKilometres(vehicle.km_driven)}</strong></div><div><MapPin size={17} /><span>{t('location')}</span><strong>{vehicle.location || '—'}</strong></div><div><UserRound size={17} /><span>{t('owner')}</span><strong>{vehicle.seller_type || t('notProvided')}</strong></div><div><ArrowLeftRight size={17} /><span>{t('transmission')}</span><strong>{vehicle.transmission || vehicle.transmission_type || t('notProvided')}</strong></div><div><ExternalLink size={17} /><span>{t('source')}</span><strong>{vehicle.source || '—'}</strong></div></div>
          <div className="detail-actions"><button className="primary-button" onClick={() => navigate(`/compare?vehicle=${encodeURIComponent(vehicle.id)}`)}><ArrowLeftRight size={17} />{t('compareThis')}</button>{originalUrlAvailable && <a className="secondary-button" href={vehicle.url} target="_blank" rel="noreferrer">{t('sourceLink')} <ExternalLink size={15} /></a>}</div>
          <p className="detail-data-note">{t('dataNote')}{demo ? ' · Sample data, not a live scraped listing.' : ''}</p>
        </section>
      </div>
    </div>
  );
}
