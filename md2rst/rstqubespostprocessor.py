import codecs
import fnmatch
import os
import re
from logging import basicConfig, getLogger, DEBUG

import docutils.utils
from docutils.io import StringOutput
from docutils import nodes

from typing import List
from sphinx.util import ensuredir

from config_constants import PATTERN_MD_INTERNAL_LINKS, PATTERN_MD_EXTERNAL_LINKS, PATTERN_MD_INTERNAL_LINKS_SPACEY, \
  PATTERN_MD_EXTERNAL_LINKS_SPACEY, PATTERN_MD_MAILTO_LINKS
from qubesrstwriter2 import QubesRstWriter
from utilz import check_file, is_not_readable, read_from, write_to, CheckRSTLinks

basicConfig(level=DEBUG)
logger = getLogger(__name__)


def find_and_replace_mailto_links(data, md_mailto_links_found, found):
  for item in md_mailto_links_found:
    found = True
    whole_phrase = item[0] + item[2]
    mailto_name = item[1]
    md_mailto_link = item[3]
    to_replace = '`' + mailto_name + '`_'
    logger.debug('MD MAILTO LINKS TO REPLACE: [%s] WITH: [%s]',
           whole_phrase,
           to_replace)
    data = data.replace(whole_phrase, to_replace)
    data += '\n\n' + '.. _' + mailto_name + ': ' + md_mailto_link + '\n'
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


def traverse_and_gather_section_ids_and_title(rst_document):
  result = {}
  for child in rst_document.children:
    if isinstance(child, docutils.nodes.section):
      for title in child.children:
        if isinstance(title, docutils.nodes.title):
          result[child['ids'][0]] = title.astext()
          if len(child.children) > 0:
            result.update(traverse_and_gather_section_ids_and_title(child))
          else:
            return result
    else:
      result.update(traverse_and_gather_section_ids_and_title(child))
  return result


