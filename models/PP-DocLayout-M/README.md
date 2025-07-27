---
license: apache-2.0
library_name: PaddleOCR
language:
- en
- zh
pipeline_tag: image-to-text
tags:
- OCR
- PaddlePaddle
- PaddleOCR
- layout_detection
---

# PP-DocLayout-M

## Introduction

A layout area localization model with balanced precision and efficiency, trained on a self-built dataset containing Chinese and English papers, magazines, contracts, books, exams, and research reports using PicoDet-L. The layout detection model includes 23 common categories: document title, paragraph title, text, page number, abstract, table of contents, references, footnotes, header, footer, algorithm, formula, formula number, image, figure caption, table, table caption, seal, figure title, figure, header image, footer image, and aside text. The key metrics are as follow:

| Model| mAP(0.5) (%) | 
|  --- | --- | 
|PP-DocLayout-M |  75.2 | 

**Note**: the evaluation set of the above accuracy indicators is a self built layout area detection data set, including 500 document type images such as Chinese and English papers, newspapers, research papers and test papers.

## Quick Start

### Installation

1. PaddlePaddle

Please refer to the following commands to install PaddlePaddle using pip:

```bash
# for CUDA11.8
python -m pip install paddlepaddle-gpu==3.0.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu118/

# for CUDA12.6
python -m pip install paddlepaddle-gpu==3.0.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu126/

# for CPU
python -m pip install paddlepaddle==3.0.0 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/
```

