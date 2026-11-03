# NordRoute — AI-Driven Distributed Logistics Scheduler

Til: o‘zbekcha interfeys qo‘llanadi; hujjat: Deutsch / English / O‘zbekcha.

## O‘zbekcha — ishga tushirish

### Docker Compose (Keycloak + Valhalla + API)

Docker Desktop va WSL2 o‘rnatilgan Windows kompyuterida:

```powershell
Copy-Item .env.example .env
notepad .env
```

`.env` faylida `TOMTOM_API_KEY` maydoniga Traffic API uchun TomTom kalitini, `KEYCLOAK_ADMIN_PASSWORD` maydoniga kuchli mahalliy parolni kiriting. Kalitlarni Git’ga yoki chatga yubormang.

```powershell
docker compose up --build
```

- Dashboard: <http://localhost:8000>
- Keycloak: <http://localhost:8080> — `.env` dagi bootstrap administrator paroli bilan kiring.
- API / OpenAPI: <http://localhost:8000/api/v1/docs>
- Health: <http://localhost:8000/health>

Valhalla birinchi ishga tushganda Geofabrik’dan Germaniyaning OSM PBF faylini yuklab, yo‘l grafini quradi. Bu bir necha GB trafik/disk va ko‘p vaqt talab qiladi; tugamaguncha optimizatsiya 503 javobi bilan ochiq xato qaytaradi. Docker loglarini `docker compose logs -f valhalla scheduler` orqali kuzating. Marshrut grafigi `valhalla-data` volume’da saqlanadi.

Realm `nordroute` avtomatik import qilinadi. Foydalanuvchini Keycloak Admin Console’da yarating, unga `dispatcher`, `viewer`, `admin` yoki `dpo` realm rolini biriktiring. SPA OAuth2 Authorization Code + PKCE ishlatadi; API imzoni, issuer’ni va audience’ni tekshiradi, rollar bo‘yicha amallarni cheklaydi. Ishlab chiqarish muhiti uchun `OIDC_ISSUER`, `OIDC_JWKS_URL`, `OIDC_AUDIENCE`, `OIDC_CLIENT_ID` va Keycloak hostname’ini o‘zingizning HTTPS domeningizga moslang.

### Lokal frontend/API (integratsiyalarni masofadan sozlash)

```powershell
Copy-Item .env.example .env
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt -r requirements-dev.txt
npm ci
npm run build
$env:AUTH_MODE = "api_key"
$env:APP_API_KEY = "local-demo-key-change-me"
uvicorn app:app --reload
```

Lokal demo API kaliti — faqat ishlab chiqish uchun. Haqiqiy marshrut hisoblash uchun `VALHALLA_URL` ishlaydigan Valhalla serveriga, `TOMTOM_API_KEY` haqiqiy TomTom Traffic API obunasiga ishora qilishi shart. Bu integratsiyalar yo‘q yoki ishlamasa, tizim taxminiy/greedy yechimga o‘tmaydi; aniq xato ko‘rsatadi.

## Nemischa

### Implementiert

- **Routing:** self-hosted Valhalla, OSM Germany graph, truck costing; echte Straßennetz-Distanzmatrix und geroutete GeoJSON-Geometrien.
- **Optimierung:** Google OR-Tools RoutingModel, Pickup/Delivery-Paarung, Gewicht-/Volumenkapazitäten, Lieferzeitpunkte, 9-Stunden-Tageslenkzeitlimit, Guided Local Search, einstellbares Solver-Zeitlimit und manuelle Freigabe.
- **Verkehr:** TomTom Traffic Flow Segment Data; aktuelle/free-flow-Geschwindigkeit an Matrix-Standorten wird zur Anpassung der Routingmatrix verwendet und kurzfristig zwischengespeichert. Ungültige API-Schlüssel, Providerfehler und Rate Limits werden sichtbar gemeldet.
- **Karte:** MapLibre GL JS, OpenStreetMap/CARTO-Grundkarte, GPS-Fahrzeuge, Routinglinien und eine separat aktualisierte TomTom-Verkehrsebene mit farbigen Flow-Segmenten, Geschwindigkeits-Popups und Ein-/Aus-Schalter.
- **Identität:** Keycloak, OpenID Connect Authorization Code + PKCE, signatur-/issuer-/audience-geprüfte JWTs, Rollen `admin`, `dispatcher`, `viewer`, `dpo`; Schreibzugriffe sind serverseitig geschützt.

### Voraussetzungen und Compose-Start

Docker Desktop/WSL2, gültiger TomTom-Traffic-API-Key und ausreichend freier Speicherplatz für den deutschen OSM-Extrakt sind nötig. Eine vollständige Deutschland-Karte benötigt mehrere GB Download und Speicher; der erste Valhalla-Graphaufbau kann lange dauern.

```powershell
Copy-Item .env.example .env
notepad .env
docker compose up --build
```

