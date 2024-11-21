# PDF-parser

## Introduction
PDF parsing is the processing of extracting elements from a PDF documents, most notably, text, tables and images. PDF parsing has become more relevant with the rise of LLM and the popularity of AI Chatbot, as LLM by nature is not good at extracting tables from a PDF.

This repository offers three code for PDF parsing, choose the mode by setting the `table_output_mode` parameter in the `extract_pdf` function. The three modes are:

1. **Mode 1: csv** General use case
   - Extracts text, images and tables
   - Includes labeling feature

2. **Mode 2: text** Table content preservation
   - Extracts text and images, includes labeling feature
   - Keeps table content in the text output in comma-separated format


3. **Method 3: bedrock** AI-generated table content description
   - Extracts text and images, includes labeling feature
   - Uses Bedrock to generate descriptive statements for table content
   - Inserts these descriptions into the text output

## Features Overview

| Method/Version | csv | text | bedrock |
|----------------|:-:|:--:|:--:|
| Text Extraction | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Image Extraction | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Table Extraction | :white_check_mark: | :x: | :white_check_mark: |
| Image & Table labeling | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Table format in text output | table content removed | comma-separated | Bedrock-generated content |

- For a better understanding, examine the example Wikipedia PDF and compare the three text outputs.
- Image and text extraction are consistent across all three methods.
- The sequence of text, images, and tables is maintained in the text output.
- Table with no consistent structure, eg dimension of table is not n x n, are extracted as screenshot, it will have no difference across all three mods

## Prerequisites

To use this code, you need to install the following Python libraries:

- [pdfplumber](https://github.com/jsvine/pdfplumber)
- [pymupdf](https://github.com/pymupdf/PyMuPDF)

You can install these libraries using pip:

```bash
pip install pdfplumber pymupdf
```


## Known Limitations

1. **Multi-page Table Handling:**
   Most PDF extraction tools, including this one, struggle with tables spanning multiple pages. The portion of the table on the second page is often treated as a new table, losing its header. 
   - Example: See the table on pages 9-10 in `Wikipedia.pdf`.

2. **Tables Without Clear Boundaries:**
   pdfplumber has difficulties extracting tables without distinct borders, common in financial statements.

3. **Chart Elements:**
   Usually from a powerpoint slide, chart element are hard to address in a batch process. 
 

## Possible solution or improvement
- Tackle the issue with chart elements
- Currently using pymupdf to extract image and screenshot, and pdfplumber for everything else. It is possible to only use pdfplumber.

## Version history
Jul 25 : Initial release, three modes (methods) are saved in three ipynb files (now in deprecated folder).  

Oct 4 : Added a new feature to take screenshot whenever table dimension is not n x n, combined all modes into one py file, renamed variable and tidy up code for better readability.   

Oct 16 : Improved the bedrock prompt and max token limit.  
