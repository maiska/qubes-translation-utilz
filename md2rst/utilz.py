import fnmatch
import json
import os
import shutil
from enum import Enum
from logging import basicConfig, getLogger, DEBUG
import urllib.request
from urllib.error import URLError

from requests.compat import urljoin

from reportlab.graphics import renderPM
from svglib.svglib import svg2rlg

from config_constants import *
from permalinks2filepath import Permalinks2Filepath

basicConfig(level=DEBUG)
logger = getLogger(__name__)


def check_file(filename: str) -> bool:
  return os.path.exists(filename) and os.path.getsize(filename) > 0


def is_base_url_available(base_url: str) -> bool:
  try:
    status_code = urllib.request.urlopen(base_url).getcode()
  except URLError as e:
    logger.debug('Base URL error: %s', e)
    return False

  return status_code == 200


def create_rtd_url(base_url: str, doc: str) -> str:
  doc_page = doc + '.html'
  return urljoin(base_url, doc_page.lstrip('/'))


def is_not_readable(path: str) -> bool:
  return not os.access(path, os.R_OK)


def is_dict_empty(dictionary: dict) -> bool:
  return dictionary is None or len(dictionary) == 0


def dump_mappings(dict_to_dump: dict, filename: str) -> None:
  with open(filename, "w") as fp:
    fp.write(json.dumps(dict_to_dump, indent=4))


def load_mappings(filename: str) -> dict:
  with open(filename, "r") as fp:
    data = fp.read()
    data = data.encode('utf8').decode('unicode_escape')
    return json.loads(data)


def get_mappings(config_toml: dict) -> (dict, dict, dict, dict):
  permalinks2filepath = Permalinks2Filepath(config_toml[MARKDOWN][ROOT_DIRECTORY])
  md_doc_permalinks_and_redirects_to_filepath_map = \
    permalinks2filepath.get_md_permalinks_and_redirects_to_filepath_mapping()
  external_redirects_mappings = permalinks2filepath.get_external_mapppings()
  md_pages_permalinks_and_redirects_to_filepath_map = \
    permalinks2filepath.get_md_permalinks_and_redirects_to_filepath_mapping_pages()
  md_sections_id_name_map = permalinks2filepath.get_section_mapppings()

  return md_doc_permalinks_and_redirects_to_filepath_map, md_pages_permalinks_and_redirects_to_filepath_map, \
       external_redirects_mappings, md_sections_id_name_map


def convert_svg_to_png(config_toml: dict) -> None:
  root_directory = config_toml[RST][RST_DIRECTORY]
  svg_files = config_toml[SVG][SVG_FILES_TO_PNG]
  run = config_toml[RUN][SVG_PNG_CONVERSION_REPLACEMENT]
  svg_file_patterns = {}

  for path, dirs, files in os.walk(os.path.abspath(root_directory)):
    for file_pattern in svg_files:
      for filename in fnmatch.filter(files, file_pattern):
        filepath = os.path.join(path, filename)
        logger.debug('Convert image (svg->png) %s', filepath)
        png_filepath = filepath.replace('.svg', '.png')
        svg_file_patterns[file_pattern] = os.path.basename(png_filepath)
        drawing = svg2rlg(filepath)
        renderPM.drawToFile(drawing, png_filepath, fmt='PNG')

  if run:
    if len(svg_file_patterns) == 0:
      for svg in svg_files:
        png_filepath = svg.replace('.svg', '.png')
        svg_file_patterns[svg] = os.path.basename(png_filepath)

    for path, dirs, files in os.walk(os.path.abspath(root_directory)):
      for filename in fnmatch.filter(files, '*.rst'):
        filepath = os.path.join(path, filename)
        written = False
        data = read_from(filepath)
        for svg in svg_file_patterns.keys():
          if svg in data:
            logger.debug('Replacing svg image with png %s in %s', filepath, svg)
            data = data.replace(svg, svg_file_patterns[svg])
            written = True

        if written:
          write_to(data, filepath)


def write_to(data: str, filepath: str) -> None:
  with open(filepath, "w") as f:
    f.write(data)


def read_from(filepath: str) -> str:
  with open(filepath, 'r') as f:
    data = f.read()
  return data


