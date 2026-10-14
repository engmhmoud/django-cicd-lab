#!/bin/sh
# Deploy one environment with an automatic rollback (Lab 8, learning/013 ch05).
#   IMAGE=ghcr.io/<owner>/<repo> deploy/deploy.sh <environment> <image@digest> <expected git sha>
#
# The digest is Lab 4's signed release; the workflow has already run `cosign verify` on it.
# 1. Rebuild the environment at its LAST KNOWN GOOD digest (the registry tag cd-<environment>):
#    the runner is ephemeral, so this stands in for "what is live right now".
# 2. Deploy the new digest (migrate job, then the app), then run the smoke test.
# 3. Pass: move the cd-<environment> pointer to the SAME digest (promotion).
#    Fail: redeploy the last known good digest, smoke-test it against ITS sha, and exit 1.
# Fails closed: a registry error is never mistaken for "first deploy".
set -eu
env_name="$1" new_ref="$2" expected_sha="$3"
repo="${IMAGE:?set IMAGE to the image repository}"

C() { docker compose -p "$env_name" -f deploy/compose.yaml "$@"; }
up() { IMAGE_REF="$1" C up -d --wait --wait-timeout 120 >/dev/null 2>&1; }

resolve() {   # prints the digest of a tag, nothing if the tag doesn't exist, exits on any other error
  if out=$(docker buildx imagetools inspect "$1" --format '{{json .Manifest}}' 2>&1); then
    printf '%s' "$out" | jq -r .digest
  elif printf '%s' "$out" | grep -qiE 'not found|manifest unknown'; then
    :   # no pointer yet: first deploy of this environment
  else
    echo "ERROR: cannot read $1 from the registry: $out" >&2
    exit 1
  fi
}

live_sha() { curl -fsS --max-time 2 http://127.0.0.1:8000/version | jq -r .sha; }

smoke() {   # $1 = expected git sha
  for path in healthz readyz; do
    i=0
    until curl -fsS --max-time 2 "http://127.0.0.1:8000/$path" >/dev/null 2>&1; do
      i=$((i + 1)); [ "$i" -ge 10 ] && { echo "  smoke: /$path FAILED"; return 1; }; sleep 1
    done
    echo "  smoke: /$path ok"
  done
  got=$(live_sha) || { echo "  smoke: /version FAILED"; return 1; }
  if [ "$got" != "$1" ]; then echo "  smoke: /version sha=$got, expected $1: FAILED"; return 1; fi
  echo "  smoke: /version sha=$got ok"
}

last_good=$(resolve "$repo:cd-$env_name")
last_good_sha=""
if [ -n "$last_good" ]; then
  echo "live (last known good, tag cd-$env_name): $repo@$last_good"
  up "$repo@$last_good"
  last_good_sha=$(live_sha)
  echo "  live sha=$last_good_sha"
else
  echo "live: nothing yet (first deploy of $env_name)"
fi

echo "deploying: $new_ref"
if up "$new_ref" && smoke "$expected_sha"; then
  # --prefer-index=false: copy the source as-is, so the pointer's digest IS the deployed digest
  # (the default wraps a single manifest in a new index with a different digest).
  if ! docker buildx imagetools create --prefer-index=false -t "$repo:cd-$env_name" "$new_ref"; then
    echo "ERROR: $env_name runs $new_ref but the cd-$env_name pointer did NOT move; fix it before the next deploy" >&2
    exit 1
  fi
  echo "pointer: cd-$env_name -> $(resolve "$repo:cd-$env_name")"
  echo "RESULT: $env_name now runs $new_ref (tag cd-$env_name moved)"
  exit 0
fi

echo "RESULT: smoke test failed on $env_name"
if [ -z "$last_good" ]; then
  echo "ROLLBACK: impossible, no previous good digest"
  exit 1
fi
echo "ROLLBACK: redeploying $repo@$last_good"
up "$repo@$last_good" && smoke "$last_good_sha" && echo "ROLLBACK: $env_name is back on $repo@$last_good"
exit 1
