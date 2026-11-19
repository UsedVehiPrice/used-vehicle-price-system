import { CarFront } from 'lucide-react';

export default function EmptyState({ title, description, action }) {
  return (
    <div className="empty-state">
      <span className="empty-icon"><CarFront size={25} /></span>
      <h3>{title}</h3>
      {description && <p>{description}</p>}
      {action}
    </div>
  );
}
