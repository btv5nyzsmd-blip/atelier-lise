#!/usr/bin/env python3
"""
Bouwt de website van Atelier Lise.

Wat dit programma doet:
  1. Leest alle teksten en prijzen uit  inhoud.yml
  2. Verkleint de foto's uit  fotos/  naar snelle webversies
  3. Maakt van de sjablonen (bouw/sjablonen) echte HTML-pagina's
  4. Zet alles samen in de map  _site/  (dat is de complete website)

Gebruik (vanuit de hoofdmap van het project):
  python3 bouw/bouw.py            -> bouwt de site één keer
  python3 bouw/bouw.py --bekijk   -> bouwt de site, opent hem in je browser
                                     en bouwt opnieuw zodra je iets opslaat
"""

import argparse
import functools
import http.server
import json
import shutil
import sys
import threading
import time
import webbrowser
from datetime import date
from pathlib import Path

try:
    import yaml
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    from PIL import Image, ImageOps
except ImportError:
    sys.exit(
        "\nEr ontbreken hulpprogramma's. Voer eerst dit commando uit:\n\n"
        "    python3 -m pip install -r bouw/requirements.txt\n"
    )

try:
    # iPhone-foto's (.heic) kunnen alleen met dit extra hulpprogramma worden gelezen
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass

HOOFDMAP = Path(__file__).resolve().parent.parent
INHOUD = HOOFDMAP / "inhoud.yml"
FOTOS = HOOFDMAP / "fotos"
SJABLONEN = HOOFDMAP / "bouw" / "sjablonen"
STATISCH = HOOFDMAP / "bouw" / "statisch"
UITVOER = HOOFDMAP / "_site"
FOTO_CACHE = HOOFDMAP / ".foto-cache"  # verkleinde foto's, zodat bouwen snel blijft

FOTO_BREEDTES = [480, 800, 1280]
FOTO_TYPES = {".jpg", ".jpeg", ".png", ".webp", ".heic"}

PAGINAS = [
    # (sjabloon,            bestandsnaam,              seo-sleutel,      menu-tekst)
    ("home.html",          "index.html",              "home",           "Home"),
    ("behandelingen.html", "behandelingen.html",      "behandelingen",  "Prijzen"),
    ("portfolio.html",     "portfolio.html",          "portfolio",      "Portfolio"),
    ("over-mij.html",      "over-mij.html",           "over_mij",       "Over mij"),
    ("vragen.html",        "veelgestelde-vragen.html", "vragen",        "Vragen"),
    ("contact.html",       "contact.html",            "contact",        "Contact"),
]


# ---------------------------------------------------------------------
#  Inhoud inlezen
# ---------------------------------------------------------------------
def lees_inhoud():
    try:
        with INHOUD.open(encoding="utf-8") as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as fout:
        regel = ""
        if hasattr(fout, "problem_mark") and fout.problem_mark:
            regel = f" rond regel {fout.problem_mark.line + 1}"
        raise SystemExit(
            f"\nOeps, er zit een foutje in inhoud.yml{regel}.\n"
            "Controleer of alle teksten tussen \"aanhalingstekens\" staan\n"
            "en of de inspringing (spaties vooraan) klopt.\n\n"
            f"Technische melding:\n{fout}\n"
        )