For details about PaddlePaddle installation, please refer to the [PaddlePaddle official website](https://www.paddlepaddle.org.cn/en/install/quick).

2. PaddleOCR

Install the latest version of the PaddleOCR inference package from PyPI:

```bash
python -m pip install paddleocr
```


### Model Usage

You can quickly experience the functionality with a single command:

```bash
paddleocr layout_detection \
    --model_name PP-DocLayout-M \
    -i https://cdn-uploads.huggingface.co/production/uploads/63d7b8ee07cd1aa3c49a2026/N5C68HPVAI-xQAWTxpbA6.jpeg
```

You can also integrate the model inference of the layout detection module into your project. Before running the following code, please download the sample image to your local machine.

```python
from paddleocr import LayoutDetection

model = LayoutDetection(model_name="PP-DocLayout-M")
output = model.predict("N5C68HPVAI-xQAWTxpbA6.jpeg", batch_size=1, layout_nms=True)
for res in output:
    res.print()
    res.save_to_img(save_path="./output/")
    res.save_to_json(save_path="./output/res.json")
```

After running, the obtained result is as follows:

```json
{'res': {'input_path': '/root/.paddlex/predict_input/N5C68HPVAI-xQAWTxpbA6.jpeg', 'page_index': None, 'boxes': [{'cls_id': 2, 'label': 'text', 'score': 0.9592978954315186, 'coordinate': [34.364605, 647.1334, 359.25348, 849.71045]}, {'cls_id': 2, 'label': 'text', 'score': 0.9474585652351379, 'coordinate': [384.4702, 735.10425, 712.5607, 850.38525]}, {'cls_id': 8, 'label': 'table', 'score': 0.9260186553001404, 'coordinate': [74.64222, 105.40775, 322.2573, 298.61948]}, {'cls_id': 8, 'label': 'table', 'score': 0.9191280603408813, 'coordinate': [439.1119, 105.92348, 664.15155, 313.46652]}, {'cls_id': 2, 'label': 'text', 'score': 0.9092753529548645, 'coordinate': [384.66946, 497.00494, 710.7119, 697.2429]}, {'cls_id': 2, 'label': 'text', 'score': 0.9040781259536743, 'coordinate': [384.18982, 345.8001, 711.05853, 458.93356]}, {'cls_id': 2, 'label': 'text', 'score': 0.8399520516395569, 'coordinate': [34.557507, 350.14252, 359.24826, 610.59717]}, {'cls_id': 0, 'label': 'paragraph_title', 'score': 0.7936450839042664, 'coordinate': [386.5935, 715.96655, 524.51276, 730.05743]}, {'cls_id': 0, 'label': 'paragraph_title', 'score': 0.7814643383026123, 'coordinate': [34.822536, 628.18286, 185.70476, 641.13354]}, {'cls_id': 0, 'label': 'paragraph_title', 'score': 0.7712311148643494, 'coordinate': [35.295662, 330.93253, 141.2789, 344.6454]}, {'cls_id': 9, 'label': 'table_title', 'score': 0.7366687655448914, 'coordinate': [34.666615, 20.018473, 358.91476, 77.21553]}, {'cls_id': 0, 'label': 'paragraph_title', 'score': 0.6932815313339233, 'coordinate': [390.4889, 476.42044, 654.44617, 491.5214]}, {'cls_id': 9, 'label': 'table_title', 'score': 0.6520973443984985, 'coordinate': [384.57758, 20.172602, 712.1298, 75.38677]}]}}
```

The visualized image is as follows:

![image/jpeg](https://cdn-uploads.huggingface.co/production/uploads/63d7b8ee07cd1aa3c49a2026/wvo4vobpM8UMZc0-M3HA0.jpeg)

For details about usage command and descriptions of parameters, please refer to the [Document](https://paddlepaddle.github.io/PaddleOCR/latest/en/version3.x/module_usage/layout_detection.html#iii-quick-integration).

### Pipeline Usage

The ability of a single model is limited. But the pipeline consists of several models can provide more capacity to resolve difficult problems in real-world scenarios.

#### PP-StructureV3

Layout analysis is a technique used to extract structured information from document images. PP-StructureV3 includes the following six modules:
* Layout Detection Module
* General OCR Sub-pipeline
* Document Image Preprocessing Sub-pipeline （Optional）
* Table Recognition Sub-pipeline （Optional）
* Seal Recognition Sub-pipeline （Optional）
* Formula Recognition Sub-pipeline （Optional）

You can quickly experience the PP-StructureV3 pipeline with a single command.

```bash
paddleocr pp_structurev3 --layout_detection_model_name PP-DocLayout-M -i https://cdn-uploads.huggingface.co/production/uploads/63d7b8ee07cd1aa3c49a2026/KP10tiSZfAjMuwZUSLtRp.png
```

You can experience the inference of the pipeline with just a few lines of code. Taking the PP-StructureV3 pipeline as an example:

```python
from paddleocr import PPStructureV3

pipeline = PPStructureV3(layout_detection_model_name="PP-DocLayout-M")
# ocr = PPStructureV3(use_doc_orientation_classify=True) # Use use_doc_orientation_classify to enable/disable document orientation classification model
# ocr = PPStructureV3(use_doc_unwarping=True) # Use use_doc_unwarping to enable/disable document unwarping module
# ocr = PPStructureV3(use_textline_orientation=True) # Use use_textline_orientation to enable/disable textline orientation classification model
# ocr = PPStructureV3(device="gpu") # Use device to specify GPU for model inference
output = pipeline.predict("./KP10tiSZfAjMuwZUSLtRp.png")
for res in output:
    res.print() ## Print the structured prediction output
    res.save_to_json(save_path="output") ## Save the current image's structured result in JSON format
    res.save_to_markdown(save_path="output") ## Save the current image's result in Markdown format
```

The default model used in pipeline is `PP-DocLayout_plus-L`, so it is needed that specifing to `PP-DocLayout-M` by argument `layout_detection_model_name`. And you can also use the local model file by argument `layout_detection_model_dir`. 
For details about usage command and descriptions of parameters, please refer to the [Document](https://paddlepaddle.github.io/PaddleOCR/latest/en/version3.x/pipeline_usage/PP-StructureV3.html#2-quick-start).

## Links

[PaddleOCR Repo](https://github.com/paddlepaddle/paddleocr)

[PaddleOCR Documentation](https://paddlepaddle.github.io/PaddleOCR/latest/en/index.html)

