import sys
import json
import extract_limbach_pdf
import verify_limbach_results

# TODO: modify matched_lab_results to only include relevant attributes? -> Depends on how the results
# are parsed to the real LIS db, so for now, all attributes are included
# TODO: multi-page handling??? -> extract_limbach_pdf.py wont read multi-page results for now

def main():

    try: 
        config = open("config.json", "r")
    except FileNotFoundError:
        print("Error: config.json not found")
        sys.exit(1)
    except PermissionError:
        print("Error: No permission to open config.json.")
        sys.exit(1)
    except OSError as e:
        print(f"Other OS error: {e}")
        sys.exit(1)

    try:
        cfg = json.loads(config.read())
    except json.JSONDecodeError:
            print("Error: The config file is not a valid JSON file.")
            config.close()
            sys.exit(1)

    # Validate the pdf_path and output_path
    if len(sys.argv) != 2:
        print("Usage: extract_limbach_pdf.py [input.pdf]")
        sys.exit(1)

    input_path = sys.argv[1]
    if input_path[-4:] != '.pdf':
        print("Error: The input file must be a PDF file.")
        sys.exit(1)

    lab_results = extract_limbach_pdf.main(input_path)
    verify_limbach_results.main(lab_results, cfg)

if __name__ == "__main__":
    main()
