#!/usr/bin/env python3
from __future__ import annotations

import json, re
from datetime import datetime, timezone
from pathlib import Path

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
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Cartelera — Magia & Teatro</title>
<style>
  body{margin:0; background:#0b0b0b; color:#f5f5f5;
       font:400 16px/1.45 "Segoe UI", Roboto, system-ui, sans-serif;}
  header{ position:sticky; top:0; background:#0f0f0fe6;
          border-bottom:1px solid #2a2a2a;}
  .wrap{max-width:1040px; margin:0 auto; padding:1rem}
  h1{margin:0 0 .4rem; font:800 22px/1.1 inherit}
  .meta{color:#b7b7b7; font-size:.875rem}
  .tabs{display:flex; gap:.6rem; margin-top:.8rem}
  .tab{padding:.55rem 1rem; border-radius:999px; cursor:pointer;
       background:#1b1b1b; color:#f5f5f5; border:1px solid #2a2a2a;
       font:700 .92rem/1 inherit;}
  .tab.active{ background:#d4af37; color:#111; }
  .panel{ background:#141414; border:1px solid #2a2a2a;
          border-radius:.875rem; padding:1rem; margin:0 1rem;}
  .list{ display:flex; flex-direction:column; gap:.8rem }
  .item{ display:flex; justify-content:space-between; align-items:center;
         background:#181818; border:1px solid #2a2a2a; border-radius:.875rem;
         padding:1rem; box-shadow:0 6px 18px rgba(0,0,0,.35);}
  .left{ display:flex; align-items:center; gap:.6rem }
  .date{ font:800 1rem/1.1 inherit; border-radius:.75rem; padding:.5rem .8rem;
         border:1px solid #3a3a3a; background:#1f1f1f;}
  .time{ font:700 .95rem/1 inherit; border-radius:999px; padding:.4rem .8rem;
         border:1px solid #3a3a3a; background:#2a2a2a;}
  .chip{ padding:.48rem .75rem; border-radius:999px; font:800 .9rem/1 inherit;}
  .chip.gray{ background:#555; color:#fff }
  .chip.green{ background:#16a34a; color:#fff }
  .chip.gold{ background:#d4af37; color:#111 }
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
document.getElementById('meta').textContent = 
  `Generado: ${gen.toLocaleDateString()} ${gen.toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})}`;

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
  return {fecha_label:r[0],hora:r[1],vendidas:r[2],fecha_iso:r[3]}; 
}
const DAYS=['Dom','Lun','Mar','Mié','Jue','Vie','Sáb'];
function dayName(f){ return DAYS[new Date(f+'T00:00:00').getDay()]; }
function render(){
  if(!active) return;
  let data=(eventos[active].table?.rows||[]).map(parseRow);
  data.sort((a,b)=> (a.fecha_iso+a.hora).localeCompare(b.fecha_iso+b.hora));

  const list=document.getElementById('list'); 
  list.innerHTML='';

  let currentMonth = "";
  data.forEach(x=>{
    const d=new Date(x.fecha_iso+'T00:00:00');
    const monthKey = `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}`;
    const monthLabel = d.toLocaleDateString('es-ES',{month:'long', year:'numeric'});

    if(monthKey !== currentMonth){
      currentMonth = monthKey;
      list.insertAdjacentHTML('beforeend', `<h3 style="margin:1rem 0 .5rem; color:#d4af37">${monthLabel}</h3>`);
    }

    const fechaLabel=`${x.fecha_label} (${dayName(x.fecha_iso)})`;
    let totalClass="chip gray";
    if(x.vendidas>=1 && x.vendidas<=9) totalClass="chip green";
    if(x.vendidas>=10) totalClass="chip gold";

    list.insertAdjacentHTML('beforeend',`
      <div class="item">
        <div class="left">
          <div class="date">${fechaLabel}</div>
          <div class="time">${x.hora}</div>
        </div>
        <span class="${totalClass}">Vendidas: <b>${x.vendidas}</b></span>
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
        if not parent: continue
        date_div = parent.find("div", class_="session-card__date")
        if not date_div: continue
        dia = date_div.find("span", class_="num_dia")
        mes = date_div.find("span", class_="mes")
        if not (dia and mes): continue
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
        if not quota_row: continue
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
            "vendidas_dt": vendidas
        })
    return funciones

# ============== PAYLOAD ================== #
def build_event_rows(funcs_dt: list[dict]) -> list[list]:
    rows = []
    for f in funcs_dt:
        rows.append([f["fecha_label"], f["hora"], f["vendidas_dt"], f["fecha_iso"]])
    return rows

def build_tabbed_payload(eventos_dt: dict[str, list[dict]]) -> dict:
    eventos_out = {}
    for nombre, funciones in eventos_dt.items():
        rows = build_event_rows(funciones)
        eventos_out[nombre] = {
            "table": {"headers": ["Fecha","Hora","Vendidas","FechaISO"], "rows": rows}
        }
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "meta": {"source": "Dinaticket", "note": "Pestañas por evento"},
        "eventos": eventos_out
    }

def write_tabs_html(payload: dict, out_html: str = "dashboard_tabs.html") -> None:
    html = TABS_HTML.replace("{{PAYLOAD_JSON}}",
        json.dumps(payload, ensure_ascii=False).replace("</script>", "<\\/script>"))
    Path(out_html).write_text(html, encoding="utf-8")
    print(f"OK ✓ Escribí {out_html} (abrilo en tu navegador).")

# ============================== MAIN ============================== #
# al final de tu script
if __name__ == "__main__":
    eventos_dt: dict[str, list[dict]] = {}
    for nombre, url in EVENTS.items():
        funciones = fetch_functions_dinaticket(url)
        eventos_dt[nombre] = funciones
        print(f"{nombre}: {len(funciones)} funciones")

    payload = build_tabbed_payload(eventos_dt)

    # >>> escribe dentro de docs/
    Path("docs").mkdir(exist_ok=True)
    from pathlib import Path
Path("docs").mkdir(exist_ok=True)
write_tabs_html(payload, out_html="docs/index.html")


