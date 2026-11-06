#!/usr/bin/env bash
# Ricrea TelcoCare com'era alla fine del primo workshop:
# Runtime con Memory, Gateway con il CRM, regole Cedar, Code Interpreter e Browser.
# Va lanciato dalla cartella del repository (~/agentcore-produzione). Dura circa 10 minuti.

set -euo pipefail
export AWS_REGION="${AWS_REGION:-us-east-1}"
RADICE="$(cd "$(dirname "$0")/.." && pwd)"
BASE="$RADICE/risorse/base"
cd "$RADICE"

passo() { printf "\n== %s  [%s]\n" "$1" "$(date +%H:%M:%S)"; }

if [ -d TelcoCare ]; then
  echo "La cartella TelcoCare esiste già: se vuoi ripartire da zero, lancia prima scripts/pulizia.sh e poi rm -rf TelcoCare."
  exit 1
fi

passo "1/6 Creo il progetto"
agentcore create --name TelcoCare --template agent-python-strands --skip-git
cd TelcoCare
agentcore remove memory --name agentMemory
agentcore add memory --name agentMemory --strategies SEMANTIC,USER_PREFERENCE,SUMMARIZATION

passo "2/6 Copio il codice dell'agente"
cp "$BASE/main.py" "$BASE/gateway_client.py" "$BASE/strumenti_aws.py" app/agent/
cp "$BASE/session.py" app/agent/memory/session.py
cp "$BASE/cdk-stack.ts" agentcore/cdk/lib/cdk-stack.ts
(cd app/agent && uv add "playwright>=1.42,<2")

passo "3/6 Creo la Lambda del CRM"
aws cloudformation deploy --stack-name telcocare-crm \
  --template-file "$BASE/crm-lambda.yaml" --capabilities CAPABILITY_IAM
CRM_ARN=$(aws cloudformation describe-stacks --stack-name telcocare-crm \
  --query "Stacks[0].Outputs[?OutputKey=='CrmFunctionArn'].OutputValue" --output text)

passo "4/6 Aggiungo il Gateway e pubblico (circa 5 minuti)"
mkdir -p schemas policies
cp "$BASE/crm_tools.json" schemas/
agentcore add gateway --name strumenti --authorizer-type AWS_IAM
agentcore add gateway-target --gateway strumenti --target-configuration \
  "{\"name\":\"crm\",\"targetType\":\"lambdaFunctionArn\",\"lambdaFunctionArn\":{\"lambdaArn\":\"$CRM_ARN\",\"toolSchemaFile\":\"schemas/crm_tools.json\"}}"
agentcore deploy

passo "5/6 Aggiungo le regole Cedar e pubblico (circa 2 minuti)"
GATEWAY_ARN=$(python3 ../scripts/id.py gateway --arn)
for F in consenti-letture accrediti-fino-a-100-euro; do
  python3 - "$BASE/$F.cedar" "policies/$F.cedar" "$GATEWAY_ARN" <<'PY'
import sys
sorgente, destinazione, arn = sys.argv[1:4]
open(destinazione, "w").write(open(sorgente).read().replace("GATEWAY_ARN", arn))
PY
done
agentcore add policy-engine --name regole --attach-to-gateways strumenti
agentcore add policy --engine regole --name ConsentiLetture --statement file://policies/consenti-letture.cedar
agentcore add policy --engine regole --name AccreditiFinoA100Euro --statement file://policies/accrediti-fino-a-100-euro.cedar
agentcore deploy

passo "6/6 Prova"
python3 ../scripts/chiedi.py --utente prova --sessione base "Sono Giulia, cliente C002. Quanto è la mia fattura di ottobre?"

echo
echo "TelcoCare è pronto. Da qui in poi lavora nella cartella $RADICE/TelcoCare."
