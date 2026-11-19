# VehicleCompare: backend developer brief

## Project description

VehicleCompare is a Tamil Nadu focused used-vehicle price comparison and analysis app. The existing Python/FastAPI project supplies vehicle listings and price data. The React + Vite frontend lets users search and filter listings, compare vehicles, review market charts, save searches in the browser, and switch between English and Tamil. It formats prices in Indian Rupees and distance in kilometres. The frontend also has persistent light and dark themes.

The current backend routes used by the frontend are `GET /vehicles`, `GET /compare`, and `GET /stats`. The frontend should continue using those existing routes.

## Requested listing image integration

The React UI already displays a vehicle image returned with a listing. Please extend the existing scraper and API serialization so each vehicle row from `GET /vehicles` can include:

```json
{
  "image_url": "https://source.example/listing-image.jpg",
  "image_alt": "White compact SUV, left side view"
}
```

Use the primary photo belonging to that exact listing. Extract it while the existing scraper visits a listing page, using that source's supported image field, structured vehicle data, or `og:image` metadata as appropriate. Normalize it to an absolute `http` or `https` URL and return `null` when a listing has no usable image. Do not attach a generic stock image to a specific scraped listing.

Keep image extraction within the existing scraper/backend workflow and follow each listing source's access rules and terms. If the source blocks browser hotlinking, consider storing an approved cached copy in the backend and return its stable URL. Avoid returning base64 image data in the JSON response.

The frontend also recognizes `imageUrl`, `photo_url`, `thumbnail_url`, or an `images` array for compatibility. `image_url` is the preferred field. `image_alt` is optional. Missing image URLs display a bundled, clearly marked representative photo in the UI.

## Handoff status

This frontend package is prepared to consume the image URL field. The backend scraper, database, schema, and API have not been changed as part of this frontend deliverable; actual scraped listing photos will appear after the backend provides the image field.
