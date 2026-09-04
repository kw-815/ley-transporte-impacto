#!/usr/bin/env python3
"""Genera pages/tema-NN-*.html a partir de content/tema-NN.json, con
header/nav/footer idénticos en las 11 páginas. También imprime el bloque
de 11 tarjetas para pegar en index.html.
"""
import json, os, sys

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

import re
import html as _html

def esc(s):
    s = _html.escape(s, quote=True)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    return s

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

def cambio_html(idx, num, item):
    tags = item.get("tags", [])
    art_tag = next((t["text"] for t in tags if t.get("type") == "art"), None)
    other_tags = [t for t in tags if t.get("type") != "art"]
    tag_html = []
    for t in other_tags:
        cls = "tag"
        if t.get("type") == "plazo":
            cls += " tag--plazo"
        tag_html.append(f'<span class="{cls}">{esc(t["text"])}</span>')
    impacto = ""
    if item.get("impacto"):
        impacto = f'\n            <p class="cambio__impacto">{esc(item["impacto"])}</p>'
    meta = ""
    if tag_html:
        meta = f'\n            <div class="cambio__meta">\n              {" ".join(tag_html)}\n            </div>'
    art_html = f'<span class="cambio__summary-art">{esc(art_tag)}</span>' if art_tag else ""
    return f'''        <details class="cambio">
          <summary class="cambio__summary">
            <span class="cambio__index" aria-hidden="true">T{num} · {idx:02d}</span>
            <span class="cambio__title">{esc(item["titulo"])}</span>
            {art_html}
            {CHEVRON_SVG}
          </summary>
          <div class="cambio__body">
            <div class="cambio__grid">
              <div class="cambio__col cambio__col--antes">
                <span class="cambio__label">Hoy</span>
                <p>{esc(item["antes"])}</p>
              </div>
              <div class="cambio__col cambio__col--ahora">
                <span class="cambio__label">Con la reforma</span>
                <p>{esc(item["ahora"])}</p>
              </div>
            </div>{impacto}{meta}
          </div>
        </details>'''

def grouped_items_html(num, items):
    """Agrupa items consecutivos por su campo opcional 'grupo', preservando
    el orden de primera aparición. Si ningún item trae 'grupo', devuelve la
    lista plana de siempre (sin encabezados)."""
    if not any(it.get("grupo") for it in items):
        return "\n\n".join(cambio_html(i + 1, num, it) for i, it in enumerate(items))

    order = []
    buckets = {}
    for i, it in enumerate(items, 1):
        g = it.get("grupo") or "Otros"
        if g not in buckets:
            buckets[g] = []
            order.append(g)
        buckets[g].append((i, it))

    blocks = []
    for g in order:
        entries = buckets[g]
        head = (
            f'        <p class="cambios-grupo__label">'
            f'<span class="cambios-grupo__dot" aria-hidden="true"></span>'
            f'{esc(g)}'
            f'<span class="cambios-grupo__count">{len(entries)}</span>'
            f'</p>'
        )
        body = "\n\n".join(cambio_html(i, num, it) for i, it in entries)
        blocks.append(head + "\n\n" + body)
    return "\n\n".join(blocks)

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
        pager_next = '''      <a class="obj-pager__link obj-pager__link--next" href="../index.html#actores">
        <small>Volver al inicio →</small>
        <strong>A quién afecta</strong>
      </a>'''

    items_html = grouped_items_html(num, data["items"])

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
      <header class="roadmap__head">
        <div>
          <p class="roadmap__eyebrow">Comparativa</p>
          <h2 class="roadmap__title">Antes y ahora</h2>
        </div>
        <p class="roadmap__count">{len(data["items"])} {"artículo" if len(data["items"]) == 1 else "artículos y disposiciones"}</p>
      </header>

      <div class="cambios">
{items_html}
      </div>
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
        print(f"wrote {out_path} ({len(data['items'])} items)")
    if missing:
        print("MISSING content files:", missing)
        sys.exit(1)

if __name__ == "__main__":
    main()
