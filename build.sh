#!/bin/bash
# Build script for Render deployment

echo "🔧 Starting build process..."

# Install Python dependencies
echo "📦 Installing Python packages..."
pip install -r requirements.txt

# Verify Git LFS files are downloaded
echo "📥 Checking Git LFS files..."
if [ -f "crop_disease_detection_model.h5" ]; then
    FILE_SIZE=$(stat -f%z "crop_disease_detection_model.h5" 2>/dev/null || stat -c%s "crop_disease_detection_model.h5" 2>/dev/null)
    if [ "$FILE_SIZE" -lt 1000000 ]; then
        echo "⚠️  Model file is too small, pulling from Git LFS..."
        git lfs pull
    else
        echo "✅ Model file exists and has correct size"
    fi
else
    echo "❌ Model file not found, pulling from Git LFS..."
    git lfs pull
fi

# Verify class names file
if [ ! -f "class_names.json" ]; then
    echo "❌ class_names.json not found!"
    exit 1
fi

echo "✅ Build complete!"
