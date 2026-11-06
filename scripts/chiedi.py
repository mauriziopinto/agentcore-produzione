#!/usr/bin/env python3
"""Manda una domanda all'agente TelcoCare e stampa la risposta in modo leggibile.

Uso (dalla cartella del progetto TelcoCare):
    python3 ../scripts/chiedi.py --utente anna --sessione uno "Ciao, sono Anna"
    python3 ../scripts/chiedi.py --endpoint produzione --utente anna "Ciao"   # un endpoint preciso
    python3 ../scripts/chiedi.py --utente op --sessione acc --approva <ID>    # risposta del responsabile
    python3 ../scripts/chiedi.py --modalita supervisore "Sono C001, ..."   # Lab 4 e seguenti
    python3 ../scripts/chiedi.py --locale "Ciao"   # agente in locale (agentcore dev --port 8181)

Lo script costruisce il payload JSON (così gli apostrofi non rompono la shell),
stampa il comando `agentcore invoke` che esegue e filtra la risposta in streaming.
Lo stesso nome di sessione, con lo stesso utente, dà sempre lo stesso ID di sessione.
"""
import argparse
import json
import os
import shlex
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import leggi  # noqa: E402


def id_sessione(utente: str, sessione: str) -> str:
    # AgentCore Runtime vuole ID di sessione di almeno 33 caratteri.
    base = f"telcocare-{utente}-{sessione}-"
    return base + "0" * max(0, 40 - len(base))


def main() -> None:
    p = argparse.ArgumentParser(description="Domanda all'agente TelcoCare")
    p.add_argument("domanda", nargs="?", help="il testo da mandare all'agente")
    p.add_argument("--utente", default="default", help="chi sta scrivendo (actorId per la Memory)")
    p.add_argument("--sessione", default="uno", help="nome breve della conversazione")
    p.add_argument("--endpoint", help="endpoint del Runtime da chiamare (default: DEFAULT, l'ultima versione)")
    p.add_argument("--runtime", default="agent", help="nome del Runtime nel progetto (default: agent)")
    p.add_argument("--modalita", help="singolo, supervisore, instradato, remoto, reclamo, sciame, sciame-senza-limiti")
    p.add_argument("--rimbalzo", action="store_true", help="Lab 11: istruzioni scritte male, che invitano al ping-pong")
    p.add_argument("--approva", metavar="ID", help="approva la richiesta di approvazione con questo ID")
    p.add_argument("--rifiuta", metavar="ID", help="rifiuta la richiesta di approvazione con questo ID")
    p.add_argument("--locale", action="store_true", help="usa l'agente in locale (agentcore dev)")
    p.add_argument("--porta", default="8181", help="porta dell'agente locale (default 8181, la 8080 è di Code Editor)")
    p.add_argument("--solo-id", action="store_true", help="stampa solo l'ID di sessione, senza chiamare l'agente")
    a = p.parse_args()

    if a.solo_id:
        print(id_sessione(a.utente, a.sessione))
        return

    if a.approva or a.rifiuta:
        risposta = "approvo" if a.approva else "rifiuto"
        corpo = {"approvazione": {"id": a.approva or a.rifiuta, "risposta": risposta}, "actorId": a.utente}
    elif a.domanda:
        corpo = {"prompt": a.domanda, "actorId": a.utente}
        if a.modalita:
            corpo["modalita"] = a.modalita
        if a.rimbalzo:
            corpo["rimbalzo"] = True
    else:
        p.error("manca la domanda")

    payload = json.dumps(corpo, ensure_ascii=False)
    comando = ["agentcore", "invoke", "--runtime", a.runtime, "--payload", payload]
    if a.locale:
        comando += ["--local", "--port", a.porta]
    else:
        comando += ["--session-id", id_sessione(a.utente, a.sessione)]
    if a.endpoint:
        comando += ["--qualifier", a.endpoint]

    print("[comando] " + " ".join(shlex.quote(c) for c in comando))
    print()
    proc = subprocess.Popen(comando, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    sys.stdin = proc.stdout
    leggi.main()
    sys.exit(proc.wait())


if __name__ == "__main__":
    main()
