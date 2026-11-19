import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Header from './Header.jsx';
import Sidebar from './Sidebar.jsx';
import StatusBanner from '../common/StatusBanner.jsx';
import { useAppData } from '../../context/AppContext.jsx';

export default function AppShell() {
  const [menuOpen, setMenuOpen] = useState(false);
  const { theme } = useAppData();
  return (
    <div className="app-shell" data-theme={theme}>
      <Sidebar open={menuOpen} onClose={() => setMenuOpen(false)} />
      <div className="app-column">
        <Header onMenuClick={() => setMenuOpen(true)} />
        <main className="main-content">
          <StatusBanner />
          <Outlet />
        </main>
      </div>
    </div>
  );
}
