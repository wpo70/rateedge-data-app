#!/bin/bash
# Rate Edge v5.1 - Unix/Mac Installation Script

echo "============================================================"
echo "   Rate Edge v5.1 - Professional IRS Swap Analytics"
echo "   Installation Script for Unix/Mac"
echo "============================================================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 not found!"
    echo "Please install Python 3.8+ from https://www.python.org/downloads/"
    exit 1
fi

echo "[1/3] Python found! Checking version..."
python3 --version

echo ""
echo "[2/3] Installing dependencies..."
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to install dependencies"
    exit 1
fi

echo ""
echo "[3/3] Verifying installation..."
python3 -c "import pandas; import matplotlib; import flask; print('All packages installed successfully!')"
if [ $? -ne 0 ]; then
    echo "[ERROR] Package verification failed"
    exit 1
fi

echo ""
echo "============================================================"
echo "   Installation Complete!"
echo "============================================================"
echo ""
echo "You can now launch Rate Edge:"
echo ""
echo "   Desktop App:  python3 launch.py"
echo "   Web App:      python3 web_app.py"
echo ""
echo "Check QUICKSTART.md for a 2-minute tutorial!"
echo ""
