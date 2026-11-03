# Technische Spezifikation (Lastenheft)
E-mail contact@hinterlandofthings.de
## AI-Driven Distributed Logistics Scheduler – Echtzeit-Routenoptimierung und Dispositions-Dashboard

**Version:** 1.0 (Entwurf) | **Zielmarkt:** Deutschland / Europäische Union | **Dokumentsprache:** Deutsch (UI und API-Dokumentation: Deutsch + Englisch)

---

## 1. Allgemeine Informationen

### 1.1 Projektziel

Entwicklung eines Backends, einer Optimierungs-Engine und eines visuellen Dispositions-Dashboards, die die Zuteilung von Ladungen zwischen Lagern und Transportfahrzeugen in Echtzeit mit KI-Unterstützung optimieren.

### 1.2 Geschäftlicher Nutzen

- Reduzierung von Kraftstoffverbrauch und CO₂-Emissionen (durch die CO₂-abhängige Lkw-Maut in Deutschland sinken die Kosten direkt).
- Verkürzung der Lieferzeiten und Vermeidung von Leerfahrten.
- Lückenlose Einhaltung der Lenk- und Ruhezeiten.
- Schnelle Reaktion auf unvorhergesehene Ereignisse (Stau, Unfall).

### 1.3 Erfolgskriterien (KPIs)

| KPI | Ziel | Messmethode |
| --- | --- | --- |
| Kraftstoffverbrauch / gefahrener km | **−10 … −15 %** gegenüber Baseline | A/B- oder Shadow-Mode-Vergleich |
| Durchschnittliche Lieferzeit | **−10 … −15 %** gegenüber Baseline | Von Auftragserstellung bis Übergabe |
| Termintreue (OTD) | ≥ 95 % | Gemessen am Zeitfenster |
| Dauer der Neuberechnung (Re-Optimierung) | p95 ≤ 10 s (≤ 200 Aufträge / ≤ 50 Fahrzeuge) | Prometheus-Metrik |
| Dashboard-Aktualisierungslatenz | p95 ≤ 2 s (GPS → Karte) | Ende-zu-Ende-Messung |
| Systemverfügbarkeit (SLA) | ≥ 99,5 % | Uptime-Monitoring |

> **Wichtig:** Damit das Ziel „bis zu 15 %“ messbar ist, wird eine *Baseline* festgelegt: (a) historische Kundendaten oder (b) ein einfacher Greedy-/Nearest-Neighbor-Algorithmus. Ein Bericht wird wöchentlich automatisch erzeugt.

---

## 2. Abgrenzung (Scope)

**Enthalten (In Scope):** Datenerfassungs-API, Optimierungs-Engine, Live-Dashboard, Alerting-System, Authentifizierung/Autorisierung, Audit-Log, CI/CD, Docker-basiertes Deployment, Dokumentation.

**Nicht enthalten (Out of Scope, Phase 1):** mobile Fahrer-App, Zahlungs-/Rechnungsmodul, vollständiger ERP-Ersatz, produktiver Einsatz eines selbstlernenden RL-Modells (nur Forschung).

---

## 3. Spezifische Anforderungen für den deutschen Markt (Compliance & lokale Vorgaben)

### 3.1 Datenschutz (DSGVO)

- GPS- und Fahrerdaten sind **personenbezogene Daten**. Rechtsgrundlage (Art. 6 DSGVO), Zweckbindung und **Datenminimierung** werden dokumentiert.
- Alle Daten werden **in der EU/im EWR** gespeichert (Datenresidenz); keine Übermittlung in Drittländer bzw. nur mit Standardvertragsklauseln (SCC).
- **Privacy by Design / by Default:** Fahrerkennungen werden pseudonymisiert (UUID); Klarnamen sind nur für berechtigte Rollen sichtbar.
- **Löschkonzept:** Rohe GPS-Spuren werden standardmäßig 90 Tage gespeichert, danach aggregiert oder gelöscht; die Aufbewahrungsrichtlinie ist konfigurierbar.
- Betroffenenrechte: Admin-Funktionen für Datenexport und Löschung (Art. 15–17 DSGVO).
- Dokumente: *Verzeichnis von Verarbeitungstätigkeiten (VVT)*, DSFA-Vorlage (Art. 35), Liste der technisch-organisatorischen Maßnahmen (TOM), Grundlage für den Auftragsverarbeitungsvertrag (AVV).
- Personenbezogene Daten werden **nicht in Logs geschrieben** (Log-Masking).

