#!/usr/bin/env python3
"""Lab 4: manda le stesse domande all'agente singolo, al supervisore e al routing deterministico,
e confronta token, chiamate al modello e tempi.

Uso (dalla cartella del progetto TelcoCare):
    python3 ../scripts/confronta.py
    python3 ../scripts/confronta.py --risposte      # stampa anche le risposte
"""
import argparse
import json
import subprocess
import time
import uuid

DOMANDE = [
    ("fattura", "Sono il cliente C002. La fattura di ottobre è giusta?"),
    ("guasto", "Sono il cliente C001. La fibra è lentissima da ieri sera, potete aprire un ticket?"),
    ("entrambi", "Sono il cliente C003. Ho una fattura scaduta e in più la linea non va da stamattina: cosa devo fare?"),
]
MODALITA = ["singolo", "supervisore", "instradato"]


def chiama(modalita: str, domanda: str) -> tuple[str, dict]:
    payload = json.dumps({"prompt": domanda, "modalita": modalita, "actorId": "confronto"}, ensure_ascii=False)
    sessione = f"confronto-{modalita}-{uuid.uuid4().hex}"
    uscita = subprocess.run(
        ["agentcore", "invoke", "--runtime", "agent", "--payload", payload, "--session-id", sessione],
        capture_output=True, text=True,
    ).stdout
    testo, costo = "", {}
    for riga in uscita.splitlines():
        if not riga.startswith("data: "):
            continue
        try:
            dato = json.loads(riga[6:])
        except json.JSONDecodeError:
            continue
        if isinstance(dato, dict) and "costo" in dato:
            costo = dato["costo"]
        elif isinstance(dato, dict):
            testo += dato.get("event", {}).get("contentBlockDelta", {}).get("delta", {}).get("text", "")
        elif isinstance(dato, str):
            testo += dato
    return testo, costo


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--risposte", action="store_true", help="stampa anche le risposte")
    a = p.parse_args()

    totali = {m: {"token": 0, "chiamate": 0, "secondi": 0.0} for m in MODALITA}
    print(f"{'domanda':<10}{'modalità':<13}{'percorso':<32}{'token':>8}{'chiamate':>10}{'secondi':>9}")
    for nome, domanda in DOMANDE:
        for modalita in MODALITA:
            inizio = time.time()
            testo, c = chiama(modalita, domanda)
            if not c:
                print(f"{nome:<10}{modalita:<13}errore: nessun conto ricevuto (dopo {time.time() - inizio:.0f} s)")
                continue
            token = c["token_input"] + c["token_output"]
            totali[modalita]["token"] += token
            totali[modalita]["chiamate"] += c["chiamate_modello"]
            totali[modalita]["secondi"] += c["secondi"]
            print(f"{nome:<10}{modalita:<13}{c['percorso']:<32}{token:>8}{c['chiamate_modello']:>10}{c['secondi']:>9}")
            if a.risposte:
                print("    " + testo.strip().replace("\n", "\n    ")[:800])
        print()
    print("Totale sulle tre domande:")
    base = totali["singolo"]["token"] or 1
    for m in MODALITA:
        t = totali[m]
        print(f"  {m:<12} {t['token']:>7} token ({100 * t['token'] / base:.0f}% del singolo), "
              f"{t['chiamate']} chiamate al modello, {t['secondi']:.0f} s")


if __name__ == "__main__":
    main()
