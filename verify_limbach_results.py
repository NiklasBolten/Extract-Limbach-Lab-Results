import json
import sys
import sqlite3

# TODO: Verify Limbach input via db comparison (patient and attribute) (own function for each?)
# TODO: throw errors for orders with db mismatches
# TODO: output matching Limbach input orders, so it can be parsed to the LIS
# TODO: multi-page handling???

def main():
    if len(sys.argv) != 2:
        print("Usage: verify_limbach_results.py [input.json]")
        sys.exit(1)

    # open and read inputted json file
    infile = open(sys.argv[1], "r")
    f = json.loads(infile.read())

    # open model LIS db
    cx = sqlite3.connect("LIS.db")
    cu = cx.cursor()

    for lab_result in f:
        verify_patient(lab_result, cu)
        # verify_parameters(lab_result, cu)

    cx.close()
    infile.close()

def verify_patient(lab_result, cu):
    attributes = ["firstname", "surname", "birthday", "gender"]
    for attribute in attributes:
        LIS_patient_attribute = get_patient_from_db(attribute, lab_result["anr"], cu)
        # print(LIS_patient_attribute)
        if LIS_patient_attribute == lab_result[attribute]:
            print(f"{attribute} correct!")
        else:
            print(f"{attribute} mismatch")
    return

def verify_parameters(lab_result, cu):
    i = 0
    attributes = ["parameter", "unit", "reference_range"]
    while i < (len(lab_result["parameters"])):
        for attribute in attributes:
            LIS_parameter_attribute = get_parameter_from_db(attribute, lab_result["anr"], cu, i)
            # print(LIS_parameter_attribute)
            print(len(lab_result["parameters"]))
            if LIS_parameter_attribute == lab_result["parameters"][i][attribute]:
                print(f"{attribute} correct!")
            else:
                print(f"{attribute} mismatch: {LIS_parameter_attribute} | {lab_result["parameters"][i][attribute]}")
        i += 1
    # TODO
    return
    
def get_patient_from_db(column, anr, cu):
    try:
        res = cu.execute(f"""
            SELECT {column} 
            FROM patients
            WHERE id IN(
                SELECT patient_id
                FROM order_number
                WHERE id = {anr})""")
        try:
            output = res.fetchone() #returns Tuple
            output = output[0] #first Element in that Tuple
            return output
        except AttributeError:
            print("AttributeError")
            return None
        except TypeError:
            print("TypeError")
            return None
    
    except KeyError:
        print("KeyError")
        return None

def get_parameter_from_db(column, anr, cu, i):
    try:
        res = cu.execute(f"""
            SELECT {column}
            FROM parameters
            WHERE id IN(
                SELECT parameter_id
                FROM order_parameters
                WHERE order_id = {anr})""")
        try:
            output = res.fetchall() #returns Tuple
            output = output[i] #ith Element in that Tuple
            return output
        except AttributeError:
            print("AttributeError")
            return None
        except TypeError:
            print("TypeError")
            return None
    except KeyError:
        print("KeyError")
        return None
    
if __name__ == '__main__':
    main()