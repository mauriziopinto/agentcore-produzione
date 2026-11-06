#!/usr/bin/env bash
# Lab 8: maschera email e numeri di telefono nei log del Runtime, e limita la conservazione a 30 giorni.
# La maschera vale per i log scritti da ora in poi. Chi ha il permesso logs:Unmask può ancora vedere
# il dato in chiaro: è quel permesso che decide chi legge i dati dei clienti.
# L'espressione regolare vuole lo spazio fra prefisso e numero, come nei dati del CRM: senza spazio
# maschererebbe anche durate e contatori numerici dei log (lo abbiamo visto succedere).
# Va lanciato dalla cartella del progetto TelcoCare.
set -euo pipefail
export AWS_REGION="${AWS_REGION:-us-east-1}"
GRUPPO="/aws/bedrock-agentcore/runtimes/$(python3 ../scripts/id.py runtime)-DEFAULT"

POLICY=$(cat <<'EOF'
{
  "Name": "telcocare-dati-personali",
  "Version": "2021-06-01",
  "Configuration": {
    "CustomDataIdentifier": [
      {"Name": "NumeroTelefono", "Regex": "\\b3\\d{2} \\d{6,7}\\b|\\b0\\d{1,3} \\d{6,8}\\b"}
    ]
  },
  "Statement": [
    {
      "Sid": "audit",
      "DataIdentifier": ["arn:aws:dataprotection::aws:data-identifier/EmailAddress", "NumeroTelefono"],
      "Operation": {"Audit": {"FindingsDestination": {}}}
    },
    {
      "Sid": "maschera",
      "DataIdentifier": ["arn:aws:dataprotection::aws:data-identifier/EmailAddress", "NumeroTelefono"],
      "Operation": {"Deidentify": {"MaskConfig": {}}}
    }
  ]
}
EOF
)

aws logs put-data-protection-policy --log-group-identifier "$GRUPPO" --policy-document "$POLICY" >/dev/null
aws logs put-retention-policy --log-group-name "$GRUPPO" --retention-in-days 30
echo "Maschera e conservazione di 30 giorni attive su $GRUPPO"
