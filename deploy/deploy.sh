#!/bin/sh
# Deploy one environment with an automatic rollback (Lab 8, learning/013 ch05).
#   IMAGE=ghcr.io/<owner>/<repo> deploy/deploy.sh <environment> <image@digest> <expected git sha>
#
# 1. Rebuild the environment at its LAST KNOWN GOOD digest (the registry tag cd-<environment>):
#    the runner is ephemeral, so this stands in for "what is live right now".
# 2. Deploy the new digest (migrate job, then the app), then run the smoke test.
# 3. Pass: move the cd-<environment> pointer to the new digest (promotion).
#    Fail: redeploy the last known good digest, smoke-test it, and exit 1 (the run is marked failed).
set -eu
env_name="$1" new_ref="$2" expected_sha="$3"
repo="${IMAGE:?set IMAGE to the image repository}"

C() { docker compose -p "$env_name" -f deploy/compose.yaml "$@"; }
resolve() { docker buildx imagetools inspect "$1" --format '{{json .Manifest}}' 2>/dev/null | jq -r .digest; }
up() { IMAGE_REF="$1" C up -d --wait --wait-timeout 120 >/dev/null 2>&1; }

smoke() {   # $1 = expected sha, or "any" for the rollback check
  for path in healthz readyz; do
    i=0
    until curl -fsS --max-time 2 "http://127.0.0.1:8000/$path" >/dev/null 2>&1; do
      i=$((i + 1)); [ "$i" -ge 10 ] && { echo "  smoke: /$path FAILED"; return 1; }; sleep 1
    done
    echo "  smoke: /$path ok"
  done
  got=$(curl -fsS --max-time 2 http://127.0.0.1:8000/version | jq -r .sha) || { echo "  smoke: /version FAILED"; return 1; }
  if [ "$1" != any ] && [ "$got" != "$1" ]; then echo "  smoke: /version sha=$got, expected $1: FAILED"; return 1; fi
  echo "  smoke: /version sha=$got ok"
}

last_good=$(resolve "$repo:cd-$env_name" || true)
if [ -n "$last_good" ]; then
  echo "live (last known good, tag cd-$env_name): $repo@$last_good"
  up "$repo@$last_good"
else
  echo "live: nothing yet (first deploy of $env_name)"
fi

echo "deploying: $new_ref"
if up "$new_ref" && smoke "$expected_sha"; then
  docker buildx imagetools create -t "$repo:cd-$env_name" "$new_ref" >/dev/null 2>&1
  echo "RESULT: $env_name now runs $new_ref (tag cd-$env_name moved)"
  exit 0
fi

echo "RESULT: smoke test failed on $env_name"
if [ -z "$last_good" ]; then
  echo "ROLLBACK: impossible, no previous good digest"
  exit 1
fi
echo "ROLLBACK: redeploying $repo@$last_good"
up "$repo@$last_good" && smoke any && echo "ROLLBACK: $env_name is back on $repo@$last_good"
exit 1
