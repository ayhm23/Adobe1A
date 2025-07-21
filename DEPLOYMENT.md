# Deployment Guide - PDF Outline Extractor

## Quick Deployment Steps

### 1. Extract and Build
```bash
unzip pdf-outline-extractor.zip
cd pdf-outline-extractor
chmod +x build.sh
./build.sh
```

### 2. Test the Solution
```bash
mkdir -p test_input test_output
# Copy your PDF files to test_input/
docker run --rm -v $(pwd)/test_input:/app/input -v $(pwd)/test_output:/app/output --network none pdf-outline-extractor:v1.0
```

### 3. Verify Results
```bash
ls test_output/
cat test_output/your-file.json
```

## Hackathon Submission Commands

The exact commands that will be used in the Adobe India Hackathon evaluation:

### Build Command
```bash
docker build --platform linux/amd64 -t mysolutionname:somerandomidentifier .
```

### Run Command  
```bash
docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output --network none mysolutionname:somerandomidentifier
```

## Performance Tuning

### For Faster Processing (Lower Quality)
Edit `config.json`:
```json
{
    "processing": {
        "max_workers": 8,
        "pdf_dpi": 150,
        "image_quality": 60
    },
    "model": {
        "confidence_threshold": 0.3
    }
}
```

### For Higher Accuracy (Slower)
```json
{
    "processing": {
        "max_workers": 4,
        "pdf_dpi": 300,
        "image_quality": 95
    },
    "model": {
        "confidence_threshold": 0.7
    }
}
```

## Troubleshooting

### Build Issues
- Ensure Docker supports linux/amd64 platform
- Check available disk space (minimum 2GB)
- Verify internet connection for dependency downloads

### Runtime Issues
- Check input directory contains .pdf files
- Ensure output directory is writable
- Monitor system memory usage

### Performance Issues
- Reduce max_workers if memory is limited
- Lower pdf_dpi for faster processing
- Adjust confidence_threshold for accuracy vs speed

## Architecture Notes

This solution uses:
- **PaddleOCR PP-DocLayoutPlus-L**: 126MB model with 83.2% mAP@0.5 accuracy
- **Multi-processing**: Utilizes all 8 CPU cores efficiently  
- **PyMuPDF**: Fast PDF to image conversion
- **Intelligent hierarchy**: Pattern-based H1/H2/H3 detection

Expected performance: 6-8 seconds for 50-page PDF on 8-core CPU system.
