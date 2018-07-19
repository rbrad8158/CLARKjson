# Standard Packages
import os
import csv
from configparser import ConfigParser
import logging
import cmd
import json
import sys
import time
import mmap
import re
import timeit

def load_environment():
    logging.debug('Parsing config.ini and environmental variables')
    config = ConfigParser()
    config.read('config.ini')

    config['main']['file_path'] = os.getenv('file_path', config['main'].get('file_path'))
    config['main']['input_csv_note_file'] = os.getenv('input_csv_note_file', config['main'].get('input_csv_note_file'))
    config['main']['input_delimiter'] = os.getenv('input_delimiter', config['main'].get('input_delimiter'))
    config['main']['condense_output'] = os.getenv('condense_output_YN', config['main'].get('condense_output_YN'))

    config['note']['pat_id_col_id'] = os.getenv('pat_id_col_id', config['note'].get('pat_id_col_id'))
    config['note']['note_id_col_id'] = os.getenv('note_id_col_id', config['note'].get('note_id_col_id'))
    config['note']['note_type_col_id'] = os.getenv('note_type_col_id', config['note'].get('note_type_col_id'))
    config['note']['note_date_col_id'] = os.getenv('note_date_col_id', config['note'].get('note_date_col_id'))
    config['note']['note_seq_col_id'] = os.getenv('note_seq_col_id', config['note'].get('note_seq_col_id'))
    config['note']['note_csn_col_id'] = os.getenv('note_csn_col_id', config['note'].get('note_csn_col_id'))
    config['note']['note_source_col_id'] = os.getenv('note_source_col_id', config['note'].get('note_source_col_id'))
    config['note']['encounter_col_id'] = os.getenv('encounter_col_id', config['note'].get('encounter_col_id'))
    config['note']['order_type_col_id'] = os.getenv('order_type_col_id', config['note'].get('order_type_col_id'))
    config['note']['label_col_id'] = os.getenv('label_col_id', config['note'].get('label_col_id'))
    config['note']['gold_std_col_id'] = os.getenv('gold_std_col_id', config['note'].get('gold_std_col_id'))

    config['system']['release'] = os.getenv('version', config['system'].get('version')) + '.' + \
                                  os.getenv('build', config['system'].get('build')) + '.' + \
                                  os.getenv('revision', config['system'].get('revision'))
    return config


