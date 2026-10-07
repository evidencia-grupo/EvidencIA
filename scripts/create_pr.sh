#!/usr/bin/env bash
set -euo pipefail

# Idempotent PR creator for branch feat/hu10-no-captions
# Usage: export GITHUB_TOKEN=ghp_xxx
# ./scripts/create_pr.sh

REPO_OWNER="evidencia-grupo"
REPO_NAME="EvidencIA"
BRANCH="feat/hu10-no-captions"
BASE_BRANCH="main"
REVIEWERS='["lipestile","luizoryone"]'

die(){ echo "ERROR: $*" >&2; exit 1; }

[ -n "${GITHUB_TOKEN:-}" ] || die "GITHUB_TOKEN not set. Export it and retry."

echo "Checking token..."
USER_JSON=$(curl -s -H "Authorization: token $GITHUB_TOKEN" -H "Accept: application/vnd.github+json" https://api.github.com/user)
if echo "$USER_JSON" | grep -q '"message"' ; then
  echo "Bad token response from GitHub:" >&2
  echo "$USER_JSON" >&2
  exit 1
fi
LOGIN=$(echo "$USER_JSON" | grep -m1 '"login"' | sed -E 's/.*"login": *"([^"]+)".*/\1/')
echo "Authenticated as: $LOGIN"

echo "Searching for existing open PR from $BRANCH..."
PR_SEARCH=$(curl -s -H "Authorization: token $GITHUB_TOKEN" -H "Accept: application/vnd.github+json" "https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/pulls?head=${REPO_OWNER}:${BRANCH}&state=open")
if echo "$PR_SEARCH" | grep -q '"message"' ; then
  echo "GitHub API error while searching PRs:" >&2
  echo "$PR_SEARCH" >&2
  exit 1
fi

# detect empty array
if [ "$(echo "$PR_SEARCH" | tr -d '\n' | sed -e 's/ //g')" = "[]" ]; then
  echo "No existing open PR found. Creating a new PR..."
  read -r -d '' PR_BODY <<'JSON'
{
  "title": "feat(HU10): Notificação rápida de ausência de transcrição (NO_CAPTIONS)",
  "head": "feat/hu10-no-captions",
  "base": "main",
  "body": "Resolve #10 — Detecção rápida de ausência de legendas (NO_CAPTIONS) no content-script e melhorias no caption-parser.\n\nTestes (Vitest) e build foram executados localmente com sucesso."
}
JSON
  CREATE_RESP=$(curl -s -X POST -H "Authorization: token $GITHUB_TOKEN" -H "Accept: application/vnd.github+json" "https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/pulls" -d "$PR_BODY")
  if echo "$CREATE_RESP" | grep -q '"message"' ; then
    echo "Error creating PR:" >&2
    echo "$CREATE_RESP" >&2
    exit 1
  fi
  PR_NUMBER=$(echo "$CREATE_RESP" | grep -m1 '"number"' | sed -E 's/.*"number": *([0-9]+).*/\1/')
  PR_URL=$(echo "$CREATE_RESP" | grep -m1 '"html_url"' | sed -E 's/.*"html_url": *"([^\"]+)".*/\1/')
  echo "Created PR: #$PR_NUMBER $PR_URL"
else
  PR_NUMBER=$(echo "$PR_SEARCH" | grep -m1 '"number"' | sed -E 's/.*"number": *([0-9]+).*/\1/')
  PR_URL=$(echo "$PR_SEARCH" | grep -m1 '"html_url"' | sed -E 's/.*"html_url": *"([^\"]+)".*/\1/')
  echo "Found existing PR: #$PR_NUMBER $PR_URL"
fi

echo "Requesting reviewers: lipestile, luizoryone"
REVIEW_RESP=$(curl -s -X POST -H "Authorization: token $GITHUB_TOKEN" -H "Accept: application/vnd.github+json" "https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/pulls/${PR_NUMBER}/requested_reviewers" -d "{\"reviewers\": [\"lipestile\",\"luizoryone\"]}")
if echo "$REVIEW_RESP" | grep -q '"message"' ; then
  echo "Warning: could not request reviewers or reviewers already requested. Response:" >&2
  echo "$REVIEW_RESP" >&2
else
  echo "Reviewers requested."
fi

echo "Posting contextual comment on the PR..."
COMMENT_BODY=$(cat <<'COMMENT'
@lipestile @luizoryone Por favor, poderiam revisar este PR referente à issue #10 (HU10)?

Principais mudanças:
- detecção rápida de ausência de legendas (NO_CAPTIONS) no content-script
- melhorias no caption-parser (sanitização e fallback de parser)

Testes locais (Vitest) e build executados com sucesso. Obrigado!
COMMENT
)
COMMENT_JSON=$(printf '%s' "$COMMENT_BODY" | python -c 'import json,sys; print(json.dumps(sys.stdin.read()))')
COMMENT_RESP=$(curl -s -X POST -H "Authorization: token $GITHUB_TOKEN" -H "Accept: application/vnd.github+json" "https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/issues/${PR_NUMBER}/comments" -d "{\"body\": $COMMENT_JSON }") || true
if echo "$COMMENT_RESP" | grep -q '"message"' ; then
  echo "Warning: failed to post comment (it may already exist). Response:" >&2
  echo "$COMMENT_RESP" >&2
else
  echo "Comment posted."
fi

echo "Done. PR number: $PR_NUMBER"
