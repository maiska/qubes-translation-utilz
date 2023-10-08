import fnmatch
import json
import os
from logging import basicConfig, getLogger, DEBUG

from reportlab.graphics import renderPM
from svglib.svglib import svg2rlg

from config_constants import URL_MAPPING, SAVE_TO_JSON, DUMP_DIRECTORY, DUMP_EXTERNAL_FILENAME, DUMP_DOCS_FILENAME, \
    DUMP_PAGES_FILENAME, MARKDOWN, ROOT_DIRECTORY, RST_DIRECTORY, SVG_FILES_TO_PNG, RST, SVG, PNG_IN_RST_FILES, \
    BASE_SITE, INTERNAL_BASE_PATH, DOC_BASE_PATH, FEED_XML
from permalinks2filepath import Permalinks2Filepath

basicConfig(level=DEBUG)
logger = getLogger(__name__)


def check_file(filename: str) -> bool:
    return os.path.exists(filename) #and os.path.getsize(filename) > 0


def is_not_readable(path):
    return not os.access(path, os.R_OK)


def is_dict_empty(dictionary):
    return dictionary is None or len(dictionary) == 0


def dump_mappings(dict_to_dump: dict, filename: str) -> None:
    with open(filename, "w") as fp:
        fp.write(json.dumps(dict_to_dump, indent=4))


def load_mappings(filename: str) -> dict:
    with open(filename, "r") as fp:
        data = fp.read()
        data = data.encode('utf8').decode('unicode_escape')
        return json.loads(data)


def get_mappings(config_toml: dict, skip_md: list) -> (dict, dict, dict):
    """

    :rtype: object
    """
    permalinks2filepath = Permalinks2Filepath(config_toml[MARKDOWN][ROOT_DIRECTORY], skip_md)
    dump_dir = config_toml[URL_MAPPING][DUMP_DIRECTORY]
    external_url_mapping_dump_filename = config_toml[URL_MAPPING][DUMP_EXTERNAL_FILENAME]
    docs_url_mapping_dump_filename = config_toml[URL_MAPPING][DUMP_DOCS_FILENAME]
    pages_url_mapping_dump_filename = config_toml[URL_MAPPING][DUMP_PAGES_FILENAME]
    if check_mappings_dump(config_toml):
        logger.debug('Reading permalink mappings from file')
        md_doc_permalinks_and_redirects_to_filepath_map = load_mappings(
            os.path.join(dump_dir, docs_url_mapping_dump_filename))
        external_redirects_mappings = load_mappings(os.path.join(dump_dir, external_url_mapping_dump_filename))
        md_pages_permalinks_and_redirects_to_filepath_map = load_mappings(
            os.path.join(dump_dir, pages_url_mapping_dump_filename))
    else:
        md_doc_permalinks_and_redirects_to_filepath_map = \
            permalinks2filepath.get_md_permalinks_and_redirects_to_filepath_mapping()
        external_redirects_mappings = permalinks2filepath.get_external_mapppings()
        md_pages_permalinks_and_redirects_to_filepath_map = \
            permalinks2filepath.get_md_permalinks_and_redirects_to_filepath_mapping_pages()

    # if needed dump them to a file if you need to reset the dir
    if config_toml[URL_MAPPING][SAVE_TO_JSON]:
        url_mapping_dump_directory = config_toml[URL_MAPPING][DUMP_DIRECTORY]
        dump_mappings(md_doc_permalinks_and_redirects_to_filepath_map, url_mapping_dump_directory +
                      docs_url_mapping_dump_filename)
        dump_mappings(external_redirects_mappings, url_mapping_dump_directory +
                      external_url_mapping_dump_filename)
        dump_mappings(md_pages_permalinks_and_redirects_to_filepath_map, url_mapping_dump_directory +
                      pages_url_mapping_dump_filename)
    return md_doc_permalinks_and_redirects_to_filepath_map, md_pages_permalinks_and_redirects_to_filepath_map, \
           external_redirects_mappings