### 3.2 Arbeitsrecht und Mitarbeiterüberwachung

- Systeme zur Fahrerortung erfordern in Deutschland in der Regel eine **Vereinbarung mit dem Betriebsrat** (BetrVG § 87 Abs. 1 Nr. 6). Das System muss **„Betriebsvereinbarung-ready“** sein: individuelle Leistungsbewertungen/Rankings sind **standardmäßig deaktiviert**, nur operative Funktionen sind aktiv.
- Die Überwachung erfolgt nur während der Arbeitszeit; außerhalb der Arbeitszeit werden keine GPS-Daten erhoben.

### 3.3 Lenk- und Ruhezeiten

Die Optimierung berücksichtigt folgende Punkte als **harte Nebenbedingungen (Hard Constraints)**:

- EU-Verordnung 561/2006 (Lenkzeit: 9 Std. täglich, 56 Std. wöchentlich, 90 Std. in zwei Wochen; 45 Minuten Pause nach 4,5 Std.; tägliche/wöchentliche Ruhezeiten);
- Arbeitszeitgesetz (ArbZG);
- Import von Fahrtenschreiberdaten (digitaler Tachograph) per API (zukünftig).

### 3.4 Verkehrsrechtliche und regulatorische Routing-Beschränkungen

- **Sonn- und Feiertagsfahrverbot für Lkw** (StVO § 30) einschließlich Feiertagskalender je Bundesland.
- **Umweltzonen** und Diesel-Fahrverbote – abhängig von der Emissionsklasse des Fahrzeugs (Euro 5/6, elektrisch).
- Fahrzeugparameter: zulässiges Gesamtgewicht, Höhe, Achslasten, Länge (Straßen- und Brückenbeschränkungen), ADR (Gefahrgut).
- **Lkw-Maut** (Toll Collect): Mautkosten nach CO₂-Klasse und Achszahl werden in die Routenkosten einbezogen.
- Rampen-Zeitfenster (Slots) und Öffnungszeiten der Lager.

### 3.5 Nachhaltigkeit und Berichtswesen

- Die CO₂-Bilanzierung folgt **ISO 14083 / GLEC Framework / DIN EN 16258** (Well-to-Wheel). Berichte sind als CSV/PDF exportierbar.
- Emissionsdaten werden per API für Kundenberichte nach **LkSG / CSRD** bereitgestellt.

### 3.6 Informationssicherheit und Standards

- Das Design orientiert sich an **ISO/IEC 27001** und **BSI IT-Grundschutz**; für Kunden aus der Automobilindustrie werden **TISAX**-Anforderungen berücksichtigt.
- Für Kunden kritischer Infrastrukturen: Vorbereitung auf **NIS2** (Meldepflichten, Lieferkettensicherheit).
- **EU AI Act:** Das System wird als *Limited/Minimal Risk* eingestuft (keine Mitarbeiterbewertung, keine vollautomatische Entscheidung mit Rechtswirkung). Algorithmische Entscheidungen sind **erklärbar** (Explainability: Warum wurde die Route geändert?) und können vom Disponenten **übersteuert** werden (Human-in-the-Loop).
- Softwarelizenzen: ausschließlich zulässige OSS-Lizenzen (MIT/Apache-2.0/BSD); eine SBOM (CycloneDX) wird erzeugt.

### 3.7 Sprache und Barrierefreiheit

- UI: **Deutsch (primär), Englisch**; i18n-Architektur (Usbekisch/Russisch später ergänzbar).
- Datums-, Zeit- und Zahlenformate nach DE-Locale (`dd.MM.yyyy`, `1.234,56`); Zeitzone **Europe/Berlin** (Sommerzeit), interne Speicherung in UTC.
- Einheiten: km, kg, m³, l/100 km.
- Barrierefreiheit: **BITV 2.0 / WCAG 2.1 AA** (Vorbereitung auf das Barrierefreiheitsstärkungsgesetz / European Accessibility Act).
- Impressum und Datenschutzerklärung (falls ein öffentlicher Bereich existiert).

