#!/usr/bin/env bash
# tools/push.sh — push có timeout, retry, log và chẩn đoán khi lỗi.
#
# Vì sao: push lên GitHub đôi khi chậm/bị treo >10 phút; `git push` trần không
# để lại bằng chứng. Script này:
#   - timeout mỗi lần thử (mặc định 300s), retry 3 lần, backoff 10/30/60s;
#   - ghi tools/push_log.jsonl (gitignore) mỗi lần thử: thời gian, exit, số commit;
#   - khi thất bại: in chẩn đoán (ahead/behind, object, SSH, gợi ý githubstatus);
#   - KHÔNG bao giờ force-push.
#
# Dùng:
#   tools/push.sh                 # origin master
#   tools/push.sh origin master
#   PUSH_TIMEOUT_SEC=600 tools/push.sh
#
# Exit: 0 = push thành công; 1 = thất bại sau tất cả lần thử; 2 = dùng sai.

set -u

REMOTE="${1:-origin}"
BRANCH="${2:-master}"
MAX_ATTEMPTS="${PUSH_MAX_ATTEMPTS:-3}"
TIMEOUT_SEC="${PUSH_TIMEOUT_SEC:-300}"
BACKOFFS=(10 30 60)
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG="$HERE/push_log.jsonl"
TMP_OUT="$(mktemp -t rad-push-out.XXXXXX)"
TMP_ERR="$(mktemp -t rad-push-err.XXXXXX)"
trap 'rm -f "$TMP_OUT" "$TMP_ERR"' EXIT

# SSH keepalive: tránh treo im lặng khi mạng chập chờn.
export GIT_SSH_COMMAND="${GIT_SSH_COMMAND:-ssh -o ServerAliveInterval=30 -o ServerAliveCountMax=6 -o ConnectTimeout=20}"

for arg in "$@"; do
  case "$arg" in
    *--force*|-f) echo "LỖI: script này không cho phép force-push." >&2; exit 2 ;;
  esac
done

ahead_count() {
  git rev-list --count "@{u}..HEAD" 2>/dev/null || echo "?"
}

log_event() {
  # log_event <attempt> <delay_before> <duration> <exit> <detail>
  python3 - "$LOG" "$REMOTE/$BRANCH" "$1" "$2" "$3" "$4" "$5" <<'PY'
import json, sys, time
path, target, attempt, delay, dur, code, detail = sys.argv[1:8]
rec = {
    "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    "target": target,
    "attempt": int(attempt),
    "delay_before_s": int(delay),
    "duration_s": round(float(dur), 2),
    "exit": int(code),
    "commits_ahead": detail,
}
with open(path, "a", encoding="utf-8") as f:
    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
PY
}

ahead="$(ahead_count)"
echo "Push $REMOTE/$BRANCH | $ahead commit chờ | timeout ${TIMEOUT_SEC}s/lần | tối đa $MAX_ATTEMPTS lần"

for i in $(seq 1 "$MAX_ATTEMPTS"); do
  delay=0
  if [ "$i" -gt 1 ]; then
    delay="${BACKOFFS[$((i-2))]:-60}"
    echo "  ↻ chờ ${delay}s rồi thử lại ($i/$MAX_ATTEMPTS)..."
    sleep "$delay"
  fi

  start=$(date +%s)
  timeout "$TIMEOUT_SEC" git push --porcelain "$REMOTE" "$BRANCH" >"$TMP_OUT" 2>"$TMP_ERR"
  code=$?
  end=$(date +%s)
  dur=$((end - start))
  ahead="$(ahead_count)"

  if [ "$code" -eq 0 ]; then
    log_event "$i" "$delay" "$dur" 0 "$ahead"
    echo "PUSH OK sau ${dur}s (lần $i/$MAX_ATTEMPTS, còn $ahead commit chờ)"
    exit 0
  fi

  log_event "$i" "$delay" "$dur" "$code" "$ahead"
  if [ "$code" -eq 124 ]; then
    echo "  ✗ lần $i: quá ${TIMEOUT_SEC}s (timeout), exit 124" >&2
  else
    echo "  ✗ lần $i: exit $code sau ${dur}s" >&2
  fi
  tail -5 "$TMP_ERR" >&2 || true
done

echo "" >&2
echo "PUSH THẤT BẠI sau $MAX_ATTEMPTS lần. Chẩn đoán:" >&2
echo "  - trạng thái: $(git status -sb | head -1)" >&2
echo "  - commit chờ: $(ahead_count)" >&2
echo "  - object: $(git count-objects -vH | tr '\n' ' ')" >&2
echo -n "  - SSH GitHub: " >&2
if timeout 15 ssh -o BatchMode=yes -T git@github.com >/dev/null 2>&1; then
  echo "OK" >&2
else
  echo "LỖI/không kết nối được" >&2
fi
echo "  - kiểm tra https://www.githubstatus.com/ nếu lỗi phía GitHub" >&2
echo "  - log các lần thử: $LOG" >&2
echo "  - KHÔNG force-push; sửa mạng/xác thực rồi chạy lại tools/push.sh" >&2
exit 1
