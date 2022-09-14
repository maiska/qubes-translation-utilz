import codecs
import fnmatch
import os
from logging import basicConfig, getLogger, DEBUG

import docutils.utils
from docutils.io import StringOutput
from sphinx.util import ensuredir

from config_constants import RST, RST_DIRECTORY
# from qubesrstwriter import QubesRstWriter, RstBuilder
from qubesrstwriter2 import QubesRstWriter, RstBuilder
from utilz import check_file, is_not_readable, is_dict_empty, get_mappings

basicConfig(level=DEBUG)
logger = getLogger(__name__)


class RSTFilePostProcessor:
    def __init__(self, file_path: str, md_doc_permalinks_and_redirects_to_filepath_map: dict,
                 md_pages_permalinks_and_redirects_to_filepath_map: dict, external_url_map: dict) -> None:
        if not check_file(file_path):
            print(file_path)
            raise ValueError("Directory parameter does not point to a directory")
        if is_not_readable(file_path):
            raise PermissionError("Directory could not be read")
        self.file_path = file_path
        if is_dict_empty(md_pages_permalinks_and_redirects_to_filepath_map):
            raise ValueError("md_pages_permalinks_and_redirects_to_filepath_map is not set")
        self.md_pages_permalinks_and_redirects_to_filepath_map = md_pages_permalinks_and_redirects_to_filepath_map

        if is_dict_empty(md_doc_permalinks_and_redirects_to_filepath_map):
            raise ValueError("md_doc_permalinks_and_redirects_to_filepath_map is not set")
        self.md_doc_permalinks_and_redirects_to_filepath_map = md_doc_permalinks_and_redirects_to_filepath_map

        if is_dict_empty(external_url_map):
            raise ValueError("external_url_map is not set")
        self.external_url_map = external_url_map

    def find_and_qube_links(self) -> None:
        # TODO Maya with
        rst_document = self.get_rst_document()
        writer = QubesRstWriter(RstBuilder(), self.md_doc_permalinks_and_redirects_to_filepath_map,
                                self.md_pages_permalinks_and_redirects_to_filepath_map,
                                self.external_url_map)
        self.write_rst_file(rst_document, writer)

    def get_rst_document(self):
        fileobj = open(self.file_path, 'r')
        default_settings = docutils.frontend.OptionParser(
            components=(docutils.parsers.rst.Parser,)).get_default_values()
        rst_document = docutils.utils.new_document(fileobj.name, default_settings)
        qubes_parser = docutils.parsers.rst.Parser()
        qubes_parser.parse(fileobj.read(), rst_document)
        fileobj.close()
        return rst_document

    def write_rst_file(self, rst_document, writer):
        destination = StringOutput(encoding='utf-8')
        writer.write(rst_document, destination)
        ensuredir(os.path.dirname(self.file_path))
        try:
            f = codecs.open(self.file_path, 'w', 'utf-8')
            try:
                f.write(writer.output)
            finally:
                f.close()
        except (IOError, OSError) as err:
            print("error writing file %s: %s" % (self.file_path, err))


def qube_links_2(rst_directory: str, md_doc_permalinks_and_redirects_to_filepath_map: dict,
                 md_pages_permalinks_and_redirects_to_filepath_map: dict,
                 external_url_map: dict, file_pattern: str = '*.rst') -> None:
    for path, dirs, files in os.walk(os.path.abspath(rst_directory)):
        for filename in fnmatch.filter(files, file_pattern):
            filepath = os.path.join(path, filename)
            rstfilepostprocesr = RSTFilePostProcessor(filepath, md_doc_permalinks_and_redirects_to_filepath_map,
                                                      md_pages_permalinks_and_redirects_to_filepath_map,
                                                      external_url_map)
            rstfilepostprocesr.find_and_qube_links()


def qube_links(config_toml: dict, file_pattern: str = '*.rst') -> None:
    md_doc_permalinks_and_redirects_to_filepath_map, md_pages_permalinks_and_redirects_to_filepath_map, \
    external_url_map = get_mappings(config_toml)
    rst_directory = config_toml[RST][RST_DIRECTORY]
    for path, dirs, files in os.walk(os.path.abspath(rst_directory)):
        for filename in fnmatch.filter(files, file_pattern):
            filepath = os.path.join(path, filename)
            rstfilepostprocesr = RSTFilePostProcessor(filepath, md_doc_permalinks_and_redirects_to_filepath_map,
                                                      md_pages_permalinks_and_redirects_to_filepath_map,
                                                      external_url_map)
            rstfilepostprocesr.find_and_qube_links()


def parse_and_validate_rst(rst_directory: str, file_pattern: str = '*.rst') -> None:
    for path, dirs, files in os.walk(os.path.abspath(rst_directory)):
        for filename in fnmatch.filter(files, file_pattern):
            filepath = os.path.join(path, filename)
            validate_rst_file(filepath)


def validate_rst_file(filepath):
    fileobj = open(filepath, 'r')
    default_settings = docutils.frontend.OptionParser(
        components=(docutils.parsers.rst.Parser,)).get_default_values()
    rst_document = docutils.utils.new_document(fileobj.name, default_settings)
    qubes_parser = docutils.parsers.rst.Parser()
    qubes_parser.parse(fileobj.read(), rst_document)
    fileobj.close()