---

## 4. Funktionale Anforderungen

### 4.1 Datenerfassung (Ingestion Service)

| ID | Anforderung | Priorität |
| --- | --- | --- |
| FR-ING-01 | Empfang von Fahrzeug-GPS-Telemetrie (lat, lon, Geschwindigkeit, Fahrtrichtung, Zeit, Genauigkeit) – REST (Batch) und WebSocket/MQTT (Stream) | Must |
| FR-ING-02 | Fahrer-Schichtstatus (Schichtbeginn/-ende, Pause, verbleibende Lenkzeit) | Must |
| FR-ING-03 | Lagerstatus: Ladungsvolumen/-gewicht, Rampenbelegung, Warteschlange, Öffnungszeiten | Must |
| FR-ING-04 | Transportaufträge: Be-/Entladeadresse, Zeitfenster, Volumen, Gewicht, Sonderanforderungen | Must |
| FR-ING-05 | Datenvalidierung (JSON Schema/Pydantic), Idempotenz (`Idempotency-Key`), Filterung von Duplikaten | Must |
| FR-ING-06 | Externe Integrationen: **SAP TM/EWM**, WMS/TMS, **EDI (EDIFACT/IFTMIN)**-Adapter (Plug-in-Architektur) | Should |
| FR-ING-07 | Adapter für Telematik-Anbieter (FMS-Standard, z. B. Webfleet, Trimble) | Should |
| FR-ING-08 | Dead-Letter-Queue und Nachverarbeitung für fehlerhafte/verspätete Daten | Must |
| FR-ING-09 | Integration von Verkehrsdaten-Anbietern (HERE/TomTom oder offene Quellen, z. B. Autobahn-GmbH-API) | Should |

**API-Regeln:** OpenAPI 3.1; Versionierung (`/api/v1`); Fehlerformat nach RFC 7807 (Problem Details); Paginierung; Rate Limiting; alle Endpunkte per OAuth2/JWT geschützt.

Beispielhafte Endpunkte:

```
POST /api/v1/telemetry/positions      # GPS-Batch
POST /api/v1/drivers/{id}/shift-events
PUT  /api/v1/warehouses/{id}/status
POST /api/v1/orders
GET  /api/v1/routes?status=active
POST /api/v1/optimizations            # manuelle Neuberechnung
GET  /api/v1/alerts?severity=high
WS   /ws/v1/live                      # Dashboard-Stream
```

### 4.2 Optimierungs-Engine (Optimization Engine)

**Problemtyp:** Dynamic Capacitated VRP with Time Windows, Pickup & Delivery, heterogene Flotte, Fahrerzeit-Restriktionen (DVRPTW / PDPTW).

