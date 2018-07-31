import cmd
import os
from CLARKjson.CLARKjson import _read_note_file
import logging
import timeit
from configparser import ConfigParser

def load_environment():
    logging.debug('Parsing config.ini and environmental variables')
    config = ConfigParser()
    config.read('config.ini')

    config['main']['file_path'] = os.getenv('file_path', config['main'].get('file_path'))
    config['main']['input_csv_note_file'] = os.getenv('input_csv_note_file', config['main'].get('input_csv_note_file'))
    config['main']['input_delimiter'] = os.getenv('input_delimiter', config['main'].get('input_delimiter'))
    config['main']['condense_output'] = os.getenv('condense_output_YN', config['main'].get('condense_output_YN'))
    config['main']['note_text_combined'] = os.getenv('note_text_combined_YN', config['main'].get('note_text_combined_YN'))
    config['main']['headers_YN'] = os.getenv('file_includes_headers_YN', config['main'].get('file_includes_headers_YN'))

    config['note']['pat_id_col_id'] = os.getenv('pat_id_col_id', config['note'].get('pat_id_col_id'))
    config['note']['note_id_col_id'] = os.getenv('note_id_col_id', config['note'].get('note_id_col_id'))
    config['note']['note_text_col_id'] = os.getenv('note_text_col_id', config['note'].get('note_text_col_id'))
    config['note']['note_type_col_id'] = os.getenv('note_type_col_id', config['note'].get('note_type_col_id'))
    config['note']['note_date_col_id'] = os.getenv('note_date_col_id', config['note'].get('note_date_col_id'))
    config['note']['label_col_id'] = os.getenv('label_col_id', config['note'].get('label_col_id'))

    config['note']['note_seq_col_id'] = os.getenv('note_seq_col_id', config['note'].get('note_seq_col_id'))
    config['note']['note_csn_col_id'] = os.getenv('note_csn_col_id', config['note'].get('note_csn_col_id'))
    config['note']['note_source_col_id'] = os.getenv('note_source_col_id',
                                                     config['note'].get('note_source_col_id'))
    config['note']['encounter_col_id'] = os.getenv('encounter_col_id', config['note'].get('encounter_col_id'))
    config['note']['order_type_col_id'] = os.getenv('order_type_col_id', config['note'].get('order_type_col_id'))
    config['note']['gold_std_col_id'] = os.getenv('gold_std_col_id', config['note'].get('gold_std_col_id'))
    config['note']['other_meta'] = os.getenv('other_meta', config['note'].get('other_meta'))

    return config


class CLARKjsonCLI(cmd.Cmd):
    def __init__(self, _meta):
        cmd.Cmd.__init__(self)
        self.__version__ =  _meta['version']
        self.__grant__ = _meta['grant']
        self.config = load_environment()
        self.intro = 'Welcome to the UNC Clinical Note JSON\'ifier. \n' \
            'Release ' + self.__version__ + ' \n ' \
            'Development of this tool is supported by ' + self.__grant__ + ' \n\n ' \
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
