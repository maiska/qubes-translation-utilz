import codecs
import fnmatch
import os
import re
from logging import basicConfig, getLogger, DEBUG

import docutils.utils
from docutils.io import StringOutput
from sphinx.util import ensuredir

from config_constants import PATTERN_MD_INTERNAL_LINKS, PATTERN_MD_EXTERNAL_LINKS, PATTERN_MD_INTERNAL_LINKS_SPACEY, \
    PATTERN_MD_EXTERNAL_LINKS_SPACEY, PATTERN_MD_MAILTO_LINKS
from qubesrstwriter2 import QubesRstWriter
from utilz import check_file, is_not_readable, is_dict_empty, read_from, write_to, CheckRSTLinks

basicConfig(level=DEBUG)
logger = getLogger(__name__)


def find_and_replace_internal_mailto_md(data, internal_mailto_md, found):
    for item in internal_mailto_md:
        found = True
        url_name = item[0]
        mail = item[1]
        url_name_to_replace = '_' + url_name[1:len(url_name) - 1].replace('\n', ' ') + ':'
        if 'mailto:' in mail:
            mailto = mail[mail.index(':') + 1:len(mail)]
            logger.debug('MD MAILTO LINKS TO REPLACE: [%s] WITH: [%s]', url_name + mail,
                         url_name_to_replace + mailto)
            data = data.replace(url_name + mail, url_name_to_replace + mailto)
        else:
            return data, False
    return data, found


def find_and_replace_external_md(data, external_md_links_found, found):
    for item in external_md_links_found:
        found = True
        url_name = item[0]
        external_url_md = item[1]
        url_name_to_replace = ' `' + url_name[1:len(url_name) - 1].replace('\n', ' ')
        external_url = ' <' + external_url_md[1:len(external_url_md) - 1] + '>`__'
        logger.debug('MD LINKS TO REPLACE: [%s] WITH: [%s]', url_name + external_url_md,
                     url_name_to_replace + external_url)
        data = data.replace(url_name + external_url_md, url_name_to_replace + external_url)
    return data, found


