# Standard Packages
import os
import csv
import logging
import json
import sys
import time
import mmap
import re


####################
# @function: _clark_required_keys
# @description:
#   Provides required JSON key formats for variables required by the CLARK!
# @input:  None
# @output: Dictionary{ Configuration Key: Print format }
# ##################
def _clark_required_keys() -> dict:
    _clark_required = {'pat_id_col_id': 'MRN',
                      'note_text_col_id': 'note',
                      'note_id_col_id': 'noteID',
                      'note_type_col_id': 'noteType',
                      'note_date_col_id': 'noteDate',
                      'label_col_id': 'label'
                       }

    return _clark_required


####################
# @function: _read_note_file
# @description:
#   Reads in a file defined in 'config.ini' and converts sequential rows into a single note where matched on noteId.
#   Writes directly to output file as each note is complete.
# @input:   config
# @output: List[Boolean, Integer, Integer]
# ##################
def _read_note_file(config):
    #Load in the file that contains our Notes
    logging.debug('Setting Up the Reading Environment...')
    input_file_path = get_input_file_path(config)
    output_file_path = get_output_file_path(config)
    input_file_headers = get_input_headers_check(config)
    read_params = get_read_params(config)
    conf_file_keys = read_params['conf_file_keys']  # [conf_col_id values]
    note_conf = read_params['note_conf'] # {conf_col_id : conf value}
    condense_output = get_condense_check(config)

    pat_counter = 0
    note_counter = 0

    def get_num_lines(file_path) -> int:
        logging.debug('Getting Number of Lines in File...')
        fp = open(file_path, "r+")
        buf = mmap.mmap(fp.fileno(), 0)
        lines = 0
        while buf.readline():
            lines += 1
        return lines

    logging.debug('Starting File Read...')
    try:
        with open(os.path.abspath(input_file_path), 'r') as file_handle:
            logging.debug('File Found. Starting File Processing.')
            curr_note = {}
            curr_note_id = 'START_SYS' + config['system']['release']
            curr_pat_id = 'START_SYS' + config['system']['release']

            pat_id_key = _clark_required_keys()['pat_id_col_id']
            note_id_key = _clark_required_keys()['note_id_col_id']
            note_text_key = _clark_required_keys()['note_text_col_id']

            total_lines = get_num_lines(input_file_path)

            print('Starting Read of Note File...')
            print_progress(0, total_lines, prefix='Progress', suffix='Complete', bar_length=50)

            if type(read_params['delimiter']) is not str:
                reader = file_handle.readlines()
            else:
                reader = csv.DictReader(file_handle, delimiter=read_params['delimiter'], skipinitialspace=True)

            read_file_keys = []
            print_keys = {}
            logging.debug('Starting Line Processing')
            logging.debug('Number of lines: ' + str(total_lines))
            logging.debug('delimiter: ' + str(read_params['delimiter']))
            for line_num, line in enumerate(reader):
                temp_note = {}
                temp_note_list = []
                is_last = False if line_num != total_lines-1 else True
                if type(read_params['delimiter']) is not str:
                    if len(line) > 0 and re.search(read_params['delimiter'], line) is not None:
                        temp_note_list = re.split(read_params['delimiter'], line)
                # else:
                #   temp_note = line

                if line_num == 0 and input_file_headers:
                    logging.debug('First Line with Headers')
                    inter_keys = temp_note_list.copy() if type(read_params['delimiter']) is not str \
                        else temp_note.values()
                    read_file_keys = [key.replace('\n', '') for key in inter_keys]

                    # Check the file headers even for a single delimiter file read by DictReader
                    if check_input_keys(read_file_keys, note_conf):
                        print_keys = get_print_formats(note_conf)
                    else:
                        break  # There's a problem with the file construction

                else:
                    logging.debug('Processing File Line : ' + str(line_num))
                    # Because we can't use the DictReader for a multi-character delimiter,
                    # we have to build the dictionary enumerate(read_file_keys)
                    logging.debug(note_conf)
                    for conf_id, conf_value in note_conf.items():
                        logging.debug(str(conf_id) + ' : ' + str(conf_value))
                        col_idx = read_file_keys.index(conf_value)
                        last_key = len(read_file_keys)-1

                        if col_idx is not None:
                            logging.debug('Print Keys: ' + str(print_keys))
                            if type(read_params['delimiter']) is not str:
                                # last column in file usually contains a '\n' , get rid of it
                                temp_note[print_keys[conf_id]] = temp_note_list[col_idx].replace('\n', '') \
                                    if col_idx == last_key else temp_note_list[col_idx]
                                logging.debug('Column Processing: ' + conf_value + ':' + temp_note_list[col_idx].replace('\n', '') + ':'
                                              + temp_note[print_keys[conf_id]])
                            else:
                                temp_note[print_keys[conf_id]] = line[print_keys[conf_id]]
                    logging.debug(note_id_key)
                    logging.debug('Temp Note ID: ' + str(temp_note[note_id_key]))
                    logging.debug('Current Note ID: ' + str(curr_note_id))

                    if curr_note_id == 'START_SYS' + config['system']['release'] and line_num > 0:
                        logging.debug("Processing First Note in File")
                        curr_note = temp_note
                        curr_note_id = temp_note[note_id_key]
                        curr_pat_id = temp_note[pat_id_key]

                    elif temp_note[note_id_key] == curr_note_id and read_params['note_text_combined'] == 'N':
                        logging.debug('Temp Note Same ''noteID'' as Current Note...')
                        curr_note[note_text_key] = curr_note[note_text_key] + temp_note[note_text_key]
                        if is_last:
                            # print('Last Line and Note!')
                            _written = _write_note(curr_note, output_file_path, is_last, condense_output)
                            if _written[0]:
                                note_counter += 1
                            else:
                                logging.error('Failed to Write')
                                break

                    elif temp_note[note_id_key] != curr_note_id and curr_note_id != 'START_SYS' + config['system']['release']:
                        logging.debug('Temp Note ''noteID'' Different From Current Note...')
                        _written = _write_note(curr_note, output_file_path, is_last, condense_output)
                        if _written[0]:
                            curr_note = temp_note
                            curr_note_id = curr_note[note_id_key]
                            note_counter += 1
                        else:
                            logging.error('Failed to Write')
                            break

                    else:
                        logging.debug('Note Exception...')
                        _written = _write_note(curr_note, output_file_path, is_last, condense_output)
                        if _written[0]:
                            note_counter += 1
                        else:
                            logging.error('Failed to Write')
                            break

                    if (curr_pat_id != temp_note[pat_id_key] and curr_pat_id != 'START_SYS' \
                            + config['system']['release']) or is_last:
                        pat_counter += 1
                        curr_pat_id = temp_note[pat_id_key]

                logging.debug('Temp note: ' + str(temp_note))
                logging.debug('Curr note: ' + str(curr_note))

                print_progress(line_num+1, total_lines, prefix='Progress', suffix='Complete', bar_length=50)
        file_handle.close()

        # if input_med_dict.has_records:
        #     med_records = input_med_dict.get_med_count()
        #     return [True, med_records, input_med_dict]
        # else:
        #     return [False, "No Notes Were Able to Be Extracted"]
    except FileNotFoundError:
        return False, "Input File Could Not Be Found (#CMDx002.3)", None

    finally:
        return True, pat_counter, note_counter


