import json
import csv
import sqlite3

def verify_limbach_results(lab_results, cfg):

    # open model LIS db
    cx = sqlite3.connect("LIS.db")
    cu = cx.cursor()
    i = 1 # counts lab results

    lab_results = json.loads(lab_results)

    matched_lab_results = []
    mismatched_lab_results = []

    for lab_result in lab_results:
        patient_mismatch_reason = None
        parameter_mismatch_reason = None
        try:
            patient_mismatch_reason = verify_patient(lab_result, cu, cfg)
        except TypeError:
            patient_mismatch_reason = f"TypeError occured! -> ANR {lab_result["anr"]} not in LIS db?"
        except sqlite3.OperationalError:
            patient_mismatch_reason = "sqlite3.OperationalError occured -> no ANR found during extract_limbach_pdf.py!"
        except (AttributeError, KeyError) as e:
            patient_mismatch_reason = f"{e} occured!"
        
        try:
            parameter_mismatch_reason = verify_parameters(lab_result, cu, cfg)
        except TypeError:
            parameter_mismatch_reason = "TypeError occured! -> Parameter not ordered in LIS db!"
        except AttributeError:
            parameter_mismatch_reason = "AttributeError occured!"
        except KeyError:
            parameter_mismatch_reason = "KeyError occured! -> No Parameter name found during extract_limbach_pdf.py!"
        
        if patient_mismatch_reason == None and parameter_mismatch_reason == None and lab_result["number_of_pages"] == "1":
            matched_lab_results.append(lab_result)
        else:
            mismatched_lab_results.append(lab_result)
            mismatched_lab_results[len(mismatched_lab_results) - 1]["page"] = i
            mismatched_lab_results[len(mismatched_lab_results) - 1]["patient_mismatch_reason"] = patient_mismatch_reason
            mismatched_lab_results[len(mismatched_lab_results) - 1]["parameter_mismatch_reason"] = parameter_mismatch_reason
        i += 1

    with open("matched_lab_results.json", 'w') as outfile:
        outfile.write(json.dumps(matched_lab_results, indent=4, ensure_ascii=False))

    with open("mismatched_lab_results.csv", 'w', newline='') as outfile:
        fieldnames = ['page', 'anr', 'firstname', 'surname', 'birthday', 'parameter_mismatch_reason', 'patient_mismatch_reason', 'number_of_pages']
        writer = csv.DictWriter(outfile, fieldnames=fieldnames, dialect='excel', delimiter='\t')
        writer.writeheader()
        for lab_result in mismatched_lab_results:
            writer.writerow({'page': lab_result['page'],
                            'anr': lab_result['anr'],
                            'firstname': lab_result['firstname'],
                            'surname': lab_result['surname'],
                            'birthday': lab_result['birthday'],
                            'parameter_mismatch_reason': lab_result['parameter_mismatch_reason'],
                            'patient_mismatch_reason': lab_result['patient_mismatch_reason'],
                            'number_of_pages': lab_result['number_of_pages']})
    

    cx.close()

def verify_patient(lab_result, cu, cfg):
    # load relevant attribute names from config
    patient_attributes = {}
    patient_attributes["firstname"] = cfg["attributes"]["firstname"]
    patient_attributes["surname"] = cfg["attributes"]["surname"]
    patient_attributes["birthday"] = cfg["attributes"]["birthday"]
    patient_attributes["gender"] = cfg["attributes"]["gender"]

    for json_attribute, LIS_attribute in patient_attributes.items():
       
        LIS_patient_attribute = get_patient_from_db(LIS_attribute, lab_result["anr"], cu)

        if LIS_patient_attribute != lab_result[json_attribute]:
            reason = f"{json_attribute} mismatch: {LIS_patient_attribute} | {lab_result[json_attribute]}"
            return reason
    return None

def verify_parameters(lab_result, cu, cfg):
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
            reason = f"TypeError: {parameter["parameter"]} exists in config.json, but is not ordered in LIS!"
            return reason
        except KeyError:
            reason = f"KeyError: {parameter["parameter"]} not in config.json"
            return reason
        
        # verify unit and reference range:
        # load relevant parameter specific attributes from config (except valid_comments; those are handled seperately)
        parameter_attributes = {}
        parameter_attributes["unit"] = cfg["parameters"][parameter["parameter"]]["unit"]
        parameter_attributes["reference_range"] = cfg["parameters"][parameter["parameter"]]["reference_range"]

        # for each attribute (not parameter_attributes; valid_comments are handled seperately!)
        for json_attribute, LIS_attribute in attribute_names.items():

            if parameter[json_attribute] != parameter_attributes[LIS_attribute]:
                reason = f"{json_attribute} mismatch: {parameter[json_attribute]} | {parameter_attributes[LIS_attribute]}"
                return reason
        
        # verify comment: 
        if "comment" in parameter:
            result = verify_comment(parameter, cfg)
            if result['success'] == True:
                parameter["comment"] = result['name'] # this ends up in the matched_lab_results.json file!
            else:
                return result['reason']
    return None
    
def verify_comment(parameter, cfg):
        valid_comments = cfg["parameters"][parameter["parameter"]]["comments"]
        if not valid_comments:
            return {'success': False, 'reason': f"No valid comments for {parameter["parameter"]} in config.json"}
        try:
            for instance in range(len(valid_comments)):
                if parameter["comment"] == valid_comments[instance]["text"]:
                    return {'success': True, 'name': valid_comments[instance]["name"]}
        except KeyError:
            return {'success': False, 'reason': f"KeyError: {valid_comments[instance]} is missing name or text key for {parameter["parameter"]} in config.json"}
        
        return {'success': False, 'reason': f"Comment for {parameter["parameter"]} not found in config.json"}

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