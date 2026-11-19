import {
  siAudi, siBmw, siFord, siHonda, siHyundai, siKia, siMahindra, siMg,
  siNissan, siRenault, siSkoda, siSuzuki, siTata, siToyota, siVolkswagen,
} from 'simple-icons';

const brandIcons = {
  Toyota: siToyota,
  Honda: siHonda,
  Hyundai: siHyundai,
  'Maruti Suzuki': siSuzuki,
  Tata: siTata,
  Mahindra: siMahindra,
  Ford: siFord,
  BMW: siBmw,
  Audi: siAudi,
  Kia: siKia,
  Renault: siRenault,
  Nissan: siNissan,
  Volkswagen: siVolkswagen,
  Skoda: siSkoda,
  MG: siMg,
};

export default function BrandLogo({ name, compact = false }) {
  const icon = brandIcons[name];
  return (
    <span className={`brand-logo ${compact ? 'brand-logo-compact' : ''}`} aria-label={`${name} logo`}>
      {icon ? <svg viewBox="0 0 24 24" role="img" aria-hidden="true" style={{ color: `#${icon.hex}` }}><path fill="currentColor" d={icon.path} /></svg> : <span className="brand-wordmark">{name}</span>}
    </span>
  );
}
