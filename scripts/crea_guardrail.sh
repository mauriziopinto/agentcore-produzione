#!/usr/bin/env bash
# Lab 8: crea un guardrail di Amazon Bedrock che maschera i dati personali nelle risposte.
# - email e numeri di telefono riconosciuti dal servizio (italiano supportato);
# - numeri di cellulare italiani con un'espressione regolare (nel listino le regex non si pagano).
# Scrive ID e versione in guardrail.json: al prossimo deploy lo stack CDK li passa al Runtime.
# Va lanciato dalla cartella del progetto TelcoCare.
set -euo pipefail
export AWS_REGION="${AWS_REGION:-us-east-1}"

ID=$(aws bedrock create-guardrail --name telcocare-dati-personali \
  --description "Workshop AgentCore: maschera email e numeri di telefono nelle risposte" \
  --blocked-input-messaging "Non posso elaborare questa richiesta." \
  --blocked-outputs-messaging "Non posso mostrare questa risposta." \
  --sensitive-information-policy-config '{
    "piiEntitiesConfig": [
      {"type": "EMAIL", "action": "ANONYMIZE", "inputEnabled": false, "outputEnabled": true, "outputAction": "ANONYMIZE"},
      {"type": "PHONE", "action": "ANONYMIZE", "inputEnabled": false, "outputEnabled": true, "outputAction": "ANONYMIZE"}
    ],
    "regexesConfig": [
      {"name": "cellulare", "description": "Numero di cellulare italiano", "pattern": "\\b3\\d{2}[ .]?\\d{6,7}\\b",
       "action": "ANONYMIZE", "inputEnabled": false, "outputEnabled": true, "outputAction": "ANONYMIZE"}
    ]
  }' \
  --tags key=Purpose,value=telcocare-workshop \
  --query guardrailId --output text)
VERSIONE=$(aws bedrock create-guardrail-version --guardrail-identifier "$ID" --query version --output text)
printf '{"id": "%s", "versione": "%s"}\n' "$ID" "$VERSIONE" > guardrail.json
echo "Guardrail $ID, versione $VERSIONE, scritto in guardrail.json"