def _write_note(in_note, output_file, is_last, condense=True):
    if os.path.exists(output_file):
        append_write = 'a'
        is_first = False
    else:
        append_write = 'w'
        is_first = True
    try:
        with open(os.path.abspath(output_file), append_write) as write_handle:
            if is_first:
                write_handle.write('[')

            json.dump(in_note, write_handle)
            # print(in_note)
            if not condense:
                write_handle.write('\n')
            if is_last:
                write_handle.write(']')
            else:
                write_handle.write(',')
        return [True]

    except FileNotFoundError:
        return [False, "Output File Could Not Be Written (#CMDx002.4)"]


def print_progress(iteration, total, prefix='', suffix='', decimals=1, bar_length=100):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        bar_length  - Optional  : character length of bar (Int)
    """
    str_format = "{0:." + str(decimals) + "f}"
    percents = str_format.format(100 * (iteration / float(total)))
    filled_length = int(round(bar_length * iteration / float(total)))
    bar = '█' * filled_length + '-' * (bar_length - filled_length)

    sys.stdout.write('\r%s |%s| %s%s %s' % (prefix, bar, percents, '%', suffix)),

    if iteration == total:
        sys.stdout.write('\n')
    sys.stdout.flush()


def check_input_keys(input_keys, conf_fields):
    logging.debug('Checking That All Required Keys Are Present...')
    logging.debug('Input Keys: ' + str(input_keys))
    logging.debug('Input Conf: ' + str(conf_fields))
    _clark_required = _clark_required_keys()
    _conf_values = list(conf_fields.values())  # conf_fields[config.ini line] = value in config.ini
    _conf_keys = list(conf_fields.keys())

    logging.debug(set(_conf_values))
    logging.debug(set(input_keys))
    if set(_conf_values) == set(input_keys):
        logging.debug('All Keys Accounted For in CONF and INPUT.')

        # Perform an initial check to make sure all required fields are present
        logging.debug('Clark Required: ' + str(_clark_required))
        for req_key in _clark_required:

            if req_key not in _conf_keys:
                logging.error('Required Key Not Found. Exiting.')
                print('Required Field is Not Populated! (xCMD005.1)\n'
                      'You must provide a value for \'' + str(req_key) +'\' in config.ini.')
                return False
            else:
                logging.debug('Key Found, Continuing...')
                continue
        return True
    else:
        for key in _conf_values:
            if key not in input_keys:
                logging.error('Key Note Found. Exiting.')
                print('Optional Field in Config is Not in Input File! (xCMD005.2)\n'
                      'You must provide a value for \'' + str(key) + '\' in input file if defined in config.ini .')
                return False
            else:
                continue
        logging.debug('Unknown Key In File Header.')
        print('Key in Input File Header Not included in config.ini. (xCMD005.3)\n'
              'All header values must be defined in config.ini!.')
        return False


def get_print_formats(in_fields):
    logging.debug('Getting Print Formats for Fields')
    _clark_required = _clark_required_keys()  # {conf_col_id : conf_value}
    logging.debug('Required: ' + str(_clark_required))
    logging.debug('Input: ' + str(in_fields))
    formats = {}
    for conf_field, conf_value in in_fields.items():
        logging.debug('in_fields line: ' + conf_field + ':' +conf_value)
        if conf_field in _clark_required:
            formats[conf_field] = _clark_required[conf_field]
        else:
            formats[conf_field] = re.sub(r'[_\-.\s]+([a-zA-Z0-9])', lambda m: m.group(1).upper(), conf_value)
    logging.debug('Print Formats: ' + str(formats))
    return formats


def get_input_file_path(config):
    from_config = config['main']['input_csv_note_file']

    if len(from_config) == 0:
        raise ValueError("Input File Path Provided in config.ini is empty (#CMDx002.1)")

    if 'input' not in from_config:
        if from_config[:1] != '\\':
            from_config = '\\'+from_config
        from_config = 'input'+from_config

    if '\/' in from_config:
        from_config = from_config.replace('\/', '\\')

    if from_config[:1] == '\\':
        from_config = '.'+from_config
    else:
        from_config = '.\\' + from_config

    return from_config


def get_output_file_path(config):
    from_config = config['main']['input_csv_note_file'].replace('.txt', '_'+time.strftime("%Y%m%d-%H%M%S")+'.json')

    if len(from_config) == 0:
        raise ValueError("Output File Path Provided in config.ini is empty (#CMDx002.2)")

    if 'output' not in from_config:
        if from_config[:1] != '\\':
            from_config = '\\'+from_config
        from_config = 'output'+from_config

    if '\/' in from_config:
        from_config = from_config.replace('\/', '\\')

    if from_config[:1] == '\\':
        from_config = '.'+from_config
    else:
        from_config = '.\\' + from_config

    return from_config


def get_input_headers_check(config):
    from_config = config['main']['headers_YN']
    if len(from_config) == 0:
        return False
    elif from_config.upper() == 'Y' or from_config.upper() == 'YES':
        return True
    else:
        return False


def get_read_params(config):
    default_delim = ','
    read_params = {'delimiter': default_delim, 'note_text_combined': config['main']['note_text_combined'],
                   'conf_file_keys': [], 'note_conf': {}}
    _required_keys = _clark_required_keys()

    if config['main']['input_delimiter'].lower() != 'default' and len(config['main']['input_delimiter']) > 0:
        if len(config['main']['input_delimiter']) > 1:
            # need to convert to regular expression instead of straight string
            clean_delim = re.escape(config['main']['input_delimiter'])
            pattern = clean_delim + '{1}'
            logging.debug(pattern)
            read_params['delimiter'] = re.compile(pattern)
        else:
            read_params['delimiter'] = config['main']['input_delimiter']

    # Process Note Keys/Parameters
    for conf_key in config['note']:
        if conf_key in _required_keys and len(config['note'][conf_key]) == 0:
            print('Required Field is Not Populated! (xCMD005.1)\n'
                  'You must provide a value for \'' + conf_key + '\' in config.ini.')
            return
        else:
            if len(config['note'][conf_key]) > 0:
                read_params['note_conf'][conf_key] = config['note'][conf_key]
                read_params['conf_file_keys'].append(read_params['note_conf'][conf_key])
            else:
                logging.debug('Key of invalid length, not loaded: ' + str(conf_key))

    if len(config['note']['other_meta']) > 0:
        temp_meta = re.split(config['note']['other_meta'], '[,]{0, 1}')
        for i in temp_meta:
            read_params['note_conf'][temp_meta[i]] = temp_meta[i]
            read_params['conf_file_keys'].append(temp_meta[i])
    logging.debug('Returning \'read_params\':' + str(read_params))
    return read_params


def get_condense_check(config):
    input_config = str(config['main']['condense_output']).upper()
    if input_config == 'Y' or input_config == 'YES':
        return True
    else:
        return False
