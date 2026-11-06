#!/usr/bin/env bash
# Lab 7: stampa un access token Cognito per un utente di prova (anna o mario).
# Uso: TOKEN=$(bash ../scripts/token.sh anna)
set -euo pipefail
export AWS_REGION="${AWS_REGION:-us-east-1}"
source ../.cognito.env
aws cognito-idp initiate-auth --client-id "$COGNITO_CLIENT_ID" --auth-flow USER_PASSWORD_AUTH \
  --auth-parameters "USERNAME=${1:?utente},PASSWORD=$COGNITO_PASSWORD" \
  --query AuthenticationResult.AccessToken --output text
