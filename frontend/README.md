# VehicleCompare frontend

This archive contains the React + Vite frontend only. It does not include or modify the Python/FastAPI backend, scraper, database, or analysis modules. The removed About page is not part of the React navigation or routes. The interface includes a persistent light/dark mode switch and English/Tamil language selection.

## Run the UI by itself

Install Node.js 20.19+ or 22.12+, extract `VehicleCompare-frontend.zip`, and open PowerShell in the extracted `VehicleCompare-frontend` folder:

```powershell
npm install
npm run dev
```

Open `http://localhost:5173` on that laptop. To open the UI from another laptop on the same Wi-Fi/LAN, find the hosting laptop's IPv4 address with `ipconfig` and open `http://<frontend-laptop-ip>:5173` on the other laptop. Vite is configured to listen on the network. Allow port 5173 through Windows Firewall if prompted.

The frontend can run without the API. In that case, it displays clearly labelled frontend demo data; the demo listings are not live scraped prices.

## Connect the existing API (optional)

The API must be available on the network. On the laptop that has the original backend project, start its existing server from the project root:

```powershell
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

In the extracted frontend folder, create `.env.local` and set the API laptop's LAN IP. Use `127.0.0.1` if the API and Vite are running on the same laptop:

```env
VITE_API_PROXY_TARGET=http://192.168.1.25:8000
```

Restart Vite after changing `.env.local`. The browser calls the same-origin `/api` proxy, which forwards requests to the existing `/vehicles`, `/compare`, and `/stats` endpoints. The two laptops need to be on the same network, and Windows Firewall must allow ports 5173 and 8000. No backend CORS or endpoint changes are needed.

## Build

```powershell
npm run build
```

This writes the production frontend to `dist/`. A production host should proxy `/api` to the existing FastAPI server.

## Data and language

Vehicle prices use Indian Rupees (₹), distance uses kilometres, and the interface supports English and Tamil. Saved searches stay in this browser's local storage. The project README identifies its included database and CSV as fake development data; the UI labels detected project samples accordingly and never describes them as live scraped listings.

Vehicle cards use listing photos when an API response includes `image_url`, `imageUrl`, `photo_url`, `thumbnail_url`, or an `images` array. If an image is missing, the frontend uses one of the included Unsplash photos as a clearly marked representative example; the photo does not claim to show the specific listed vehicle.

For the backend developer's image integration task and project summary, see [BACKEND-DEVELOPER-BRIEF.md](./BACKEND-DEVELOPER-BRIEF.md). The frontend is ready to display `image_url` from `/vehicles`; actual listing-image extraction must be supplied by the existing backend scraper.

## Dashboard and vehicle photos

Each bundled vehicle photo shows one car. The Unsplash representative images are by [Portafolio](https://unsplash.com/photos/a-modern-grey-suv-parked-indoors-xmU9BijGe3g), [the studio photo contributor](https://unsplash.com/photos/dark-blue-suv-parked-in-a-studio-with-spotlights-u4JORqhtIS4), and [Hyundai Motor Group](https://unsplash.com/photos/a-grey-suv-parked-in-front-of-a-building-h8MDN-Rhi_Y), [Hyundai Motor Group](https://unsplash.com/photos/modern-grey-suv-parked-on-a-sunny-city-street-1Itag9LwJ4E), and [Hyundai Motor Group](https://unsplash.com/photos/a-silver-suv-sits-against-a-dark-background-nh6bNAKdjVk). The photos are used under the [Unsplash License](https://unsplash.com/license).
