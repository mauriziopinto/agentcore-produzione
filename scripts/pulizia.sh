#!/usr/bin/env bash
# Pulizia finale: cancella tutto quello che il workshop ha creato nel tuo account.
# Va lanciato dalla cartella del progetto TelcoCare.
#
# 1. toglie tutte le risorse dal progetto e fa il deploy del progetto vuoto: il CLI cancella
#    lo stack AgentCore-TelcoCare-default (Runtime, Memory, Gateway, regole, endpoint, valutazioni);
# 2. cancella lo stack della Lambda del CRM (telcocare-crm), con la tabella degli accrediti;
# 3. cancella il pool Cognito (Lab 7), il guardrail (Lab 8) e gli allarmi (Lab 10), se esistono;
# 4. cancella i log group rimasti che contengono TelcoCare o telcocare nel nome.

set -u
REGIONE="${AWS_REGION:-us-east-1}"

if [ ! -f agentcore/agentcore.json ]; then
  echo "Lancia lo script dalla cartella del progetto TelcoCare (quella che contiene agentcore/agentcore.json)."
  exit 1
fi

echo "== 1/4 Risorse AgentCore del progetto"
agentcore remove all --yes
agentcore deploy --yes

echo
echo "== 2/4 Stack della Lambda del CRM"
if aws cloudformation describe-stacks --region "$REGIONE" --stack-name telcocare-crm >/dev/null 2>&1; then
  aws cloudformation delete-stack --region "$REGIONE" --stack-name telcocare-crm
  aws cloudformation wait stack-delete-complete --region "$REGIONE" --stack-name telcocare-crm
  echo "stack telcocare-crm cancellato"
else
  echo "stack telcocare-crm non presente"
fi

echo
echo "== 3/4 Cognito, guardrail, allarmi"
if [ -f ../.cognito.env ]; then
  # shellcheck disable=SC1091
  source ../.cognito.env
  aws cognito-idp delete-user-pool --region "$REGIONE" --user-pool-id "$COGNITO_POOL_ID" && echo "pool Cognito $COGNITO_POOL_ID cancellato"
  rm -f ../.cognito.env
fi
if [ -f guardrail.json ]; then
  ID=$(python3 -c "import json; print(json.load(open('guardrail.json'))['id'])")
  aws bedrock delete-guardrail --region "$REGIONE" --guardrail-identifier "$ID" && echo "guardrail $ID cancellato"
  rm -f guardrail.json
fi
ALLARMI=$(aws cloudwatch describe-alarms --region "$REGIONE" --alarm-name-prefix telcocare- --query 'MetricAlarms[].AlarmName' --output text)
if [ -n "$ALLARMI" ]; then
  aws cloudwatch delete-alarms --region "$REGIONE" --alarm-names $ALLARMI && echo "allarmi cancellati: $ALLARMI"
fi

echo
echo "== 4/4 Log group rimasti"
GRUPPI=$(aws logs describe-log-groups --region "$REGIONE" \
  --query "logGroups[?contains(logGroupName,'TelcoCare') || contains(logGroupName,'telcocare')].logGroupName" \
  --output text)
if [ -z "$GRUPPI" ] || [ "$GRUPPI" = "None" ]; then
  echo "nessun log group da cancellare"
else
  for G in $GRUPPI; do
    aws logs delete-log-group --region "$REGIONE" --log-group-name "$G" && echo "cancellato $G"
  done
fi

echo
echo "Pulizia completata."