class RSTDirectoryPostProcessor:
  def __init__(self, rst_directory: str, qubes_rst_links_checker: CheckRSTLinks, files_to_skip: list,
               advanced_warning_files = List[str]) -> None:
    self.rst_directory = rst_directory
    self.qubes_rst_links_checker = qubes_rst_links_checker
    if files_to_skip is None:
      self.rst_files_to_skip = []
    else:
      self.rst_files_to_skip = files_to_skip
    self.advanced_warning_files = advanced_warning_files

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
 
  def add_icons(self, file_patterns: list, icons: str) -> None:
    for path, dirs, files in os.walk(os.path.abspath(self.rst_directory)):
      for file_pattern in file_patterns:
        for filename in fnmatch.filter(files, file_pattern):
          if filename.endswith(file_pattern):
            filepath = os.path.join(path, filename)
            data = read_from(filepath)
            data = data + icons
            logger.debug("Reading RST file [%s] and adding icons", filepath)
            write_to(data, filepath)

  def find_hcl_pattern(self, role:str, text:str, md_uri:str)-> list[tuple[str, str, str]]:
    """
    Find the pattern in a text and return the matched strings.

    Args:
        text (str): The text to search for the pattern.

    Returns:
        list[tuple[str, str, str]]: A list of tuples containing the matched strings.
    """

    pattern = role+ r"`([^`]+?) " + md_uri
    matches = re.findall(pattern, text)

    return [(role+"`", match, md_uri) for match in matches]

  def search_replace_custom_qubes_links(self, links_to_replace: dict, file_pattern: str = '*.rst') -> None:
    for path, dirs, files in os.walk(os.path.abspath(self.rst_directory)):
      for filename in fnmatch.filter(files, file_pattern):

        filepath = os.path.join(path, filename)

        logger.debug("Reading RST file %s and replacing custom QUBES strings markdown links", filepath)

        with open(filepath, 'r', encoding='utf-8') as file:
          lines = file.readlines()
        found = False
        new_lines = []

        for to_replace, replace_with in links_to_replace.items():
          new_lines = []
          for line in lines:
            if to_replace in line:
              l = line
              if ":" in to_replace:
                role = ':ref:'
              else:
                role = ':doc:'
              matches = self.find_hcl_pattern(role, line, to_replace)

              for match in matches:
                to_r = match[0] + match[1] +" " + match[2]
                w_r = "`" + match[1] + " " + replace_with
                line = line.replace(to_r, w_r)
              found = True
              logger.debug("String to replace: [%s] with: [%s]", l, line)
            new_lines.append(line)
          lines = new_lines
        if found:
          with open(filepath, 'w', encoding='utf-8') as file:
            file.writelines(lines)

  def search_replace_custom_links(self, links_to_replace: dict, file_pattern: str = '*.rst') -> None:
    for path, dirs, files in os.walk(os.path.abspath(self.rst_directory)):
      for filename in fnmatch.filter(files, file_pattern):
        filepath = os.path.join(path, filename)
        data = read_from(filepath)
        found = False
        for to_replace, replace_with in links_to_replace.items():
          if to_replace in data or (to_replace.find('\n') and re.search(re.escape(to_replace), data, re.DOTALL)):
            data = data.replace(to_replace, replace_with)
            found = True
            logger.debug("Reading RST file %s and replacing custom strings markdown links", filepath)
            logger.debug("String to replace: [%s] with: [%s]", to_replace, replace_with)
            
        if found:
          write_to(data, filepath)


  def check_replaced_custom_links(self, links_to_replace: dict, file_pattern: str = '*.rst') -> None:
    replaced_dict = {key:False for key in links_to_replace.values()}
    for path, dirs, files in os.walk(os.path.abspath(self.rst_directory)):
      for filename in fnmatch.filter(files, file_pattern):
        filepath = os.path.join(path, filename)
        data = read_from(filepath)
        for replace_with in links_to_replace.values():
          if replace_with in data or (replace_with.find('\n') and re.search(re.escape(replace_with), data, re.DOTALL)):
            replaced_dict[replace_with] = True

    logger.debug('################################')
    logger.debug('################################')
    logger.debug('############## Replaced value NOT found in rst doc ##################')
    logger.debug([key for key, value in replaced_dict.items() if value is False])
    logger.debug('################################')
    logger.debug('################################')


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
    external_md_links_found = re.findall(PATTERN_MD_EXTERNAL_LINKS, data)
    if len(external_md_links_found) > 0:
      data, found = find_and_replace_external_md(data, external_md_links_found, found)
    external_md_links_found_spacey = re.findall(PATTERN_MD_EXTERNAL_LINKS_SPACEY, data)
    if len(external_md_links_found_spacey) > 0:
      data, found = find_and_replace_external_md(data, external_md_links_found_spacey, found)

    mailto_markdown_links_found = re.findall(PATTERN_MD_MAILTO_LINKS, data)
    if len(mailto_markdown_links_found) > 0:
      data, found = find_and_replace_mailto_links(data, mailto_markdown_links_found, found)
    return data, found

  def qube_links_2(self, file_pattern: str = '*.rst') -> None:
    for path, dirs, files in os.walk(os.path.abspath(self.rst_directory)):
      for filename in fnmatch.filter(files, file_pattern):
        filepath = os.path.join(path, filename)
        if not os.path.basename(filepath) in self.rst_files_to_skip:
          rst_file_postprocessor = RSTFilePostProcessor(filepath,
                                  self.qubes_rst_links_checker, self.rst_directory,
                                  self.advanced_warning_files)
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
      url = self.qubes_rst_links_checker.check_cross_referencing_escape_uri()

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
  def __init__(self, file_path: str, qubes_rst_links_checker, rst_directory: str, advanced_warning_files: List[str]) -> None:
    if not check_file(file_path):
      raise ValueError("Directory parameter does not point to a directory: " + file_path)
    if not check_file(rst_directory):

      raise ValueError("Directory parameter does not point to a directory: " + rst_directory)
    if is_not_readable(file_path):
      raise PermissionError("Directory could not be read")
    if not advanced_warning_files:
      raise ValueError("Advanced warning files is empty" )

    self.file_path = file_path
    self.qubes_rst_links_checker = qubes_rst_links_checker
    self.rst_directory = rst_directory
    self.advanced_warning_files = advanced_warning_files

  def find_and_qube_links(self) -> None:
    rst_document = self.get_rst_document()
    writer = QubesRstWriter(self.qubes_rst_links_checker, self.rst_directory, self.advanced_warning_files)
    self.write_rst_file(rst_document, writer)

  # noinspection PyUnresolvedReferences
  def get_rst_document(self):
    logger.debug("Reading docutils document object from a RST file %s", self.file_path)
    fileobj = open(self.file_path, 'r', encoding='utf-8')
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
      f = codecs.open(self.file_path, 'w', encoding='utf-8')
      try:
        f.write(writer.output)
      finally:
        f.close()
    except (IOError, OSError) as err:
      print("error writing file %s: %s" % (self.file_path, err))


# noinspection PyUnresolvedReferences
def validate_rst_file(filepath):
  logger.debug("Reading and parsing an RST file %s, check for errors below!", filepath)
  fileobj = open(filepath, 'r', encoding='utf-8')
  default_settings = docutils.frontend.OptionParser(
    components=(docutils.parsers.rst.Parser,)).get_default_values()
  rst_document = docutils.utils.new_document(fileobj.name, default_settings)
  qubes_parser = docutils.parsers.rst.Parser()
  qubes_parser.parse(fileobj.read(), rst_document)
  fileobj.close()
