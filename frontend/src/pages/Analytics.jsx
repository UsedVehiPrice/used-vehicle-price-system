import { useEffect, useMemo, useState } from 'react';
import { BarChart3, CarFront, Fuel, IndianRupee } from 'lucide-react';
import { BarChart, Bar, CartesianGrid, Cell, Line, LineChart, Pie, PieChart, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis } from 'recharts';
import { useAppData } from '../context/AppContext.jsx';
import { fetchMarketStats } from '../services/api.js';
import { formatCurrency, formatCurrencyCompact, formatNumber } from '../utils/currency.js';
import { formatKilometres } from '../utils/distance.js';
import { translate } from '../utils/translations.js';
import EmptyState from '../components/common/EmptyState.jsx';

const CHART_COLORS = ['#1d6ee9', '#ffbd32', '#35a17a', '#7b61d1', '#e9824f', '#41a9ba'];

function ChartCard({ title, subtitle, children }) {
  return <section className="chart-card"><div className="chart-card-heading"><div><h2>{title}</h2>{subtitle && <p>{subtitle}</p>}</div><span className="chart-card-mark"><BarChart3 size={17} /></span></div><div className="chart-frame">{children}</div></section>;
}

function CurrencyTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return <div className="chart-tooltip"><strong>{label || payload[0].payload.name || payload[0].payload.year}</strong><span>{formatCurrency(payload[0].value)}</span></div>;
}

