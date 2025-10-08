#!/bin/bash
# Documentation cleanup script
# Moves legacy and temporary documentation to archive directories

set -e

echo "🧹 Spanish-F5 Documentation Cleanup"
echo "===================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create archive directories
echo "Creating archive directories..."
mkdir -p archive/session-reports
mkdir -p archive/legacy-docs

# Session reports (temporary/historical)
SESSION_REPORTS=(
    "API_TESTS_RESULTS.md"
    "CODE_COVERAGE_REPORT.md"
    "COVERAGE_ANALYSIS.md"
    "FINAL_COVERAGE_REPORT.md"
    "FINAL_SESSION_SUMMARY.md"
    "FULL_TEST_SUITE_RESULTS.md"
    "IMPLEMENTATION_CHECKLIST.md"
    "PHASE_4_5_COMPLETE.md"
    "PROJECT_CODE_COVERAGE.md"
    "SESSION_SUMMARY.md"
    "TEST_FIXES_SUMMARY.md"
    "TEST_SUCCESS_SUMMARY.md"
)

# Legacy documentation (superseded)
LEGACY_DOCS=(
    "MODULAR_ARCHITECTURE_SUMMARY.md"
    "README_ENHANCEMENTS.md"
    "REGIONAL_SPANISH_IMPLEMENTATION.md"
    "ROADMAP.md"
    "TTS_QUALITY_IMPROVEMENTS.md"
)

# Archive session reports
echo ""
echo -e "${YELLOW}Archiving session reports...${NC}"
ARCHIVED_SESSIONS=0
for file in "${SESSION_REPORTS[@]}"; do
    if [ -f "$file" ]; then
        mv "$file" archive/session-reports/
        echo -e "${GREEN}✓${NC} Moved $file"
        ((ARCHIVED_SESSIONS++))
    else
        echo "  ⊘ $file not found (skipped)"
    fi
done

# Archive legacy documentation
echo ""
echo -e "${YELLOW}Archiving legacy documentation...${NC}"
ARCHIVED_LEGACY=0
for file in "${LEGACY_DOCS[@]}"; do
    if [ -f "$file" ]; then
        mv "$file" archive/legacy-docs/
        echo -e "${GREEN}✓${NC} Moved $file"
        ((ARCHIVED_LEGACY++))
    else
        echo "  ⊘ $file not found (skipped)"
    fi
done

# Create README files in archive directories
echo ""
echo "Creating archive README files..."

cat > archive/session-reports/README.md << 'EOF'
# Session Reports Archive

This directory contains historical session reports and temporary documentation from development sessions.

## Contents

- Coverage reports
- Test results summaries
- Implementation checklists
- Phase completion reports
- Session summaries

## Purpose

These files are archived for historical reference. For current information:

- **Test coverage**: Run `pytest --cov=src/f5_tts tests/`
- **Test results**: Run `pytest tests/ -v`
- **Implementation status**: Check main README.md and docs/

## Date Archived

2025-01-08
EOF

cat > archive/legacy-docs/README.md << 'EOF'
# Legacy Documentation Archive

This directory contains documentation that has been superseded by new comprehensive guides.

## Contents

- Older architecture summaries
- Previous README enhancements
- Original regional Spanish implementation docs
- Outdated roadmaps
- TTS quality improvement notes

## Migration

Information from these files has been integrated into:

- `README.md` - Main project overview
- `ARCHITECTURE.md` - System architecture
- `docs/SPANISH_REGIONAL_GUIDE.md` - Regional features
- `docs/API_REFERENCE.md` - API documentation
- `docs/DEVELOPER_GUIDE.md` - Development guide

## Date Archived

2025-01-08
EOF

echo -e "${GREEN}✓${NC} Created archive README files"

# Summary
echo ""
echo "===================================="
echo -e "${GREEN}✓ Cleanup Complete!${NC}"
echo ""
echo "Summary:"
echo "  Session reports archived: $ARCHIVED_SESSIONS"
echo "  Legacy docs archived: $ARCHIVED_LEGACY"
echo "  Total files moved: $((ARCHIVED_SESSIONS + ARCHIVED_LEGACY))"
echo ""
echo "Archive locations:"
echo "  • archive/session-reports/ - Historical session files"
echo "  • archive/legacy-docs/ - Superseded documentation"
echo ""
echo "Active documentation:"
echo "  • README.md - Main project overview"
echo "  • docs/ - Comprehensive guides and references"
echo ""
echo "See DOCUMENTATION_CLEANUP.md for details."
