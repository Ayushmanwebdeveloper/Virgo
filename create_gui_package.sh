#!/bin/bash
# Quick Download Script for Virgo GUI
# Run this from the Virgo repository root

echo "=========================================="
echo "Virgo GUI - Quick Download Helper"
echo "=========================================="
echo ""

# Check if virgo_gui folder exists
if [ ! -d "virgo_gui" ]; then
    echo "❌ Error: virgo_gui folder not found"
    echo "   Make sure you're in the Virgo repository root"
    exit 1
fi

echo "Creating downloadable package..."
echo ""

# Create a tarball
tar -czf virgo_gui_v2.0.tar.gz virgo_gui/

if [ $? -eq 0 ]; then
    SIZE=$(du -h virgo_gui_v2.0.tar.gz | cut -f1)
    echo "✅ Success!"
    echo ""
    echo "Package created: virgo_gui_v2.0.tar.gz"
    echo "Size: $SIZE"
    echo ""
    echo "To extract on another machine:"
    echo "  tar -xzf virgo_gui_v2.0.tar.gz"
    echo "  cd virgo_gui"
    echo "  ./launch_gui.sh"
    echo ""
else
    echo "❌ Failed to create package"
    exit 1
fi
