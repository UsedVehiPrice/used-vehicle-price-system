import { ArrowRight } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import heroPhoto from '../assets/hero-suv.jpg';
import { useAppData } from '../context/AppContext.jsx';
import { translate } from '../utils/translations.js';
import BrandLogo from '../components/common/BrandLogo.jsx';
import VehicleCard from '../components/vehicles/VehicleCard.jsx';
import EmptyState from '../components/common/EmptyState.jsx';

const featuredBrands = ['Toyota', 'Honda', 'Hyundai', 'Maruti Suzuki', 'Tata', 'Mahindra'];

export default function Home() {
  const { vehicles, dataState, language } = useAppData();
  const navigate = useNavigate();
  const t = (key) => translate(language, key);
  const latest = [...vehicles].sort((a, b) => (b.year || 0) - (a.year || 0)).slice(0, 3);

  return (
    <div className="home-page page-enter">
      <section className="hero-banner">
        <img className="hero-photo" src={heroPhoto} alt="White SUV on a road" />
        <div className="hero-photo-wash" />
        <div className="hero-content">
          <h1>{t('heroTitle').split('\n').map((line) => <span key={line}>{line}</span>)}</h1>
          <p>{t('heroSubtitle').split('\n').map((line) => <span key={line}>{line}</span>)}</p>
          <Link className="primary-button hero-cta" to="/compare">{t('startComparing')} <ArrowRight size={18} /></Link>
        </div>
      </section>

      <section className="brand-section" aria-labelledby="popular-brands-heading">
        <div className="section-heading-row">
          <div>
            <h2 id="popular-brands-heading">{t('popularBrands')}</h2>
          </div>
          <Link to="/vehicles" className="view-all-link">{t('viewAll')} <ArrowRight size={17} /></Link>
        </div>
        <div className="brand-grid">
          {featuredBrands.map((brand) => (
            <button className="brand-card" key={brand} onClick={() => navigate(`/vehicles?brand=${encodeURIComponent(brand)}`)}>
              <BrandLogo name={brand} />
              <span className="brand-card-name">{brand}</span>
            </button>
          ))}
        </div>
      </section>

      <section className="recent-section">
        <div className="section-heading-row">
          <div><h2>{t('recentlyListed')}</h2><p className="section-subtitle">{t('recentSubtitle')}</p></div>
          <Link to="/vehicles" className="view-all-link">{t('browseVehicles')} <ArrowRight size={17} /></Link>
        </div>
        {dataState.loading ? <div className="loading-row"><span className="spinner" /> Loading available listings…</div> : latest.length ? (
          <div className="vehicle-card-grid home-vehicle-grid">{latest.map((vehicle) => <VehicleCard key={vehicle.id} vehicle={vehicle} compact onCompare={(item) => navigate(`/compare?vehicle=${encodeURIComponent(item.id)}`)} />)}</div>
        ) : <EmptyState title={t('emptyData')} description={t('emptyDataHint')} />}
      </section>
    </div>
  );
}