export default function Analytics() {
  const { vehicles, dataState, language } = useAppData();
  const t = (key) => translate(language, key);
  const [apiRows, setApiRows] = useState([]);
  const [statsLoading, setStatsLoading] = useState(true);

  useEffect(() => {
    let active = true;
    fetchMarketStats().then((rows) => { if (active) setApiRows(rows); }).catch(() => { if (active) setApiRows([]); }).finally(() => { if (active) setStatsLoading(false); });
    return () => { active = false; };
  }, []);

  const computed = useMemo(() => {
    const average = vehicles.length ? vehicles.reduce((sum, vehicle) => sum + vehicle.price, 0) / vehicles.length : 0;
    const groups = (selector) => {
      const map = new Map();
      vehicles.forEach((vehicle) => {
        const key = selector(vehicle);
        if (!key) return;
        const current = map.get(key) || { name: key, count: 0, total: 0 };
        current.count += 1;
        current.total += vehicle.price;
        map.set(key, current);
      });
      return [...map.values()].map((item) => ({ ...item, avg: Math.round(item.total / item.count) }));
    };
    const apiBrandMap = new Map();
    apiRows.forEach((row) => {
      const current = apiBrandMap.get(row.brand) || { name: row.brand, count: 0, total: 0 };
      current.count += Number(row.listings) || 0;
      current.total += (Number(row.avg_price) || 0) * (Number(row.listings) || 0);
      apiBrandMap.set(row.brand, current);
    });
    const apiYearMap = new Map();
    apiRows.forEach((row) => {
      const year = Number(row.year);
      if (!year) return;
      const current = apiYearMap.get(year) || { year, count: 0, total: 0 };
      current.count += Number(row.listings) || 0;
      current.total += (Number(row.avg_price) || 0) * (Number(row.listings) || 0);
      apiYearMap.set(year, current);
    });
    const brandStats = (apiBrandMap.size ? [...apiBrandMap.values()].map((item) => ({ ...item, avg: Math.round(item.total / Math.max(1, item.count)) })) : groups((vehicle) => vehicle.brand)).sort((a, b) => b.avg - a.avg).slice(0, 8);
    const yearStats = (apiYearMap.size ? [...apiYearMap.values()].map((item) => ({ ...item, avg: Math.round(item.total / Math.max(1, item.count)) })) : groups((vehicle) => vehicle.year ? String(vehicle.year) : '')).map((item) => ({ year: Number(item.year || item.name), avg: item.avg })).filter((item) => item.year).sort((a, b) => a.year - b.year);
    const fuelStats = groups((vehicle) => vehicle.fuel_type).sort((a, b) => b.count - a.count);
    const cityStats = groups((vehicle) => vehicle.location).sort((a, b) => b.avg - a.avg).slice(0, 8);
    const allPoints = vehicles.filter((vehicle) => vehicle.km_driven != null && vehicle.price > 0);
    const pointStep = Math.max(1, Math.ceil(allPoints.length / 180));
    const points = allPoints.filter((_, index) => index % pointStep === 0).map((vehicle) => ({ x: vehicle.km_driven, y: vehicle.price, name: `${vehicle.brand} ${vehicle.model}`, city: vehicle.location }));
    const topFuel = fuelStats[0]?.name || '—';
    return { average, brandStats, yearStats, fuelStats, cityStats, points, topFuel };
  }, [vehicles, apiRows]);

  if (!vehicles.length && !dataState.loading) return <div className="page-enter"><div className="page-heading-row"><div><div className="eyebrow">AVAILABLE PROJECT DATA</div><h1>{t('analyticsTitle')}</h1><p>{t('analyticsSub')}</p></div></div><EmptyState title={t('emptyData')} description={t('emptyDataHint')} /></div>;

  return (
    <div className="analytics-page page-enter">
      <div className="page-heading-row"><div><div className="eyebrow">{t('marketInsights').toUpperCase()}</div><h1>{t('analyticsTitle')}</h1><p>{t('analyticsSub')}</p></div><span className="data-source-chip">{statsLoading ? t('updatingAnalysis') : apiRows.length ? t('apiAnalysis') : t('computedAnalysis')}</span></div>
      <div className="analytics-stat-grid">
        <article className="analytics-stat-card"><span className="analytics-stat-icon stat-blue"><IndianRupee size={19} /></span><span className="analytics-stat-label">{t('averagePrice')}</span><strong>{formatCurrency(computed.average)}</strong><small>{t('dataNote')}</small></article>
        <article className="analytics-stat-card"><span className="analytics-stat-icon stat-yellow"><CarFront size={19} /></span><span className="analytics-stat-label">{t('totalListings')}</span><strong>{formatNumber(vehicles.length)}</strong><small>{dataState.mode === 'project-sample' || dataState.mode === 'frontend-demo' ? t('sampleListings') : t('availableDataset')}</small></article>
        <article className="analytics-stat-card"><span className="analytics-stat-icon stat-green"><Fuel size={19} /></span><span className="analytics-stat-label">{t('popularFuel')}</span><strong>{computed.topFuel}</strong><small>{formatNumber(computed.fuelStats[0]?.count || 0)} listings</small></article>
      </div>

      <div className="analytics-chart-grid">
        <ChartCard title={t('avgByBrand')} subtitle="Used vehicle asking price · ₹">
          <ResponsiveContainer width="100%" height="100%"><BarChart data={computed.brandStats} margin={{ top: 8, right: 8, bottom: 2, left: 0 }}><CartesianGrid stroke="#edf1f7" vertical={false} /><XAxis dataKey="name" tick={{ fontSize: 11, fill: '#77849a' }} axisLine={false} tickLine={false} interval={0} /><YAxis tickFormatter={formatCurrencyCompact} tick={{ fontSize: 10, fill: '#8894a7' }} axisLine={false} tickLine={false} width={72} /><Tooltip content={<CurrencyTooltip />} /><Bar dataKey="avg" fill="#1d6ee9" radius={[6, 6, 0, 0]} maxBarSize={36} /></BarChart></ResponsiveContainer>
        </ChartCard>
        <ChartCard title={t('priceByYear')} subtitle="Average listing price by manufacturing year">
          <ResponsiveContainer width="100%" height="100%"><LineChart data={computed.yearStats} margin={{ top: 8, right: 12, bottom: 2, left: 0 }}><CartesianGrid stroke="#edf1f7" vertical={false} /><XAxis dataKey="year" tick={{ fontSize: 11, fill: '#77849a' }} axisLine={false} tickLine={false} /><YAxis tickFormatter={formatCurrencyCompact} tick={{ fontSize: 10, fill: '#8894a7' }} axisLine={false} tickLine={false} width={72} /><Tooltip content={<CurrencyTooltip />} /><Line type="monotone" dataKey="avg" stroke="#347be3" strokeWidth={3} dot={{ r: 3, fill: '#fff', strokeWidth: 2 }} activeDot={{ r: 5 }} /></LineChart></ResponsiveContainer>
        </ChartCard>
        <ChartCard title={t('fuelMix')} subtitle="Fuel types in available vehicle listings">
          <ResponsiveContainer width="100%" height="100%"><PieChart><Pie data={computed.fuelStats} dataKey="count" nameKey="name" cx="50%" cy="50%" innerRadius={61} outerRadius={95} paddingAngle={4} cornerRadius={5}>{computed.fuelStats.map((entry, index) => <Cell key={entry.name} fill={CHART_COLORS[index % CHART_COLORS.length]} />)}</Pie><Tooltip formatter={(value, name) => [`${formatNumber(value)} listings`, name]} /><text x="50%" y="48%" textAnchor="middle" className="donut-total">{formatNumber(vehicles.length)}</text><text x="50%" y="57%" textAnchor="middle" className="donut-caption">listings</text></PieChart></ResponsiveContainer>
        </ChartCard>
        <ChartCard title={t('cityPrices')} subtitle="Average asking prices by location">
          <ResponsiveContainer width="100%" height="100%"><BarChart data={computed.cityStats} layout="vertical" margin={{ top: 0, right: 12, bottom: 0, left: 8 }}><CartesianGrid stroke="#edf1f7" horizontal={false} /><XAxis type="number" tickFormatter={formatCurrencyCompact} tick={{ fontSize: 10, fill: '#8894a7' }} axisLine={false} tickLine={false} /><YAxis type="category" dataKey="name" width={92} tick={{ fontSize: 11, fill: '#77849a' }} axisLine={false} tickLine={false} /><Tooltip content={<CurrencyTooltip />} /><Bar dataKey="avg" fill="#4ba787" radius={[0, 5, 5, 0]} maxBarSize={24} /></BarChart></ResponsiveContainer>
        </ChartCard>
        <ChartCard title={t('priceVsKm')} subtitle="Each point represents a listing · kilometres">
          <ResponsiveContainer width="100%" height="100%"><ScatterChart margin={{ top: 8, right: 18, bottom: 6, left: 0 }}><CartesianGrid stroke="#edf1f7" /><XAxis type="number" dataKey="x" name="Kilometres" tickFormatter={(value) => `${Math.round(value / 1000)}k`} tick={{ fontSize: 10, fill: '#8894a7' }} axisLine={false} tickLine={false} /><YAxis type="number" dataKey="y" name="Asking price" tickFormatter={formatCurrencyCompact} tick={{ fontSize: 10, fill: '#8894a7' }} axisLine={false} tickLine={false} width={72} /><Tooltip formatter={(value, name) => [name === 'Asking price' ? formatCurrency(value) : formatKilometres(value), name]} labelFormatter={(_, payload) => payload?.[0]?.payload?.name || ''} /><Scatter data={computed.points} fill="#347be3" fillOpacity={0.65} /></ScatterChart></ResponsiveContainer>
        </ChartCard>
      </div>
    </div>
  );
}