| ID | Anforderung | Priorität |
| --- | --- | --- |
| FR-OPT-01 | **Google OR-Tools** (Routing Library + CP-SAT) als primärer Solver; Startlösung + Guided-Local-Search-Metaheuristik | Must |
| FR-OPT-02 | Zielfunktion (mit konfigurierbaren Gewichten): Distanz, Kraftstoff, Maut, Zeit, Verspätungsstrafe, CO₂, Minimierung der Fahrzeuganzahl | Must |
| FR-OPT-03 | Nebenbedingungen: Kapazität (kg/m³), Zeitfenster, Lenk- und Ruhezeiten (3.3), Sonntagsfahrverbot (3.4), Fahrzeugtyp/Emissionsklasse, Rampen-Slots | Must |
| FR-OPT-04 | **Inkrementelle Re-Optimierung** (Rolling Horizon): nur betroffene Touren werden neu berechnet; minimale Abweichung vom bestehenden Plan (Stabilisierung) | Must |
| FR-OPT-05 | Distanz-/Zeitmatrix auf Basis des realen Straßennetzes: **OSRM / Valhalla / GraphHopper** (OSM-basiert, Self-Hosted, Lkw-Profil) | Must |
| FR-OPT-06 | ML-Modell zur Prognose der Ankunftszeit (ETA) (scikit-learn / Gradient Boosting) unter Berücksichtigung historischer Geschwindigkeiten sowie Tageszeit und Wochentag | Should |
| FR-OPT-07 | Hyperparameter-Tuning mit **Optuna** (offline); Ergebnisse werden in MLflow nachverfolgt | Should |
| FR-OPT-08 | Reinforcement Learning (z. B. Attention-basiertes RL) – **Forschungsphase (R&D)**; Produktivbetrieb erst, wenn nachgewiesen besser als OR-Tools | Could |
| FR-OPT-09 | Genetic Algorithm und weitere Metaheuristiken werden über eine Solver-Schnittstelle (*Strategy Pattern*) als Benchmark angebunden | Could |
| FR-OPT-10 | **Shadow Mode:** Der neue Algorithmus rechnet parallel zum laufenden Plan; Ergebnisse werden verglichen, aber nicht angewendet | Should |
| FR-OPT-11 | Entscheidungserklärung: Begründung für jede Änderung (z. B. „Unfall auf A7 → +18 Min.“) sowie Darstellung von Einsparung/Verschlechterung | Must |
| FR-OPT-12 | Der Disponent kann Pläne manuell bestätigen, ändern oder ablehnen (Auto-Apply-Modus konfigurierbar) | Must |
| FR-OPT-13 | Solver-Zeitlimit (konfigurierbar, Standard 5–10 s) und Rückgabe der „bisher besten“ Lösung | Must |

**Begründung der Algorithmuswahl:** OR-Tools ist branchenerprobt, deterministisch und gut erklärbar; RL kann bei harten rechtlichen Nebenbedingungen derzeit noch keine Garantien bieten. Daher ein Hybrid-Ansatz: *OR-Tools (Basis) + ML (ETA-/Bedarfsprognose) + RL (R&D)*.

### 4.3 Live-Dashboard (Analytics UI)

| ID | Anforderung | Priorität |
| --- | --- | --- |
| FR-UI-01 | Interaktive Karte (**MapLibre GL JS** + OpenStreetMap-Vektorkacheln; selbst gehosteter Tile-Server oder Mapbox) | Must |
| FR-UI-02 | Echtzeit-Bewegung der Fahrzeuge (Animation, Fahrtrichtung, Statusfarbe: unterwegs/wartend/verspätet/Pause) | Must |
| FR-UI-03 | Auslastung der Lager (Rampenbelegung, Wartezeit) – Heatmap/Indikator | Must |
| FR-UI-04 | Tourdetails: Stopps, ETA, verbleibende Lenkzeit, Ladungsauslastung | Must |
| FR-UI-05 | Alert-Center: Filtern, Quittieren (Acknowledge), Historie | Must |
| FR-UI-06 | „Was-wäre-wenn“-Simulation (What-if): Auswirkung eines neuen Auftrags oder einer gesperrten Straße | Should |
| FR-UI-07 | KPI-Panel: Kraftstoff, km, OTD, CO₂, Einsparung in % (gegenüber Baseline) | Must |
| FR-UI-08 | Gantt-/Timeline-Ansicht (Fahrzeug × Zeit) | Should |
| FR-UI-09 | Rollen: Admin, Disponent, Viewer, Datenschutzbeauftragter (Audit-Einsicht) | Must |
| FR-UI-10 | Dark-/Light-Mode, Tastaturnavigation, WCAG 2.1 AA | Should |

### 4.4 Alerting-System

| ID | Anforderung | Priorität |
| --- | --- | --- |
| FR-ALR-01 | Erkennung von Ereignissen: Stau (ETA-Abweichung > Schwellwert), Unfall/Straßensperrung (Verkehrs-API), Fahrzeugpanne, Lagerüberlastung, drohendes Ende der Arbeitszeit, drohende Zeitfensterverletzung | Must |
| FR-ALR-02 | Ereignis → **automatische Neuberechnung** → neuen Plan vorschlagen oder anwenden (konfigurierbar) | Must |
| FR-ALR-03 | Benachrichtigungskanäle: Dashboard, E-Mail (SMTP), Webhook, Slack/MS Teams; später SMS/Push | Must |
| FR-ALR-04 | Alert-Stufen (Info/Warning/Critical), Eskalationsregeln, Zusammenfassung wiederholter Alerts (Deduplizierung) | Should |
| FR-ALR-05 | Regelkonfiguration über die UI (Schwellwerte, Verspätungsminuten) | Should |
| FR-ALR-06 | Alle Alerts und automatischen Entscheidungen werden im Audit-Log gespeichert | Must |

