"""Strumenti gestiti da AWS: Code Interpreter e Browser.

Il codice scritto dal modello gira in una sandbox isolata di AgentCore, non nel Runtime.
Le pagine web si aprono in un browser remoto isolato, guidato con Playwright via CDP.
"""
import json
import os

from bedrock_agentcore.tools.browser_client import browser_session
from bedrock_agentcore.tools.code_interpreter_client import code_session
from strands import tool

REGION = os.getenv("AWS_REGION", "us-east-1")


def _prepara_playwright() -> None:
    """Nel pacchetto CodeZip il binario node di Playwright perde il permesso di esecuzione.
    Lo copiamo in /tmp, lo rendiamo eseguibile e diciamo a Playwright di usare quella copia."""
    import inspect
    import shutil
    import stat

    import playwright

    originale = os.path.join(os.path.dirname(inspect.getfile(playwright)), "driver", "node")
    if os.access(originale, os.X_OK):
        return
    copia = "/tmp/playwright-node"
    if not os.path.exists(copia):
        shutil.copyfile(originale, copia)
        os.chmod(copia, stat.S_IRWXU)
    os.environ["PLAYWRIGHT_NODEJS_PATH"] = copia


@tool
def esegui_python(codice: str) -> str:
    """Esegue codice Python in una sandbox isolata (AgentCore Code Interpreter) e restituisce l'output.
    Usalo per calcoli, statistiche, tabelle e analisi di dati. Stampa i risultati con print().

    Args:
        codice: il codice Python da eseguire
    """
    with code_session(REGION) as client:
        risposta = client.invoke("executeCode", {"code": codice, "language": "python"})
        for evento in risposta["stream"]:
            return json.dumps(evento["result"], ensure_ascii=False)
    return "nessun risultato"


@tool
def leggi_pagina_web(url: str) -> str:
    """Apre una pagina web in un browser remoto isolato (AgentCore Browser) e restituisce
    il titolo e il testo visibile della pagina, al massimo 6000 caratteri.

    Args:
        url: indirizzo completo della pagina, per esempio https://it.wikipedia.org/wiki/Fibra_ottica
    """
    from playwright.sync_api import sync_playwright

    _prepara_playwright()
    with browser_session(REGION) as client:
        ws_url, headers = client.generate_ws_headers()
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(ws_url, headers=headers)
            context = browser.contexts[0] if browser.contexts else browser.new_context()
            page = context.pages[0] if context.pages else context.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            titolo = page.title()
            testo = page.inner_text("body")
            browser.close()
    return f"Titolo: {titolo}\n\n{testo[:6000]}"
