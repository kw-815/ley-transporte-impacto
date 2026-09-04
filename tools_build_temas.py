#!/usr/bin/env python3
"""Genera pages/tema-NN-*.html a partir de content/tema-NN.json, con
header/nav/footer idénticos en las 11 páginas.

Cada tema se divide en dos bloques:
  - Artículos: directrices de fondo, agrupadas por subtema, cada subtema
    con una calificación de impacto (alto/medio/bajo) y ordenadas de
    mayor a menor impacto.
  - Disposiciones: como/cuando se implementa, mostradas como línea de
    tiempo por plazo (las sin plazo explícito van en un bloque aparte,
    "vigentes desde la publicación").
"""
import json, os, sys, re
import html as _html

SITE = os.path.dirname(os.path.abspath(__file__))
CONTENT = os.path.join(SITE, "content")
PAGES = os.path.join(SITE, "pages")

THEMES = [
    (1, "tema-01-gobernanza", "Gobernanza institucional y rectoría del sistema", "Gobernanza", "tema-01-gobernanza.jpg"),
    (2, "tema-02-competencias-gad", "Competencias de los GAD y control operativo del tránsito", "Competencias GAD", "tema-02-competencias.jpg"),
    (3, "tema-03-titulos-habilitantes", "Títulos habilitantes, rutas y frecuencias", "Títulos y rutas", "tema-03-titulos.jpg"),
    (4, "tema-04-tarifas-multas", "Tarifas, multas y procedimiento sancionador", "Tarifas y multas", "tema-04-tarifas.jpg"),
    (5, "tema-05-seguridad-vial", "Seguridad vial y protección de usuarios vulnerables", "Seguridad vial", "tema-05-seguridad.jpg"),
    (6, "tema-06-delivery", "Delivery y reparto a domicilio", "Delivery", "tema-06-delivery.jpg"),
    (7, "tema-07-licencias-escuelas", "Licencias, conductores y escuelas de conducción", "Licencias y escuelas", "tema-07-licencias.jpg"),
    (8, "tema-08-digitalizacion", "Digitalización, registros y control tecnológico", "Digitalización", "tema-08-digitalizacion.jpg"),
    (9, "tema-09-homologacion-sppat", "Homologación, revisión técnica, aseguramiento y SPPAT", "Homologación y SPPAT", "tema-09-homologacion.jpg"),
    (10, "tema-10-terminales", "Servicios conexos: terminales terrestres y estaciones", "Terminales", "tema-10-terminales.jpg"),
    (11, "tema-11-electromovilidad", "Electromovilidad y micromovilidad", "Electromovilidad", "tema-11-electromovilidad.jpg"),
]

# (slug, nombre_grupo) -> "alto" | "medio" | "bajo"
# Calificación por SUBGRUPO de artículos (no por item individual), para
# ordenar de mayor a menor impacto dentro del bloque "Artículos" de cada
# tema. Ajustar aquí si el contenido cambia.
GROUP_IMPACT = {
    ("tema-01-gobernanza", "Directorio y órganos rectores"): "bajo",
    ("tema-01-gobernanza", "Dirección Ejecutiva, CTE y Policía"): "bajo",
    ("tema-01-gobernanza", "Implementación"): "bajo",

    ("tema-02-competencias-gad", "Control operativo en la vía"): "alto",
    ("tema-02-competencias-gad", "Placas, matriculación y CRTV"): "alto",
    ("tema-02-competencias-gad", "Competencias de los GAD (COOTAD)"): "medio",
    ("tema-02-competencias-gad", "Transición y disposiciones de cierre"): "bajo",

    ("tema-03-titulos-habilitantes", "Modalidades de transporte"): "alto",
    ("tema-03-titulos-habilitantes", "Títulos habilitantes"): "alto",
    ("tema-03-titulos-habilitantes", "Estudios técnicos y rutas"): "alto",
    ("tema-03-titulos-habilitantes", "Implementación"): "medio",

    ("tema-04-tarifas-multas", "Tarifas"): "alto",
    ("tema-04-tarifas-multas", "Sanciones y garantías procesales"): "medio",
    ("tema-04-tarifas-multas", "Reglas de multas e implementación"): "medio",

    ("tema-05-seguridad-vial", "Conducta y protección vial"): "medio",
    ("tema-05-seguridad-vial", "Circulación en playas"): "medio",
    ("tema-05-seguridad-vial", "Peatones y biciusuarios"): "bajo",
    ("tema-05-seguridad-vial", "Plan Nacional y criterios"): "bajo",

    ("tema-06-delivery", "El servicio y sus requisitos"): "alto",
    ("tema-06-delivery", "Registro y sanciones"): "alto",
    ("tema-06-delivery", "Implementación"): "medio",

    ("tema-07-licencias-escuelas", "Escuelas de conducción y trámites"): "alto",
    ("tema-07-licencias-escuelas", "Emisión y renovación de licencias"): "medio",
    ("tema-07-licencias-escuelas", "Formación de conductores"): "medio",

    ("tema-08-digitalizacion", "Peajes"): "alto",
    ("tema-08-digitalizacion", "Identificación y GPS vehicular"): "alto",
    ("tema-08-digitalizacion", "Registro Nacional Integral"): "medio",
    ("tema-08-digitalizacion", "Transporte por cuenta propia"): "bajo",

    ("tema-09-homologacion-sppat", "Seguros y pólizas"): "alto",
    ("tema-09-homologacion-sppat", "Homologación y seguridad técnica"): "medio",
    ("tema-09-homologacion-sppat", "SPPAT"): "medio",
    ("tema-09-homologacion-sppat", "Matrícula y trámites"): "bajo",

    ("tema-11-electromovilidad", "Vehículos eléctricos livianos"): "alto",
    ("tema-11-electromovilidad", "Micromovilidad"): "medio",
    ("tema-11-electromovilidad", "Otros usos de vehículos eléctricos"): "medio",
    ("tema-11-electromovilidad", "Implementación"): "bajo",
}