---

## 5. Nichtfunktionale Anforderungen

| Kategorie | Anforderung |
| --- | --- |
| **Performance** | Ingest von 1.000 Fahrzeugen × 1 Position/5 s (≈ 200 Nachrichten/s); ≥ 500 gleichzeitige Dashboard-Sitzungen per WebSocket |
| **Skalierbarkeit** | Services skalieren horizontal (stateless); Optimizer-Worker skalieren über eine Warteschlange |
| **Zuverlässigkeit** | At-least-once-Zustellung, idempotente Consumer, Graceful Degradation (Ausfall der Verkehrs-API → Weiterbetrieb mit historischen Geschwindigkeiten) |
| **Sicherheit** | OAuth2/OIDC (Keycloak oder Kunden-IdP, SAML/SSO), RBAC, TLS 1.2+, mTLS zwischen Services (Prod), Secrets in Vault/Docker Secrets, OWASP ASVS L2, Verschlüsselung ruhender Daten (at rest) |
| **Observability** | OpenTelemetry (Trace/Metrics/Logs), Prometheus + Grafana, strukturierte JSON-Logs, Health-/Readiness-Endpunkte |
| **Audit** | Unveränderliches Audit-Log (wer, was, wann) |
| **Backup** | PostgreSQL PITR, tägliches Backup, RPO ≤ 15 Min., RTO ≤ 2 Std. |
| **Kompatibilität** | Moderne Browser (Chrome, Firefox, Edge, Safari – jeweils die letzten 2 Versionen) |
| **Codequalität** | Testabdeckung ≥ 80 %, statische Analyse (Linter, Typprüfung), SemVer |

---

## 6. Systemarchitektur

### 6.1 Gesamtüberblick (modularer Microservice-Ansatz)

```
[Telematik/ERP/WMS] → [Ingestion Service (FastAPI)] → [Message Broker: Redis Streams / Kafka*]
                                                             │
                         ┌───────────────────────────────────┼─────────────────────┐
                         ▼                                   ▼                     ▼
              [Optimization Engine]               [Alert/Event Service]      [PostgreSQL + PostGIS]
           (OR-Tools, ML, Routing-Engine)        (Regelwerk, Benachr.)        (+ TimescaleDB optional)
                         │                                   │
                         └──────────────► [API Gateway / BFF] ◄────────────────┘
                                                   │ REST + WebSocket
                                                   ▼
                                      [Analytics UI (React + MapLibre)]
```

\*Redis Streams für kleine Installationen; Kafka (Redpanda) für große Kunden.

### 6.2 Services

| Service | Verantwortung | Technologie |
| --- | --- | --- |
| `ingestion-service` | Empfang, Validierung, Normalisierung, Schreiben in den Broker | Python 3.12, FastAPI, Pydantic v2 |
| `optimization-engine` | Routenberechnung, ETA-Modell, Re-Optimierung | Python, OR-Tools, scikit-learn, Optuna |
| `routing-engine` | Straßennetz, Distanz-/Zeitmatrizen (Lkw-Profil) | OSRM oder Valhalla (OSM-Germany-Extract) |
| `alert-service` | Ereigniserkennung, Regeln, Benachrichtigungen | Python, FastAPI |
| `api-gateway` (BFF) | Authentifizierung, REST/WS-Aggregation | FastAPI |
| `analytics-ui` | Dashboard | React 18 + TypeScript, Vite, MapLibre GL, TanStack Query, i18next |
| `postgres` | Datenbank | PostgreSQL 16 + PostGIS 3 |
| `broker` | Ereignisbus | Redis 7 (Streams) / Kafka |
| `observability` | Metriken und Logs | Prometheus, Grafana, Loki, OTel Collector |
| `keycloak` (optional) | Identity | Keycloak |

