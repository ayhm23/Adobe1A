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
echo "🔨 Building Docker image: adobe1a"

# Remove existing image if it exists
docker rmi adobe1a 2>/dev/null || true

# Build new image
docker build --platform=linux/amd64 -t adobe1a .


if [ $? -eq 0 ]; then
    echo "✅ Docker image built successfully!"
    echo "📊 Image size:"
    docker images adobe1a --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
    echo ""
    echo "🚀 To test the image:"
    echo "   mkdir -p test_input test_output"
    echo "   cp your-file.pdf test_input/"
    echo "   docker run --rm -v "$(pwd)/test_input:/app/input" -v "$(pwd)/test_output:/app/output" adobe1a"
    echo "   docker run --rm -v \$(pwd)/test_input:/app/input -v \$(pwd)/test_output:/app/output --network none adobe1a"
else
    echo "❌ Docker build failed!"
    exit 1
fi
