import localVehicleFallback from '../assets/hero-suv.jpg';
import blueStudioSuvPhoto from '../assets/candidate-blue-vw-studio.jpg';
import greyShowroomSuvPhoto from '../assets/candidate-grey-suv-showroom.jpg';
import kiaBuildingSuvPhoto from '../assets/candidate-kia-building.jpg';
import kiaCitySuvPhoto from '../assets/candidate-kia-city.jpg';
import genesisStudioSuvPhoto from '../assets/candidate-genesis-gv60-studio.jpg';

export const representativeVehiclePhotos = [
  {
    url: blueStudioSuvPhoto,
    photoPage: 'https://unsplash.com/photos/dark-blue-suv-parked-in-a-studio-with-spotlights-u4JORqhtIS4',
  },
  {
    url: greyShowroomSuvPhoto,
    photoPage: 'https://unsplash.com/photos/a-modern-grey-suv-parked-indoors-xmU9BijGe3g',
  },
  {
    url: kiaBuildingSuvPhoto,
    photoPage: 'https://unsplash.com/photos/a-grey-suv-parked-in-front-of-a-building-h8MDN-Rhi_Y',
  },
  {
    url: kiaCitySuvPhoto,
    photoPage: 'https://unsplash.com/photos/modern-grey-suv-parked-on-a-sunny-city-street-1Itag9LwJ4E',
  },
  {
    url: genesisStudioSuvPhoto,
    photoPage: 'https://unsplash.com/photos/a-silver-suv-sits-against-a-dark-background-nh6bNAKdjVk',
  },
];

const demoPhotoById = {
  'demo-2': 1,
  'demo-7': 2,
  'demo-10': 0,
};

const photoByBrand = {
  mahindra: 0,
  tata: 2,
  kia: 3,
  hyundai: 4,
  'maruti suzuki': 1,
  toyota: 0,
  honda: 2,
};

function imageUrl(value) {
  if (typeof value === 'string') return value.trim();
  if (value && typeof value === 'object') return value.url || value.src || value.image_url || '';
  return '';
}

export function getVehicleImage(vehicle) {
  const apiImage = imageUrl(vehicle?.image_url || vehicle?.imageUrl || vehicle?.photo_url || vehicle?.thumbnail_url)
    || imageUrl(Array.isArray(vehicle?.images) ? vehicle.images[0] : '');
  if (apiImage) return { url: apiImage, representative: false };

  const providedRepresentative = imageUrl(vehicle?.representative_image_url);
  if (providedRepresentative) return { url: providedRepresentative, representative: true };

  const brandKey = String(vehicle?.brand || '').trim().toLowerCase();
  const photoIndex = demoPhotoById[vehicle?.id] ?? photoByBrand[brandKey] ?? 0;
  return { url: representativeVehiclePhotos[photoIndex].url, representative: true };
}

export { localVehicleFallback };
