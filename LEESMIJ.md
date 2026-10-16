# Website Atelier Lise

Website voor Atelier Lise: gellak & nail art aan huis in Zwolle.

---

## Wat staat waar?

```
atelier-lise/
├── inhoud.yml          ← ALLE teksten en prijzen. Dit pas je aan.
├── fotos/              ← Alle foto's. Hier zet je nieuwe foto's neer.
│   ├── sfeer.jpg       ← grote foto op de homepage
│   ├── lise.jpg        ← foto van Lise (pagina "Over mij")
│   └── portfolio/      ← foto's van haar werk: 01.jpg, 02.jpg, ...
├── bouw/               ← de "machinekamer". Hoef je niet aan te komen.
│   ├── bouw.py         ← programma dat de site in elkaar zet
│   ├── sjablonen/      ← opbouw van de pagina's (HTML)
│   └── statisch/       ← vormgeving (CSS), lettertypes, logo
└── _site/              ← de uiteindelijke website (wordt automatisch gemaakt)
```

**Kort gezegd:** jij werkt alleen in `inhoud.yml` en in de map `fotos/`.
Het programma `bouw.py` maakt daar elke keer de website van.

---

## Een prijs of tekst aanpassen

1. Open `inhoud.yml`.
2. Zoek de tekst die je wilt veranderen (op de Mac: `Cmd + F`).
3. Verander alleen wat **tussen de aanhalingstekens** staat:

   ```yaml
   - naam: "Gellak handen"
     prijs: "€27"        ← verander bijvoorbeeld in "€29"
   ```

4. Sla op. Klaar.

**Let op:**
- Laat de `"aanhalingstekens"` staan.
- Wil je een aanhalingsteken *in* de tekst? Gebruik `’` (bijvoorbeeld `’s avonds`).
- Gebruik spaties aan het begin van een regel, geen tab. Kopieer bij twijfel een bestaande regel.

Een **nieuwe behandeling** toevoegen? Kopieer een heel blok van `- naam:` tot en met `tekst:`, plak het eronder en pas het aan.

---

## Foto's toevoegen of vervangen

- Gewoon de foto's van je telefoon gebruiken, ook iPhone-foto's (`.heic`). Het bouwprogramma verkleint ze zelf.
- **Portfolio:** zet foto's in `fotos/portfolio/`. Ze verschijnen op volgorde van naam,
  dus noem ze `01.jpg`, `02.jpg`, enz. Wil je een beschrijving onder de foto?
  Zet de bestandsnaam met een tekst onder `portfolio:` in `inhoud.yml`.
- **Foto van Lise:** vervang `fotos/lise.jpg` (de naam moet `lise` blijven).
- **Sfeerfoto homepage:** vervang `fotos/sfeer.jpg`.

De foto's die er nu in staan zijn **tijdelijke voorbeeldfoto's**. Vervang ze door echte foto's.

---

## De site bekijken op je Mac

### Eenmalig: voorbereiden

Open het programma **Terminal** (`Cmd + spatie`, typ "Terminal", druk op Enter).
Je ziet een venster waarin je commando's typt. Na elk commando druk je op Enter.

1. Controleer of Python er is (het programma waarmee `bouw.py` draait):
   ```
   python3 --version
   ```
   Zie je iets als `Python 3.12.1`? Dan is het goed. Krijg je een melding om
   "ontwikkelaarstools" te installeren? Klik op **Installeren**, wacht tot het klaar is en probeer het opnieuw.

2. Ga naar de map van de website. Typ `cd ` (met een spatie erachter) en
   **sleep dan de map `atelier-lise` vanuit Finder in het Terminal-venster**.
   Het pad wordt dan vanzelf ingevuld. Druk op Enter.
   *(`cd` betekent "change directory": ga naar deze map.)*

3. Installeer de hulpprogramma's die `bouw.py` gebruikt (voor het lezen van teksten en het verkleinen van foto's):
   ```
   python3 -m pip install -r bouw/requirements.txt
   ```

### Elke keer: bekijken

Ga in Terminal naar de map (stap 2 hierboven) en typ:
```
python3 bouw/bouw.py --bekijk
```
De site opent in je browser. Pas je iets aan in `inhoud.yml` of de fotomap, dan
wordt de site vanzelf opnieuw gebouwd. Ververs je browser (`Cmd + R`) om het te zien.
Stoppen doe je met `Ctrl + C` in Terminal.

---

## Online zetten

De map `.github/workflows/` bevat een opdracht voor GitHub: bij elke wijziging
bouwt GitHub de site zelf en zet hem online (GitHub Pages, gratis).
Je kunt dan ook **direct op github.com** teksten aanpassen en foto's uploaden.
Je hebt je Mac daar dus niet voor nodig.
