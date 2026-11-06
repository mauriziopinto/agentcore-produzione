#!/usr/bin/env python3
"""Costruisce le pagine del sito: ogni file .html di questa cartella è il contenuto di <main>,
con il titolo nella prima riga come commento <!-- titolo: ... -->. Uso: python3 docs/_pezzi/costruisci.py"""
import pathlib
import re

QUI = pathlib.Path(__file__).parent
SITO = QUI.parent

MODELLO = """<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{titolo}</title>
<link rel="stylesheet" href="assets/stile.css">
</head>
<body>
<header class="testata">
  <button class="menu-bottone" type="button">Menu</button>
  <a href="index.html"><span class="marchio">AgentCore</span> in produzione</a>
  <span class="spazio"></span>
  <span>TelcoCare</span>
</header>
<div class="contenitore">
<nav class="indice"></nav>
<main>
{contenuto}
</main>
</div>
<script src="assets/sito.js"></script>
</body>
</html>
"""

for pezzo in sorted(QUI.glob("*.html")):
    testo = pezzo.read_text()
    m = re.match(r"<!-- titolo: (.*?) -->\n", testo)
    if not m:
        raise SystemExit(f"{pezzo.name}: manca la riga <!-- titolo: ... -->")
    (SITO / pezzo.name).write_text(MODELLO.format(titolo=m.group(1), contenuto=testo[m.end():].strip()))
    print("scritto", pezzo.name)
