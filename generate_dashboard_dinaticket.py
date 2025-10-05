#!/usr/bin/env python3
from __future__ import annotations

import json, re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

# ===================== CONFIG ===================== #
EVENTS = {
    "Disfruta": "https://www.dinaticket.com/es/provider/10402/event/4905281",
    "Miedo": "https://www.dinaticket.com/es/provider/10402/event/4915778",
    "Escondido": "https://www.dinaticket.com/es/provider/20073/event/4930233",
}

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123 Safari/537.36"}

MESES = {
    "Ene.": "01", "Feb.": "02", "Mar.": "03", "Abr.": "04", "May.": "05", "Jun.": "06",
    "Jul.": "07", "Ago.": "08", "Sep.": "09", "Oct.": "10", "Nov.": "11", "Dic.": "12"
}

# ================== TEMPLATE (HTML) ================== #
TABS_HTML = r"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8"/>
<!-- iOS: ocupar toda la pantalla y respetar notch -->
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover"/>
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="theme-color" content="#0b0b0b">
<meta name="format-detection" content="telephone=no">
<meta name="color-scheme" content="dark">
<title>Cartelera — Magia & Teatro</title>
<link rel="apple-touch-icon" href="./icons/apple-touch-icon.png">
<style>
  :root{
    --bg:#0b0b0b; --bg2:#0e0e0e; --panel:#121212; --card:#181818;
    --ink:#f7f7f7; --muted:#b9b9b9; --hair:#2a2a2a;
    --cta:#d4af37; --ok:#16a34a; --warn:#f59e0b; --sold:#7a7a7a;
    --r:.875rem; --rx:999px; --inside:.9rem; --shadow:0 10px 30px rgb(0 0 0 / .35);
  }
  @media (prefers-color-scheme: light){
    :root{ --bg:#fafafa; --bg2:#fff; --panel:#ffffff; --card:#ffffff; --ink:#0a0a0a; --muted:#555; --hair:#e8e8e8 }
    body{ background:linear-gradient(180deg,#fff 0%,#fafafa 100%) }
  }
  html,body{height:100%}
  body{
    margin:0; color:var(--ink);
    background:
      radial-gradient(1200px 600px at 50% -200px, #1a1a1a80 0%, transparent 70%),
      linear-gradient(180deg, var(--bg2) 0%, var(--bg) 100%);
    font:500 clamp(15px, 1.6vw, 16px)/1.5 "SF Pro Text","Segoe UI",Roboto,system-ui,sans-serif;
    -webkit-font-smoothing:antialiased; -moz-osx-font-smoothing:grayscale;
    -webkit-text-size-adjust:100%;
    min-height:100dvh; padding-bottom: env(safe-area-inset-bottom);
    color-scheme: dark light; overflow-y: overlay; -webkit-tap-highlight-color: transparent;
  }
  header{
    position:sticky; top:0; z-index:10; padding-top:max(.25rem, env(safe-area-inset-top));
    background: color-mix(in oklab, #0f0f0f 80%, transparent);
    border-bottom:1px solid var(--hair);
    backdrop-filter: saturate(180%) blur(14px); -webkit-backdrop-filter:saturate(180%) blur(14px);
  }
  .wrap{max-width:1040px; margin:0 auto; padding: clamp(.75rem, 1.8vw, 1rem)}
  h1{margin:0 0 .3rem; font:800 clamp(18px, 3.4vw, 24px)/1.1 "SF Pro Display", system-ui, sans-serif; letter-spacing:.2px}
  .meta{color:var(--muted); font-size:.92rem}

  .tabs{
    display:flex; gap:.6rem; margin-top:.7rem; overflow-x:auto; padding:.2rem 0 .4rem;
    -webkit-overflow-scrolling:touch; overscroll-behavior-x:contain; scroll-snap-type:x proximity;
  }
  .tabs::-webkit-scrollbar{display:none}
  .tab{
    scroll-snap-align:start; padding:.68rem 1.1rem; border-radius: var(--rx);
    border:1px solid var(--hair); background: linear-gradient(180deg,#1b1b1b,#161616);
    color:var(--ink); font:700 .97rem/1 inherit; min-height:44px; letter-spacing:.2px;
    transform: translateZ(0); transition: transform .08s ease, background .2s, border-color .2s;
    touch-action: manipulation;
  }
  .tab:active{ transform: scale(.98) }
  .tab:focus-visible{ outline:2px solid var(--cta); outline-offset:2px }
  .tab.active{
    background: radial-gradient(120% 200% at 50% -60%, #ffe9a6 0%, #d4af37 55%, #b88a1c 100%);
    color:#161616; border-color: #a07f1a; box-shadow: 0 2px 14px #d4af3740 inset;
  }

  .panel{
    background: linear-gradient(180deg, color-mix(in oklab,var(--panel) 85%, transparent), var(--panel));
    border:1px solid var(--hair); border-radius: var(--r); padding: calc(var(--inside) + .1rem);
    margin: 0 clamp(.5rem, 2vw, 1rem); box-shadow: var(--shadow);
  }
  .list{ display:flex; flex-direction:column; gap:.85rem }

  .item{
    display:flex; justify-content:space-between; align-items:center; gap:.9rem;
    background: linear-gradient(180deg, var(--card), color-mix(in oklab, var(--card) 90%, #000 10%));
    border:1px solid var(--hair); border-radius: var(--r); padding: .95rem; box-shadow: var(--shadow);
  }
  .item:active{ transform: translateY(1px) }

  .left{ display:flex; align-items:center; gap:.7rem; flex-wrap:wrap }
  .date{ font:800 1rem/1.1 inherit; border-radius:.75rem; padding:.55rem .85rem; border:1px solid #333a; background: #202020 }
  .time{ font:700 .96rem/1 inherit; border-radius: var(--rx); padding:.5rem .85rem; border:1px solid #3a3a3a; background: #2a2a2a }

  .chip{ padding:.52rem .86rem; border-radius: var(--rx); font:800 .93rem/1 inherit; letter-spacing:.2px; border:1px solid transparent }
  .chip.gray{ background: linear-gradient(180deg,#6b6b6b,#585858); color:#fff; border-color:#4d4d4d }
  .chip.green{ background: linear-gradient(180deg, #22c55e, #16a34a); color:#fff; border-color:#128a3d; box-shadow: 0 0 0 1px #0003 inset }
  .chip.gold{ background: radial-gradient(100% 100% at 30% 0%, #fff2b3 0%, #f2cc5c 40%, #d4af37 100%); color:#111; border-color:#a07f1a; box-shadow: 0 0 0 1px #0002 inset }
  .chip.warn{ background: linear-gradient(180deg,#fbcf7e,#f59e0b); color:#111; border-color:#b47207 }
  .chip.sold{ background: linear-gradient(180deg,#8b8b8b,#6b6b6b); color:#1a1a1a; border-color:#555; text-decoration: line-through; text-decoration-thickness:2px }

  .meter{ width:100%; height:8px; border-radius:6px; background:#2a2a2a; border:1px solid #3a3a3a; overflow:hidden; margin-top:.35rem }
  .fill{ height:100%; width:0%; background: linear-gradient(90deg, #22c55e, #f59e0b 60%, #d4af37); transition: width .35s ease }

  .meta2{ color:var(--muted); font:600 .86rem/1.2 system-ui; margin-top:.25rem }

  .month{
    position: sticky; top: calc(56px + env(safe-area-inset-top));
    margin: 1rem 0 .5rem; padding:.35rem 0;
    color: var(--cta); background: linear-gradient(180deg, transparent 0%, color-mix(in oklab,var(--panel) 45%, transparent) 100%);
    backdrop-filter: blur(2px); font: 800 .95rem/1.2 inherit; letter-spacing:.4px; z-index: 1;
  }
  @media (max-width: 520px){
    .panel{margin: 0; padding: .8rem}
    .item{flex-direction:column; align-items:stretch; gap:.75rem}
    .left{justify-content:space-between}
    .chip{align-self:flex-end}
  }
  @media (prefers-reduced-motion: reduce){
    *{scroll-behavior:auto; transition:none !important; animation:none !important}
  }
</style>
</head>
<body>
  <header>
    <div class="wrap">
      <h1>Cartelera — Escalera de Jacob y Escondido</h1>
      <div class="meta" id="meta"></div>
      <div class="tabs" id="tabs"></div>
    </div>
  </header>
  <main class="wrap">
    <section class="panel">
      <div id="list" class="list"></div>
    </section>
  </main>
<script id="PAYLOAD" type="application/json">{{PAYLOAD_JSON}}</script>
<script>
const payload = JSON.parse(document.getElementById('PAYLOAD').textContent);
const eventos = payload.eventos || {};
const gen = new Date(payload.generated_at);

// “hace X min”
const diffMin = Math.max(0, Math.round((Date.now() - gen.getTime())/60000));
const ago = diffMin===0 ? "justo ahora" : diffMin===1 ? "hace 1 min" : `hace ${diffMin} min`;
document.getElementById('meta').textContent =
  `Generado: ${gen.toLocaleDateString('es-ES')} ${gen.toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})} — ${ago}`;

const tabsEl=document.getElementById('tabs'); let active=Object.keys(eventos)[0]||null;
if(active){
  Object.keys(eventos).forEach((k,i)=>{
    const rows=(eventos[k].table?.rows)||[];
    const b=document.createElement('button');
    b.className='tab'+(i===0?' active':''); b.dataset.tab=k; b.textContent=`${k} (${rows.length})`;
    b.onclick=()=>setActive(k); tabsEl.appendChild(b);
  });
  document.body.className=active;
}

function setActive(k){ active=k; document.body.className=k;
  document.querySelectorAll('.tab').forEach(t=>t.classList.toggle('active',t.dataset.tab===k));
  render();
}
function parseRow(r){
  // [FechaLabel, Hora, Vendidas, FechaISO, Capacidad, Stock]
  return {fecha_label:r[0],hora:r[1],vendidas:r[2],fecha_iso:r[3],cap:r[4]??null,stock:r[5]??null};
}
const DAYS=['Dom','Lun','Mar','Mié','Jue','Vie','Sáb'];
function dayName(f){ return DAYS[new Date(f+'T00:00:00').getDay()]; }

function render(){
  if(!active) return;
  let data=(eventos[active].table?.rows||[]).map(parseRow);
  data.sort((a,b)=> (a.fecha_iso+a.hora).localeCompare(b.fecha_iso+b.hora));

  const list=document.getElementById('list'); list.innerHTML='';
  let currentMonth = "";
  data.forEach(x=>{
    const d=new Date(x.fecha_iso+'T00:00:00');
    const monthKey = `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}`;
    const monthLabel = d.toLocaleDateString('es-ES',{month:'long', year:'numeric'});
    if(monthKey !== currentMonth){
      currentMonth = monthKey;
      list.insertAdjacentHTML('beforeend', `<h3 class="month">${monthLabel}</h3>`);
    }

    const fechaLabel=`${x.fecha_label} (${dayName(x.fecha_iso)})`;
    // Lógica de chips por defecto
    let totalClass="chip gray";
    if(x.vendidas>=1 && x.vendidas<=9) totalClass="chip green";
    if(x.vendidas>=10) totalClass="chip gold";

    // Si es la pestaña "Escondido", mostrar capacidad/stock + barra
    const isEscondido = (active === "Escondido");
    let rightHTML = `<span class="${totalClass}">Vendidas: <b>${x.vendidas}</b></span>`;

    if(isEscondido && x.cap){
      const cap = Number(x.cap)||0;
      const stock = (x.stock==null)? null : Number(x.stock);
      const vendidas = Number(x.vendidas)||0;
      const pct = cap>0 ? Math.round((vendidas/cap)*100) : 0;

      // Elegir chip según estado
      let chipClass = "chip green";
      if(stock===0) chipClass = "chip sold";
      else if(pct>=70) chipClass = "chip gold";
      else if(pct>=40) chipClass = "chip warn";

      const stockTxt = (stock==null) ? "" : ` — quedan ${stock}`;
      rightHTML = `
        <div style="min-width:220px; text-align:right">
          <span class="${chipClass}">Vendidas: <b>${vendidas}</b> / ${cap}${stockTxt}</span>
          <div class="meter" aria-hidden="true"><div class="fill" style="width:${Math.min(100, Math.max(0, pct))}%"></div></div>
          <div class="meta2">${pct}% de ocupación</div>
        </div>`;
    }

    list.insertAdjacentHTML('beforeend',`
      <div class="item">
        <div class="left">
          <div class="date">${fechaLabel}</div>
          <div class="time">${x.hora}</div>
        </div>
        ${rightHTML}
      </div>`);
  });
}
if(active) render();
</script>
</body>
</html>"""

# ================== SCRAPER ================== #
def fetch_functions_dinaticket(url: str, timeout: int = 20) -> list[dict]:
    r = requests.get(url, headers=UA, timeout=timeout)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    funciones = []
    for session in soup.find_all("div", class_="js-session-row"):
        parent = session.find_parent("div", class_="js-session-group")
        if not parent:
            continue

        date_div = parent.find("div", class_="session-card__date")
        if not date_div:
            continue
        dia = date_div.find("span", class_="num_dia")
        mes = date_div.find("span", class_="mes")
        if not (dia and mes):
            continue

        mes_num = MESES.get(mes.text.strip(), "01")
        anio = datetime.now().year
        fecha_iso = f"{anio}-{mes_num}-{dia.text.strip().zfill(2)}"
        fecha_dt = datetime.strptime(fecha_iso, "%Y-%m-%d")
        fecha_label = fecha_dt.strftime("%d %b %Y")

        hora_span = session.find("span", class_="session-card__time-session")
        hora_txt = (hora_span.text or "").strip()
        h = hora_txt.lower().replace(" ", "").replace("h", ":")
        m = re.match(r"^(\d{1,2})(?::?(\d{2}))?$", h)
        if m:
            hh = int(m.group(1)); mm = int(m.group(2) or "00")
            hora = f"{hh:02d}:{mm:02d}"
        else:
            hora = hora_txt.strip()

        quota_row = session.find("div", class_="js-quota-row")
        if not quota_row:
            continue
        try:
            capacidad = int(quota_row.get("data-quota-total", 0))
            stock = int(quota_row.get("data-stock", 0))
            vendidas = max(0, capacidad - stock)
        except Exception:
            continue

        funciones.append({
            "fecha_label": fecha_label,
            "fecha_iso": fecha_iso,
            "hora": hora,
            "vendidas_dt": vendidas,
            "capacidad": capacidad,
            "stock": stock
        })
    return funciones

# ============== PAYLOAD ================== #
def build_event_rows(funcs_dt: list[dict]) -> list[list]:
    # [FechaLabel, Hora, Vendidas, FechaISO, Capacidad, Stock]
    return [[f["fecha_label"], f["hora"], f["vendidas_dt"], f["fecha_iso"], f.get("capacidad"), f.get("stock")] for f in funcs_dt]

def build_tabbed_payload(eventos_dt: dict[str, list[dict]]) -> dict:
    eventos_out = {}
    for nombre, funciones in eventos_dt.items():
        rows = build_event_rows(funciones)
        eventos_out[nombre] = {"table": {"headers": ["Fecha","Hora","Vendidas","FechaISO","Capacidad","Stock"], "rows": rows}}
    return {
        "generated_at": datetime.now(ZoneInfo("Europe/Madrid")).isoformat(),
        "meta": {"source": "Dinaticket", "note": "Pestañas por evento; Escondido muestra capacidad/stock y ocupación"},
        "eventos": eventos_out
    }

def write_tabs_html(payload: dict, out_html: str = "dashboard_tabs.html") -> None:
    html = TABS_HTML.replace(
        "{{PAYLOAD_JSON}}",
        json.dumps(payload, ensure_ascii=False).replace("</script>", "<\\/script>")
    )
    Path(out_html).write_text(html, encoding="utf-8")
    print(f"OK ✓ Escribí {out_html} (abrilo en tu navegador).")

# ============================== MAIN ============================== #
if __name__ == "__main__":
    eventos_dt: dict[str, list[dict]] = {}
    for nombre, url in EVENTS.items():
        funciones = fetch_functions_dinaticket(url)
        eventos_dt[nombre] = funciones
        print(f"{nombre}: {len(funciones)} funciones")

    payload = build_tabbed_payload(eventos_dt)
    Path("docs").mkdir(exist_ok=True)
    write_tabs_html(payload, out_html="docs/index.html")