def esc(s):
    s = _html.escape(s, quote=True)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    return s

def impacto_html(text, cls="cambio__text"):
    """Un item puede traer varios parrafos separados por una linea en
    blanco ("\n\n"); cada uno se renderiza como su propio <p>, sin fundir
    el contenido en un solo bloque."""
    paras = [p.strip() for p in re.split(r"\n\s*\n", text.strip()) if p.strip()]
    if not paras:
        paras = [text]
    return "\n            ".join(f'<p class="{cls}">{esc(p)}</p>' for p in paras)

def nav_html(current_num):
    items = []
    for num, slug, nombre, corto, _img in THEMES:
        cur = ' aria-current="page"' if num == current_num else ""
        items.append(
            f'    <a class="obj-nav-top__item obj-nav-top__item--{num}" href="{slug}.html"{cur}>\n'
            f'      <small>{num:02d}</small><span>{corto}</span>\n'
            f'    </a>'
        )
    return '<nav class="wrap obj-nav-top" aria-label="Temas de la reforma">\n  <div class="obj-nav-top__grid">\n' + "\n".join(items) + "\n  </div>\n</nav>"

CHEVRON_SVG = '<svg class="cambio__chevron" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 7.5 10 12.5 15 7.5"/></svg>'

def art_tag_of(item):
    return next((t["text"] for t in item.get("tags", []) if t.get("type") == "art"), "")

def plazo_tag_of(item):
    return next((t["text"] for t in item.get("tags", []) if t.get("type") == "plazo"), "")

def is_disposicion(item):
    a = art_tag_of(item).strip().lower()
    return a.startswith("disposición") or a.startswith("disposicion")

def cambio_html(item):
    art_tag = art_tag_of(item)
    plazo_tag = plazo_tag_of(item)
    tag_html = []
    if plazo_tag:
        tag_html.append(f'<span class="tag tag--plazo">{esc(plazo_tag)}</span>')
    if art_tag:
        tag_html.append(f'<span class="tag tag--art">{esc(art_tag)}</span>')
    meta = ""
    if tag_html:
        meta = f'\n            <div class="cambio__meta">\n              {" ".join(tag_html)}\n            </div>'
    return f'''        <details class="cambio">
          <summary class="cambio__summary">
            <span class="cambio__title">{esc(item["titulo"])}</span>
            {CHEVRON_SVG}
          </summary>
          <div class="cambio__body">
            {impacto_html(item["impacto"])}{meta}
          </div>
        </details>'''

def impact_badge(level):
    if not level:
        return ""
    label = {"alto": "Alto", "medio": "Medio", "bajo": "Bajo"}.get(level, level.title())
    return f'<span class="cambios-grupo__impact cambios-grupo__impact--{level}">{label}</span>'

