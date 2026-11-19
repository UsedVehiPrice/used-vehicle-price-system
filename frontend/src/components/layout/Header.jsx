import { useEffect, useState } from 'react';
import { Menu, Search, UserRound, ChevronDown, Check, Moon, Sun } from 'lucide-react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAppData } from '../../context/AppContext.jsx';
import { translate } from '../../utils/translations.js';

export default function Header({ onMenuClick }) {
  const navigate = useNavigate();
  const location = useLocation();
  const { language, setLanguage, theme, toggleTheme } = useAppData();
  const [query, setQuery] = useState('');
  const [profileOpen, setProfileOpen] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    setQuery(params.get('search') || '');
  }, [location.search]);

  function submitSearch(event) {
    event.preventDefault();
    const value = query.trim();
    navigate(value ? `/vehicles?search=${encodeURIComponent(value)}` : '/vehicles');
    setProfileOpen(false);
  }

  return (
    <header className="topbar">
      <button className="mobile-menu icon-button" onClick={onMenuClick} aria-label={translate(language, 'openMenu')}><Menu size={21} /></button>
      <form className="global-search" role="search" onSubmit={submitSearch}>
        <Search className="search-leading-icon" size={19} />
        <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder={translate(language, 'search')} aria-label={translate(language, 'searchVehicles')} />
        <button type="submit" aria-label={translate(language, 'searchButton')}><Search size={19} /></button>
      </form>
      <button className="theme-toggle" type="button" onClick={toggleTheme} aria-label={translate(language, theme === 'dark' ? 'switchToLight' : 'switchToDark')} aria-pressed={theme === 'dark'}>
        {theme === 'dark' ? <Sun size={17} /> : <Moon size={17} />}
        <span>{translate(language, theme === 'dark' ? 'lightMode' : 'darkMode')}</span>
      </button>
      <div className="profile-wrap">
        <button className={`profile-button ${profileOpen ? 'profile-active' : ''}`} onClick={() => setProfileOpen((value) => !value)} aria-label={translate(language, 'profile')} aria-expanded={profileOpen}>
          <span className="profile-avatar"><UserRound size={19} /></span>
          <span className="profile-language">{language === 'ta' ? 'தமிழ்' : 'EN'}</span>
          <ChevronDown size={14} />
        </button>
        {profileOpen && (
          <div className="profile-menu">
            <div className="profile-menu-title">{translate(language, 'language')}</div>
            {[['en', translate(language, 'english')], ['ta', translate(language, 'tamil')]].map(([value, label]) => (
              <button className="language-option" key={value} onClick={() => { setLanguage(value); setProfileOpen(false); }}>
                <span>{label}</span>{language === value && <Check size={16} />}
              </button>
            ))}
          </div>
        )}
      </div>
    </header>
  );
}