####################
# @function: _read_note_file
# @input:   config
# @output: List[Boolean, Integer, Dictionary]
# ##################
def _read_note_file(config):
    #Load in the file that contains our Notes in CSV
    # PAT_MRN|~|ENC_CSN|~|NOTE_TYPE|~|ORDR_TYPE|~|NOTE_DATE|~|NOTE_ID|~|SEQ_NUM|~|NOTE_TEXT|~|NOTE_CSN|~|NOTE_SOURCE|~|LAST_ADMIT_DT|~|LAST_DISCHARGE_DT|~|LABEL|~|INCLUDE_LABEL
    logging.debug('Parsing Input Note File...')
    input_file_path = get_input_file_path(config)
    output_file_path = get_output_file_path(config)
    read_params = get_read_params(config)
    field_names = read_params['fields']
    condense_output = get_condense_check(config)

    pat_counter = 0
    note_counter = 0

    def get_num_lines(file_path):
        fp = open(file_path, "r+")
        buf = mmap.mmap(fp.fileno(), 0)
        lines = 0
        while buf.readline():
            lines += 1
        return lines

    try:
        with open(os.path.abspath(input_file_path), 'r') as file_handle:
            curr_note = {}
            curr_note_id = 'START_SYS' + config['system']['release']
            curr_pat_id = 'START_SYS' + config['system']['release']

            pat_id_key = read_params['pat_id']
            note_id_key = read_params['note_id_col_id']
            note_text_key = read_params['note_text_col_id']
            logging.debug(note_text_key)
            total_lines = get_num_lines(input_file_path)

            print_progress(0, total_lines, prefix='Progress', suffix='Complete', bar_length=50)

            if type(read_params['delimeter']) is not str:
                reader = file_handle.readlines()
            else:
                reader = csv.DictReader(file_handle, delimiter=read_params['delimeter'], skipinitialspace=True)

            file_keys = []
            print('Starting Read of Note File...')
            logging.debug('Starting Line Processing')
            for line_num, line in enumerate(reader):
                temp_note = {}
                is_last = False if line_num != total_lines else True
                if type(read_params['delimeter']) is not str:
                    # logging.debug(re.split(read_params['delimeter'], line))
                    if line_num == 0:
                        logging.debug('First Line')
                        file_keys = re.split(read_params['delimeter'], line)
                        continue

                    elif re.search(read_params['delimeter'], line) is not None and len(line) > 0:
                        # logging.debug('File Line: ' + str(line_num))
                        temp_note_list = re.split(read_params['delimeter'], line)
                        # logging.debug(temp_note_list)
                        for i, key in enumerate(file_keys):
                            if key in field_names:
                                temp_note[key] = temp_note_list[i]
                                # logging.debug(key + ':' + temp_note_list[i] + ':' + temp_note[key])
                    else:
                        continue

                else:
                    if len(read_params['delimeter']) == 1:
                        for field in field_names:
                            temp_note[field] = line[field]

                if curr_note_id == 'START_SYS' + config['system']['release'] and line_num > 0:
                    curr_note = temp_note
                    curr_note_id = temp_note[note_id_key]
                    curr_pat_id = temp_note[pat_id_key]

                elif temp_note[note_id_key] == curr_note_id and read_params['note_text_combined_yn'] == 'N':
                    curr_note[note_text_key] = curr_note[note_text_key] + temp_note[note_text_key]

                elif temp_note[note_id_key] != curr_note_id and curr_note_id != 'START':
                    _written = _write_note(curr_note, output_file_path, is_last, condense_output)
                    if _written[0]:
                        curr_note = temp_note
                        curr_note_id = curr_note[note_id_key]
                        note_counter += 1
                    else:
                        break

                else:
                    _written = _write_note(curr_note, output_file_path, is_last, condense_output)
                    if _written[0]:
                        continue
                    else:
                        break

                if is_last:
                    _written = _write_note(curr_note, output_file_path, is_last, condense_output)
                    if _written[0]:
                        note_counter += 1
                    else:
                        break

                if curr_pat_id != temp_note[pat_id_key] and curr_pat_id != 'START_SYS' \
                        + config['system']['release']:
                    pat_counter += 1
                    curr_pat_id = temp_note[pat_id_key]

                print_progress(line_num+1, total_lines, prefix='Progress', suffix='Complete', bar_length=50)

        file_handle.close()

        # if input_med_dict.has_records:
        #     med_records = input_med_dict.get_med_count()
        #     return [True, med_records, input_med_dict]
        # else:
        #     return [False, "No Notes Were Able to Be Extracted"]
    except FileNotFoundError:
        return [False, "Input File Could Not Be Found (#CMDx002.3)"]

    finally:
        return [True, pat_counter, note_counter]

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
            if not condense:
                write_handle.write('\n')
            if is_last:
                write_handle.write(']')

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


