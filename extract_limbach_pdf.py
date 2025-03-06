from io import StringIO
import sys
import json
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTTextBoxHorizontal
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument

def main():
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

    output_string = StringIO()
    with open(input_path, 'rb') as in_file:
        parser = PDFParser(in_file)
        doc = PDFDocument(parser)
        rsrcmgr = PDFResourceManager()
        device = PDFPageAggregator(rsrcmgr, laparams=LAParams())
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        page_number = 0
        for page in PDFPage.create_pages(doc):
            page_number += 1
            output_string.write(f"Page number: {page_number}\n")
            interpreter.process_page(page)
            layout = device.get_result()

            # Initialize text_lines of entire page
            text_lines = []
            for element in layout:
                if isinstance(element, LTTextBoxHorizontal):
                    for text_line in element:
                        text_lines.append(text_line)

            # Extract patient infos and lab results
            for text_line in text_lines:
                x0, y0, _, _ = text_line.bbox  # Coordinates of the text
                if y0 >= 514 and y0 <= 515:  # Check if the text is in the range of the patient infos
                    output_string.write(extract_patient_infos(text_line, x0))
                elif y0 < 461:  # Check if the text is in the range of the lab results, beneath "Untersuchung"
                    output_string.write(extract_lab_results(text_line, x0, y0, text_lines))

    # Write the extracted text to the output file
    lines = output_string.getvalue().split('\n')
    i = 0
    # Combine multi-line comments into one string
    for line in lines:
        if lines[i].startswith("Comment: "):
            while lines[i + 1].startswith("Comment: "):
                lines[i] = lines[i] + '\n' + lines[i + 1][9:]
                lines.pop(i + 1)
        print(f"{i}: {lines[i]}")
        i += 1
    

    with open(output_path, 'w') as output_file:
        # TODO: clean up the text PROPERLY
        for line in lines:
            line = line.replace('(cid:13)', '')
            output_file.write(line + '\n')
        



def extract_patient_infos(text_line, x0):
    output = ''
    if x0 >= 55 and x0 <= 56:
        name_split = text_line.get_text().strip().split(',') # splits the name at the comma
        if len(name_split) == 2:
            firstname = name_split[1].strip() # strips the whitespace after the comma
            surname = name_split[0]
            output = (f"Vorname: {firstname}\nNachname: {surname}\n")
        else:
            output = (f"WARNING: Vorname or Nachname: None\n")

    elif x0 >= 361 and x0 <= 362:
        birth_gender = text_line.get_text().strip()
        birth_gender_split = birth_gender.split('/')
        if len(birth_gender_split) == 2:
            birthday = birth_gender_split[0]
            gender = birth_gender_split[1].strip() #strips the whitespace after the slash
            output = (f"Geburtsdatum: {birthday}\nGeschlecht: {gender}\n")
    elif x0 >= 464 and x0 <= 465:
        anr = text_line.get_text().strip()[10:] #slices "Ext.-Nr: " from the beginning of the string
        output = (f"ANR: {anr}\n")
    return output

def extract_lab_results(text_line, x0, y0, text_lines):
    output = ''
    if x0 >= 65 and x0 <= 66:
        # differentiate between parameter + value + unit + reference ranges and comments
        for value_unit_line in text_lines:
            value_unit_x0, value_unit_y0, _, _ = value_unit_line.bbox

            # if there is a (value_unit_)line on a similar y-coordinate and to the right of the text_line, 
            # text_line is a parameter and value_unit_line is the value + unit

            if int (value_unit_y0) in range(int (y0 - 5), int (y0 + 5)) and value_unit_x0 > x0: 

                # text_line is a parameter in this case
                parameter = text_line.get_text().strip()
                output = (f"Parameter: {parameter}\n")

                value_unit = value_unit_line.get_text().strip()
                value_unit_split = value_unit.split(' ')
                if len(value_unit_split) == 2:
                    value = value_unit_split[0]
                    unit = value_unit_split[1]
                    output = (f"{output}Value: {value}\nUnit: {unit}\n")
                else:
                    value = value_unit
                    unit = "None"
                    output = (f"{output}Value: {value}\n")
                    output = (f"{output}Unit: {unit}\n")

                # check for reference ranges
                # if there is a (reference_range_)line on a similar y-coordinate and to the right of the 
                # value_unit_line, value_unit_line is the value + unit and reference_range_line is the reference range

                for reference_range_line in text_lines:
                    reference_range_x0, reference_range_y0, _, _ = reference_range_line.bbox
                    if int (reference_range_y0) in range(int (value_unit_y0 - 5), int (value_unit_y0 + 5)) and reference_range_x0 > value_unit_x0:
                        reference_range = reference_range_line.get_text().strip()
                        output = (f"{output}Reference Range: {reference_range}\n")
                        return output
                reference_range = "None"
                output = (f"{output}Reference Range: {reference_range}\n")
                return output
    
        # if the text is not a parameter, it is a comment
        
        comment = text_line.get_text().strip()
        output = (f"Comment: {comment}\n")

    return output

main()