#!/usr/bin/env bash
# Lab 5: porta in TelcoCare il codice di tutti i lab da fare da soli (dal 5 all'11) e lo pubblica.
# Dopo questo passo ogni lab cambia solo l'infrastruttura, quindi i lab si possono fare in qualunque ordine.
# Va lanciato dalla cartella del progetto TelcoCare. Dura circa 3 minuti.
set -euo pipefail
export AWS_REGION="${AWS_REGION:-us-east-1}"
P=../risorse/percorso
if [ ! -f agentcore/agentcore.json ]; then echo "Lancialo dalla cartella TelcoCare."; exit 1; fi
cp "$P"/{main.py,squadra.py,remoto.py,reclamo.py,sciame.py,gateway_client.py,approvazione.py,strumenti_aws.py} app/agent/
cp "$P/load.py" app/agent/model/load.py
cp "$P/cdk-stack.ts" agentcore/cdk/lib/cdk-stack.ts
# Lo specialista remoto del Lab 9 usa il client A2A di Strands.
(cd app/agent && uv add "strands-agents[a2a]>=1.62.0,<2.0.0")
agentcore deploy
echo "Codice del percorso pubblicato."
