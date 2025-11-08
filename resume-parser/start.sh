#!/bin/bash
echo "Installing dependencies..."
pip install -r requirements.txt
echo ""
echo "Starting Resume Parser server..."
echo "Open http://127.0.0.1:5000 in your browser"
echo ""
python app.py