class RSTDirectoryPostProcessor:
    def __init__(self, rst_directory: str, md_doc_permalinks_and_redirects_to_filepath_map: dict,
                 md_pages_permalinks_and_redirects_to_filepath_map: dict, external_redirects_map: dict,
                 files_to_skip: list) -> None:
        if is_not_readable(rst_directory):
            raise PermissionError("Directory could not be read")
        self.rst_directory = rst_directory
        if is_dict_empty(md_pages_permalinks_and_redirects_to_filepath_map):
            raise ValueError("md_pages_permalinks_and_redirects_to_filepath_map is not set")
        self.md_pages_permalinks_and_redirects_to_filepath_map = md_pages_permalinks_and_redirects_to_filepath_map

        if is_dict_empty(md_doc_permalinks_and_redirects_to_filepath_map):
            raise ValueError("md_doc_permalinks_and_redirects_to_filepath_map is not set")
        self.md_doc_permalinks_and_redirects_to_filepath_map = md_doc_permalinks_and_redirects_to_filepath_map

        if is_dict_empty(external_redirects_map):
            raise ValueError("external_redirects_map is not set")
        self.external_redirects_map = external_redirects_map
        if files_to_skip is None:
            self.rst_files_to_skip = []
        else:
            self.rst_files_to_skip = files_to_skip

    def search_replace_md_links(self, file_pattern: str = '*.rst') -> None:
        for path, dirs, files in os.walk(os.path.abspath(self.rst_directory)):
            for filename in fnmatch.filter(files, file_pattern):
                filepath = os.path.join(path, filename)
                data = read_from(filepath)

                logger.debug("Reading RST file %s and replacing leftover markdown links if any", filepath)
                found = False
                data, found = self.convert_leftover_markdown_links_in(data, found)

                if found:
                    write_to(data, filepath)

    def search_replace_md_links_single(self, filepath: str) -> None:
        logger.debug("Reading RST file %s and replacing leftover markdown links if any", filepath)
        data = read_from(filepath)
        found = False
        data, found = self.convert_leftover_markdown_links_in(data, found)

        if found:
            write_to(data, filepath)

    def convert_leftover_markdown_links_in(self, data, found):
        internal_md_links_found = re.findall(PATTERN_MD_INTERNAL_LINKS, data)
        if len(internal_md_links_found) > 0:
            data, found = self.find_and_replace_internal_md(data, found, internal_md_links_found)
        internal_md_links_found_spacey = re.findall(PATTERN_MD_INTERNAL_LINKS_SPACEY, data)
        if len(internal_md_links_found_spacey) > 0:
            data, found = self.find_and_replace_internal_md(data, found, internal_md_links_found_spacey)
        internal_md_mailto_links_found = re.findall(PATTERN_MD_MAILTO_LINKS, data)
        if len(internal_md_mailto_links_found) > 0:
            data, found = find_and_replace_internal_mailto_md(data, found, internal_md_mailto_links_found)
        external_md_links_found = re.findall(PATTERN_MD_EXTERNAL_LINKS, data)
        if len(external_md_links_found) > 0:
            data, found = find_and_replace_external_md(data, external_md_links_found, found)
        external_md_links_found_spacey = re.findall(PATTERN_MD_EXTERNAL_LINKS_SPACEY, data)
        if len(external_md_links_found_spacey) > 0:
            data, found = find_and_replace_external_md(data, external_md_links_found_spacey, found)
        return data, found

    def qube_links_2(self, file_pattern: str = '*.rst') -> None:
        for path, dirs, files in os.walk(os.path.abspath(self.rst_directory)):
            for filename in fnmatch.filter(files, file_pattern):
                filepath = os.path.join(path, filename)
                # TODO Maya Test
                # data = read_from(filepath)
                # if '</doc/' in data: and all the oder cases such as <# etc.
                if not os.path.basename(filepath) in self.rst_files_to_skip:
                    rst_file_postprocessor = RSTFilePostProcessor(filepath,
                                                                  self.md_doc_permalinks_and_redirects_to_filepath_map,
                                                                  self.md_pages_permalinks_and_redirects_to_filepath_map,
                                                                  # TODO
                                                                  self.external_redirects_map)
                    rst_file_postprocessor.find_and_qube_links()

    def parse_and_validate_rst(self, file_pattern: str = '*.rst') -> None:
        for path, dirs, files in os.walk(os.path.abspath(self.rst_directory)):
            for filename in fnmatch.filter(files, file_pattern):
                filepath = os.path.join(path, filename)
                validate_rst_file(filepath)

    def find_and_replace_internal_md(self, data, found, internal_md_links_found):
        for item in internal_md_links_found:
            url_name = item[0]
            external_url = item[1]
            found_string_phrase = url_name + external_url
            perm = external_url[1:len(external_url) - 1]
            filepath_map = self.md_doc_permalinks_and_redirects_to_filepath_map
            to_filepath_map = self.md_pages_permalinks_and_redirects_to_filepath_map
            redirects_map = self.external_redirects_map
            check_rst_links = CheckRSTLinks(perm, filepath_map, to_filepath_map, redirects_map)
            url = check_rst_links.check_cross_referencing_escape_uri()

            if url.startswith('http') or url.startswith('ftp'):
                url_name_to_replace = ' `' + url_name[1:len(url_name) - 1].strip().replace('`', '').replace(
                    '\n', ' ')
                url_to_replace = ' <' + url + '>`__'
            else:
                url_name_to_replace = ' :doc:`' + url_name[1:len(url_name) - 1].strip().replace('`', '').replace(
                    '\n', ' ')
                url_to_replace = ' <' + url + '>`'
            logger.debug('MARKDOWN TO REPLACE: [%s] WITH: [%s] ',
                         found_string_phrase,
                         url_name_to_replace + url_to_replace)
            data = data.replace(found_string_phrase, url_name_to_replace + url_to_replace)
            found = True
        return data, found


class RSTFilePostProcessor:
    def __init__(self, file_path: str, md_doc_permalinks_and_redirects_to_filepath_map: dict,
                 md_pages_permalinks_and_redirects_to_filepath_map: dict, external_redirects_map: dict) -> None:
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

        if is_dict_empty(external_redirects_map):
            raise ValueError("external_redirects_map is not set")
        self.external_redirects_map = external_redirects_map

    def find_and_qube_links(self) -> None:
        # TODO Maya with
        rst_document = self.get_rst_document()
        writer = QubesRstWriter(self.md_doc_permalinks_and_redirects_to_filepath_map,
                                self.md_pages_permalinks_and_redirects_to_filepath_map,
                                self.external_redirects_map)
        self.write_rst_file(rst_document, writer)

    # noinspection PyUnresolvedReferences
    def get_rst_document(self):
        logger.debug("Reading docutils document object from a RST file %s", self.file_path)
        fileobj = open(self.file_path, 'r')
        default_settings = docutils.frontend.OptionParser(
            components=(docutils.parsers.rst.Parser,)).get_default_values()
        rst_document = docutils.utils.new_document(fileobj.name, default_settings)
        qubes_parser = docutils.parsers.rst.Parser()
        qubes_parser.parse(fileobj.read(), rst_document)
        fileobj.close()
        return rst_document

    def write_rst_file(self, rst_document, writer):
        logger.debug("Writing docutils document object to a RST file %s", self.file_path)
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


# noinspection PyUnresolvedReferences
def validate_rst_file(filepath):
    logger.debug("Reading and parsing an RST file %s, check for errors below!", filepath)
    fileobj = open(filepath, 'r')
    default_settings = docutils.frontend.OptionParser(
        components=(docutils.parsers.rst.Parser,)).get_default_values()
    rst_document = docutils.utils.new_document(fileobj.name, default_settings)
    qubes_parser = docutils.parsers.rst.Parser()
    qubes_parser.parse(fileobj.read(), rst_document)
    fileobj.close()
