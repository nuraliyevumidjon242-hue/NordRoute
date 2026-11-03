let authConfig = null;
let oidcDiscovery = null;
let mapInstance = null;
let mapReady = false;
const translations = {
  de: {
    workspace:"LEITSTELLE",overview:"Übersicht",fleet:"Flotte",orders:"Aufträge",routes:"Routen",alerts:"Meldungen",
    privacy:"Datenschutzmodus aktiv",dispatcher:"Disposition",live:"LIVE",controlCenter:"CONTROL CENTER · DEUTSCHLAND",
    heading:"Guten Tag, Leitstelle",headingNote:"Hier ist die Lage Ihrer Flotte in Echtzeit.",optimize:"Routen optimieren",
    fleetMap:"Flottenübersicht",livePositions:"Live-Positionen in Deutschland",allVehicles:"Alle Fahrzeuge",moving:"Unterwegs",
    waiting:"Wartend",break:"Pause",attention:"Aufmerksamkeit",activeNotifications:"Aktive Meldungen",
    allNotifications:"Alle Meldungen ansehen",recentOrders:"Aktuelle Aufträge",orderOverview:"Auftragsübersicht des heutigen Tages",
    allOrders:"Alle Aufträge",warehouses:"Lagerauslastung",rampOccupancy:"Rampenauslastung in Echtzeit",
    demoDisclaimer:"Demo-Daten · Keine produktive Rechts- oder Routenfreigabe",vehicles:"Fahrzeuge unterwegs",
    openOrders:"Offene Aufträge",distance:"Geplante Distanz",fuel:"Kraftstoff (geschätzt)",onTime:"Termintreue",
    vsBaseline:"gegenüber Baseline",today:"heute",route:"Route",vehicle:"Fahrzeug",status:"Status",priority:"Priorität",capacity:"Kapazität",
    delivery:"Zustellung",due:"Zeitfenster",origin:"Start",destination:"Ziel",acknowledge:"Quittieren",acked:"Quittiert",
    level:"Stufe",event:"Ereignis",time:"Zeit",actions:"Aktion",confirm:"Bestätigen",reject:"Ablehnen",
    suggested:"Vorgeschlagen",active:"Aktiv",assigned:"Zugewiesen",open:"Offen",normal:"Normal",high:"Hoch",critical:"Kritisch",
    warning:"Warnung",info:"Info",noAlerts:"Keine offenen Meldungen.",noOrders:"Keine Aufträge vorhanden.",
    noRoutes:"Noch keine Routenvorschläge. Optimieren Sie, um Vorschläge zu erstellen.",optimizationDone:"Routenberechnung abgeschlossen.",
    optimizationError:"Optimierung fehlgeschlagen: ",loadError:"Daten konnten nicht geladen werden: ",
    routeDecision:"Routenentscheidung gespeichert.",lastUpdated:"Aktualisiert",ramps:"Rampen",queue:"Warteschlange",
    online:"Online",mapCaption:"SCHEMATISCHE KARTE · NICHT NAVIGIERBAR",demand:"Aufträge in Planung",
    distanceNote:"geschätzte km · aktive Routen",fuelNote:"l · Modellschätzung",otdNote:"Ziel ≥ 95 %",
    vehicleMap:"Fahrzeuge",ordersView:"Aufträge",routesView:"Routenvorschläge",alertsView:"Meldungshistorie",
    footprint:"Geschätzte CO₂-Emissionen",saving:"Einsparung vs. Baseline",unassigned:"nicht zugewiesen",
    disclaimer:"Hinweis: Demo-Optimierung mit Luftlinien-Näherung; keine Straßennetz-, Maut- oder Rechtsprüfung.",
    breakTime:"Pausenmin.",signIn:"Anmelden",signOut:"Abmelden",traffic:"Echtzeitverkehr",
    mapUnavailable:"Kartenstil konnte nicht geladen werden.",trafficUnavailable:"Echtzeitverkehr nicht verfügbar",
    trafficLive:"TomTom live",admin:"Administration",viewer:"Nur ansehen",dpo:"Datenschutz"
  },
  en: {
    workspace:"DISPATCH",overview:"Overview",fleet:"Fleet",orders:"Orders",routes:"Routes",alerts:"Alerts",
    privacy:"Privacy mode active",dispatcher:"Dispatcher",live:"LIVE",controlCenter:"CONTROL CENTER · GERMANY",
    heading:"Good day, dispatch",headingNote:"Here is your fleet situation in real time.",optimize:"Optimize routes",
    fleetMap:"Fleet overview",livePositions:"Live positions in Germany",allVehicles:"All vehicles",moving:"On route",
    waiting:"Waiting",break:"Break",attention:"Needs attention",activeNotifications:"Active notifications",
    allNotifications:"View all alerts",recentOrders:"Recent orders",orderOverview:"Today's order overview",
    allOrders:"All orders",warehouses:"Warehouse capacity",rampOccupancy:"Live dock occupancy",
    demoDisclaimer:"Demo data · Not for production routing or legal clearance",vehicles:"Vehicles on route",
    openOrders:"Open orders",distance:"Planned distance",fuel:"Fuel (estimated)",onTime:"On-time delivery",
    vsBaseline:"vs. baseline",today:"today",route:"Route",vehicle:"Vehicle",status:"Status",priority:"Priority",capacity:"Capacity",
    delivery:"Delivery",due:"Time window",origin:"Origin",destination:"Destination",acknowledge:"Acknowledge",acked:"Acknowledged",
    level:"Level",event:"Event",time:"Time",actions:"Action",confirm:"Confirm",reject:"Reject",
    suggested:"Suggested",active:"Active",assigned:"Assigned",open:"Open",normal:"Normal",high:"High",critical:"Critical",
    warning:"Warning",info:"Info",noAlerts:"No active alerts.",noOrders:"No orders available.",
    noRoutes:"No route suggestions yet. Run optimization to create a proposal.",optimizationDone:"Route optimization completed.",
    optimizationError:"Optimization failed: ",loadError:"Could not load data: ",
    routeDecision:"Route decision saved.",lastUpdated:"Updated",ramps:"Docks",queue:"Queue",
    online:"Online",mapCaption:"SCHEMATIC MAP · NOT FOR NAVIGATION",demand:"Orders in planning",
    distanceNote:"estimated km · active routes",fuelNote:"L · model estimate",otdNote:"Target ≥ 95 %",
    vehicleMap:"Vehicles",ordersView:"Orders",routesView:"Route proposals",alertsView:"Alert history",
    footprint:"Estimated CO₂ emissions",saving:"Savings vs. baseline",unassigned:"unassigned",
    disclaimer:"Note: demo optimizer uses straight-line estimates; no road network, toll or legal checks.",
    breakTime:"Break min",signIn:"Sign in",signOut:"Sign out",traffic:"Live traffic",
    mapUnavailable:"Map style could not be loaded.",trafficUnavailable:"Live traffic unavailable",
    trafficLive:"TomTom live",admin:"Administrator",viewer:"Read only",dpo:"Data protection"
  },
  uz: {
    workspace:"DISPECHERLIK",overview:"Umumiy ko‘rinish",fleet:"Transportlar",orders:"Buyurtmalar",routes:"Yo‘nalishlar",alerts:"Ogohlantirishlar",
    privacy:"Maxfiylik rejimi yoqilgan",dispatcher:"Dispetcher",live:"JONLI",controlCenter:"BOSHQARUV MARKAZI · GERMANIYA",
    heading:"Xayrli kun, dispetcher",headingNote:"Transportlar holati real vaqt rejimida.",optimize:"Yo‘nalishlarni optimallashtirish",
    fleetMap:"Transportlar holati",livePositions:"Germaniya bo‘ylab jonli joylashuv",allVehicles:"Barcha transportlar",moving:"Harakatda",
    waiting:"Kutmoqda",break:"Tanaffus",attention:"Diqqat talab qiladi",activeNotifications:"Faol bildirishnomalar",
    allNotifications:"Barcha ogohlantirishlar",recentOrders:"So‘nggi buyurtmalar",orderOverview:"Bugungi buyurtmalar",
    allOrders:"Barcha buyurtmalar",warehouses:"Ombor bandligi",rampOccupancy:"Yuklash joylari bandligi",
    demoDisclaimer:"Demo ma’lumotlari · Ishlab chiqarish uchun huquqiy/routing tasdig‘i emas",vehicles:"Harakatdagi transportlar",
    openOrders:"Ochiq buyurtmalar",distance:"Rejalashtirilgan masofa",fuel:"Yoqilg‘i (taxminiy)",onTime:"O‘z vaqtida yetkazish",
    vsBaseline:"bazaviy rejaga nisbatan",today:"bugun",route:"Yo‘nalish",vehicle:"Transport",status:"Holati",priority:"Muhimlik",capacity:"Sig‘im",
    delivery:"Yetkazish",due:"Vaqt oralig‘i",origin:"Jo‘natish",destination:"Manzil",acknowledge:"Tasdiqlash",acked:"Tasdiqlandi",
    level:"Daraja",event:"Hodisa",time:"Vaqt",actions:"Amal",confirm:"Tasdiqlash",reject:"Rad etish",
    suggested:"Taklif qilindi",active:"Faol",assigned:"Taqsimlangan",open:"Ochiq",normal:"Oddiy",high:"Yuqori",critical:"Jiddiy",
    warning:"Ogohlantirish",info:"Ma’lumot",noAlerts:"Faol ogohlantirish yo‘q.",noOrders:"Buyurtmalar mavjud emas.",
    noRoutes:"Yo‘nalish takliflari yo‘q. Taklif yaratish uchun optimallashtiring.",optimizationDone:"Yo‘nalishlar hisoblandi.",
    optimizationError:"Optimallashtirish xatosi: ",loadError:"Ma’lumotlarni yuklab bo‘lmadi: ",
    routeDecision:"Yo‘nalish qarori saqlandi.",lastUpdated:"Yangilandi",ramps:"Yuklash joylari",queue:"Navbat",
    online:"Tarmoqda",mapCaption:"SXEMATIK XARITA · NAVIGATSIYA UCHUN EMAS",demand:"Rejadagi buyurtmalar",
    distanceNote:"taxminiy km · faol yo‘nalishlar",fuelNote:"l · model taxmini",otdNote:"Maqsad ≥ 95 %",
    vehicleMap:"Transportlar",ordersView:"Buyurtmalar",routesView:"Yo‘nalish takliflari",alertsView:"Ogohlantirishlar tarixi",
    footprint:"Taxminiy CO₂ chiqindisi",saving:"Bazaviy rejaga nisbatan tejam",unassigned:"taqsimlanmadi",
    disclaimer:"Eslatma: demo optimizatsiyasi taxminiy masofaga asoslangan; yo‘l, boj va qonunlar tekshirilmaydi.",
    breakTime:"Tanaffus daq.",signIn:"Kirish",signOut:"Chiqish",traffic:"Jonli trafik",
    mapUnavailable:"Xarita uslubini yuklab bo‘lmadi.",trafficUnavailable:"Jonli trafik mavjud emas",
    trafficLive:"TomTom jonli",admin:"Administrator",viewer:"Faqat ko‘rish",dpo:"Ma’lumotlarni himoya qilish"
  }
};

