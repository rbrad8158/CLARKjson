## CLARK! Note "JSON'ifier"
### Description
The CLARK! Note "JSON'ifier" program is designed to take a text or csv file containing clinical notes and construct a 
JSON object that can easily be digested by the CLARK! application. It is designed to be dynamic to incorporate as much
additional metadata as desired but also ensure the required data elements are present for CLARK! to digest.

#### What is CLARK! ?
CLARK! is a machine-learning classifier developed through a collaboration between NC TraCS and CoVar Applied 
Technologies, a Durham, NC-based machine learning company. CLARK! is designed to take clinical notes as input, and 
classify those notes based on features defined by the user as regular expressions.


### Instructions
##### Note Extract
A text or CSV file must be prepared from your clinical data that includes at minimum the following items:
1. Patient ID (Usually Medical Record Number)
2. Note Text (either single lines or an already pre-compiled note)
3. Unique Note ID
4. Note Type
5. Note Date
6. Label (i.e. disease group)

Additional data can be included as metadata if desired and defined in the "config.ini".

##### App Configuration - Config.ini
The "config.ini" needs to be updated to contain specifics to your note extract.
A number of parameters are available for you to customize how the application processes your note file. Definitions for 
each parameter are available below:

- file_path : Custom file path to where the input file is located
- input_csv_note_file : Name of the input note file (either .txt or .csv)
- input_delimiter : The delimiter used to separate columns of data in your note file. This can be a single character 
such as a "," or multicharacter "|~|". It is important to use a delimiter that you are confident does not appear 
anywhere in a clinical note.
- condense_output_YN : To save on space you can set this to "Y" to prevent line breaks from being input at the end of 
each note. By default line breaks are inserted for readability.
- note_text_combined_YN : If you have already pre-compiled your notes and do not need to combine multiple lines set this 
to "Y" to simplify the programs processing of your note file
- file_includes_headers_YN : If your input file contains file headers, set to "Y" to ensure proper processing. 
**The headers in your file must match exactly with your config.ini settings below**

The following parameters allow some customization to the program. The values for each parameter below must match 
exactly with what is used in your input file.
##### Required Parameters
- pat_id_col_id : Patient ID
- note_text_col_id : Note Text 
- note_id_col_id : Note ID
- note_type_col_id : Note Type
- note_date_col_id : Note Date
- label_col_id : Note Label

##### Optional Parameters
- note_seq_col_id
- note_csn_col_id
- note_source_col_id
- encounter_col_id
- order_type_col_id
- gold_std_col_id
- other_meta : A comma delimited list of additional metadata columns included in your note file.

After completing the setup of "config.ini" you can run the program and follow the instructions within the App to 
produce your JSON'ified Note File.


### About
This App was developed by:

    Author(s): Robert Bradford
    Organization : University of North Carolina at Chapel Hill 
    Department : Translational and Clinical Sciences Institute (TraCS)
                    https://tracs.unc.edu
                    https://github.com/nctracs
    Support : Development of this tool is supported by NCATS NIH CTSA Grant UL1TR002489