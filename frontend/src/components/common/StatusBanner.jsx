import { AlertCircle, CheckCircle2, Database } from 'lucide-react';
import { useAppData } from '../../context/AppContext.jsx';
import { translate } from '../../utils/translations.js';

export default function StatusBanner() {
  const { dataState, language } = useAppData();
  if (dataState.mode === 'api' || dataState.mode === 'loading' || dataState.mode === 'empty') return null;
  const isSample = dataState.mode === 'project-sample';
  const title = isSample ? translate(language, 'projectSample') : translate(language, 'demoTitle');
  const body = isSample ? translate(language, 'demoMessage') : translate(language, 'apiMessage');
  const Icon = isSample ? Database : AlertCircle;
  return (
    <div className={`status-banner ${isSample ? 'status-banner-sample' : ''}`} role="status">
      <Icon size={17} />
      <span><strong>{title}</strong> <span className="status-copy">{body}</span></span>
    </div>
  );
}
