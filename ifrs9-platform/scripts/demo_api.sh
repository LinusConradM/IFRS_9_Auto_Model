#!/bin/bash

# IFRS 9 Platform API Demo Script
# This script demonstrates the Phase 1 critical APIs

echo "=========================================="
echo "IFRS 9 Platform API Demo"
echo "=========================================="
echo ""

# Step 1: Login as maker
echo "1. Login as maker1..."
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=maker1&password=Maker@123456")

ACCESS_TOKEN=$(echo $LOGIN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
echo "✅ Login successful!"
echo "Token: ${ACCESS_TOKEN:0:50}..."
echo ""

# Step 2: Get current user info
echo "2. Get current user info..."
curl -s -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $ACCESS_TOKEN" | python3 -m json.tool
echo ""

# Step 3: Request a staging override
echo "3. Request staging override for LOAN001..."
OVERRIDE_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/staging/overrides \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "instrument_id": "LOAN001",
    "override_stage": "STAGE_2",
    "justification": "Customer experiencing temporary cash flow issues due to delayed receivables from major client"
  }')

echo "$OVERRIDE_RESPONSE" | python3 -m json.tool
OVERRIDE_ID=$(echo $OVERRIDE_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['override_id'])" 2>/dev/null || echo "")
echo ""

# Step 4: List pending overrides
echo "4. List pending overrides..."
curl -s -X GET http://localhost:8000/api/v1/staging/overrides/pending \
  -H "Authorization: Bearer $ACCESS_TOKEN" | python3 -m json.tool
echo ""

# Step 5: Login as checker
echo "5. Login as checker1..."
CHECKER_LOGIN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=checker1&password=Checker@123456")

CHECKER_TOKEN=$(echo $CHECKER_LOGIN | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
echo "✅ Checker login successful!"
echo ""

# Step 6: Approve the override (if we have an override_id)
if [ ! -z "$OVERRIDE_ID" ]; then
  echo "6. Approve staging override as checker..."
  curl -s -X POST "http://localhost:8000/api/v1/staging/overrides/$OVERRIDE_ID/approve" \
    -H "Authorization: Bearer $CHECKER_TOKEN" | python3 -m json.tool
  echo ""
fi

# Step 7: Calculate EAD
echo "7. Calculate EAD for LOAN001..."
curl -s -X POST http://localhost:8000/api/v1/ead/calculate \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "instrument_id": "LOAN001",
    "facility_type": "TERM_LOAN",
    "outstanding_balance": "500000.00",
    "undrawn_commitment": "100000.00",
    "reporting_date": "2026-03-05"
  }' | python3 -m json.tool
echo ""

# Step 8: Get CCF configuration
echo "8. Get CCF configuration..."
curl -s -X GET http://localhost:8000/api/v1/ead/ccf \
  -H "Authorization: Bearer $ACCESS_TOKEN" | python3 -m json.tool
echo ""

# Step 9: List off-balance sheet exposures
echo "9. List off-balance sheet exposures..."
curl -s -X GET http://localhost:8000/api/v1/ead/off-balance-sheet \
  -H "Authorization: Bearer $ACCESS_TOKEN" | python3 -m json.tool
echo ""

echo "=========================================="
echo "Demo Complete!"
echo "=========================================="
echo ""
echo "API Documentation: http://localhost:8000/api/docs"
echo "ReDoc: http://localhost:8000/api/redoc"