def check_mappings_dump(config_toml: dict) -> bool:
    url_mapping_dump_directory = config_toml[URL_MAPPING][DUMP_DIRECTORY]
    return config_toml[URL_MAPPING][SAVE_TO_JSON] and \
           check_file(url_mapping_dump_directory + config_toml[URL_MAPPING][DUMP_EXTERNAL_FILENAME]) and \
           check_file(url_mapping_dump_directory + config_toml[URL_MAPPING][DUMP_DOCS_FILENAME]) and \
           check_file(url_mapping_dump_directory + config_toml[URL_MAPPING][DUMP_PAGES_FILENAME])


def convert_svg_to_png(config_toml):
    root_directory = config_toml[RST][RST_DIRECTORY]
    svg_files = config_toml[SVG][SVG_FILES_TO_PNG]
    run = config_toml[SVG][PNG_IN_RST_FILES]
    svg_filepatterns = {}

    for path, dirs, files in os.walk(os.path.abspath(root_directory)):
        for file_pattern in svg_files:
            for filename in fnmatch.filter(files, file_pattern):
                filepath = os.path.join(path, filename)
                png_filepath = filepath.replace('.svg', '.png')
                svg_filepatterns[file_pattern] = os.path.basename(png_filepath)
                drawing = svg2rlg(filepath)
                renderPM.drawToFile(drawing, png_filepath, fmt='PNG')

    if run:
        if len(svg_filepatterns) == 0:
            for svg in svg_files:
                png_filepath = svg.replace('.svg', '.png')
                svg_filepatterns[svg] = os.path.basename(png_filepath)

        for path, dirs, files in os.walk(os.path.abspath(root_directory)):
            for filename in fnmatch.filter(files, '*.rst'):
                filepath = os.path.join(path, filename)
                written = False
                data = read_from(filepath)
                for svg in svg_filepatterns.keys():
                    if svg in data:
                        data = data.replace(svg, svg_filepatterns[svg])
                        written = True

                if written:
                    write_to(data, filepath)


def write_to(data, filepath):
    with open(filepath, "w") as f:
        f.write(data)


def read_from(filepath):
    with open(filepath, 'r') as f:
        data = f.read()
    return data


