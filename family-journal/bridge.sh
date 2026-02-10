#!/bin/bash
#
# Discord-to-Family-Journal Bridge Shell Script
#
# Usage:
#   ./bridge.sh "Message text here" "attachment_url1,attachment_url2" "Diana,Jade,Julian"
#   ./bridge.sh --test "Message text here" "attachment_url1"  # Send to Landon for testing
#
# Arguments:
#   $1 = Message text (required) OR --test flag
#   $2 = Attachment URLs (optional, comma-separated)
#   $3 = Kid recipients (optional, defaults to all 3 kids)
#
# Examples:
#   ./bridge.sh "Today was great!"
#   ./bridge.sh --test "Testing the system!"  # Sends to Landon
#   ./bridge.sh "Look at this photo!" "https://example.com/photo.jpg"
#   ./bridge.sh "Story time!" "https://img1.jpg,https://img2.jpg" "Diana,Jade"
#

set -e  # Exit on error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="${SCRIPT_DIR}/discord_journal_bridge.py"
VENV_PATH="${SCRIPT_DIR}/family-journal-app/venv"
PYTHON_BIN="${VENV_PATH}/bin/python"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default recipients (all 3 kids)
DEFAULT_RECIPIENTS="Diana Atlas,Jade Atlas,Julian Atlas"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║       Discord-to-Family-Journal Bridge Script            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check for help flag
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    echo "Usage: $0 \"message_text\" [attachment_urls] [kid_recipients]"
    echo "       $0 --test \"message_text\" [attachment_urls]"
    echo ""
    echo "Arguments:"
    echo "  message_text      The Discord message content (required)"
    echo "  --test           Test mode - sends to Landon instead of kids"
    echo "  attachment_urls   Comma-separated URLs of attachments (optional)"
    echo "  kid_recipients   Comma-separated kid names: Diana,Jade,Julian (optional, default: all)"
    echo ""
    echo "@Mention support:"
    echo "  @Diana - Include Diana in the story"
    echo "  @Jade  - Include Jade in the story"
    echo "  @Julian - Include Julian in the story"
    echo "  #Diana, #Jade, #Julian also work!"
    echo ""
    echo "Examples:"
    echo "  $0 \"Today was amazing!\""
    echo "  $0 \"Check out these photos!\" \"https://example.com/photo.jpg\""
    echo "  $0 \"Hello Diana!\" \"\" \"Diana\""
    echo "  $0 --test \"Testing the system!\"  # Sends to Landon"
    exit 0
fi

# Check for test mode
TEST_MODE=false
if [[ "$1" == "--test" ]]; then
    TEST_MODE=true
    shift
fi

# Validate arguments
if [[ -z "$1" ]]; then
    echo -e "${RED}❌ Error: Message text is required${NC}"
    echo "Usage: $0 \"message_text\" [attachment_urls] [kid_recipients]"
    exit 1
fi

MESSAGE="$1"
ATTACHMENTS="${2:-}"
RECIPIENTS="${3:-$DEFAULT_RECIPIENTS}"

if [[ "$TEST_MODE" == "true" ]]; then
    echo -e "${YELLOW}🧪 TEST MODE ENABLED - Will send to Landon${NC}"
fi

echo -e "${YELLOW}📝 Message:${NC} ${MESSAGE}"
if [[ -n "$ATTACHMENTS" ]]; then
    echo -e "${YELLOW}📎 Attachments:${NC} $ATTACHMENTS"
fi
echo -e "${YELLOW}👧 Recipients:${NC} $RECIPIENTS"
echo ""

# Check if Python script exists
if [[ ! -f "$PYTHON_SCRIPT" ]]; then
    echo -e "${RED}❌ Error: Python script not found at ${PYTHON_SCRIPT}${NC}"
    exit 1
fi

# Use virtual environment if available, otherwise system Python
if [[ -d "$VENV_PATH" && -f "${PYTHON_BIN}" ]]; then
    PYTHON_CMD="$PYTHON_BIN"
else
    PYTHON_CMD="python3"
fi

echo -e "${GREEN}🚀 Running bridge with Python: ${PYTHON_CMD}${NC}"
echo ""

# Run the bridge
if [[ "$TEST_MODE" == "true" ]]; then
    "$PYTHON_CMD" "$PYTHON_SCRIPT" \
        --message "$MESSAGE" \
        --attachments "$ATTACHMENTS" \
        --test
else
    "$PYTHON_CMD" "$PYTHON_SCRIPT" \
        --message "$MESSAGE" \
        --attachments "$ATTACHMENTS" \
        --kids "$RECIPIENTS"
fi

# Check exit code
EXIT_CODE=$?

if [[ $EXIT_CODE -eq 0 ]]; then
    echo -e "${GREEN}✅ Bridge completed successfully!${NC}"
else
    echo -e "${RED}❌ Bridge failed with exit code ${EXIT_CODE}${NC}"
fi

exit $EXIT_CODE