def get_path_from(perm: str, mapping: dict) -> str:
  path = ''
  if perm in mapping.keys():
    path = mapping[perm]
  elif perm + '/' in mapping.keys():
    path = mapping[perm + '/']
  elif perm[0:len(perm) - 1] in mapping.keys():
    path = mapping[perm[0:len(perm) - 1]]
  return path


def replace_page_aux(perm_match: str, path: str) -> str:
  if '#' in perm_match:
    return QUBESOS_SITE + path + '/' + perm_match[perm_match.index('#'):len(perm_match)] if not path.startswith(
      '/') else QUBESOS_SITE[0:len(QUBESOS_SITE) - 1] + path + '/' + perm_match[
                                       perm_match.index('#'):len(perm_match)]
  else:
    return QUBESOS_SITE + path


def get_url(path: str) -> str:
  logger.debug('>>>> pages path %s ' % path)
  if path.startswith('/'):
    url = QUBESOS_SITE + path[1:len(path)] + '/'
  else:
    url = QUBESOS_SITE + path + '/'
  return url

def post_convert_index_rst(copy_from_dir: str, directory_to_convert: str) -> None:

  if os.path.exists(os.path.join(directory_to_convert, "doc.rst")):
    os.remove(os.path.join(directory_to_convert, "doc.rst"))
    shutil.copy(os.path.join(copy_from_dir, 'index.rst'), directory_to_convert)


def post_convert(copy_from_dir: str, directory_to_convert: str,
         rst_config_files: list ,
         rst_files: list ) -> None:

  for f in rst_files:
    existing_files = [os.path.join(path, name) for path, subdirs, files in
              os.walk(directory_to_convert) for name in files if name == f]
    assert len(existing_files) == 1

    shutil.copy(os.path.join(copy_from_dir, f), existing_files[0])

  for file_name in rst_config_files:
    file_to_copy = os.path.join(copy_from_dir, file_name)
    logger.info('Copying [%s] to [%s]', file_to_copy, directory_to_convert)
    shutil.copy(file_to_copy, directory_to_convert)


class Mappings(Enum):
  ALL = 1
  DOC = 2
  PAGES = 3


