#! /usr/bin/env python3
import codecs
import os
import shutil
import sys
from argparse import ArgumentParser
from logging import basicConfig, getLogger, DEBUG, Formatter, FileHandler

import docutils.core
import docutils.frontend
import docutils.nodes
import docutils.parsers
import docutils.parsers.rst
import docutils.utils
import pygments
import tomli
from docutils.io import StringOutput
from sphinx.util import ensuredir

from config_constants import *
from pandocconverter import PandocConverter
from qubesrstwriter import QubesRstWriter, RstBuilder
from rstqubespostprocessor import parse_and_validate_rst, qube_links_2
from utilz import get_mappings

basicConfig(level=DEBUG)
logger = getLogger(__name__)


def configure_logging(log_name: str) -> None:
    handler = FileHandler(log_name)
    handler.setLevel(DEBUG)
    formatter = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def get_configuration(configuration: str) -> dict:
    try:
        with open(configuration, mode="rb") as fp:
            config_dict = tomli.load(fp)
    except FileNotFoundError:
        print("Configuration file not found!")
        sys.exit(1)
    except PermissionError:
        print("Configuration file not readable!")
        sys.exit(1)
    return config_dict


def copy_manual_rst(config_toml: dict):
    copy_from_dir = config_toml[RST][COPY_FROM_DIR]
    rst_file_names_to_copy = config_toml[RST][RST_FILE_NAMES]
    rst_directory = config_toml[RST][RST_DIRECTORY]
    logger.info("Copy from %s directory to %s", copy_from_dir, rst_file_names_to_copy)
    for file_name in rst_file_names_to_copy:
        file_to_copy = os.path.join(copy_from_dir, file_name)
        shutil.copy(file_to_copy, os.path.join(rst_directory, os.path.dirname(file_name)))

def convert_md_to_rst(config_toml: dict) -> None:
    rst_directory = config_toml[RST][RST_DIRECTORY]
    # TODO Maya test
    copy_from_dir = config_toml[RST][COPY_FROM_DIR]
    md_file_names_to_copy = config_toml[RST][MD_FILE_NAMES]
    rst_dir_to_remove = config_toml[RST][DIRECTORY_TO_REMOVE]

    logger.info("Converting from Markdown to RST")
    rst_converter = PandocConverter(rst_directory)

    if config_toml[RUN][COPY_MD_FILES]:
        logger.info("Copy from %s directory to %s", copy_from_dir, md_file_names_to_copy)
        rst_converter.prepare_convert(copy_from_dir, md_file_names_to_copy)

    logger.info("Convert to RST")
    rst_converter.traverse_directory_and_convert()

    logger.info("Deleting Markdown files")
    rst_converter.remove_obsolete_files()

    if config_toml[RUN][REMOVE_RST_DIRECTORY]:
        logger.info("Deleting %s directory", rst_dir_to_remove)
        rst_converter.remove_whole_directory(rst_dir_to_remove)

    if config_toml[RUN][COPY_RST_FILES]:
        logger.info("Copy from %s directory", copy_from_dir)
        rst_converter.post_convert(copy_from_dir)

    if config_toml[RUN][REMOVE_HIDDEN_FILES]:
        rst_converter.remove_obsolete_files(config_toml[RST][HIDDEN_FILES_TO_REMOVE])

    logger.info("Conversion and cleaning done")


def run(config_toml: dict) -> None:
    # gather the mappings before converting
    if config_toml[RUN][MD_MAP]:
        md_doc_permalinks_and_redirects_to_filepath_map, md_pages_permalinks_and_redirects_to_filepath_map, \
        external_redirects_mappings = get_mappings(config_toml)

    logger.debug("md_doc_permalinks_and_redirects_to_filepath_map")
    logger.debug(md_doc_permalinks_and_redirects_to_filepath_map)
    logger.debug("md_pages_permalinks_and_redirects_to_filepath_map")
    logger.debug(md_pages_permalinks_and_redirects_to_filepath_map)
    logger.debug("external_redirects_mappings")
    logger.debug(external_redirects_mappings)

    if config_toml[RUN][PYPANDOC] and config_toml[RUN][MD_MAP]:
        convert_md_to_rst(config_toml)

    if config_toml[RUN][DOCUTILS_VALIDATE] and config_toml[RUN][MD_MAP]:
        parse_and_validate_rst(config_toml[RST][RST_DIRECTORY])

    if config_toml[RUN][QUBES_RST] and config_toml[RUN][MD_MAP]:
        # TODO Maya FIRST
        qube_links_2(config_toml[RST][RST_DIRECTORY], md_doc_permalinks_and_redirects_to_filepath_map,
                                md_pages_permalinks_and_redirects_to_filepath_map,
                                external_redirects_mappings)
        pass

    if config_toml[TEST][RUN]:
        run_single_rst_test(config_toml, external_redirects_mappings, md_doc_permalinks_and_redirects_to_filepath_map,
                            md_pages_permalinks_and_redirects_to_filepath_map)

    if config_toml[RUN][COPY_RST_FILES]:
        copy_manual_rst(config_toml)


def run_single_rst_test(config_toml, external_redirects_mappings, md_doc_permalinks_and_redirects_to_filepath_map,
                        md_pages_permalinks_and_redirects_to_filepath_map):
    file_name = config_toml[TEST][FILE_NAME]
    fileobj = open(file_name, 'r')
    # noinspection PyUnresolvedReferences
    default_settings = docutils.frontend.OptionParser(components=(docutils.parsers.rst.Parser,)).get_default_values()
    rst_document = docutils.utils.new_document(fileobj.name, default_settings)
    # noinspection PyUnresolvedReferences
    qubes_parser = docutils.parsers.rst.Parser()
    qubes_parser.parse(fileobj.read(), rst_document)
    fileobj.close()
    writer = QubesRstWriter(RstBuilder(), md_doc_permalinks_and_redirects_to_filepath_map,
                            md_pages_permalinks_and_redirects_to_filepath_map,
                            external_redirects_mappings)
    destination = StringOutput(encoding='utf-8')
    writer.write(rst_document, destination)
    ensuredir(os.path.dirname(file_name))
    try:
        f = codecs.open(file_name + '.test', 'w', 'utf-8')
        try:
            f.write(writer.output)
        finally:
            f.close()
    except (IOError, OSError) as err:
        print("error writing file %s: %s" % (file_name, err))


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config = get_configuration(args.config)
    configure_logging(config['log'][LOGFILE])
    logger.info("Configuration dump: %s", config)

    # "add" shell_session alias to bash lexer
    pygments.lexers._mapping.LEXERS['BashLexer'] = (
        pygments.lexers._mapping.LEXERS['BashLexer'][0],
        pygments.lexers._mapping.LEXERS['BashLexer'][1],
        pygments.lexers._mapping.LEXERS['BashLexer'][2] + ('shell_session',),
        pygments.lexers._mapping.LEXERS['BashLexer'][3],
        pygments.lexers._mapping.LEXERS['BashLexer'][4],
    )

    run(config)