def get_read_params(config):
    default_delim = ','
    read_params = {'delimeter': default_delim, 'fields': []}

    if config['main']['input_delimiter'].lower() != 'default' and len(config['main']['input_delimiter']) > 0:
        if len(config['main']['input_delimiter']) > 1:
            # need to convert to regular expression instead of straight string
            clean_delim =  re.escape(config['main']['input_delimiter'])
            pattern = '[' + clean_delim + ']{1}'
            read_params['delimeter'] = re.compile(pattern)
        else:
            read_params['delimeter'] = config['main']['input_delimiter']

    if len(config['note']['pat_id_col_id']) > 0:
        read_params['pat_id'] = config['note']['pat_id_col_id']
        read_params['fields'].append(read_params['pat_id'])

    if len(config['note']['note_id_col_id']) > 0:
        read_params['note_id_col_id'] = config['note']['note_id_col_id']
        read_params['fields'].append(read_params['note_id_col_id'])

    if len(config['note']['note_text_combined_yn']) > 0:
        read_params['note_text_combined_yn'] = config['note']['note_text_combined_yn'].upper()

    if len(config['note']['note_text_col_id']) > 0:
        read_params['note_text_col_id'] = config['note']['note_text_col_id']
        read_params['fields'].append(read_params['note_text_col_id'])

    if len(config['note']['note_date_col_id']) > 0:
        read_params['note_date_col_id'] = config['note']['note_date_col_id']
        read_params['fields'].append(read_params['note_date_col_id'])

    if len(config['note']['note_seq_col_id']) > 0:
        read_params['note_seq_col_id'] = config['note']['note_seq_col_id']
        read_params['fields'].append(read_params['note_seq_col_id'])

    if len(config['note']['note_csn_col_id']) > 0:
        read_params['note_csn_col_id'] = config['note']['note_csn_col_id']
        read_params['fields'].append(read_params['note_csn_col_id'])

    if len(config['note']['note_source_col_id']) > 0:
        read_params['note_source_col_id'] = config['note']['note_source_col_id']
        read_params['fields'].append(read_params['note_source_col_id'])

    if len(config['note']['encounter_col_id']) > 0:
        read_params['encounter_col_id'] = config['note']['encounter_col_id']
        read_params['fields'].append(read_params['encounter_col_id'])

    if len(config['note']['order_type_col_id']) > 0:
        read_params['order_type_col_id'] = config['note']['order_type_col_id']
        read_params['fields'].append(read_params['order_type_col_id'])

    if len(config['note']['label_col_id']) > 0:
        read_params['label_col_id'] = config['note']['label_col_id']
        read_params['fields'].append(read_params['label_col_id'])

    if len(config['note']['gold_std_col_id']) > 0:
        read_params['gold_std_col_id'] = config['note']['gold_std_col_id']
        read_params['fields'].append(read_params['gold_std_col_id'])

    return read_params

def get_condense_check(config):
    input_config = str(config['main']['condense_output']).upper()
    if input_config == 'Y' or input_config == 'YES':
        return True
    else:
        return False

class NoteJsonifierCLI(cmd.Cmd):
    def __init__(self):
        cmd.Cmd.__init__(self)
        self.config = load_environment()
        self.intro = 'Welcome to the UNC Clinical Note JSON\'ifier. \n' \
            'Release ' + self.config['system']['release'] + '\n ' \
            'Development of this tool is supported by NCATS NIH CTSA Grant UL1TR002489 \n\n ' \
            'Type help or ? to list commands.\n '

    @staticmethod
    def do_exit(self):
        """Close the window, and exit:  EXIT"""
        # if _file_loaded and not _results_saved:
        #     print('It looks like you loaded a file but haven\'t done anything yet.')
        #     _exit_check = self.prompt('Are you sure you want to exit? [Y/N]')
        #     if _exit_check.upper() == 'Y':
        #         print('Until next time...')
        #         return True
        #     else:
        #         return False
        # else:
        print('Until next time...')
        return True

    def do_readnotes(self, arg):
        """Read in the local note file to convert to JSON"""
        tic = timeit.default_timer()
        _result = _read_note_file(self.config);
        if _result[0]:
            print('\nNumber of Patients: ' + str(_result[1]))
            print('\nNumber of Notes: ' + str(_result[2]))
        toc = timeit.default_timer()
        elapsed = str(round(toc-tic, 2))
        print('\nElapsed Time: ' + str(elapsed) + ' seconds')

if __name__ == "__main__":
    if sys.version_info[0] < 3:
        raise RuntimeError("This program requires the Python 3 interpreter")

    os.makedirs(os.path.dirname(os.path.join('logs', 'main.log')), exist_ok=True)
    # noinspection SpellCheckingInspection
    logging.basicConfig(filename=os.path.join('logs', 'main.log'),
                        format='%(asctime)s %(funcName)-12s %(levelname)-8s %(message)s',
                        filemode='w', level=logging.DEBUG)
    console = logging.StreamHandler()
    # console.setLevel(logging.DEBUG)
    console.setLevel(logging.DEBUG)

    # set a format which is simpler for console use
    # noinspection SpellCheckingInspection
    formatter = logging.Formatter('%(funcName)-20s: %(levelname)-8s %(message)s')
    # tell the handler to use this format
    console.setFormatter(formatter)
    # add the handler to the root logger
    logging.getLogger('').addHandler(console)

    logging.debug('Python version ' + sys.version)

    NoteJsonifierCLI().cmdloop()