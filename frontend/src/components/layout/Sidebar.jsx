import { ArrowLeftRight, BarChart3, Bookmark, Home, CarFront, X } from 'lucide-react';
import { NavLink } from 'react-router-dom';
import heroPhoto from '../../assets/hero-suv.jpg';
import { useAppData } from '../../context/AppContext.jsx';
import { translate } from '../../utils/translations.js';

const navItems = [
  { to: '/', key: 'home', icon: Home },
  { to: '/compare', key: 'compare', icon: ArrowLeftRight },
  { to: '/analytics', key: 'analytics', icon: BarChart3 },
  { to: '/saved-searches', key: 'saved', icon: Bookmark },
];

export default function Sidebar({ open, onClose }) {
  const { language } = useAppData();
  return (
    <>
      <button className={`sidebar-scrim ${open ? 'is-visible' : ''}`} onClick={onClose} aria-label={translate(language, 'closeMenu')} tabIndex={open ? 0 : -1} />
      <aside className={`sidebar ${open ? 'sidebar-open' : ''}`}>
        <button className="sidebar-close icon-button" onClick={onClose} aria-label={translate(language, 'closeMenu')}><X size={19} /></button>
        <NavLink to="/" className="brand-lockup" onClick={onClose} aria-label="VehicleCompare home">
          <span className="brand-symbol"><CarFront size={42} strokeWidth={1.8} /></span>
          <span className="brand-title">VehicleCompare</span>
        </NavLink>
        <nav className="side-navigation" aria-label="Primary navigation">
          {navItems.map(({ to, key, icon: Icon }) => (
            <NavLink key={to} to={to} end={to === '/'} onClick={onClose} className={({ isActive }) => `side-link ${isActive ? 'active' : ''}`}>
              <Icon size={19} strokeWidth={2.1} />
              <span>{translate(language, key)}</span>
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-promo">
          <div className="promo-copy">{translate(language, 'driveSmart').split('\n').map((line) => <span key={line}>{line}</span>)}</div>
          <div className="promo-glow" />
          <img className="promo-photo" src={heroPhoto} alt="" />
        </div>
        <div className="sidebar-footnote">{translate(language, 'tnIndia')}</div>
      </aside>
    </>
  );
}