def articulos_html(slug, items):
    """Agrupa los items tipo 'artículo' por su campo 'grupo', ordena los
    subgrupos de mayor a menor impacto (según GROUP_IMPACT) y renderiza
    cada uno con su encabezado + badge de impacto."""
    if not items:
        return ""
    if not any(it.get("grupo") for it in items):
        body = "\n\n".join(cambio_html(it) for it in items)
        return f'<div class="cambios">\n{body}\n      </div>'

    order = []
    buckets = {}
    for it in items:
        g = it.get("grupo") or "Otros"
        if g not in buckets:
            buckets[g] = []
            order.append(g)
        buckets[g].append(it)

    rank = {"alto": 0, "medio": 1, "bajo": 2}
    order.sort(key=lambda g: rank.get(GROUP_IMPACT.get((slug, g)), 1))

    blocks = []
    for g in order:
        entries = buckets[g]
        level = GROUP_IMPACT.get((slug, g))
        head = (
            f'        <p class="cambios-grupo__label">'
            f'<span class="cambios-grupo__dot" aria-hidden="true"></span>'
            f'{esc(g)}'
            f'{impact_badge(level)}'
            f'<span class="cambios-grupo__count">{len(entries)}</span>'
            f'</p>'
        )
        body = "\n\n".join(cambio_html(it) for it in entries)
        blocks.append(head + "\n\n" + body)
    return '<div class="cambios">\n' + "\n\n".join(blocks) + "\n      </div>"

PLAZO_DAYS_RE = [
    (re.compile(r"(\d+)\s*años?"), lambda n: n * 365),
    (re.compile(r"(\d+)\s*días?"), lambda n: n),
]

def plazo_sort_key(item):
    p = plazo_tag_of(item)
    if not p:
        return 0
    low = p.lower()
    for rx, conv in PLAZO_DAYS_RE:
        m = rx.search(low)
        if m:
            return conv(int(m.group(1)))
    return 9999

def disposiciones_html(items):
    """Linea de tiempo por plazo. Las que no traen plazo explicito van en
    un bloque aparte, 'vigentes desde la publicacion'."""
    if not items:
        return ""
    con_plazo = [it for it in items if plazo_tag_of(it)]
    sin_plazo = [it for it in items if not plazo_tag_of(it)]
    con_plazo.sort(key=plazo_sort_key)

    parts = []
    if con_plazo:
        rows = []
        for it in con_plazo:
            plazo = plazo_tag_of(it)
            rows.append(f'''      <article class="timeline__item">
        <span class="timeline__plazo">{esc(plazo)}</span>
        <span class="timeline__dot" aria-hidden="true"></span>
        <div class="timeline__body">
          <p class="timeline__plazo-mobile">{esc(plazo)}</p>
          <p class="timeline__title">{esc(it["titulo"])}</p>
          {impacto_html(it["impacto"], cls="timeline__text")}
        </div>
      </article>''')
        parts.append('<div class="timeline">\n' + "\n".join(rows) + "\n    </div>")
    if sin_plazo:
        rows = []
        for it in sin_plazo:
            art_tag = art_tag_of(it)
            art_html = f'<span class="tag tag--art">{esc(art_tag)}</span>' if art_tag else ""
            rows.append(f'''        <details class="cambio">
          <summary class="cambio__summary">
            <span class="cambio__title">{esc(it["titulo"])}</span>
            {CHEVRON_SVG}
          </summary>
          <div class="cambio__body">
            {impacto_html(it["impacto"])}
            <div class="cambio__meta">{art_html}</div>
          </div>
        </details>''')
        parts.append(
            '<div class="cambios-sin-plazo">\n'
            '        <p class="cambios-sin-plazo__label">Vigentes desde la publicación, sin plazo transitorio</p>\n'
            '        <div class="cambios">\n' + "\n\n".join(rows) + "\n        </div>\n      </div>"
        )
    return "\n\n".join(parts)

