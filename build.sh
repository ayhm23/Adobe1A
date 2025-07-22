#!/bin/bash
set -e

echo "🏗️  Building PDF Outline Extractor Docker Image"
echo "=============================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

echo "✅ Docker is running"

# Build the Docker image
echo "🔨 Building Docker image: pdf-outline-extractor:v1.0"

# Remove existing image if it exists
docker rmi pdf-outline-extractor:v1.0 2>/dev/null || true

# Build new image
docker build --platform linux/amd64 -t pdf-outline-extractor:v1.0 .

if [ $? -eq 0 ]; then
    echo "✅ Docker image built successfully!"
    echo "📊 Image size:"
    docker images pdf-outline-extractor:v1.0 --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
    echo ""
    echo "🚀 To test the image:"
    echo "   mkdir -p test_input test_output"
    echo "   cp your-file.pdf test_input/"
    echo "   docker run --rm -v "$(pwd)/test_input:/app/input" -v "$(pwd)/test_output:/app/output" pdf-outline-extractor:v1.0"
    echo "   docker run --rm -v \$(pwd)/test_input:/app/input -v \$(pwd)/test_output:/app/output --network none pdf-outline-extractor:v1.0"
else
    echo "❌ Docker build failed!"
    exit 1
fi