class CheckRSTLinks:
    def __init__(self,
                 md_doc_permalinks_and_redirects_to_filepath_map: dict,
                 md_pages_permalinks_and_redirects_to_filepath_map: dict,
                 external_redirects_map: dict,
                 internal_labels: dict,
                 docname: str) -> None:
        self.docname = docname
        self.section = ''
        self.uri = None
        if is_dict_empty(md_pages_permalinks_and_redirects_to_filepath_map):
            raise ValueError("md_pages_permalinks_and_redirects_to_filepath_map is not set")
        self.md_pages_permalinks_and_redirects_to_filepath_map = md_pages_permalinks_and_redirects_to_filepath_map

        if is_dict_empty(md_doc_permalinks_and_redirects_to_filepath_map):
            raise ValueError("md_doc_permalinks_and_redirects_to_filepath_map is not set")
        self.md_doc_permalinks_and_redirects_to_filepath_map = md_doc_permalinks_and_redirects_to_filepath_map

        if is_dict_empty(external_redirects_map):
            raise ValueError("external_redirects_map is not set")
        self.external_redirects_map = external_redirects_map

        self.internal_labels = internal_labels

        self._translated_uri = None

    @property
    def translated_uri(self):
        if self._translated_uri is None:
            self._translated_uri = self.check_cross_referencing_escape_uri()
        return self._translated_uri

    def set_uri(self, uri):
        if '#' in uri:
            uri, section = uri.split('#', 1)
        else:
            section = ''
        self.uri = uri
        self.section = section
        self._translated_uri = None

    def check_cross_referencing_escape_uri(self) -> str:
        uri = self.uri
        if uri.startswith(BASE_SITE + 'doc'):
            uri = uri[len(BASE_SITE) - 1:]

        doc_name = self.get_path_from_md_internal_mapping(uri, 'doc').lstrip('/')
        if uri == '':
            print(f'self.docname [%s]----------------------1111111111111', self.docname)
            print(f'self.internal_labels [%s]----------------------222222222222222', self.internal_labels)
            target_labels = self.internal_labels[self.docname]
        elif doc_name in self.internal_labels:
            target_labels = self.internal_labels[doc_name]
        else:
            target_labels = {}
        internal_section = self.section.replace('#', '')
        if internal_section in target_labels:
            internal_section = target_labels[internal_section]
        elif internal_section and 'http:' not in uri:
            print(f'unknown label {internal_section} in {uri}, applying heuristic')
            if internal_section == 'how-to-guides':
                internal_section = 'how-to guides'
            elif internal_section not in (
                    'qubes-devel', 'qubes-users', 'qubes-announce', 'qubes-project', 'qubes-translation'):
                internal_section = internal_section.replace('-', ' ')

        if self.uri == '' and self.section:
            return self.docname + ':' + internal_section
        elif self.uri.startswith('/news/'):
            uri = BASE_SITE + self.uri[1:len(self.uri)]
        elif self.uri in INTERNAL_BASE_PATH:
            uri = BASE_SITE
        elif uri in DOC_BASE_PATH:
            uri = '/index'
            if internal_section:
                uri = '/index:' + internal_section
        elif self.uri in FEED_XML:
            uri = BASE_SITE + FEED_XML[1:len(FEED_XML)]
        elif doc_name:
            # sections
            # perm_match = uri
            uri = '/' + doc_name
            if internal_section:
                uri += ':' + internal_section
        elif self.uri.startswith('/attachment/'):
            uri = self.uri
        elif uri.startswith('/'):
            path = self.get_path_from_md_internal_mapping(uri, 'pages')
            if path:
                uri = get_url(path)
            else:
                uri = get_url(self.get_path_from_md_internal_mapping(uri, 'all'))
            if self.section:
                uri += '#' + self.section
            print(f'non-doc {self.uri} traslated to {uri}')
        elif self.uri.endswith('_'):
            logger.debug('ends with uri %s', self.uri)
            uri = self.uri[:-1] + '\\_'
        else:
            logger.debug(self.uri)
            logger.debug(" it should be an external link")
        return uri

    def get_path_from_md_internal_mapping(self, uri, map):
        path = ''
        if map == 'pages':
            return get_path_from(uri, self.md_pages_permalinks_and_redirects_to_filepath_map)
        if map == 'doc':
            return get_path_from(uri, self.md_doc_permalinks_and_redirects_to_filepath_map)
        if map == 'all':
            path = get_path_from(uri, self.md_doc_permalinks_and_redirects_to_filepath_map)
            if len(path) == 0:
                path = get_path_from(uri, self.external_redirects_map)
        return path

    def get_cross_referencing_role(self):
        uri = self.translated_uri
        role = ''
        if uri.startswith('/news'):
            role = ''
        elif uri == '/index':
            role = ':doc:'
        elif uri.startswith('/attachment'):
            role = ':download:'
        elif not uri.startswith('http') and ':' in uri:
            role = ':ref:'
        elif uri.startswith('/') and uri not in self.external_redirects_map.keys():
            role = ':doc:'
        elif self.uri == '' and self.section:
            role = ':ref:'
        elif BASE_SITE in uri:
            role = ''

        return role


    def set_section(self, section):
        self.section = section
        self._translated_uri = None


def get_path_from(perm, mapping):
    path = ''
    if perm in mapping.keys():
        path = mapping[perm]
    elif perm + '/' in mapping.keys():
        path = mapping[perm + '/']
    elif perm[0:len(perm) - 1] in mapping.keys():
        path = mapping[perm[0:len(perm) - 1]]
    return path


def replace_page_aux(perm_match, path):
    if '#' in perm_match:
        section = perm_match[perm_match.index('#'):]
    else:
        section = ''
    return BASE_SITE + path + '/' + section if not path.startswith(
        '/') else BASE_SITE[:-1] + path + '/' + section


def get_url(path):
    logger.debug('>>>> pages path %s ' % path)
    if path.startswith('/'):
        url = BASE_SITE + path[1:len(path)] + '/'
    else:
        url = BASE_SITE + path + '/'
    return url
