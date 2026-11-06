#!/usr/bin/env bash
# Fa il replay del dataset di test su un endpoint del Runtime e applica il quality gate.
# Uso (dalla cartella del progetto TelcoCare):
#   bash ../scripts/prove.sh                 # endpoint DEFAULT, cioè l'ultima versione pubblicata
#   bash ../scripts/prove.sh produzione      # un endpoint preciso
# Dura circa 4 minuti: 1 minuto per le conversazioni, 3 di attesa perché le trace siano pronte.

set -uo pipefail
ENDPOINT="${1:-DEFAULT}"
PROVE="${PROVE:-../risorse/lab1/prove.jsonl}"
RISULTATI="risultati-$ENDPOINT-$(date +%H%M%S).json"
# Un utente nuovo a ogni giro: altrimenti la Memory ricorda le risposte dei giri precedenti
# e i test non partono puliti.
UTENTE="collaudo-$(date +%s)"

echo "Test su endpoint $ENDPOINT, utente $UTENTE, file $PROVE"
agentcore eval ondemand simulate \
  --runtime-id "$(python3 ../scripts/id.py runtime)" \
  --endpoint "$ENDPOINT" \
  --payload-template "{\"prompt\":\"{input}\",\"actorId\":\"$UTENTE\"}" \
  --dataset "$PROVE" \
  --evaluators Builtin.GoalSuccessRate Builtin.TrajectoryAnyOrderMatch \
  --json > "$RISULTATI" || { echo "simulate non è riuscito: guarda $RISULTATI"; exit 2; }

echo "Risultati completi in $RISULTATI"
echo
python3 ../scripts/riepilogo_prove.py "$RISULTATI" --dettagli
