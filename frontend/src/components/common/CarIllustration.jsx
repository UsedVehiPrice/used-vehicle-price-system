import { useId } from 'react';

export default function CarIllustration({ tone = 'white', className = '' }) {
  const id = `${tone === 'blue' ? 'carBlue' : 'carWhite'}${useId().replaceAll(':', '')}`;
  const paint = `url(#${id}Paint)`;
  return (
    <svg className={className} viewBox="0 0 680 390" role="img" aria-label="Modern compact SUV illustration" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id={`${id}Paint`} x1=".1" y1="0" x2=".88" y2="1">
          <stop offset="0" stopColor={tone === 'blue' ? '#74b7ff' : '#fff'} />
          <stop offset=".42" stopColor={tone === 'blue' ? '#2676c8' : '#edf3f8'} />
          <stop offset=".78" stopColor={tone === 'blue' ? '#114783' : '#b8c4cf'} />
          <stop offset="1" stopColor={tone === 'blue' ? '#082547' : '#82909e'} />
        </linearGradient>
        <linearGradient id={`${id}Glass`} x1="0" y1="0" x2=".8" y2="1">
          <stop offset="0" stopColor="#527087" />
          <stop offset=".48" stopColor="#142b40" />
          <stop offset="1" stopColor="#071421" />
        </linearGradient>
        <linearGradient id={`${id}Road`} x1="0" x2="0" y1="0" y2="1">
          <stop stopColor="#ffffff" stopOpacity=".42" />
          <stop offset="1" stopColor="#ffffff" stopOpacity="0" />
        </linearGradient>
        <filter id={`${id}Shadow`} x="-30%" y="-30%" width="160%" height="180%">
          <feGaussianBlur stdDeviation="11" />
        </filter>
      </defs>
      <ellipse cx="356" cy="329" rx="251" ry="25" fill="#163147" opacity=".28" filter={`url(#${id}Shadow)`} />
      <path d="M92 278c18-18 40-27 75-36l58-81c21-29 50-43 88-46l98-7c31-2 58 9 81 31l68 67c35 12 55 27 65 49l-7 45c-2 13-13 22-26 22h-39c-7-44-34-69-75-69s-70 26-79 68H263c-6-42-32-67-73-67s-69 26-78 67H90c-11 0-18-10-15-21z" fill={paint} stroke={tone === 'blue' ? '#174d7e' : '#98a7b3'} strokeWidth="3" />
      <path d="m244 160-61 83 143 1 18-127-31 1c-31 1-51 12-69 42z" fill={`url(#${id}Glass)`} stroke="#aebbc4" strokeWidth="3" />
      <path d="m357 117-16 127 178 1-73-73c-20-20-41-29-69-29z" fill={`url(#${id}Glass)`} stroke="#aebbc4" strokeWidth="3" />
      <path d="M223 248h353c29 0 52 8 72 23l-1 19c-36-6-49 8-52 39h-25c-7-42-35-68-76-68s-69 26-78 68H263c-6-42-32-67-73-67s-69 26-78 67H90c-11 0-18-10-15-21l17-30c21-15 61-27 131-30z" fill={`url(#${id}Paint)`} opacity=".83" />
      <path d="M581 222c33 8 53 21 67 40l-4 21-51-4-13-57z" fill="#101c28" />
      <path d="M593 227c22 8 35 17 45 32l-36-2z" fill="#eaf3fb" />
      <path d="m98 277 35-4-10 17-32 2z" fill="#fff3c4" />
      <path d="m639 284 20 2-2 13-22-1z" fill="#ffddd2" />
      <path d="M274 281h272" stroke="#fff" strokeOpacity=".46" strokeWidth="3" />
      <path d="M270 168h77m18-28h44" stroke="#dce8ef" strokeOpacity=".56" strokeWidth="3" />
      <path d="M372 252v29m134-29v29" stroke="#667985" strokeWidth="3" />
      <path d="M399 255h23" stroke="#687987" strokeWidth="4" strokeLinecap="round" />
      <path d="M484 255h23" stroke="#687987" strokeWidth="4" strokeLinecap="round" />
      <g>
        <circle cx="190" cy="307" r="47" fill="#101923" />
        <circle cx="190" cy="307" r="30" fill="#768693" />
        <circle cx="190" cy="307" r="20" fill="#d2dae0" />
        <circle cx="190" cy="307" r="8" fill="#82919d" />
        <path d="M190 278v58m-29-29h58m-49-20 41 41m0-41-41 41" stroke="#8997a1" strokeWidth="4" />
      </g>
      <g>
        <circle cx="512" cy="307" r="47" fill="#101923" />
        <circle cx="512" cy="307" r="30" fill="#768693" />
        <circle cx="512" cy="307" r="20" fill="#d2dae0" />
        <circle cx="512" cy="307" r="8" fill="#82919d" />
        <path d="M512 278v58m-29-29h58m-49-20 41 41m0-41-41 41" stroke="#8997a1" strokeWidth="4" />
      </g>
      <path d="m80 346 566 0" stroke={`url(#${id}Road)`} strokeWidth="4" />
    </svg>
  );
}