### 6.3 Architekturprinzipien

- Ereignisgesteuert (Event-Driven), **leichtes CQRS** (getrennte Schreib- und Lesemodelle, wo sinnvoll).
- Jeder Service besitzt ein eigenes Schema (Vermeidung des Shared-DB-Anti-Patterns: eine PostgreSQL-Instanz, mehrere Schemata).
- **Strategy Pattern** für Solver; Austausch des Algorithmus per Konfiguration.
- 12-Factor-App; Konfiguration über Umgebungsvariablen.
- Architekturentscheidungen werden als **ADR (Architecture Decision Records)** in `docs/adr/` geführt.
- Dokumentation: **arc42**-Vorlage + C4-Diagramme (in deutschen Unternehmen weit verbreitet).

---

## 7. Datenmodell (konzeptionell)

**Zentrale Tabellen (mit PostGIS-Typen):**

| Tabelle | Wichtige Felder |
| --- | --- |
| `vehicles` | id, plate (pseudonymisiert), type, max\_weight\_kg, max\_volume\_m3, height\_m, emission\_class, fuel\_type, consumption\_l\_100km, depot\_id |
| `drivers` | id (UUID), qualification (ADR usw.), employment\_status |
| `driver_shifts` | id, driver\_id, vehicle\_id, start\_ts, end\_ts, driven\_minutes, break\_minutes, weekly\_driven\_minutes |
| `warehouses` | id, name, `geom GEOGRAPHY(Point,4326)`, opening\_hours, ramp\_count, capacity\_m3 |
| `warehouse_status` | warehouse\_id, ts, load\_m3, occupied\_ramps, queue\_length, wait\_minutes |
| `orders` | id, pickup\_location, delivery\_location (`geom`), time\_window\_start/end, weight\_kg, volume\_m3, priority, status |
| `vehicle_positions` | vehicle\_id, ts, `geom`, speed\_kmh, heading, accuracy\_m – **Hypertable/partitioniert**, GiST-Index |
| `routes` | id, vehicle\_id, plan\_version, status, total\_km, est\_fuel\_l, est\_co2\_kg, est\_toll\_eur |
| `route_stops` | route\_id, sequence, order\_id, eta, arrival\_actual, service\_minutes |
| `optimization_runs` | id, trigger (schedule/alert/manual), solver, params, duration\_ms, objective\_before/after, explanation JSONB |
| `alerts` | id, type, severity, entity\_ref, geom, created\_at, acked\_by, resolved\_at |
| `audit_log` | id, actor, action, entity, before/after JSONB, ts |

**Regeln:** Zeit – `timestamptz` (UTC); Indizes: GiST (räumlich), BRIN/B-Tree (Zeit); Migrationen mit **Alembic**; GPS-Partitionierung monatlich; Retention-Job gemäß 3.1.

---

## 8. Technologie-Stack (finale Empfehlung)

| Schicht | Auswahl | Begründung |
| --- | --- | --- |
| Backend | **Python 3.12 + FastAPI** (asynchron, automatische OpenAPI) | Eine Sprache für OR-Tools/ML |
| KI/ML | OR-Tools, scikit-learn, Optuna, MLflow, pandas/NumPy | Industriestandard |
| Routing | OSRM oder Valhalla/GraphHopper (OSM, Germany-Extract, Lkw-Profil) | Self-Hosted, DSGVO-konform, keine Lizenzkosten |
| Frontend | **React + TypeScript**, MapLibre GL, Vite | Weit verbreitet, hohe Nachfrage im deutschen Markt |
| Datenbank | **PostgreSQL 16 + PostGIS** (+ TimescaleDB optional) | Gemäß Vorgabe |
| Broker | Redis Streams → Kafka (Skalierung) | Schrittweise |
| Container | Docker, Docker Compose; später Kubernetes/Helm | Gemäß Vorgabe |
| CI/CD | GitHub Actions | Gemäß Vorgabe |
| Qualität | Ruff, mypy, pytest, ESLint, Prettier, Vitest, Playwright |  |
| Sicherheit | Trivy, Bandit, pip-audit/npm audit, Dependabot, CodeQL, gitleaks |  |

---

## 9. Deployment und CI/CD