# ---------------------------------------------------------------------
#  Foto's verkleinen
# ---------------------------------------------------------------------
def verwerk_foto(bron: Path, naam: str, deelversie: bool = False):
    """Maakt webp-versies in een paar breedtes. Geeft info terug voor de HTML."""
    FOTO_CACHE.mkdir(exist_ok=True)
    doel_map = UITVOER / "fotos"
    doel_map.mkdir(parents=True, exist_ok=True)

    with Image.open(bron) as origineel:
        beeld = ImageOps.exif_transpose(origineel).convert("RGB")
    breedte, hoogte = beeld.size

    versies = []
    for b in FOTO_BREEDTES:
        if b > breedte and versies:
            break
        b = min(b, breedte)
        bestand = f"{naam}-{b}.webp"
        cache = FOTO_CACHE / bestand
        if not cache.exists() or cache.stat().st_mtime < bron.stat().st_mtime:
            h = round(hoogte * b / breedte)
            beeld.resize((b, h), Image.LANCZOS).save(cache, "WEBP", quality=80, method=6)
        shutil.copy2(cache, doel_map / bestand)
        versies.append((b, f"fotos/{bestand}"))

    # Eén jpg-versie voor als iemand de site deelt via WhatsApp/Instagram
    deel = FOTO_CACHE / f"{naam}-deel.jpg"
    if deelversie:
        if not deel.exists() or deel.stat().st_mtime < bron.stat().st_mtime:
            b = min(1200, breedte)
            beeld.resize((b, round(hoogte * b / breedte)), Image.LANCZOS).save(
                deel, "JPEG", quality=82, optimize=True, progressive=True
            )
        shutil.copy2(deel, doel_map / deel.name)

    return {
        "src": versies[min(1, len(versies) - 1)][1],
        "srcset": ", ".join(f"{pad} {b}w" for b, pad in versies),
        "breedte": breedte,
        "hoogte": hoogte,
        "groot": versies[-1][1],
        "deel": f"fotos/{deel.name}",
    }


def zoek_foto(stam: str):
    """Zoekt bijvoorbeeld fotos/lise.jpg of fotos/lise.png."""
    for ext in FOTO_TYPES:
        for pad in (FOTOS / f"{stam}{ext}", FOTOS / f"{stam}{ext.upper()}"):
            if pad.exists():
                return pad
    return None


def verwerk_fotos(inhoud):
    fotos = {}
    for stam in ("sfeer", "lise"):
        pad = zoek_foto(stam)
        if pad:
            fotos[stam] = verwerk_foto(pad, stam, deelversie=(stam == "sfeer"))
        else:
            print(f"  Let op: geen foto gevonden voor fotos/{stam}.jpg")

    teksten = {p["foto"]: p.get("tekst", "") for p in (inhoud.get("portfolio") or [])}
    portfolio = []
    map_ = FOTOS / "portfolio"
    for pad in sorted(map_.iterdir() if map_.exists() else []):
        if pad.suffix.lower() not in FOTO_TYPES:
            continue
        info = verwerk_foto(pad, "portfolio-" + pad.stem.lower().replace(" ", "-"))
        info["tekst"] = teksten.get(pad.name, "")
        portfolio.append(info)
    fotos["portfolio"] = portfolio
    return fotos


# ---------------------------------------------------------------------
#  Pagina's maken
# ---------------------------------------------------------------------
def structured_data(inhoud, fotos):
    """Gegevens voor Google, zodat het bedrijf in lokale zoekresultaten verschijnt."""
    b = inhoud["bedrijf"]
    data = {
        "@context": "https://schema.org",
        "@type": "NailSalon",
        "name": b["naam"],
        "description": inhoud["seo"]["home"]["omschrijving"],
        "address": {
            "@type": "PostalAddress",
            "addressLocality": b["plaats"],
            "addressRegion": "Overijssel",
            "addressCountry": "NL",
        },
        "areaServed": b["plaats"],
        "priceRange": "€€",
        "sameAs": [f"https://www.instagram.com/{b['instagram']}/"],
        "paymentAccepted": b.get("betalen", ""),
    }
    if b.get("website"):
        data["url"] = b["website"].rstrip("/") + "/"
        if "sfeer" in fotos:
            data["image"] = data["url"] + fotos["sfeer"]["deel"]
    aanbod = []
    for groep in inhoud.get("behandelingen") or []:
        for item in groep["items"]:
            aanbod.append({"@type": "Offer", "name": item["naam"], "description": item.get("tekst", ""),
                           "priceSpecification": {"@type": "PriceSpecification", "priceCurrency": "EUR",
                                                  "price": "".join(c for c in item["prijs"] if c.isdigit() or c == ",").replace(",", ".") or "0"}})
    data["hasOfferCatalog"] = {"@type": "OfferCatalog", "name": "Behandelingen", "itemListElement": aanbod}
    return json.dumps(data, ensure_ascii=False, indent=2)


