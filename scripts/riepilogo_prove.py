#!/usr/bin/env python3
"""Riassume l'output JSON di `agentcore eval ondemand simulate` e fa da cancello di qualità.

Uso:
    agentcore eval ondemand simulate ... --json > risultati.json
    python3 ../scripts/riepilogo_prove.py risultati.json            # soglia 100%
    python3 ../scripts/riepilogo_prove.py risultati.json --soglia 90

Stampa una riga per ogni prova, con l'esito di ogni valutatore, e alla fine la percentuale
di prove superate. Esce con codice 1 se la percentuale è sotto la soglia: in una pipeline
questo ferma il rilascio.
"""
import argparse
import json
import sys


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("file", help="file JSON prodotto da simulate --json")
    p.add_argument("--soglia", type=float, default=100.0, help="percentuale minima di prove superate (default 100)")
    p.add_argument("--dettagli", action="store_true", help="stampa anche la spiegazione dei valutatori per le prove fallite")
    a = p.parse_args()

    dati = json.load(open(a.file))
    nomi = {s["sessionId"]: s["exampleId"] for s in dati.get("sessions", [])}
    esiti: dict[str, dict[str, tuple]] = {}
    for r in dati.get("results", []):
        sessione = r.get("context", {}).get("spanContext", {}).get("sessionId")
        prova = nomi.get(sessione, sessione)
        valutatore = r.get("evaluatorId", "?").replace("Builtin.", "")
        esiti.setdefault(prova, {})[valutatore] = (r.get("value"), r.get("explanation") or r.get("errorMessage") or "")

    valutatori = sorted({v for e in esiti.values() for v in e})
    print(f"{'prova':<22}" + "".join(f"{v:<26}" for v in valutatori))
    superate = 0
    for prova in sorted(esiti):
        riga = f"{prova:<22}"
        ok = True
        for v in valutatori:
            valore = esiti[prova].get(v, (None, ""))[0]
            if valore is None:
                riga += f"{'-':<26}"
            elif valore >= 1:
                riga += f"{'ok':<26}"
            else:
                riga += f"{'NO':<26}"
                ok = False
        superate += ok
        print(riga)
        if a.dettagli and not ok:
            for v in valutatori:
                valore, spiegazione = esiti[prova].get(v, (None, ""))
                if valore is not None and valore < 1:
                    print(f"    {v}: {spiegazione[:400]}")

    totale = len(esiti)
    for f in dati.get("failures", []):
        print(f"[errore] {f}")
    percentuale = 100.0 * superate / totale if totale else 0.0
    print(f"\nProve superate: {superate} su {totale} ({percentuale:.0f}%), soglia {a.soglia:.0f}%")
    if percentuale < a.soglia:
        print("CANCELLO CHIUSO: questa versione non va rilasciata.")
        sys.exit(1)
    print("CANCELLO APERTO: la versione si può rilasciare.")


if __name__ == "__main__":
    main()