### 9.1 Docker und lokaler Start

- Für jeden Service ein **Multi-Stage-Dockerfile**, Non-Root-User, minimales Image (`python:3.12-slim`), `HEALTHCHECK`.
- `docker-compose.yml` – die vollständige Umgebung startet mit **einem einzigen Befehl**: `docker compose up --build`.
- `docker-compose.override.yml` (Dev: Hot Reload), `docker-compose.prod.yml`.
- **Seed-/Demodaten** und ein **GPS-Simulator** (`simulator`): erzeugt synthetische Fahrzeuge und Aufträge im deutschen Raum (z. B. Korridor Hamburg–Berlin–München), sodass die Demo sofort lauffähig ist.
- `.env.example`, `Makefile` (`make up`, `make test`, `make lint`, `make seed`).
- Beim ersten Start wird ein OSM-Extract geladen (z. B. Geofabrik „Germany“ oder kleiner „Hamburg“) – für die Demo ist standardmäßig die kleinere Region voreingestellt.

### 9.2 GitHub-Actions-Pipeline

| Stufe | Inhalt |
| --- | --- |
| **Lint & Typprüfung** | Ruff, mypy, ESLint, tsc |
| **Unit-Tests** | pytest (≥ 80 % Abdeckung), Vitest |
| **Integrationstests** | `docker compose` mit PostgreSQL/PostGIS + Redis; API-Vertragstests (Schemathesis/OpenAPI) |
| **Optimizer-Benchmark** | Standard-VRPTW-Datensätze (Solomon) und synthetische DE-Szenarien; bei Regression wird die Pipeline rot |
| **E2E** | Playwright (Login → Karte → Alert → Neuberechnung) |
| **Security** | CodeQL, Trivy (Image + Abhängigkeiten), gitleaks, SBOM (CycloneDX) |
| **Build & Publish** | Docker-Images nach GHCR (Tags: `sha`, `semver`) |
| **Deploy (Staging)** | main-Branch → automatisch; Produktion – manuelle Freigabe (Environment Protection) |

Branch-Strategie: Trunk-Based oder GitHub Flow; Pflicht-Review für Pull Requests, Status-Checks, Conventional Commits.

---

## 10. Teststrategie

- **Unit:** Prüfung der Nebenbedingungen (Ruhezeiten, Sonntagsfahrverbot), ETA-Berechnung, Validierung.
- **Integration:** Kette Ingestion → Broker → Optimizer → DB; PostGIS-Abfragen.
- **Property-Based-Tests (Hypothesis):** Kapazitäts- oder Arbeitszeitgrenzen werden nie verletzt.
- **Optimizer-Qualitätstests:** Vergleich mit der Baseline (Greedy), Bericht über die Einsparung in %.
- **Lasttests (k6/Locust):** 200 Nachrichten/s Ingest, 500 WS-Sitzungen.
- **Chaos-/Fehlertests:** Ausfall der Verkehrs-API, Neustart des Brokers.
- **Sicherheit:** OWASP-ZAP-Baseline-Scan.

---

## 11. Lieferumfang (Deliverables)

1. Quellcode (Monorepo) und README (Startanleitung auf Deutsch/Englisch).
2. OpenAPI-Spezifikation und Postman-/Bruno-Collection.
3. arc42-Architekturdokumentation + C4-Diagramme + ADRs.
4. DSGVO-Paket: VVT-Vorlage, TOM-Liste, DSFA-Entwurf, Löschkonzept.
5. Algorithmus-Dokumentation: Modell, Zielfunktion, Nebenbedingungen, Benchmark-Ergebnisse.
6. Runbook (Betriebshandbuch), Monitoring-Dashboards.
7. Benutzerhandbuch (für Disponenten, auf Deutsch).
8. Demo-Video und Seed-Daten.

---

## 12. Projektphasen (Roadmap)

