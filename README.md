# Description:

## What's Included:

- Within `limbach/`: `extract_limbach_pdf.py` & `verify_limbach_results.py`, initialized as Python modules
    
- `main.py`, the main program
    
- `config.json`, containing correct attribute names, expected parameter attributes, and known comments for each parameter
    
- `debug/extract_text_with_coordinates.py`: a program to extract text from a PDF file with corresponding coordinates
    
- `schema.sql`, as a reference for the model database, which needs to be built for running the program outside an actual laboratory information system (LIS)
    
- A bundled `.exe` for simple Windows usage, built with PyInstaller

# Building the executable:
## Requirements:
- A Windows machine (Only tested on Windows 10)
- a `LIS.db` file, structured like `schema.sql`
## Installation:
- Unzip the package inside a directory
- build an sqlite3 db called `LIS.db`, that is structured like `schema.sql`

# Building the python script:
## Requirements:
- Any modern OS, that supports Python3
- Python3
- pdfminer.six (installable via pip)
## Installation:
- Clone this repository into a directory
- "pip install pdfminer.six'
- build an sqlite3 db called `LIS.db`, that is structured like `schema.sql`

# Setting up `config.json`:
`config.json` is split into two dictionary objects:
## attributes
This object should only be of concern when linking the program to the LIS. The key names are identical to the key names specified for the output json (and csv) files via `extract_limbach_pdf.py`. **Do not change the key names**, unless you also want to modify the python code.
The associated values for each key are needed when looking up these attributes inside the LIS. For the schematic model LIS db, those value names are almost identical to the key names, for an actual LIS, other values might be neccessary.
```json
"attributes":
{
	"parameter": "name",
	"value": "value",
	"unit": "unit",
	"reference_range": "reference_range",
	"firstname": "firstname",
	"surname": "surname",
	"birthday": "birthday",
	"gender": "gender"
}
```
## parameters
This object stores every parameter with its desired attribute values, aswell as associated comments.
In some cases, the desired attribute values reported in Labor Limbach's lab result may differ from the attribute values defined inside the LIS. Each parameter is stored as an individual key, where the key is the string, that `extract_limbach_pdf.py` returned in `extracted_lab_results.json` as the parameter name. It's value is a dictionary, storing the parameter name inside the LIS, the unit and reference range you deem as correct, aswell as every comment suitable for this parameter.
- the "name" field links the parameter to the LIS. Depending on the implementation of this Program into the LIS, a unique ID might also be a suitable value
- "unit" and "reference_range" store the correct unit and reference range, that should be returned by `extract_limbach_pdf.py` as the unit and reference_range field.
- the "comments" field is a list, that can hold a variable number of unique comments. Each comment consists of:
	-  a "name" field, that represents the name for this comment, that is stored inside the LIS.
	- a "text" field, that represents the string, that `extract_limbach_pdf.py` returned in `extracted_lab_results.json`.
```json
"parameters":
{
	"Parameter name read by extract_limbach_pdf":
	{
		"name": "Parameter name in own LIS",
		"unit": "Unit to be read by extract_limbach_pdf",
		"reference_range": "Reference range to be read by extract_limbach_pdf",
		"comments":
		[
			{
				"name": "comment name in own LIS",
				"text": "comment text to be read by extract_limbach_pdf"
			},
			{
				"name": "name 2",
				"text": "text 2"
			}
		]
	},
	...
}
```
# Usage:
- Drag the pdf to be extracted into the root directory
	- Running the executable: double click `extract_limbach_pdf.exe`
	- Running the python script: "python main.py"
- A terminal window should open, asking for the name of the input pdf. Pressing enter defaults to `Befunddruck.pdf`, which is the default pdf name when downloading a collection of lab results from Labor Limbach.
- 3 Files will be generated: 
	1. `matched_lab_results.json` -> parse this to the LIS
	2. `mismatched_lab_results.csv` -> manual correction required
	3. `debug/extracted_lab_results.json` -> for debugging purposes