Tragen Sie `TOMTOM_API_KEY` und ein starkes `KEYCLOAK_ADMIN_PASSWORD` in `.env` ein. Die Keycloak-Realm wird importiert; Benutzer werden anschließend in der Admin Console angelegt und erhalten eine Realm-Rolle. Niemals Produktionsgeheimnisse in den Quellcode, Chat oder Git eintragen.

Dashboard: <http://localhost:8000> · Keycloak: <http://localhost:8080> · OpenAPI: <http://localhost:8000/api/v1/docs>

### Karte und Datenquellen

MapLibre-Bibliotheksdateien werden lokal gebündelt. Die konfigurierte CARTO-Vektorkarte nutzt OpenStreetMap-Daten und benötigt eine Internetverbindung. Für einen abgeschotteten EU-Produktionsbetrieb ist eine selbst gehostete, lizenzkonform betriebene Tile-Infrastruktur einzurichten.

TomTom-Trafficdaten werden **nicht** als vollständige abschnittsgenaue Live-Routenzeit abgefragt: aktuelle Segmentgeschwindigkeiten an Matrixpunkten skalieren die Valhalla-Fahrzeiten. Der geschützte Endpunkt `/api/v1/traffic` liefert verfügbare TomTom-Flow-Segmentgeometrien als GeoJSON; das Dashboard aktualisiert die Ebene minütlich und zeigt den Datenstatus. Nicht alle Fahrzeugpositionen liegen auf einem erfassbaren Verkehrssegment. TomTom-Nutzungsbedingungen, Quoten und Datenlizenz prüfen.

## English

The application integrates a Germany OSM/Valhalla truck-road matrix, TomTom live flow-segment speed adjustments and GeoJSON overlays, Google OR-Tools pickup/delivery optimization, MapLibre maps, and Keycloak OIDC/PKCE with server-enforced RBAC. The authenticated `/api/v1/traffic` endpoint serves available TomTom segment geometries; the map refreshes them every 60 seconds and reports when data is unavailable. Copy `.env.example` to `.env`, enter a licensed TomTom API key and a strong Keycloak bootstrap password, and run `docker compose up --build`. Valhalla downloads and builds the full Germany map on first start; optimization remains unavailable until the graph is ready.

## API and validation

In OIDC mode, use a Keycloak-issued access token in the `Authorization: Bearer ...` header. The dashboard signs in through Authorization Code + PKCE. API roles: `admin` (all), `dispatcher` (operational writes), `viewer` (read-only), `dpo` (read and audit). Development mode accepts `X-API-Key` and must not be exposed publicly.

```powershell
python -m pip install -r requirements.txt -r requirements-dev.txt
python -B -m pytest -q -p no:cacheprovider
ruff check app.py services tests
node --check static\app.js
npm ci
npm run build
```

## Bekannte Grenzen / Remaining production work

Die aktuelle Software ist trotz der echten Routing-, Traffic-, Karten- und Login-Integrationen **nicht vollständig zertifiziert oder für automatische Disposition freigegeben**:

- TomTom-Verkehr passt die Fahrzeit anhand der abgefragten Matrix-Endpunkte an; es berechnet derzeit keine vollständige TomTom-Traffic-Route pro Straßenkante. Fehlende Flow-Segmente werden gezählt und nicht als Live-Daten ausgegeben.
- Die Tageslenkzeit wird auf höchstens 9 Stunden begrenzt; gesetzliche 45-Minuten-Pausen nach 4,5 Stunden sind **keine harte Solver-Bedingung**. Wochen-/Doppelwochenlenkzeit, Ruhezeiten, Feiertage, ADR, Umweltzonen, Rampen-Slots und Toll Collect müssen noch integriert und juristisch validiert werden.
- Fuel, CO₂ und Maut sind Modell-/Platzhalterwerte; es existieren noch keine Tachographen-, realen Verbrauchs-, Maut- oder Baseline-Messdaten. Nicht erhobene OTD-/Savings-KPIs werden als `—` angezeigt.
- Das MVP nutzt weiterhin SQLite. Für Mehrbenutzerbetrieb sind PostgreSQL/PostGIS, echte Migrationen, verschlüsselte Backups, Audit-Log-Härtung, Rate Limiting, TLS/Reverse Proxy, Secrets Manager, Monitoring und Datenschutz-Lösch-/Exportprozesse zu ergänzen.
- Keycloak läuft in Compose mit `start-dev`; dieser Modus ist ausschließlich für lokale Entwicklung. Für Produktion Keycloak im gehärteten Produktionsmodus mit TLS, persistenten Backups, Mailversand, getrenntem Operator-Zugang und externem IdP betreiben.
- Die Karte bezieht CARTO/OSM-Kacheln von extern; Lizenz, Attributionspflichten, EU-Datenresidenz und Offlinebetrieb separat prüfen.

Routen werden deshalb nur als menschlich bestätigungspflichtige Vorschläge erstellt. Gesetzliche und betriebliche Freigabe durch eine qualifizierte Fachperson bleibt zwingend.
