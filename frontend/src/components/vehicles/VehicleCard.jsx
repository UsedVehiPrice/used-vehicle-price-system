import { ArrowUpRight, Bookmark, MapPin, Gauge, Fuel, CalendarDays, ArrowLeftRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { formatCurrency } from '../../utils/currency.js';
import { formatKilometres } from '../../utils/distance.js';
import { useAppData } from '../../context/AppContext.jsx';
import { translate } from '../../utils/translations.js';
import { getVehicleImage, localVehicleFallback } from '../../utils/vehicleImages.js';

export default function VehicleCard({ vehicle, compact = false, onCompare }) {
  const navigate = useNavigate();
  const { language, dataState } = useAppData();
  const demo = vehicle.source === 'Frontend demo' || dataState.mode === 'project-sample';
  const photo = getVehicleImage(vehicle);
  const photoAlt = photo.representative
    ? `${vehicle.brand} ${vehicle.model} representative vehicle photo`
    : vehicle.image_alt || vehicle.imageAlt || `${vehicle.brand} ${vehicle.model} listing photo`;
  return (
    <article className={`vehicle-card ${compact ? 'vehicle-card-compact' : ''}`}>
      <button className="vehicle-image" onClick={() => navigate(`/vehicles/${encodeURIComponent(vehicle.id)}`)} aria-label={`${vehicle.brand} ${vehicle.model} ${translate(language, 'detailTitle')}`}>
        <img className="vehicle-photo" src={photo.url} alt={photoAlt} loading="lazy" onError={(event) => { event.currentTarget.onerror = null; event.currentTarget.src = localVehicleFallback; }} />
        {(demo || photo.representative) && <span className={`vehicle-image-tag ${photo.representative ? 'vehicle-image-tag-photo' : ''}`}>{photo.representative ? translate(language, 'representativePhoto') : translate(language, 'sampleLabel')}</span>}
        <span className="vehicle-image-arrow"><ArrowUpRight size={16} /></span>
      </button>
      <div className="vehicle-card-body">
        <div className="vehicle-card-topline">
          <div>
            <div className="vehicle-title">{vehicle.brand} {vehicle.model}</div>
            <div className="vehicle-location"><MapPin size={13} />{vehicle.location || translate(language, 'notProvided')}</div>
          </div>
          <div className="vehicle-price">{formatCurrency(vehicle.price)}</div>
        </div>
        <div className="vehicle-quick-facts">
          <span><CalendarDays size={14} />{vehicle.year || '—'}</span>
          <span><Gauge size={14} />{formatKilometres(vehicle.km_driven)}</span>
          <span><Fuel size={14} />{vehicle.fuel_type || '—'}</span>
        </div>
        <div className="vehicle-card-footer">
          <span className="listing-source">{vehicle.source || translate(language, 'notProvided')}</span>
          <button className="text-action" onClick={() => onCompare?.(vehicle)}><ArrowLeftRight size={15} />{translate(language, 'compare')}</button>
        </div>
      </div>
    </article>
  );
}
