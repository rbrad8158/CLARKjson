import os
import sys
import logging
from distutils.util import convert_path
__version__ = '0.0.0'


if __name__ == "__main__":
    if sys.version_info[0] < 3:
        raise RuntimeError("This program requires the Python 3 interpreter")
    else:
        from CLARKjson.CLARKjsoncli import CLARKjsonCLI

        _metapath = convert_path('CLARKjson/_metadata.py')
        _meta = {}
        try:
            with open(_metapath) as _metafile:
                exec(_metafile.read(), globals(), _meta)
        except EnvironmentError:
            raise RuntimeError("if %s.py exists, it is required to be well-formed" % (_metapath,))
        else:
            os.makedirs(os.path.dirname(os.path.join('logs', 'main.log')), exist_ok=True)
            # noinspection SpellCheckingInspection
            logging.basicConfig(filename=os.path.join('logs', 'main.log'),
                                format='%(asctime)s %(funcName)-12s %(levelname)-8s %(message)s',
                                filemode='w', level=logging.DEBUG)
            console = logging.StreamHandler()
            # console.setLevel(logging.DEBUG)
            console.setLevel(logging.ERROR)

            # set a format which is simpler for console use
            # noinspection SpellCheckingInspection
            formatter = logging.Formatter('%(funcName)-20s: %(levelname)-8s %(message)s')
            # tell the handler to use this format
            console.setFormatter(formatter)
            # add the handler to the root logger
            logging.getLogger('').addHandler(console)

            logging.debug('Python version ' + sys.version)

            CLARKjsonCLI(_meta).cmdloop()