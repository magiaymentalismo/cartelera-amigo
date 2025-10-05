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
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover"/>
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="theme-color" content="#0f1115">
<meta name="format-detection" content="telephone=no">
<meta name="color-scheme" content="dark light">
<title>Cartelera — Magia & Teatro</title>
<link rel="apple-touch-icon" href="./icons/apple-touch-icon.png">
<style>
  :root{
    /* Paleta accesible (alto contraste) */
    --bg:#0f1115;        /* fondo */
    --panel:#151922;     /* panel */
    --card:#1a1f2b;      /* tarjetas */
    --ink:#e9eef3;       /* texto principal */
    --muted:#aeb6c2;     /* texto secundario */
    --hair:#242a34;      /* bordes */
    --accent:#3b82f6;    /* azul accesible */
    --good:#16a34a;      /* verde accesible */
    --warn:#f59e0b;      /* ámbar accesible */
    --sold:#6b7280;      /* gris “sold out” */

    --r:.9rem;           /* radio tarjetas */
    --rx:999px;          /* radio pills */
    --pad:1rem;
    --shadow:0 10px 28px rgba(0,0,0,.35);
  }
  @media (prefers-color-scheme: light){
    :root{
      --bg:#f7f8fa; --panel:#ffffff; --card:#ffffff; --ink:#0b0e12; --muted:#586174; --hair:#e7eaf0;
      --accent:#2563eb;
    }
  }

  html,body{height:100%}
  body{
    margin:0; color:var(--ink);
    background: linear-gradient(180deg, var(--bg) 0%, #0c0f13 100%);
    font:600 clamp(16px, 1.9vw, 17px)/1.55 "SF Pro Text","Segoe UI",Roboto,system-ui,sans-serif;
    -webkit-font-smoothing:antialiased; -moz-osx-font-smoothing:grayscale;
    -webkit-text-size-adjust:100%;
    min-height:100dvh; padding-bottom: env(safe-area-inset-bottom);
    overflow-y: overlay; -webkit-tap-highlight-color: transparent;
  }

  header{
    position:sticky; top:0; z-index:10; padding-top:max(.25rem, env(safe-area-inset-top));
    background:rgba(11,13,17,.7);
    border-bottom:1px solid var(--hair);
    backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
  }

  .wrap{max-width:1040px; margin:0 auto; padding: clamp(.8rem, 2vw, 1rem)}
  h1{margin:0 0 .35rem; font:800 clamp(18px, 3.2vw, 24px)/1.1 "SF Pro Display",system-ui,sans-serif; letter-spacing:.2px}
  .meta{color:var(--muted); font-size:.95rem}

  /* TABS (scrollables, alto contraste) */
  .tabs{display:flex; gap:.6rem; margin-top:.7rem; overflow-x:auto; padding:.2rem 0 .4rem;
        -webkit-overflow-scrolling:touch; overscroll-behavior-x:contain; scroll-snap-type:x proximity;}
  .tabs::-webkit-scrollbar{display:none}
  .tab{
    scroll-snap-align:start; padding:.7rem 1.05rem; border-radius:var(--rx);
    border:1px solid var(--hair); background:#171b23; color:var(--ink);
    font:800 .98rem/1 inherit; min-height:44px; letter-spacing:.2px; touch-action:manipulation;
    transition: background .15s ease, border-color .15s ease, transform .06s ease;
  }
  .tab:active{ transform:scale(.98) }
  .tab:focus-visible{ outline:2px solid var(--accent); outline-offset:2px }
  .tab.active{ background:var(--accent); border-color:#1e40af; color:#fff }

  /* PANEL + LISTA */
  .panel{ background:var(--panel); border:1px solid var(--hair); border-radius:var(--r);
          padding:calc(var(--pad) - .1rem); margin:0 clamp(.6rem, 2vw, 1rem); box-shadow:var(--shadow); }
  .list{ display:flex; flex-direction:column; gap:.9rem }

  /* TARJETA */
  .item{
    display:flex; justify-content:space-between; align-items:center; gap:1rem;
    background:var(--card); border:1px solid var(--hair); border-radius:var(--r); padding:.95rem 1rem;
    box-shadow:var(--shadow);
  }
  .left{ display:flex; align-items:center; gap:.8rem; flex-wrap:wrap }
  .date{ font:900 1rem/1.1 inherit; border-radius:.75rem; padding:.55rem .85rem; border:1px solid #2a3140; background:#10131a }
  .time{ font:800 .96rem/1 inherit; border-radius:var(--rx); padding:.5rem .85rem; border:1px solid #2a3140; background:#171b23 }

  /* CHIPS (sólidos y contrastados) */
  .chip{ padding:.52rem .86rem; border-radius:var(--rx); font:800 .93rem/1 inherit; border:1px solid transparent; letter-spacing:.2px }
  .chip.gray { background:#374151; color:#e5e7eb; border-color:#4b5563 }
  .chip.green{ background:#16a34a; color:#fff;    border-color:#15803d }
  .chip.gold { background:#3b82f6; color:#fff;    border-color:#2563eb } /* usamos azul como “alta demanda” */
  .chip.warn { background:#f59e0b; color:#111;    border-color:#b45309 }
  .chip.sold { background:#6b7280; color:#111;    border-color:#4b5563; text-decoration: line-through; text-decoration-thickness:2px }

  /* Medidor de ocupación (Escondido) */
  .meter{ width:100%; height:8px; border-radius:6px; background:#0f131a; border:1px solid #2a3140; overflow:hidden; margin-top:.4rem }
  .fill{ height:100%; width:0%; background:#3b82f6; transition:width .25s ease } /* azul accesible */
  .meta2{ color:var(--muted); font:700 .86rem/1.2 system-ui; margin-top:.25rem }

  /* Encabezado de mes sticky */
  .month{ position:sticky; top:calc(56px + env(safe-area-inset-top));
          margin:1rem 0 .5rem; padding:.25rem 0; font:900 .95rem/1.25 inherit;
          color:var(--accent); background:linear-gradient(180deg,transparent 0%,rgba(0,0,0,.15) 100%); z-index:1 }

  /* Móvil */
  @media (max-width: 520px){
    .panel{ margin:0; padding:.85rem }
    .item{ flex-direction:column; align-items:stretch; gap:.8rem }
    .left{ justify-content:space-between }
    .chip{ align-self:flex-end }
  }

  /* Accesibilidad */
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
    // Chip básico por si no hay capacidad
    let totalClass="chip gray";
    if(x.vendidas>=1 && x.vendidas<=9) totalClass="chip green";
    if(x.vendidas>=10) totalClass="chip gold";

    // Escondido: mostrar capacidad/stock + barra
    const isEscondido = (active === "Escondido");
    let rightHTML = `<span class="${totalClass}">Vendidas: <b>${x.vendidas}</b></span>`;

    if(isEscondido && x.cap){
      const cap = Number(x.cap)||0;
      const stock = (x.stock==null)? null : Number(x.stock);
      const vendidas = Number(x.vendidas)||0;
      const pct = cap>0 ? Math.round((vendidas/cap)*100) : 0;

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
        "meta": {"source": "Dinaticket", "note": "Legible alto contraste; Escondido con capacidad/stock y % ocupación"},
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
