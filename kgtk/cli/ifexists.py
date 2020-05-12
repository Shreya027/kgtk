"""Filter a KGTK file based on whether one or more records exist in a second
KGTK file with matching values for one or more fields.

TODO: Need KgtkWriterOptions
"""

from argparse import Namespace, SUPPRESS
from pathlib import Path
import sys
import typing

from kgtk.cli_argparse import KGTKArgumentParser
from kgtk.io.kgtkreader import KgtkReader, KgtkReaderOptions
from kgtk.io.kgtkwriter import KgtkWriter
from kgtk.join.ifexists import IfExists
from kgtk.value.kgtkvalueoptions import KgtkValueOptions

def parser():
    return {
        'help': 'Filter a KGTK file',
        'description': 'Filter a KGTK file based on whether one or more records exist in a second KGTK file with matching values for one or more fields.'
    }


def add_arguments_extended(parser: KGTKArgumentParser, parsed_shared_args: Namespace):
    """
    Parse arguments
    Args:
        parser (argparse.ArgumentParser)
    """

    _expert: bool = parsed_shared_args._expert

    # This helper function makes it easy to suppress options from
    # The help message.  The options are still there, and initialize
    # what they need to initialize.
    def h(msg: str)->str:
        if _expert:
            return msg
        else:
            return SUPPRESS

    parser.add_argument(      "input_kgtk_file", nargs="?", help="The KGTK file to filter. May be omitted or '-' for stdin.", type=Path)

    parser.add_argument(      "--input-keys", "--left-keys", dest="input_keys", help="The key columns in the file being filtered.", nargs='*')

    parser.add_argument(      "--filter-on", dest="filter_kgtk_file", help="The KGTK file to filter against.", type=Path, required=True)

    parser.add_argument(      "--filter-keys", "--right-keys", dest="filter_keys", help="The key columns in the filter-on file.", nargs='*')

    parser.add_argument("-o", "--output-file", dest="output_kgtk_file", help="The KGTK file to write", type=Path, default=None)

    # This argument is retained for compatability with earlier versions of this command.
    parser.add_argument(      "--error-limit", dest="error_limit",
                              help=h("The maximum number of errors per input fule (default=%(default)s)"),
                              default=KgtkReaderOptions.ERROR_LIMIT_DEFAULT)

    parser.add_argument(      "--field-separator", dest="field_separator",
                              help=h("Separator for multifield keys (default=%(default)s)")
                              , default=IfExists.FIELD_SEPARATOR_DEFAULT)

    KgtkReader.add_debug_arguments(parser, expert=_expert)
    KgtkReaderOptions.add_arguments(parser, mode_options=True, who="input", expert=_expert)
    KgtkReaderOptions.add_arguments(parser, mode_options=True, who="filter", expert=_expert)
    KgtkValueOptions.add_arguments(parser, expert=_expert)

def run(input_kgtk_file: typing.Optional[Path],
        filter_kgtk_file: Path,
        output_kgtk_file: typing.Optional[Path],
        input_keys: typing.Optional[typing.List[str]],
        filter_keys: typing.Optional[typing.List[str]],
        
        field_separator: str = IfExists.FIELD_SEPARATOR_DEFAULT,

        errors_to_stdout: bool = False,
        errors_to_stderr: bool = True,
        verbose: bool = False,
        very_verbose: bool = False,

        **kwargs # Whatever KgtkFileOptions and KgtkValueOptions want.
)->int:
    # import modules locally
    from kgtk.exceptions import KGTKException


    # Select where to send error messages, defaulting to stderr.
    error_file: typing.TextIO = sys.stdout if errors_to_stdout else sys.stderr

    # Build the option structures.
    input_reader_options: KgtkReaderOptions = KgtkReaderOptions.from_dict(kwargs, who="input", fallback=True)
    filter_reader_options: KgtkReaderOptions = KgtkReaderOptions.from_dict(kwargs, who="filter", fallback=True)
    value_options: KgtkValueOptions = KgtkValueOptions.from_dict(kwargs)

    try:
        ie: IfExists = IfExists(
            input_file_path=input_kgtk_file,
            input_keys=input_keys,
            filter_file_path=filter_kgtk_file,
            filter_keys=filter_keys,
            output_file_path=output_kgtk_file,
            field_separator=field_separator,
            input_reader_options=input_reader_options,
            filter_reader_options=filter_reader_options,
            value_options=value_options,
            error_file=error_file,
            verbose=verbose,
            very_verbose=very_verbose,
        )
        
        ie.process()

        return 0

    except SystemExit as e:
        raise KGTKException("Exit requested")
    except Exception as e:
        raise KGTKException(str(e))
