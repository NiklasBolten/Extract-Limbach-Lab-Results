import json
import sys
import sqlite3

# TODO: modify mismatched_lab_results to include reason for mismatch, aswell as the full lab result
# as a file, that can be displayed as an excel sheet (probably as csv file)
# TODO: modify matched_lab_results to only include relevant attributes? -> Depends on how the results
# are parsed to the real LIS db, so for now, all attributes are included
# TODO: multi-page handling??? -> extract_limbach_pdf.py wont read multi-page results for now

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

def main():
    if len(sys.argv) != 2:
        print("Usage: verify_limbach_results.py [input.json]")
        sys.exit(1)

    if sys.argv[1][-5:] != '.json':
        print("Error: The input file must be a JSON file.")
        sys.exit(1)

    # open model LIS db
    cx = sqlite3.connect("LIS.db")
    cu = cx.cursor()
    i = 1 # counts lab results

    # open and read inputted json file
    infile = open(sys.argv[1], "r")
    try:
        f = json.loads(infile.read())
    except json.JSONDecodeError:
        print("Error: The input file is not a valid JSON file.")
        infile.close()
        cx.close()
        config.close()
        sys.exit(1)

    matched_lab_results = []
    mismatched_lab_results = []

    for lab_result in f:
        print(f"\nlab result {i}: ANR: {lab_result["anr"]}\n")
        is_matched = True
        try:
            if not verify_patient(lab_result, cu):
                is_matched = False
        except TypeError:
            print(f"TypeError occured! -> ANR {lab_result["anr"]} not in LIS db?")
            is_matched = False
        except sqlite3.OperationalError:
            print(f"sqlite3.OperationalError occured -> no ANR found during extract_limbach_pdf.py!")
            is_matched = False
        except (AttributeError, KeyError) as e:
            print(f"{e} occured!")
            is_matched = False
        
        try:
            if not verify_parameters(lab_result, cu):
                is_matched = False
        except TypeError:
            print(f"TypeError occured! -> Parameter not ordered in LIS db!")
            is_matched = False
        except AttributeError:
            print(f"AttributeError occured!")
            is_matched = False
        except KeyError:
            print(f"KeyError occured! -> No Parameter name found during extract_limbach_pdf.py!")
            is_matched = False
        
        if is_matched:
            matched_lab_results.append(lab_result)
        else:
            mismatched_lab_results.append(lab_result)            
        i += 1

    with open("matched_lab_results.json", 'w') as outfile:
        outfile.write(json.dumps(matched_lab_results, indent=4, ensure_ascii=False))

    with open("mismatched_lab_results.json", 'w') as outfile:
        outfile.write(json.dumps(mismatched_lab_results, indent=4, ensure_ascii=False))
    

    cx.close()
    infile.close()
    config.close()

def verify_patient(lab_result, cu):
    # load relevant attribute names from config
    patient_attributes = {}
    patient_attributes["firstname"] = cfg["attributes"]["firstname"]
    patient_attributes["surname"] = cfg["attributes"]["surname"]
    patient_attributes["birthday"] = cfg["attributes"]["birthday"]
    patient_attributes["gender"] = cfg["attributes"]["gender"]

    for json_attribute, LIS_attribute in patient_attributes.items():
       
        LIS_patient_attribute = get_patient_from_db(LIS_attribute, lab_result["anr"], cu)

        if LIS_patient_attribute == lab_result[json_attribute]:
            print(f"{json_attribute} correct!")
        else:
            print(f"{json_attribute} mismatch: {LIS_patient_attribute} | {lab_result[json_attribute]}")
            return False
    print("\n")
    return True

def verify_parameters(lab_result, cu):
    # load relevant attribute names (not parameter specific!) from config
    # provides correct keys for unit and reference range verification
    attribute_names = {}
    attribute_names["unit"] = cfg["attributes"]["unit"]
    attribute_names["reference_range"] = cfg["attributes"]["reference_range"]

    # for each parameter
    for parameter in lab_result["parameters"]:

        # check if parameter is ordered in LIS; this also verifies the parameter's name
        try:
            get_parameter_from_db(cfg["attributes"]["parameter"], lab_result["anr"], cu, cfg["parameters"][parameter["parameter"]]["name"])
        except TypeError:
            print(f"TypeError: {parameter["parameter"]} exists in config.json, but is not ordered in LIS!")
            return False
        except KeyError:
            print(f"KeyError: {parameter["parameter"]} not in config.json")
            return False
        
        print(f"{cfg["parameters"][parameter["parameter"]]["name"]}:")

        # verify unit and reference range:
        # load relevant parameter specific attributes from config (except valid_comments; those are handled seperately)
        parameter_attributes = {}
        parameter_attributes["unit"] = cfg["parameters"][parameter["parameter"]]["unit"]
        parameter_attributes["reference_range"] = cfg["parameters"][parameter["parameter"]]["reference_range"]

        # for each attribute (not parameter_attributes; valid_comments are handled seperately!)
        for json_attribute, LIS_attribute in attribute_names.items():

            if parameter[json_attribute] == parameter_attributes[LIS_attribute]:
                print(f"{json_attribute} correct!")
            else:
                print(f"{json_attribute} mismatch: {parameter[json_attribute]} | {parameter_attributes[LIS_attribute]}")
                return False
        
        # verify comment: 
        if "comment" in parameter:
            comment_name = verify_comment(parameter)
            if comment_name:
                print(f"comment correct -> {comment_name}")
            else:
                print("comment not found!")
                return False
        print("\n")
    return True
    
def verify_comment(parameter):
        valid_comments = cfg["parameters"][parameter["parameter"]]["comments"]
        if not valid_comments: # No valid comments in config.json
            return False
        try:
            for instance in range(len(valid_comments)):
                if parameter["comment"] == valid_comments[instance]["text"]:
                    return valid_comments[instance]["name"]
        except KeyError:
            print(f"KeyError: {valid_comments[instance]} is missing name or text key in config.json")
        return False

def get_patient_from_db(column, anr, cu):
    res = cu.execute(f"""
        SELECT {column} 
        FROM patients
        WHERE id IN(
            SELECT patient_id
            FROM order_number
            WHERE id = {anr})""")
    output = res.fetchone() # returns Tuple
    output = output[0] # first (and only!) Element in that Tuple
    return output


def get_parameter_from_db(column, anr, cu, parameter_name):
    res = cu.execute(f"""
        SELECT {column}
        FROM parameters
        WHERE id IN(
            SELECT parameter_id
            FROM order_parameters
            WHERE order_id = {anr})
        AND name = "{parameter_name}"
            """)
    output = res.fetchone() # returns Tuple
    output = output[0] # first (and only!) Element in that Tuple
    return output
    
if __name__ == '__main__':
    main()