class CheckRSTLinks:
  def __init__(self, uri: str, md_doc_permalinks_and_redirects_to_filepath_map: dict,
         md_pages_permalinks_and_redirects_to_filepath_map: dict, external_redirects_map: dict,
         md_sections_ids_names_map: dict
         ) -> None:
    self.section = ''
    self.uri = uri
    if is_dict_empty(md_pages_permalinks_and_redirects_to_filepath_map):
      raise ValueError("md_pages_permalinks_and_redirects_to_filepath_map is not set")
    self.md_pages_permalinks_and_redirects_to_filepath_map = md_pages_permalinks_and_redirects_to_filepath_map

    if is_dict_empty(md_doc_permalinks_and_redirects_to_filepath_map):
      raise ValueError("md_doc_permalinks_and_redirects_to_filepath_map is not set")
    self.md_doc_permalinks_and_redirects_to_filepath_map = md_doc_permalinks_and_redirects_to_filepath_map

    if is_dict_empty(external_redirects_map):
      raise ValueError("external_redirects_map is not set")
    self.external_redirects_map = external_redirects_map
    if is_dict_empty(md_sections_ids_names_map):
      raise ValueError("md_sections_ids_names_map is not set")
    self.md_sections_ids_names_map = md_sections_ids_names_map

  def set_uri(self, uri: str) -> None:
    self.uri = uri

  # TODO create RSTCheckFiles and initialize it first and remove obsolete code
  def get_custom_section_name(self) -> str:
    result = self.section.replace('#', '')
    result = result.replace('-', ' ')
    if self.section in self.md_sections_ids_names_map.keys():
      name = self.md_sections_ids_names_map[self.section]
      result = name.lower()
    result = result.replace('’', '\'')
    result = result.replace('”', '"')
    result = result.replace('“', '"')
    result = result.replace('/', '\/')
    return result

  def check_cross_referencing_escape_uri(self) -> str:
    uri = self.uri
    if self.uri.startswith('/news/'):
      uri = QUBESOS_SITE + self.uri[1:len(self.uri)]
    elif self.uri in self.md_pages_permalinks_and_redirects_to_filepath_map.keys():
      uri = QUBESOS_SITE + self.uri[1:len(self.uri)] if self.uri.startswith('/') \
        else QUBESOS_SITE + self.uri[len(self.uri)]
      if len(self.section) > 0:
        uri += '#' + self.section if uri.endswith('/') else '/#' + self.section
    elif self.uri.startswith('#'):
      uri = self.uri.replace('-', ' ')
      # TODO inline section this is done in depart_reference should be here
    elif self.uri in INTERNAL_BASE_PATH:
      uri = QUBESOS_SITE
    elif self.uri in DOC_BASE_PATH:
      uri = '/index'
    elif self.uri in FEED_XML:
      uri = QUBESOS_SITE + FEED_XML[1:len(FEED_XML)]
    elif self.uri.startswith('/doc/#'):
      uri = '/index' + ':' + self.get_custom_section_name()
    elif len(self.section) > 0 and self.uri.startswith('/') and not self.uri.startswith('/attachment'):
      # sections
      perm = self.uri
      if perm in DOC_BASE_PATH:
        uri = '/' + self.uri[self.uri.index('#'):len(self.uri)]
      else:
        path = self.get_path_from_md_internal_mapping(Mappings.PAGES)
        if len(path) > 0:
          uri = replace_page_aux(self.uri, path)
        else:
          path = self.get_path_from_md_internal_mapping(Mappings.ALL)
          tmp_section = self.get_custom_section_name()
          if path.startswith('/'):
            path = path[1:len(path)]
          if len(path) > 0:
            uri = path + ':' + tmp_section
    elif '/attachment/' in self.uri and '.pdf' in self.uri and self.uri.startswith('/'):
      to_replace = self.uri[self.uri.find('/'):self.uri.rfind('/') + 1]
      uri = self.uri.replace(to_replace, '/_static/')
    elif self.uri.startswith('/'):
      path = self.get_path_from_md_internal_mapping(Mappings.PAGES)
      if len(path) > 0:
        uri = get_url(path)
      else:
        uri = self.get_path_from_md_internal_mapping(Mappings.ALL)
    elif self.uri.endswith('_'):
      logger.debug('ends with uri %s', self.uri)
      uri = self.uri[:-1] + '\\_'
    else:
      logger.debug(self.uri)
      logger.debug(" it should be an external link")
    logger.debug('For uri [%s], the rst compliant url is [%s]', self.uri, uri)
    return uri

  def get_path_from_md_internal_mapping(self, permalink_maps: Mappings = Mappings.ALL) -> str:
    path = ''
    if permalink_maps == Mappings.PAGES:
      path = get_path_from(self.uri, self.md_pages_permalinks_and_redirects_to_filepath_map)
    if permalink_maps == Mappings.DOC:
      path = get_path_from(self.uri, self.md_doc_permalinks_and_redirects_to_filepath_map)
    if permalink_maps == Mappings.ALL:
      path = get_path_from(self.uri, self.md_doc_permalinks_and_redirects_to_filepath_map)
      if len(path) == 0:
        path = get_path_from(self.uri, self.external_redirects_map)
    logger.debug('For uri [%s], path is [%s]', self.uri, path)
    return path

  def get_cross_referencing_role(self) -> str:
    role = ''
    # TODO refactor
    # news are part of the original qubes  os website
    if self.uri.startswith('/news') or self.uri in FEED_XML or QUBESOS_SITE in self.uri:
      role = ''
    elif self.uri.startswith('/') and '#' in self.uri and not self.uri.startswith('/attachment') or \
        self.uri.startswith('/') and len(self.section) > 0 and \
        self.uri in self.md_doc_permalinks_and_redirects_to_filepath_map.keys():
      role = ':ref:'
    # external documentation, pages are part of the original qubes  os website
    # and thus no internal links
    # the same for attachments
    elif self.uri.startswith('/') and \
        not self.uri.startswith('/attachment') and \
        self.uri not in self.external_redirects_map.keys() and \
        self.uri not in self.md_pages_permalinks_and_redirects_to_filepath_map.keys():
      role = ':doc:'
    logger.debug('For uri [%s], the role is [%s]', self.uri, role)
    return role

  def set_section(self, section: str) -> None:
    self.section = section
