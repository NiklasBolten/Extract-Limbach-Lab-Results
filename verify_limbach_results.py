import json
import sys
import sqlite3

# TODO: output matching Lab Results, so they can be parsed to the LIS
# TODO: output mismatched Lab Results to a separate log file
# TODO: multi-page handling???

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

    for lab_result in f:
        print(f"\nlab result {i}: ANR: {lab_result["anr"]}\n")
        try:
            if not verify_patient(lab_result, cu):
                print("Patient verification Failed!")
                i += 1
                continue
        except TypeError:
            print(f"TypeError occured! -> ANR {lab_result["anr"]} not in LIS db?")
            i += 1
            continue
        except sqlite3.OperationalError:
            print(f"sqlite3.OperationalError occured -> no ANR found during extract_limbach_pdf.py!")
            i += 1
            continue
        except (AttributeError, KeyError) as e:
            print(f"{e} occured!")
            i += 1
            continue
        
        try:
            verify_parameters(lab_result, cu)
        except TypeError:
            print(f"TypeError occured! -> Parameter not ordered in LIS db!")
            i += 1
            continue
        except AttributeError:
            print(f"AttributeError occured!")
            i += 1
            continue
        except KeyError:
            print(f"KeyError occured! -> No Parameter name found during extract_limbach_pdf.py!")
            i += 1
            continue
        i += 1

    cx.close()
    infile.close()
    config.close()

def verify_patient(lab_result, cu):
    # load correct attribute names
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
    return True

def verify_parameters(lab_result, cu):
    # load correct attribute names
    parameter_attributes = {}
    parameter_attributes["parameter"] = cfg["attributes"]["parameter"]
    parameter_attributes["unit"] = cfg["attributes"]["unit"]
    parameter_attributes["reference_range"] = cfg["attributes"]["reference_range"]

    # for each parameter
    for parameter in lab_result["parameters"]:
        # load correct parameter attribute values from config
        LIS_parameter_attributes = {}
        try:
            LIS_parameter_attributes["name"] = cfg["parameters"][parameter["parameter"]]["name"]
        except KeyError:
            print(f"KeyError: {parameter["parameter"]} not in config.json")
            continue

        LIS_parameter_attributes["unit"] = cfg["parameters"][parameter["parameter"]]["unit"]
        LIS_parameter_attributes["reference_range"] = cfg["parameters"][parameter["parameter"]]["reference_range"]

        print(f"\n{LIS_parameter_attributes["name"]}:")
        # for each attribute
        for json_attribute, LIS_attribute in parameter_attributes.items():
            try:
                LIS_parameter_attribute = get_parameter_from_db(LIS_attribute, lab_result["anr"], cu, LIS_parameter_attributes["name"])
            except TypeError:
                print(f"TypeError: {parameter["parameter"]} exists in config.json, but is not ordered in LIS!")
                break

            if LIS_parameter_attribute == LIS_parameter_attributes[LIS_attribute]:
                print(f"{json_attribute} correct!")
            else:
                print(f"{LIS_parameter_attributes["name"]}: {json_attribute} mismatch: {LIS_parameter_attribute} | {LIS_parameter_attributes[LIS_attribute]}")
    return
    
def get_patient_from_db(column, anr, cu):
    res = cu.execute(f"""
        SELECT {column} 
        FROM patients
        WHERE id IN(
            SELECT patient_id
            FROM order_number
            WHERE id = {anr})""")
    output = res.fetchone() #returns Tuple
    output = output[0] #first (and only!) Element in that Tuple
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
    output = res.fetchone() #returns Tuple
    output = output[0] #first (and only!) Element in that Tuple
    return output
    
if __name__ == '__main__':
    main()