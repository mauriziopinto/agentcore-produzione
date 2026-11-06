#!/usr/bin/env bash
# Lab 10: due allarmi CloudWatch sul Runtime, come per qualunque servizio in produzione.
# - errori del servizio (SystemErrors) sull'endpoint indicato: almeno 1 in 5 minuti;
# - latenza p90 dell'endpoint sopra una soglia, in millisecondi (default 30000).
# Uso (dalla cartella del progetto TelcoCare):
#   bash ../scripts/crea_allarmi.sh                    # endpoint DEFAULT, soglia 30 s
#   bash ../scripts/crea_allarmi.sh produzione 20000
# Gli allarmi non mandano notifiche: in produzione si collega un topic SNS con --alarm-actions.
set -euo pipefail
export AWS_REGION="${AWS_REGION:-us-east-1}"
ENDPOINT="${1:-DEFAULT}"
SOGLIA_MS="${2:-30000}"
ARN=$(python3 ../scripts/id.py runtime --arn)
NOME_RUNTIME=$(basename "$ARN" | sed -E 's/-[A-Za-z0-9]+$//')
DIMENSIONI="Name=Resource,Value=$ARN Name=Operation,Value=InvokeAgentRuntime Name=Name,Value=$NOME_RUNTIME::$ENDPOINT"

aws cloudwatch put-metric-alarm --alarm-name "telcocare-$ENDPOINT-errori" \
  --alarm-description "Workshop AgentCore: errori del servizio sul Runtime TelcoCare ($ENDPOINT)" \
  --namespace AWS/Bedrock-AgentCore --metric-name SystemErrors --dimensions $DIMENSIONI \
  --statistic Sum --period 300 --evaluation-periods 1 --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold --treat-missing-data notBreaching

aws cloudwatch put-metric-alarm --alarm-name "telcocare-$ENDPOINT-latenza" \
  --alarm-description "Workshop AgentCore: latenza p90 del Runtime TelcoCare ($ENDPOINT) sopra $SOGLIA_MS ms" \
  --namespace AWS/Bedrock-AgentCore --metric-name Latency --dimensions $DIMENSIONI \
  --extended-statistic p90 --period 60 --evaluation-periods 1 --threshold "$SOGLIA_MS" \
  --comparison-operator GreaterThanThreshold --treat-missing-data notBreaching

echo "Allarmi creati: telcocare-$ENDPOINT-errori e telcocare-$ENDPOINT-latenza (soglia $SOGLIA_MS ms)"
aws cloudwatch describe-alarms --alarm-name-prefix "telcocare-$ENDPOINT" \
  --query 'MetricAlarms[].[AlarmName,StateValue]' --output table
