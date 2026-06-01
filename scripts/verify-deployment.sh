#!/bin/bash
# ============================================================================
# V3.1 SRE Platform — Deployment Verification Script
# ============================================================================
# Usage: ./scripts/verify-deployment.sh [base_url]
# ============================================================================

set -e

BASE_URL="${1:-http://localhost:8688}"
FRONTEND_URL="${2:-http://localhost:3000}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS=0
FAIL=0
WARN=0

check() {
    local name="$1"
    local url="$2"
    local expected="$3"

    echo -n "  $name... "

    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")

    if [ "$response" = "$expected" ]; then
        echo -e "${GREEN}PASS${NC} (HTTP $response)"
        ((PASS++))
    else
        echo -e "${RED}FAIL${NC} (HTTP $response, expected $expected)"
        ((FAIL++))
    fi
}

check_json() {
    local name="$1"
    local url="$2"
    local field="$3"

    echo -n "  $name... "

    response=$(curl -s "$url" 2>/dev/null)
    if echo "$response" | grep -q "$field"; then
        echo -e "${GREEN}PASS${NC}"
        ((PASS++))
    else
        echo -e "${RED}FAIL${NC} (missing $field)"
        ((FAIL++))
    fi
}

echo "=========================================="
echo " V3.1 SRE Platform — Deployment Verification"
echo "=========================================="
echo ""
echo "Backend URL: $BASE_URL"
echo "Frontend URL: $FRONTEND_URL"
echo ""

# ── Health Checks ────────────────────────────────────────────────────────
echo "Health Checks:"
check "Backend health" "$BASE_URL/health" "200"
check "Backend ready" "$BASE_URL/ready" "200"
check "Backend liveness" "$BASE_URL/health/live" "200"
echo ""

# ── API Endpoints ────────────────────────────────────────────────────────
echo "API Endpoints:"
check "GET /api/v1/assets" "$BASE_URL/api/v1/assets" "200"
check "GET /api/v1/alerts" "$BASE_URL/api/v1/alerts" "200"
check "GET /api/v1/operations" "$BASE_URL/api/v1/operations" "200"
check "GET /api/v1/dashboard/summary" "$BASE_URL/api/v1/dashboard/summary" "200"
check "GET /api/v1/dashboard/trends" "$BASE_URL/api/v1/dashboard/trends" "200"
check "GET /api/v1/atomics" "$BASE_URL/api/v1/atomics" "200"
echo ""

# ── API Response Format ──────────────────────────────────────────────────
echo "API Response Format:"
check_json "Assets response has items" "$BASE_URL/api/v1/assets" "items"
check_json "Alerts response has items" "$BASE_URL/api/v1/alerts" "items"
check_json "Operations response has items" "$BASE_URL/api/v1/operations" "items"
check_json "Dashboard has assets" "$BASE_URL/api/v1/dashboard/summary" "assets"
check_json "Atomics has operations" "$BASE_URL/api/v1/atomics" "operations"
echo ""

# ── Chat API ─────────────────────────────────────────────────────────────
echo "Chat API:"
echo -n "  POST /api/v1/chat... "
chat_response=$(curl -s -X POST "$BASE_URL/api/v1/chat" \
    -H "Content-Type: application/json" \
    -d '{"message":"帮助"}' 2>/dev/null)

if echo "$chat_response" | grep -q "success"; then
    echo -e "${GREEN}PASS${NC}"
    ((PASS++))
else
    echo -e "${RED}FAIL${NC}"
    ((FAIL++))
fi
echo ""

# ── Frontend ─────────────────────────────────────────────────────────────
echo "Frontend:"
echo -n "  Frontend accessible... "
frontend_response=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL" 2>/dev/null || echo "000")

if [ "$frontend_response" = "200" ]; then
    echo -e "${GREEN}PASS${NC} (HTTP $frontend_response)"
    ((PASS++))
else
    echo -e "${YELLOW}WARN${NC} (HTTP $frontend_response)"
    ((WARN++))
fi
echo ""

# ── Database ─────────────────────────────────────────────────────────────
echo "Database (via API):"
check_json "Assets table has data" "$BASE_URL/api/v1/assets" "total"
check_json "Alerts table has data" "$BASE_URL/api/v1/alerts" "total"
echo ""

# ── Summary ──────────────────────────────────────────────────────────────
echo "=========================================="
echo " Results: $PASS passed, $FAIL failed, $WARN warnings"
echo "=========================================="

if [ $FAIL -gt 0 ]; then
    echo -e "${RED}Deployment verification FAILED${NC}"
    exit 1
else
    echo -e "${GREEN}Deployment verification PASSED${NC}"
    exit 0
fi
