#!/usr/bin/env bash
# Lab 7: crea un pool Amazon Cognito con due clienti di prova, anna (C002) e mario (C001).
# Il pool NON permette la registrazione autonoma: gli utenti li crea solo l'amministratore.
# Scrive gli identificativi in ../.cognito.env (leggibile solo da te) e ne stampa il riepilogo.
# Va lanciato dalla cartella del progetto TelcoCare.

set -euo pipefail
export AWS_REGION="${AWS_REGION:-us-east-1}"
FILE="../.cognito.env"

if [ -f "$FILE" ]; then
  echo "Esiste già $FILE: il pool è già stato creato."; cat "$FILE" | grep -v PASSWORD; exit 0
fi

POOL=$(aws cognito-idp create-user-pool --pool-name telcocare-clienti \
  --admin-create-user-config AllowAdminCreateUserOnly=true \
  --policies 'PasswordPolicy={MinimumLength=12,RequireUppercase=true,RequireLowercase=true,RequireNumbers=true,RequireSymbols=false}' \
  --user-pool-tags Purpose=telcocare-workshop \
  --query UserPool.Id --output text)
CLIENT=$(aws cognito-idp create-user-pool-client --user-pool-id "$POOL" --client-name telcocare-app \
  --no-generate-secret --explicit-auth-flows ALLOW_USER_PASSWORD_AUTH ALLOW_REFRESH_TOKEN_AUTH \
  --query UserPoolClient.ClientId --output text)

PASSWORD="Tc$(python3 -c 'import secrets; print(secrets.token_hex(8))')A1"
for UTENTE in anna mario; do
  aws cognito-idp admin-create-user --user-pool-id "$POOL" --username "$UTENTE" \
    --message-action SUPPRESS >/dev/null
  aws cognito-idp admin-set-user-password --user-pool-id "$POOL" --username "$UTENTE" \
    --password "$PASSWORD" --permanent
done

umask 077
cat > "$FILE" <<EOF
COGNITO_POOL_ID=$POOL
COGNITO_CLIENT_ID=$CLIENT
COGNITO_DISCOVERY_URL=https://cognito-idp.$AWS_REGION.amazonaws.com/$POOL/.well-known/openid-configuration
COGNITO_PASSWORD=$PASSWORD
EOF

echo "Pool $POOL, client $CLIENT, utenti anna e mario."
echo "Controllo che la registrazione autonoma sia rifiutata:"
if aws cognito-idp sign-up --client-id "$CLIENT" --username intruso --password "Intruso123456A" >/dev/null 2>&1; then
  echo "  ATTENZIONE: la registrazione autonoma è aperta. Chiama chi conduce il workshop."
  exit 1
else
  echo "  rifiutata, come deve essere."
fi
