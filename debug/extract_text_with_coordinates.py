from io import StringIO
import sys
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTTextBoxHorizontal
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument

# Validate the pdf_path and output_path
if len(sys.argv) != 3:
    print("Usage: extract_limbach_pdf.py [input.pdf] [output.txt]")
    sys.exit(1)

input_path = sys.argv[1]
if input_path[-4:] != '.pdf':
    print("Error: The input file must be a PDF file.")
    sys.exit(1)

output_path = sys.argv[2]
if output_path[-4:] != '.txt':
    print("Error: The output file must be a TXT file.")
    sys.exit(1)

def extract_text_with_coordinates(pdf_path, output_path):
    output_string = StringIO()
    with open(pdf_path, 'rb') as in_file:
        parser = PDFParser(in_file)
        doc = PDFDocument(parser)
        rsrcmgr = PDFResourceManager()
        device = PDFPageAggregator(rsrcmgr, laparams=LAParams())
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        page_number = 1
        for page in PDFPage.create_pages(doc):
            output_string.write(f"Page Number: {page_number}")
            page_number += 1
            interpreter.process_page(page)
            layout = device.get_result()
            for element in layout:
                if isinstance(element, LTTextBoxHorizontal):
                    for text_line in element:
                        x0, y0, x1, y1 = text_line.bbox  # Coordinates of the text
                        output_string.write(f"Text: {text_line.get_text().strip()} at ({x0}, {y0}, {x1}, {y1})\n")
    
    with open(output_path, 'w') as output_file:
        output_file.write(output_string.getvalue())

# Usage
extract_text_with_coordinates(input_path, output_path)