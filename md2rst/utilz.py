import fnmatch
import json
import os
from logging import basicConfig, getLogger, DEBUG

from reportlab.graphics import renderPM
from svglib.svglib import svg2rlg

from config_constants import URL_MAPPING, SAVE_TO_JSON, DUMP_DIRECTORY, DUMP_EXTERNAL_FILENAME, DUMP_DOCS_FILENAME, \
    DUMP_PAGES_FILENAME, MARKDOWN, ROOT_DIRECTORY, RST_DIRECTORY, SVG_FILES_TO_PNG, RST, SVG, PNG_IN_RST_FILES
from permalinks2filepath import Permalinks2Filepath

basicConfig(level=DEBUG)
logger = getLogger(__name__)


def check_file(filename: str) -> bool:
    return os.path.exists(filename) and os.path.getsize(filename) > 0


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


def get_mappings(config_toml: dict) -> (dict, dict, dict):
    """

    :rtype: object
    """
    permalinks2filepath = Permalinks2Filepath(config_toml[MARKDOWN][ROOT_DIRECTORY])
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
                with open(filepath, 'r') as f:
                    data = f.read()
                    for svg in svg_filepatterns.keys():
                        if svg in data:
                            data = data.replace(svg, svg_filepatterns[svg])
                            written = True

                if written:
                    with open(filepath, "w") as f:
                        f.write(data)