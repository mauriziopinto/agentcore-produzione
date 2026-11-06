#!/usr/bin/env python3
"""Fa puntare un endpoint del Runtime a una versione, modificando agentcore/agentcore.json.

Uso (dalla cartella del progetto TelcoCare):
    python3 ../scripts/punta_endpoint.py produzione 4     # promozione alla versione 4
    python3 ../scripts/punta_endpoint.py produzione 2     # ritorno alla versione 2
Poi: agentcore deploy

Il file agentcore.json è la fonte di verità: la modifica resta nel progetto, si vede
nella revisione del codice e si annulla come ogni altra modifica.
"""
import json
import sys

FILE = "agentcore/agentcore.json"


def main() -> None:
    if len(sys.argv) != 3 or not sys.argv[2].isdigit():
        sys.exit("uso: punta_endpoint.py <endpoint> <versione>")
    nome, versione = sys.argv[1], int(sys.argv[2])
    progetto = json.load(open(FILE))
    runtime = next((r for r in progetto.get("runtimes", []) if r.get("name") == "agent"), None)
    if runtime is None or nome not in runtime.get("endpoints", {}):
        sys.exit(f"l'endpoint {nome} non esiste nel progetto: aggiungilo con agentcore add runtime-endpoint")
    prima = runtime["endpoints"][nome]["version"]
    runtime["endpoints"][nome]["version"] = versione
    json.dump(progetto, open(FILE, "w"), indent=2)
    open(FILE, "a").write("\n")
    print(f"endpoint {nome}: versione {prima} -> {versione}. Ora lancia: agentcore deploy")


if __name__ == "__main__":
    main()
