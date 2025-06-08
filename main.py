import sys
import json
from limbach.extract_limbach_pdf import extract_limbach_pdf
from limbach.verify_limbach_results import verify_limbach_results

# TODO: modify matched_lab_results to only include relevant attributes? -> Depends on how the results
# are parsed to the real LIS db, so for now, all attributes are included
# TODO: multi-page handling??? -> extract_limbach_pdf.py returns reported number of pages, verify_limbach_results.py
# appends lab_result to mismatched_lab_results if number_of_pages is not 1


def main():

    try: 
        config = open("config.json", "r", encoding="utf-8")
    except FileNotFoundError:
        print("Error: config.json not found")
        input("Press Enter to exit...")
        sys.exit(1)
    except PermissionError:
        print("Error: No permission to open config.json.")
        input("Press Enter to exit...")
        sys.exit(1)
    except OSError as e:
        print(f"Other OS error: {e}")
        input("Press Enter to exit...")
        sys.exit(1)

    try:
        cfg = json.loads(config.read())
    except json.JSONDecodeError:
        print("Error: The config file is not a valid JSON file.")
        input("Press Enter to exit...")
        config.close()
        sys.exit(1)

    input_path = input("Name of the PDF file to extract lab results from (default: Befunddruck.pdf): ")
    if input_path == "":
        print("No input file specified, using default: Befunddruck.pdf")
        input_path = "Befunddruck.pdf"
    elif input_path[-4:] != ".pdf":
        print("Error: The input file must be a PDF file.")
        input("Press Enter to exit...")
        sys.exit(1)

    try:
        lab_results = extract_limbach_pdf(input_path)
    except FileNotFoundError:
        print(f"Error: {input_path} not found.")
        input("Press Enter to exit...")
        sys.exit(1)

    verify_limbach_results(lab_results, cfg)


if __name__ == "__main__":
    main()