def build_page(theme, data):
    num, slug, nombre, corto, img = theme
    prev_theme = THEMES[num - 2] if num > 1 else None
    next_theme = THEMES[num] if num < 11 else None

    pager_prev = ""
    if prev_theme:
        pn, pslug, pnombre, _pc, _pi = prev_theme
        pager_prev = f'''      <a class="obj-pager__link" href="{pslug}.html">
        <small>← Tema {pn:02d}</small>
        <strong>{esc(pnombre)}</strong>
      </a>'''
    else:
        pager_prev = '''      <a class="obj-pager__link" href="../index.html#temas">
        <small>← Volver</small>
        <strong>Los 11 temas</strong>
      </a>'''

    pager_next = ""
    if next_theme:
        nn, nslug, nnombre, _nc, _ni = next_theme
        pager_next = f'''      <a class="obj-pager__link obj-pager__link--next" href="{nslug}.html">
        <small>Tema {nn:02d} →</small>
        <strong>{esc(nnombre)}</strong>
      </a>'''
    else:
        pager_next = '''      <a class="obj-pager__link obj-pager__link--next" href="../index.html#calendario">
        <small>Volver al inicio →</small>
        <strong>Calendario de cumplimiento</strong>
      </a>'''

    articulos = [it for it in data["items"] if not is_disposicion(it)]
    disposiciones = [it for it in data["items"] if is_disposicion(it)]

    bloque_articulos = ""
    if articulos:
        bloque_articulos = f'''    <div class="roadmap-sub">
      <header class="roadmap-sub__head">
        <p class="roadmap-sub__eyebrow">Directrices</p>
        <h2 class="roadmap-sub__title">Artículos</h2>
        <p class="roadmap-sub__lead">Los cambios de fondo: qué exige, prohíbe o autoriza la reforma.</p>
      </header>
      {articulos_html(slug, articulos)}
    </div>'''

    bloque_disposiciones = ""
    if disposiciones:
        bloque_disposiciones = f'''    <div class="roadmap-sub">
      <header class="roadmap-sub__head">
        <p class="roadmap-sub__eyebrow">Implementación</p>
        <h2 class="roadmap-sub__title">Disposiciones</h2>
        <p class="roadmap-sub__lead">Cómo y cuándo se pone en marcha lo anterior — plazos y responsables de cada paso.</p>
      </header>
      {disposiciones_html(disposiciones)}
    </div>'''

    return f'''<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{esc(nombre)} — Reforma a la Ley de Tránsito — Keyword</title>
  <meta name="description" content="{esc(data.get("meta_desc", nombre))}" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700&display=swap" />
  <link rel="stylesheet" href="../css/styles.css" />
</head>
<body class="obj-page--{num}">

<header class="site-header">
  <div class="wrap site-header__inner">
    <a href="../index.html" class="brand" aria-label="Keyword — inicio">
      <img src="../img/logo-keyword-white.svg" alt="Keyword" class="brand__logo" />
    </a>
    <nav class="nav-crumbs" aria-label="Ruta de navegación">
      <a href="../index.html">Reforma a la Ley de Tránsito</a> · <span>{esc(corto)}</span>
    </nav>
  </div>
</header>

<main>

{nav_html(num)}

<section class="obj-hero obj-hero--{num}" aria-labelledby="titulo-tema">
  <div class="wrap">
    <p class="obj-hero__kicker">Tema {num:02d} de 11</p>
    <div class="obj-hero__row">
      <h1 class="obj-hero__name" id="titulo-tema">{esc(nombre)}</h1>
      <span class="obj-hero__num" aria-hidden="true">{num:02d}</span>
    </div>

    <div class="pilar-framing">
      <p class="pilar-framing__eyebrow">En síntesis</p>
      <p class="pilar-framing__text">{esc(data["en_sintesis"])}</p>
    </div>

    <div class="roadmap">
{bloque_articulos}

{bloque_disposiciones}
    </div>

    <nav class="obj-pager" aria-label="Navegación entre temas">
{pager_prev}
{pager_next}
    </nav>
  </div>
</section>

</main>

<footer class="site-footer">
  <div class="wrap site-footer__inner">
    <img src="../img/logo-keyword-white.svg" alt="Keyword" class="site-footer__logo" />
    <p class="site-footer__copy">©Todos los derechos reservados</p>
    <p class="site-footer__contact">Contacto: <a href="mailto:info@keyword.com.ec">info@keyword.com.ec</a></p>
  </div>
</footer>

</body>
</html>
'''

def main():
    missing = []
    for theme in THEMES:
        num, slug, nombre, corto, img = theme
        content_path = os.path.join(CONTENT, f"{slug}.json")
        if not os.path.exists(content_path):
            missing.append(slug)
            continue
        with open(content_path, encoding="utf-8") as f:
            data = json.load(f)
        html = build_page(theme, data)
        out_path = os.path.join(PAGES, f"{slug}.html")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)
        n_art = sum(1 for it in data["items"] if not is_disposicion(it))
        n_disp = len(data["items"]) - n_art
        print(f"wrote {out_path} ({n_art} articulos, {n_disp} disposiciones)")
    if missing:
        print("MISSING content files:", missing)
        sys.exit(1)

if __name__ == "__main__":
    main()