def bouw():
    start = time.time()
    inhoud = lees_inhoud()

    # Oude uitvoer leeggooien (behalve foto's: die worden hergebruikt)
    if UITVOER.exists():
        shutil.rmtree(UITVOER)
    UITVOER.mkdir()
    shutil.copytree(STATISCH, UITVOER / "assets")

    fotos = verwerk_fotos(inhoud)

    env = Environment(loader=FileSystemLoader(SJABLONEN), autoescape=select_autoescape(["html", "xml"]),
                      trim_blocks=True, lstrip_blocks=True)
    b = inhoud["bedrijf"]
    website = (b.get("website") or "").rstrip("/")
    algemeen = {
        "inhoud": inhoud,
        "b": b,
        "fotos": fotos,
        "menu": [(bestand, tekst) for _, bestand, _, tekst in PAGINAS],
        "instagram_url": f"https://www.instagram.com/{b['instagram']}/",
        # ig.me opent op telefoons direct een chat met het account
        "bericht_url": f"https://ig.me/m/{b['instagram']}",
        "website": website,
        "jaar": date.today().year,
        "structured_data": structured_data(inhoud, fotos),
        "faq_data": json.dumps({
            "@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": v["vraag"],
                            "acceptedAnswer": {"@type": "Answer", "text": v["antwoord"]}}
                           for v in inhoud.get("vragen") or []],
        }, ensure_ascii=False, indent=2),
    }

    for sjabloon, bestand, seo_sleutel, _ in PAGINAS:
        html = env.get_template(sjabloon).render(
            **algemeen, pagina=bestand, seo=inhoud["seo"][seo_sleutel],
            canonical=f"{website}/{'' if bestand == 'index.html' else bestand}" if website else "",
        )
        (UITVOER / bestand).write_text(html, encoding="utf-8")

    (UITVOER / "404.html").write_text(env.get_template("404.html").render(**algemeen, pagina="404.html",
                                      seo={"titel": "Pagina niet gevonden | " + b["naam"], "omschrijving": ""},
                                      canonical=""), encoding="utf-8")

    # Voor zoekmachines
    robots = "User-agent: *\nAllow: /\n"
    if website:
        robots += f"Sitemap: {website}/sitemap.xml\n"
        urls = "\n".join(
            f"  <url><loc>{website}/{'' if f == 'index.html' else f}</loc><lastmod>{date.today()}</lastmod></url>"
            for _, f, _, _ in PAGINAS)
        (UITVOER / "sitemap.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}\n</urlset>\n', encoding="utf-8")
    (UITVOER / "robots.txt").write_text(robots, encoding="utf-8")
    (UITVOER / ".nojekyll").write_text("")  # vertelt GitHub Pages: niets aan de bestanden veranderen

    print(f"  Klaar! Website gebouwd in {time.time() - start:.1f} sec. ({len(fotos['portfolio'])} portfoliofoto's)")


# ---------------------------------------------------------------------
#  Bekijken op je eigen computer
# ---------------------------------------------------------------------
def laatste_wijziging():
    paden = [INHOUD, *FOTOS.rglob("*"), *SJABLONEN.rglob("*"), *STATISCH.rglob("*")]
    return max((p.stat().st_mtime for p in paden if p.is_file()), default=0)


def bekijk(poort=8000):
    bouw()
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(UITVOER))
    handler.log_message = lambda *a: None
    server = http.server.ThreadingHTTPServer(("127.0.0.1", poort), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    adres = f"http://localhost:{poort}"
    print(f"\n  De site draait op {adres}")
    print("  Wijzig iets en sla op: de site wordt vanzelf opnieuw gebouwd (ververs je browser).")
    print("  Stoppen? Druk op Ctrl + C.\n")
    webbrowser.open(adres)
    vorige = laatste_wijziging()
    try:
        while True:
            time.sleep(1)
            nu = laatste_wijziging()
            if nu != vorige:
                vorige = nu
                try:
                    bouw()
                except SystemExit as fout:
                    print(fout)
    except KeyboardInterrupt:
        print("\n  Gestopt.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bouwt de website van Atelier Lise")
    parser.add_argument("--bekijk", action="store_true", help="open de site in je browser en bouw opnieuw bij wijzigingen")
    args = parser.parse_args()
    bekijk() if args.bekijk else bouw()