| Phase | Dauer | Ergebnis |
| --- | --- | --- |
| **0. Discovery** | 2 Wochen | Anforderungen, KPI-Baseline, DSGVO-/Betriebsrat-Analyse, ADRs |
| **1. Foundation (MVP-Core)** | 4 Wochen | Repo, Docker Compose, CI, DB-Schema, Ingestion-API, Simulator |
| **2. Optimizer v1** | 4 Wochen | OR-Tools VRPTW, Routing-Engine, Nebenbedingungen (3.3–3.4), Benchmark |
| **3. Dashboard v1** | 4 Wochen | Karte, Live-Bewegung, Lagerstatus, KPIs |
| **4. Alerts & Re-Optimierung** | 3 Wochen | Ereigniserkennung, automatische Neuberechnung, Benachrichtigungen |
| **5. Hardening** | 3 Wochen | Sicherheit, Lasttests, Dokumentation, Pilotreife |
| **6. Pilot (Shadow Mode)** | 6–8 Wochen | Bestätigung des 15-%-Ziels mit realen Daten |
| **7. R&D (parallel)** | laufend | ML-ETA, RL-Experimente |

---

## 13. Abnahmekriterien (Acceptance Criteria)

1. Nach `docker compose up` ist das Dashboard innerhalb von ≤ 5 Minuten unter `http://localhost:3000` erreichbar und zeigt Simulationsdaten.
2. Im Testszenario mit 50 Fahrzeugen / 200 Aufträgen erzielt der Optimizer gegenüber der Baseline **mindestens 10 %** (Ziel 15 %) Einsparung bei Kraftstoff/Zeit – belegt durch einen Benchmark-Bericht.
3. Bei einem simulierten Unfallereignis erscheint der Alert innerhalb von ≤ 5 s und ein neuer Plan wird innerhalb von ≤ 10 s vorgeschlagen.
4. Keine erzeugte Route verletzt die Vorgaben der VO (EG) 561/2006 oder das Sonntagsfahrverbot (durch automatisierte Tests nachgewiesen).
5. Die GitHub-Actions-Pipeline ist in allen Stufen grün; Abdeckung ≥ 80 %; keine kritischen Schwachstellen.
6. DSGVO-Dokumentenpaket sowie Retention-/Löschfunktion sind vorhanden und getestet.
7. Die UI funktioniert vollständig auf Deutsch und Englisch.

---

## 14. Risiken und Gegenmaßnahmen

| Risiko | Auswirkung | Gegenmaßnahme |
| --- | --- | --- |
| 15-%-Ziel wird nicht erreicht (Baseline bereits gut) | Hoch | Baseline-Analyse vor dem Pilot; Ziel als realistische Spanne (10–15 %) festlegen |
| Echtzeit-Berechnung zu langsam (große Probleme) | Mittel | Rolling Horizon, Zoneneinteilung (Clustering), Zeitlimit, Dekomposition |
| DSGVO-/Betriebsrat-Hürden | Hoch | Frühzeitige Abstimmung, Pseudonymisierung, Deaktivierung individueller KPIs |
| Kosten/Lizenzen für Verkehrsdaten | Mittel | Abstraktionsschicht; offene Quellen + Wechsel zu kostenpflichtigem Anbieter möglich |
| Qualität des OSM-Routings (Lkw-Beschränkungen unvollständig) | Mittel | Zusätzliche Restriktionsebene, vom Kunden bestätigte „Sperrzonen“ |
| Instabilität des RL-Modells | Mittel | Nur R\&D; im Produktivbetrieb bleibt OR-Tools die Basis |

---

## 15. Anhang: Monorepo-Struktur (Empfehlung)

```
logistics-scheduler/
├── services/
│   ├── ingestion/
│   ├── optimizer/
│   ├── alerts/
│   ├── gateway/
│   └── simulator/
├── frontend/            # React + MapLibre
├── infra/
│   ├── docker/  ├── routing/  └── observability/
├── db/migrations/       # Alembic
├── docs/
│   ├── arc42/  ├── adr/  ├── dsgvo/  └── api/
├── .github/workflows/   # ci.yml, security.yml, release.yml
├── docker-compose.yml
├── Makefile
└── README.md
```

---

**Hinweis:** Dieses Dokument wird in der Discovery-Phase gemeinsam mit dem Kunden präzisiert. Rechtliche Abschnitte (DSGVO, BetrVG, VO (EG) 561/2006) sollten von einer juristischen Fachperson geprüft werden.