let language = localStorage.getItem("nordroute-language") || "de";
let dashboard = null;
let currentView = "overview";
let noticeTimer;
let latestVehicles = [];
let latestRoutes = [];
let liveTraffic = {type:"FeatureCollection",features:[]};
const t = key => translations[language]?.[key] || translations.de[key] || key;
const esc = value => String(value ?? "").replace(/[&<>"']/g, char => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[char]));
const number = (value, digits=0) => value==null?"—":new Intl.NumberFormat(language === "de" ? "de-DE" : language === "uz" ? "uz-UZ" : "en-GB",{maximumFractionDigits:digits,minimumFractionDigits:digits}).format(value);
const stamp = value => new Intl.DateTimeFormat(language === "de" ? "de-DE" : language === "uz" ? "uz-UZ" : "en-GB",{hour:"2-digit",minute:"2-digit",timeZone:"Europe/Berlin"}).format(new Date(value));
const formatDue = value => {
  const date=new Date(value);
  return Number.isNaN(date.getTime())?esc(value):esc(new Intl.DateTimeFormat(language==="de"?"de-DE":language==="uz"?"uz-UZ":"en-GB",{day:"2-digit",month:"2-digit",hour:"2-digit",minute:"2-digit",timeZone:"Europe/Berlin"}).format(date));
};

function base64Url(bytes) {
  let binary="";
  bytes.forEach(byte=>{binary+=String.fromCharCode(byte);});
  return btoa(binary).replace(/\+/g,"-").replace(/\//g,"_").replace(/=+$/,"");
}
function tokenClaims(token=sessionStorage.getItem("nordroute-access-token")) {
  if(!token)return null;
  try {
    const payload=token.split(".")[1].replace(/-/g,"+").replace(/_/g,"/");
    return JSON.parse(new TextDecoder().decode(Uint8Array.from(atob(payload),char=>char.charCodeAt(0))));
  } catch { return null; }
}
async function loadOidcDiscovery() {
  if(!oidcDiscovery) {
    const response=await fetch(`${authConfig.oidc_issuer.replace(/\/$/,"")}/.well-known/openid-configuration`);
    if(!response.ok)throw new Error(`OIDC discovery returned HTTP ${response.status}`);
    oidcDiscovery=await response.json();
  }
  return oidcDiscovery;
}
function updateAuthControls() {
  const isOidc=authConfig?.auth_mode==="oidc";
  const claims=tokenClaims();
  document.getElementById("login-button").hidden=!isOidc||Boolean(claims);
  document.getElementById("logout-button").hidden=!isOidc||!claims;
  document.getElementById("user-name").textContent=claims?.preferred_username||claims?.name||"—";
  const roles=claims?.realm_access?.roles||[];
  const role=roles.find(value=>["admin","dispatcher","viewer","dpo"].includes(value));
  document.getElementById("user-role").textContent=role?t(role):isOidc?"—":t("dispatcher");
  document.getElementById("optimize-button").hidden=isOidc&&(!roles.includes("admin")&&!roles.includes("dispatcher"));
}
function canDispatch() {
  if(authConfig?.auth_mode!=="oidc")return true;
  const roles=tokenClaims()?.realm_access?.roles||[];
  return roles.includes("admin")||roles.includes("dispatcher");
}
async function completeLoginRedirect() {
  const params=new URLSearchParams(location.search);
  if(params.has("error"))throw new Error(params.get("error_description")||params.get("error"));
  const code=params.get("code");
  if(!code)return;
  const state=params.get("state");
  const expected=sessionStorage.getItem("nordroute-oidc-state");
  const verifier=sessionStorage.getItem("nordroute-oidc-verifier");
  sessionStorage.removeItem("nordroute-oidc-state");
  sessionStorage.removeItem("nordroute-oidc-verifier");
  if(!state||!expected||state!==expected||!verifier)throw new Error("OIDC state or PKCE verification failed.");
  const discovery=await loadOidcDiscovery();
  const response=await fetch(discovery.token_endpoint,{
    method:"POST",
    headers:{"Content-Type":"application/x-www-form-urlencoded"},
    body:new URLSearchParams({
      grant_type:"authorization_code",
      client_id:authConfig.oidc_client_id,
      code,
      redirect_uri:`${location.origin}/`,
      code_verifier:verifier
    })
  });
  if(!response.ok)throw new Error(`OIDC token exchange returned HTTP ${response.status}`);
  const tokens=await response.json();
  sessionStorage.setItem("nordroute-access-token",tokens.access_token);
  if(tokens.refresh_token)sessionStorage.setItem("nordroute-refresh-token",tokens.refresh_token);
  if(tokens.id_token)sessionStorage.setItem("nordroute-id-token",tokens.id_token);
  history.replaceState(null,"",location.pathname);
}
async function startLogin() {
  const discovery=await loadOidcDiscovery();
  const random=new Uint8Array(64);
  crypto.getRandomValues(random);
  const verifier=base64Url(random);
  const state=base64Url(crypto.getRandomValues(new Uint8Array(32)));
  const challenge=base64Url(new Uint8Array(await crypto.subtle.digest("SHA-256",new TextEncoder().encode(verifier))));
  sessionStorage.setItem("nordroute-oidc-state",state);
  sessionStorage.setItem("nordroute-oidc-verifier",verifier);
  const url=new URL(discovery.authorization_endpoint);
  url.search=new URLSearchParams({
    client_id:authConfig.oidc_client_id,
    redirect_uri:`${location.origin}/`,
    response_type:"code",
    scope:"openid profile email",
    code_challenge:challenge,
    code_challenge_method:"S256",
    state
  });
  location.assign(url);
}
async function getAccessToken() {
  let accessToken=sessionStorage.getItem("nordroute-access-token");
  let claims=tokenClaims(accessToken);
  if(claims?.exp>Date.now()/1000+30)return accessToken;
  const refreshToken=sessionStorage.getItem("nordroute-refresh-token");
  if(!refreshToken)return null;
  const discovery=await loadOidcDiscovery();
  const response=await fetch(discovery.token_endpoint,{
    method:"POST",
    headers:{"Content-Type":"application/x-www-form-urlencoded"},
    body:new URLSearchParams({
      grant_type:"refresh_token",
      client_id:authConfig.oidc_client_id,
      refresh_token:refreshToken
    })
  });
  if(!response.ok) {
    sessionStorage.removeItem("nordroute-access-token");
    sessionStorage.removeItem("nordroute-refresh-token");
    sessionStorage.removeItem("nordroute-id-token");
    updateAuthControls();
    return null;
  }
  const tokens=await response.json();
  sessionStorage.setItem("nordroute-access-token",tokens.access_token);
  if(tokens.refresh_token)sessionStorage.setItem("nordroute-refresh-token",tokens.refresh_token);
  return tokens.access_token;
}
async function signOut() {
  const idToken=sessionStorage.getItem("nordroute-id-token");
  for(const key of ["nordroute-access-token","nordroute-refresh-token","nordroute-id-token"])sessionStorage.removeItem(key);
  updateAuthControls();
  if(idToken) {
    const discovery=await loadOidcDiscovery();
    const url=new URL(discovery.end_session_endpoint);
    url.search=new URLSearchParams({
      client_id:authConfig.oidc_client_id,
      id_token_hint:idToken,
      post_logout_redirect_uri:`${location.origin}/`
    });
    location.assign(url);
  } else location.reload();
}

function showNotice(message, error=false) {
  const box=document.getElementById("notice");
  box.textContent=message;
  box.hidden=false;
  box.classList.toggle("error",error);
  clearTimeout(noticeTimer);
  noticeTimer=setTimeout(()=>{box.hidden=true;},7000);
}
async function api(path,options={}) {
  const headers={"Content-Type":"application/json",...(options.headers||{})};
  if(authConfig?.auth_mode==="oidc") {
    const token=await getAccessToken();
    if(!token) {
      updateAuthControls();
      throw new Error(t("signIn"));
    }
    headers.Authorization=`Bearer ${token}`;
  } else if(authConfig?.api_key)headers["X-API-Key"]=authConfig.api_key;
  const response=await fetch(path,{...options,headers});
  if(!response.ok) {
    const body=await response.json().catch(()=>({}));
    if(response.status===401&&authConfig?.auth_mode==="oidc")updateAuthControls();
    throw new Error(body.detail?.title || body.title || `${response.status} ${response.statusText}`);
  }
  return response.status===204?null:response.json();
}
function setLanguage(code) {
  language=translations[code]?code:"de";
  localStorage.setItem("nordroute-language",language);
  document.documentElement.lang=language;
  document.getElementById("language").value=language;
  document.querySelectorAll("[data-i18n]").forEach(node=>{node.textContent=t(node.dataset.i18n);});
  const liveCount=liveTraffic.live_points||0;
  document.getElementById("traffic-status").textContent=liveCount?`● ${t("trafficLive")} · ${liveCount}`:`● ${t("trafficUnavailable")}`;
  document.getElementById("traffic-status").classList.toggle("live",liveCount>0);
  render();
}
function renderKpis(k) {
  const cards=[
    ["vehicles","▤",number(k.vehicles_active),t("online"),""],
    ["openOrders","▧",number(k.orders_open),t("demand"),""],
    ["distance","⌁",`${number(k.distance_km)} km`,t("distanceNote"),""],
    ["fuel","◉",`${number(k.fuel_l,1)} l`,t("fuelNote"),""],
    ["footprint","◌",`${number(k.co2_kg)} kg`,t("vsBaseline"),""],
    ["saving","↗",k.baseline_saving_percent==null?"—":`${number(k.baseline_saving_percent,1)}%`,t("vsBaseline"),"positive"],
    ["onTime","✓",k.otd_percent==null?"—":`${number(k.otd_percent,1)}%`,t("otdNote"),"positive"]
  ];
  document.getElementById("kpi-grid").innerHTML=cards.map(([label,icon,value,foot,style])=>
    `<article class="kpi-card"><div class="kpi-top"><span class="kpi-label">${esc(t(label))}</span><span class="kpi-icon">${icon}</span></div><div class="kpi-value">${esc(value)}</div><div class="kpi-foot ${style}">${esc(foot)}</div></article>`).join("");
}
function mapData() {
  return {
    vehicles:{
      type:"FeatureCollection",
      features:latestVehicles.map(vehicle=>({
        type:"Feature",
        geometry:{type:"Point",coordinates:[vehicle.lon,vehicle.lat]},
        properties:{label:vehicle.label,status:vehicle.status,speed:vehicle.speed_kmh,heading:vehicle.heading}
      }))
    },
    routes:{
      type:"FeatureCollection",
      features:latestRoutes.filter(route=>route.geometry?.type==="LineString"&&route.geometry.coordinates?.length>1).map(route=>({
        type:"Feature",
        geometry:route.geometry,
        properties:{vehicle:route.vehicle_id,status:route.status,orders:route.order_ids.join(", "),distance:route.distance_km}
      }))
    },
    traffic:liveTraffic
  };
}
function updateMapData() {
  if(!mapInstance||!mapReady)return;
  const data=mapData();
  mapInstance.getSource("fleet")?.setData(data.vehicles);
  mapInstance.getSource("routes")?.setData(data.routes);
  mapInstance.getSource("traffic")?.setData(data.traffic);
}
function renderMap(vehicles,routes) {
  latestVehicles=vehicles;
  latestRoutes=routes;
  if(!window.maplibregl) {
    document.getElementById("map").textContent=t("mapUnavailable");
    showNotice(t("mapUnavailable"),true);
    return;
  }
  if(!mapInstance) {
    mapInstance=new maplibregl.Map({
      container:"map",
      style:authConfig?.map_style_url,
      center:[10.45,51.1],
      zoom:5.2,
      minZoom:4,
      maxZoom:18,
      attributionControl:true
    });
    mapInstance.addControl(new maplibregl.NavigationControl({showCompass:true}),"top-right");
    mapInstance.on("load",()=>{
      mapInstance.addSource("traffic",{type:"geojson",data:{type:"FeatureCollection",features:[]}});
      mapInstance.addLayer({
        id:"traffic-lines",type:"line",source:"traffic",
        paint:{
          "line-color":["case",["==",["get","road_closure"],true],"#c83b3b",["<",["get","speed_ratio"],0.4],"#e74f50",["<",["get","speed_ratio"],0.7],"#e5a331","#20a577"],
          "line-width":5,"line-opacity":0.78
        }
      });
      mapInstance.addSource("routes",{type:"geojson",data:{type:"FeatureCollection",features:[]}});
      mapInstance.addLayer({
        id:"route-lines",type:"line",source:"routes",
        paint:{"line-color":["match",["get","status"],"aktiv","#218d70","#4969e9"],"line-width":4,"line-opacity":0.8}
      });
      mapInstance.addSource("fleet",{type:"geojson",data:{type:"FeatureCollection",features:[]}});
      mapInstance.addLayer({
        id:"fleet-points",type:"circle",source:"fleet",
        paint:{
          "circle-radius":["interpolate",["linear"],["zoom"],4,5,12,9],
          "circle-color":["match",["get","status"],"Pause","#8793a7","wartend","#edae45","#20ad7d"],
          "circle-stroke-color":"#fff","circle-stroke-width":2
        }
      });
      mapInstance.addLayer({
        id:"fleet-labels",type:"symbol",source:"fleet",
        layout:{"text-field":["get","label"],"text-size":10,"text-offset":[0,1.3],"text-anchor":"top","text-allow-overlap":false},
        paint:{"text-color":"#27344a","text-halo-color":"#ffffff","text-halo-width":1.5}
      });
      mapInstance.on("click","fleet-points",event=>{
        const properties=event.features?.[0]?.properties;
        if(!properties)return;
        new maplibregl.Popup({closeButton:true,offset:12})
          .setLngLat(event.lngLat)
          .setHTML(`<strong>${esc(properties.label)}</strong><br>${esc(properties.status)} · ${number(properties.speed)} km/h`)
          .addTo(mapInstance);
      });
      mapInstance.on("click","route-lines",event=>{
        const properties=event.features?.[0]?.properties;
        if(!properties)return;
        new maplibregl.Popup({closeButton:true,offset:10})
          .setLngLat(event.lngLat)
          .setHTML(`<strong>${esc(properties.vehicle)}</strong><br>${esc(properties.orders)}<br>${number(properties.distance,1)} km`)
          .addTo(mapInstance);
      });
      mapInstance.on("click","traffic-lines",event=>{
        const properties=event.features?.[0]?.properties;
        if(!properties)return;
        new maplibregl.Popup({closeButton:true,offset:10})
          .setLngLat(event.lngLat)
          .setHTML(`<strong>${esc(t("trafficLive"))}</strong><br>${number(properties.current_speed_kmh)} / ${number(properties.free_flow_speed_kmh)} km/h${properties.road_closure==="true"||properties.road_closure===true?`<br>${esc(t("critical"))}`:""}`)
          .addTo(mapInstance);
      });
      mapInstance.on("mouseenter","fleet-points",()=>{mapInstance.getCanvas().style.cursor="pointer";});
      mapInstance.on("mouseleave","fleet-points",()=>{mapInstance.getCanvas().style.cursor="";});
      mapInstance.on("mouseenter","route-lines",()=>{mapInstance.getCanvas().style.cursor="pointer";});
      mapInstance.on("mouseleave","route-lines",()=>{mapInstance.getCanvas().style.cursor="";});
      mapInstance.on("mouseenter","traffic-lines",()=>{mapInstance.getCanvas().style.cursor="pointer";});
      mapInstance.on("mouseleave","traffic-lines",()=>{mapInstance.getCanvas().style.cursor="";});
      mapReady=true;
      updateMapData();
    });
    mapInstance.on("error",event=>{
      if(event.error)console.error("Map rendering error",event.error);
    });
  }
  updateMapData();
}
function renderAlerts(alerts,limit=4) {
  const active=alerts.filter(a=>!a.acknowledged);
  document.getElementById("open-alert-count").textContent=active.length;
  document.getElementById("alert-count").textContent=active.length;
  const list=limit?active.slice(0,limit):alerts;
  if(!list.length)return `<div class="empty-state">${esc(t("noAlerts"))}</div>`;
  return list.map(a=>{
    const severity=a.severity==="critical"?"critical":a.severity==="warning"?"warning":"info";
    return `<div class="alert-item"><span class="alert-symbol ${severity}">${severity==="critical"?"!":severity==="warning"?"△":"i"}</span><div class="alert-copy"><strong>${esc(a.kind.toUpperCase())}</strong><p>${esc(a.message)}</p><div class="alert-meta"><span class="severity-pill ${severity}">${esc(t(severity))}</span><span>${stamp(a.created_at)}</span>${a.acknowledged?`<span>${esc(t("acked"))}</span>`:""}</div></div>${!a.acknowledged&&limit&&canDispatch()?`<button class="ack-button" data-ack="${esc(a.id)}">${esc(t("acknowledge"))}</button>`:""}</div>`;
  }).join("");
}
function statusPill(status) {
  const cls=status==="offen"?"open":status==="vorgeschlagen"?"suggested":"";
  const label=status==="offen"?t("open"):status==="vorgeschlagen"?t("suggested"):status==="aktiv"?t("active"):status==="zugewiesen"?t("assigned"):esc(status);
  return `<span class="status-pill ${cls}">${esc(label)}</span>`;
}
function vehicleStatusPill(status) {
  const label=status==="unterwegs"?t("moving"):status==="wartend"?t("waiting"):status==="Pause"?t("break"):status;
  const cls=status==="wartend"?"open":status==="Pause"?"paused":"";
  return `<span class="status-pill ${cls}">${esc(label)}</span>`;
}
function renderOrders(orders,limit=4) {
  if(!orders.length)return `<div class="empty-state">${esc(t("noOrders"))}</div>`;
  const rows=(limit?orders.slice(0,limit):orders).map(o=>`<tr><td class="order-id">${esc(o.id)}</td><td>${esc(o.pickup)} <span aria-hidden="true">→</span> ${esc(o.delivery)}</td><td>${number(o.weight_kg)} kg · ${esc(t(o.priority==="hoch"?"high":"normal"))}</td><td>${formatDue(o.due_at)}</td><td>${statusPill(o.status)}</td></tr>`).join("");
  return `<table class="data-table"><thead><tr><th>${esc(t("route"))}</th><th>${esc(t("origin"))} → ${esc(t("destination"))}</th><th>${esc(t("capacity"))} · ${esc(t("priority"))}</th><th>${esc(t("due"))}</th><th>${esc(t("status"))}</th></tr></thead><tbody>${rows}</tbody></table>`;
}
function renderWarehouses(items) {
  return items.map(w=>{
    const percentage=Math.round(w.occupied_ramps/w.ramp_count*100);
    const color=percentage>=80?"high":percentage>=60?"medium":"";
    return `<div class="warehouse-row"><div><div class="warehouse-name">${esc(w.name)}</div><div class="warehouse-city">${esc(w.city)}</div></div><div class="progress-track"><div class="progress-fill ${color}" style="width:${Math.min(percentage,100)}%"></div></div><span class="warehouse-percent">${percentage}%</span><span class="ramp-caption">${w.occupied_ramps}/${w.ramp_count} ${esc(t("ramps"))} · ${w.queue_length} ${esc(t("queue"))} · ${w.wait_minutes} min</span></div>`;
  }).join("");
}
function renderDetails() {
  const panel=document.getElementById("detail-panel");
  const overview=document.getElementById("overview-grid"),lower=document.getElementById("lower-grid");
  overview.hidden=currentView!=="overview";lower.hidden=currentView!=="overview";panel.hidden=currentView==="overview";
  const nav=document.querySelectorAll(".nav-item");
  nav.forEach(item=>item.classList.toggle("active",item.dataset.view===currentView));
  const titles={overview:t("overview"),fleet:t("fleetView"),orders:t("ordersView"),routes:t("routesView"),alerts:t("alertsView")};
  const title=titles[currentView]||t(currentView);
  document.getElementById("page-title").textContent=title;
  document.getElementById("heading").innerHTML=`${esc(title)} <span>↗</span>`;
  if(currentView==="overview"){panel.innerHTML="";if(mapInstance)requestAnimationFrame(()=>mapInstance.resize());return;}
  let content="";
  if(currentView==="fleet") {
    content=`<div class="panel-header"><div><h2>${esc(t("vehicleMap"))}</h2><p>${esc(t("livePositions"))}</p></div></div><div class="table-wrap"><table class="data-table"><thead><tr><th>${esc(t("vehicle"))}</th><th>${esc(t("status"))}</th><th>${esc(t("capacity"))}</th><th>km/h</th><th>GPS ±m</th><th>Lenkzeit · min</th></tr></thead><tbody>${dashboard.vehicles.map(v=>`<tr><td class="order-id">${esc(v.label)}</td><td>${vehicleStatusPill(v.status)}</td><td>${number(v.max_weight_kg)} kg · ${number(v.max_volume_m3)} m³</td><td>${number(v.speed_kmh)}</td><td>${number(v.accuracy_m,1)}</td><td>${number(v.driven_minutes)} / 540</td></tr>`).join("")}</tbody></table></div>`;
  } else if(currentView==="orders") content=`<div class="panel-header"><div><h2>${esc(t("ordersView"))}</h2><p>${esc(t("orderOverview"))}</p></div></div><div class="table-wrap">${renderOrders(dashboard.orders,0)}</div>`;
  else if(currentView==="routes") {
    const routes=dashboard.routes;
    content=`<div class="panel-header"><div><h2>${esc(t("routesView"))}</h2><p>${esc(t("disclaimer"))}</p></div></div>${routes.length?`<div class="table-wrap"><table class="data-table"><thead><tr><th>${esc(t("route"))}</th><th>${esc(t("vehicle"))}</th><th>km</th><th>l</th><th>CO₂ kg</th><th>€</th><th>${esc(t("breakTime"))}</th><th>${esc(t("status"))}</th><th>${esc(t("actions"))}</th></tr></thead><tbody>${routes.map(r=>`<tr><td class="order-id">${esc(r.order_ids.join(", "))}</td><td>${esc(r.vehicle_id)}</td><td>${number(r.distance_km,1)}</td><td>${number(r.fuel_l,1)}</td><td>${number(r.co2_kg,1)}</td><td>${number(r.toll_eur,2)}</td><td>${number(r.break_minutes||0)}</td><td>${statusPill(r.status)}</td><td>${r.status==="vorgeschlagen"&&canDispatch()?`<div class="route-actions"><button class="small-action confirm" data-decision="confirm" data-route="${esc(r.id)}">${esc(t("confirm"))}</button><button class="small-action" data-decision="reject" data-route="${esc(r.id)}">${esc(t("reject"))}</button></div>`:"—"}</td></tr>`).join("")}</tbody></table></div>`:`<div class="empty-state">${esc(t("noRoutes"))}</div>`}`;
  } else content=`<div class="panel-header"><div><h2>${esc(t("alertsView"))}</h2><p>${esc(t("activeNotifications"))}</p></div></div><div class="alert-list">${renderAlerts(dashboard.alerts,0)}</div>`;
  panel.innerHTML=content;
}
function render() {
  if(!dashboard)return;
  renderKpis(dashboard.kpis);
  renderMap(dashboard.vehicles,dashboard.routes);
  document.getElementById("alert-list").innerHTML=renderAlerts(dashboard.alerts);
  document.getElementById("recent-orders").innerHTML=renderOrders(dashboard.orders);
  document.getElementById("warehouse-list").innerHTML=renderWarehouses(dashboard.warehouses);
  document.getElementById("fleet-count").textContent=dashboard.vehicles.length;
  document.getElementById("orders-count").textContent=dashboard.kpis.orders_open;
  document.getElementById("last-updated").textContent=`${t("lastUpdated")} ${stamp(dashboard.generated_at)}`;
  document.getElementById("today-label").textContent=new Intl.DateTimeFormat(language==="de"?"de-DE":language==="uz"?"uz-UZ":"en-GB",{weekday:"short",day:"2-digit",month:"short",timeZone:"Europe/Berlin"}).format(new Date());
  renderDetails();
}
async function refresh() {
  try { dashboard=await api("/api/v1/dashboard"); render(); }
  catch(error) { showNotice(t("loadError")+error.message,true); }
}
async function refreshTraffic() {
  const status=document.getElementById("traffic-status");
  try {
    liveTraffic=await api("/api/v1/traffic");
    const liveCount=liveTraffic.live_points||0;
    status.textContent=liveCount?`● ${t("trafficLive")} · ${liveCount}`:`● ${t("trafficUnavailable")}`;
    status.classList.toggle("live",liveCount>0);
    updateMapData();
  } catch(error) {
    liveTraffic={type:"FeatureCollection",features:[]};
    status.textContent=`● ${t("trafficUnavailable")}: ${error.message}`;
    status.classList.remove("live");
    updateMapData();
    console.warn("Traffic layer unavailable:",error.message);
  }
}
document.getElementById("language").addEventListener("change",event=>setLanguage(event.target.value));
document.getElementById("theme-toggle").addEventListener("click",()=>{document.body.classList.toggle("dark");localStorage.setItem("nordroute-dark",document.body.classList.contains("dark")?"1":"0");});
document.getElementById("traffic-toggle").addEventListener("click",event=>{
  const visible=event.currentTarget.getAttribute("aria-pressed")!=="true";
  event.currentTarget.setAttribute("aria-pressed",String(visible));
  if(mapReady)mapInstance.setLayoutProperty("traffic-lines","visibility",visible?"visible":"none");
});
document.getElementById("login-button").addEventListener("click",()=>{startLogin().catch(error=>showNotice(error.message,true));});
document.getElementById("logout-button").addEventListener("click",()=>{signOut().catch(error=>showNotice(error.message,true));});
document.getElementById("navigation").addEventListener("click",event=>{const item=event.target.closest("[data-view]");if(item){currentView=item.dataset.view;render();}});
document.addEventListener("click",async event=>{
  const view=event.target.closest("[data-view]");
  if(view){currentView=view.dataset.view;render();return;}
  const ack=event.target.closest("[data-ack]");
  if(ack){try{await api(`/api/v1/alerts/${encodeURIComponent(ack.dataset.ack)}/acknowledge`,{method:"POST"});await refresh();}catch(e){showNotice(e.message,true);}return;}
  const decision=event.target.closest("[data-decision]");
  if(decision){try{await api(`/api/v1/routes/${encodeURIComponent(decision.dataset.route)}/decision`,{method:"POST",body:JSON.stringify({decision:decision.dataset.decision})});showNotice(t("routeDecision"));await refresh();}catch(e){showNotice(e.message,true);}}
});
document.getElementById("optimize-button").addEventListener("click",async event=>{
  const button=event.currentTarget;button.disabled=true;
  try{const result=await api("/api/v1/optimizations",{method:"POST",body:JSON.stringify({})});await refresh();currentView="routes";render();showNotice(`${t("optimizationDone")} ${result.routes.length} · ${result.unassigned_order_ids.length} ${t("unassigned")}. ${t("disclaimer")}`);}
  catch(error){showNotice(t("optimizationError")+error.message,true);}
  finally{button.disabled=false;}
});

let liveSocket=null;
function connectLive() {
  if(!("WebSocket" in window)||liveSocket?.readyState===WebSocket.OPEN)return;
  const socketProtocol=location.protocol==="https:"?"wss:":"ws:";
  const url=`${socketProtocol}//${location.host}/ws/v1/live`;
  if(authConfig?.auth_mode==="oidc") {
    getAccessToken().then(token=>{
      if(!token)return;
      liveSocket=new WebSocket(url,["nordroute",`bearer.${token}`]);
      attachLiveHandlers(liveSocket);
    }).catch(error=>console.warn("Live stream authentication failed",error));
    return;
  }
  liveSocket=new WebSocket(`${url}?api_key=${encodeURIComponent(authConfig?.api_key||"")}`);
  attachLiveHandlers(liveSocket);
}
function attachLiveHandlers(socket) {
  socket.addEventListener("message",event=>{
    try { dashboard=JSON.parse(event.data);render(); }
    catch(error) { console.error("Invalid live dashboard payload",error); }
  });
  socket.addEventListener("error",()=>console.warn("Live stream unavailable; dashboard will refresh periodically."));
  socket.addEventListener("close",()=>{liveSocket=null;setTimeout(connectLive,5000);});
}
async function initialize() {
  document.getElementById("language").value=language;
  document.body.classList.toggle("dark",localStorage.getItem("nordroute-dark")==="1");
  const response=await fetch("/api/v1/config");
  if(!response.ok)throw new Error(`Application configuration returned HTTP ${response.status}`);
  authConfig=await response.json();
  if(authConfig.auth_mode==="oidc")await completeLoginRedirect();
  updateAuthControls();
  setLanguage(language);
  if(authConfig.auth_mode==="oidc"&&!tokenClaims())showNotice(t("signIn"));
  await refresh();
  await refreshTraffic();
  connectLive();
  setInterval(refresh,15000);
  setInterval(refreshTraffic,60000);
}
initialize().catch(error=>showNotice(error.message,true));
