#!/usr/bin/env python3
"""Rende leggibile la risposta in streaming di `agentcore invoke`.

Uso:
    agentcore invoke --runtime agent --payload '{"prompt":"..."}' 2>&1 | python3 ../scripts/leggi.py

Stampa il testo della risposta e, su righe separate, gli strumenti che l'agente
ha chiamato. Le righe che non riconosce (errori, riepilogo finale) le stampa così come sono.
"""
import json
import sys


def main() -> None:
    in_testo = False
    for riga in sys.stdin:
        riga = riga.rstrip("\n")
        if not riga.startswith("data: "):
            if riga.startswith("status="):
                campi = dict(p.split("=", 1) for p in riga.split() if "=" in p)
                if in_testo:
                    print()
                    in_testo = False
                print(f"[sessione] {campi.get('runtime-session-id', '-')}  [http] {campi.get('status', '-')}")
            elif riga.strip():
                if in_testo:
                    print()
                    in_testo = False
                print(riga)
            continue
        try:
            dato = json.loads(riga[len("data: "):])
        except json.JSONDecodeError:
            print(riga[len("data: "):])
            continue
        if isinstance(dato, str):
            print(dato)
            continue
        if isinstance(dato, dict) and "grafo" in dato:
            if in_testo:
                print()
                in_testo = False
            g = dato["grafo"]
            print(f"\n[percorso] {g.get('percorso')}  [stato] {g.get('stato')}")
            print(f"[token] {g.get('token_input')} in ingresso, {g.get('token_output')} in uscita")
            if g.get("controllo_finale"):
                print(f"[ultimo controllo] {g.get('controllo_finale')}")
            continue
        if isinstance(dato, dict) and "limite_raggiunto" in dato:
            if in_testo:
                print()
                in_testo = False
            print(f"\n[limite raggiunto] {dato['limite_raggiunto']}: l'agente si è fermato prima di finire")
            continue
        if isinstance(dato, dict) and "costo" in dato:
            if in_testo:
                print()
                in_testo = False
            c = dato["costo"]
            print(f"\n[costo] {c.get('modalita')} ({c.get('percorso')}): {c.get('token_input')} token in ingresso, "
                  f"{c.get('token_output')} in uscita, {c.get('chiamate_modello')} chiamate al modello, {c.get('secondi')} s")
            for nome, v in (c.get("per_agente") or {}).items():
                print(f"        {nome}: {v.get('input')} in, {v.get('output')} out, {v.get('chiamate_modello')} chiamate")
            continue
        if isinstance(dato, dict) and "approvazione_richiesta" in dato:
            if in_testo:
                print()
                in_testo = False
            richiesta = dato["approvazione_richiesta"]
            print(f"\n[approvazione richiesta] {json.dumps(richiesta.get('dettagli'), ensure_ascii=False)}")
            print(f"[id approvazione] {richiesta.get('id')}", flush=True)
            continue
        evento = dato.get("event", {}) if isinstance(dato, dict) else {}

        inizio = evento.get("contentBlockStart", {}).get("start", {})
        if "toolUse" in inizio:
            if in_testo:
                print()
                in_testo = False
            print(f"\n[strumento] {inizio['toolUse'].get('name')}", flush=True)

        delta = evento.get("contentBlockDelta", {}).get("delta", {})
        if "text" in delta:
            print(delta["text"], end="", flush=True)
            in_testo = True

        uso = evento.get("metadata", {}).get("usage")
        if uso:
            if in_testo:
                print()
                in_testo = False
            print(f"[token] input {uso.get('inputTokens')}, output {uso.get('outputTokens')}")

        if isinstance(dato, dict) and "error" in dato:
            print(f"\n[errore] {dato['error']}")
    if in_testo:
        print()


if __name__ == "__main__":
    main()
