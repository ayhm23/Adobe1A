#!/bin/bash

echo "🧪 Testing PDF Outline Extractor"
echo "================================"

# Create test directories
mkdir -p test_input test_output

echo "📁 Test directories created"

# Check if Docker image exists
if ! docker images pdf-outline-extractor:v1.0 --format '{{.Repository}}' | grep -q pdf-outline-extractor; then
    echo "❌ Docker image not found. Please run ./build.sh first"
    exit 1
fi

echo "✅ Docker image found"

# Run a quick test (you would need to add a sample PDF)
echo "🏃 Running extraction test..."

docker run --rm \
  -v $(pwd)/test_input:/app/input \
  -v $(pwd)/test_output:/app/output \
  --network none \
  pdf-outline-extractor:v1.0

if [ $? -eq 0 ]; then
    echo "✅ Test completed successfully!"

    # Show results
    if [ "$(ls -A test_output)" ]; then
        echo "📊 Generated output files:"
        ls -la test_output/

        echo ""
        echo "📄 Sample output:"
        for json_file in test_output/*.json; do
            if [ -f "$json_file" ]; then
                echo "--- $(basename $json_file) ---"
                head -20 "$json_file" 2>/dev/null || echo "File is binary or unreadable"
                echo ""
                break
            fi
        done
    else
        echo "⚠️  No output files generated (check if PDFs are in test_input/)"
    fi
else
    echo "❌ Test failed!"
    exit 1
fi

echo "🎉 All tests passed!"
