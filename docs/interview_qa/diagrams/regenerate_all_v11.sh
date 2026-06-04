#!/bin/bash
# Batch regenerate all architecture diagrams with v11 style
# Updated: 2026-06-04 - Added Quality Gate v11 horizontal layout
# Usage: ./regenerate_all_v11.sh

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
V11_SCRIPT="$HOME/.claude/skills/mermaid-to-png/mermaid-to-png-v11.js"

echo "==================================="
echo "Batch Regenerating Architecture Diagrams with v11 Style"
echo "========================="
echo "Script directory: $SCRIPT_DIR"
echo "v11 script: $V11_SCRIPT"
echo ""

# Check if v11 script exists
if [ ! -f "$V11_SCRIPT" ]; then
    echo "Error: v11 script not found at $V11_SCRIPT"
    exit 1
fi

# Diagrams to regenerate
DIAGRAMS=(
    "01_system_architecture_v11.md"
    "02_openspec_pipeline.md"
    "03_multi_agent.md"
    "04_quality_gate_v11.md"
    "05_eventbus.md"
)

# Function to generate a diagram with appropriate settings
generate_diagram() {
    local diagram="$1"
    local diagram_path="$SCRIPT_DIR/$diagram"

    if [ ! -f "$diagram_path" ]; then
        echo "⚠️  Skipping: $diagram (file not found)"
    return 1
  fi

    echo "----------------------------------------------"
    echo "Processing: $diagram"
    echo "------------------------------"

    # Special size for Quality Gate v11 (horizontal layout)
    if [[ "$diagram" == "04_quality_gate_v11.md" ]]; then
        echo "📐 Using horizontal layout: 4800x2400 @ 3x"
        node "$V11_SCRIPT" "$diagram_path" "$SCRIPT_DIR" --width=4800 --height=2400 --scale=3 --background=white
    else
        echo "📐 Using v11 preset: 3600x4800 @ 3x"
        node "$V11_SCRIPT" "$diagram_path" "$SCRIPT_DIR" --style=v11
    fi

    return $?
}

SUCCESS_COUNT=0
TOTAL_COUNT=${#DIAGRAMS[@]}

for diagram in "${DIAGRAMS[@]}"; do
    if generate_diagram "$diagram"; then
        echo "✅ Successfully generated: $diagram"
        ((SUCCESS_COUNT++))
    else
        echo "❌ Failed to generate: $diagram"
    fi
    echo ""
done

echo "================================"
echo "Batch Generation Complete"
echo "======================================="
echo "Success: $SUCCESS_COUNT/$TOTAL_COUNT diagrams"
echo ""

# List generated files
echo "Generated files:"
ls -lh "$SCRIPT_DIR"/*-diagram-1.png 2>/dev/null | tail -5 | awk '{print "  " $9 " (" $5 ")"}'

echo ""
echo "✨ Done! All diagrams regenerated with v11 style."
echo ""
echo "Note: 04_quality_gate uses horizontal layout (4800x2400)"
echo "      Others use standard v11 layout (3600x4800)"
