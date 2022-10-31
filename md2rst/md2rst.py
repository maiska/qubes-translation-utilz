#! /usr/bin/env python3
import codecs
import os
import sys
from argparse import ArgumentParser
from logging import basicConfig, getLogger, DEBUG, Formatter, FileHandler
import git

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

from markdownredirector import MarkdownRedirector
from config_constants import *

from pandocconverter import PandocConverter
from qubesrstwriter2 import QubesRstWriter
from rstqubespostprocessor import validate_rst_file, RSTDirectoryPostProcessor
from utilz import get_mappings, convert_svg_to_png, is_not_readable, CheckRSTLinks

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


def git_init_add_submodule(config_toml: dict) -> None:
    origin_url = config_toml[GIT][ORIGIN_URL]
    attachment_url = config_toml[GIT][ATTACHMENT_URL]
    rst_directory = config_toml[RST][RST_DIRECTORY]
    bare_repo = git.Repo.init(rst_directory)
    origin = bare_repo.create_remote('origin', origin_url)
    assert origin.exists()
    logger.info(rst_directory)
    attachment_submodule_path = os.path.join(rst_directory, 'attachment')
    logger.info(attachment_submodule_path)
    git.Submodule.add(bare_repo, 'attachment', attachment_submodule_path, attachment_url)

    bare_repo.git.add(all=True)
    bare_repo.git.commit('-S', '-m',
                         "Initialize repo, add attachment submodule, \n pandoc convert and rst cross links fixing")


def convert_md_to_rst(config_toml: dict) -> None:
    rst_directory = config_toml[RST][RST_DIRECTORY]
    copy_from_dir = config_toml[RST][COPY_FROM_DIR]
    md_file_names_to_copy = config_toml[RST][MD_FILE_NAMES]
    rst_config_files_to_copy = config_toml[RST][RST_CONFIG_FILES]
    rst_files_to_copy = config_toml[RST][RST_FILES]
    rst_dirs_to_remove = config_toml[RST][DIRECTORIES_TO_REMOVE]
    root_directory = config_toml[MARKDOWN][ROOT_DIRECTORY]

    logger.info("Converting from Markdown to RST")
    rst_converter = PandocConverter(rst_directory)

    if config_toml[RUN][COPY_MD_FILES]:
        logger.info("Copy from %s directory to %s", copy_from_dir, md_file_names_to_copy)
        rst_converter.prepare_convert(root_directory, copy_from_dir, md_file_names_to_copy)

    logger.info("Convert to RST")
    rst_converter.traverse_directory_and_convert()

    logger.info("Deleting Markdown files")
    rst_converter.remove_obsolete_files()

    if config_toml[RUN][REMOVE_RST_DIRECTORY]:
        logger.info("Deleting %s directories", rst_dirs_to_remove)
        rst_converter.remove_whole_directory(rst_dirs_to_remove)

    if config_toml[RUN][COPY_RST_FILES]:
        logger.info("Copy from %s directory to %s", copy_from_dir, rst_config_files_to_copy)
        rst_converter.post_convert(copy_from_dir, rst_config_files_to_copy, rst_files_to_copy)

    if config_toml[RUN][REMOVE_RST_FILES]:
        logger.info("Remove hidden files [%s] from converted rst doc directory ",
                    config_toml[RST][FILES_TO_REMOVE])
        rst_converter.remove_obsolete_files(config_toml[RST][FILES_TO_REMOVE])

    logger.info("Conversion and cleaning done")


def run(config_toml: dict) -> None:
    # gather the mappings before converting
    if not config_toml[RUN][MD_MAP] and not is_not_readable(config_toml[MARKDOWN][ROOT_DIRECTORY]) and not \
            config_toml[RUN][REDIRECT_MARKDOWN]:
        print("Please configure gathering of markdown url mapping")
        return

    md_doc_permalinks_and_redirects_to_filepath_map, md_pages_permalinks_and_redirects_to_filepath_map, \
    external_redirects_map, md_sections_id_name_map = get_mappings(config_toml)
    qubes_rst_links_checker = CheckRSTLinks('', md_doc_permalinks_and_redirects_to_filepath_map,
                                            md_pages_permalinks_and_redirects_to_filepath_map,
                                            external_redirects_map, md_sections_id_name_map)

    rst_directory_post_processor = RSTDirectoryPostProcessor(config_toml[RST][RST_DIRECTORY],
                                                             qubes_rst_links_checker,
                                                             config_toml[RST][SKIP_FILES])

    logger.debug("md_doc_permalinks_and_redirects_to_filepath_map")
    logger.debug(md_doc_permalinks_and_redirects_to_filepath_map)
    logger.debug("md_pages_permalinks_and_redirects_to_filepath_map")
    logger.debug(md_pages_permalinks_and_redirects_to_filepath_map)
    logger.debug("external_redirects_mappings")
    logger.debug(external_redirects_map)
    logger.debug("md_sections_id_name_map")
    logger.debug(md_sections_id_name_map)
    logger.debug(len(md_sections_id_name_map))

    if config_toml[RUN][PYPANDOC]:
        logger.debug("------------------------------------------------")
        logger.debug("------------------------------------------------")
        logger.debug("-------------------- PYPANDOC ----------------------------")
        convert_md_to_rst(config_toml)

    if config_toml[RUN][DOCUTILS_VALIDATE]:
        logger.debug("------------------------------------------------")
        logger.debug("------------------------------------------------")
        logger.debug("-------------------- DOCUTILS_VALIDATE ----------------------------")
        rst_directory_post_processor.parse_and_validate_rst()

    if config_toml[RUN][QUBES_RST]:
        logger.debug("------------------------------------------------")
        logger.debug("------------------------------------------------")
        logger.debug("-------------------- QUBES_RST ----------------------------")
        rst_directory_post_processor.qube_links_2()

    if config_toml[RUN]['git_init']:
        logger.debug("------------------------------------------------")
        logger.debug("------------------------------------------------")
        logger.debug("-------------------- GIT INIT, ADD SUBMODULE ----------------------------")
        git_init_add_submodule(config_toml)

    if config_toml[RUN][SVG_PNG_CONVERSION_REPLACEMENT]:
        logger.debug("------------------------------------------------")
        logger.debug("------------------------------------------------")
        logger.debug("-------------------- SVG_PNG_CONVERSION_REPLACEMENT ----------------------------")
        convert_svg_to_png(config_toml)

    if config_toml[RUN][HANDLE_LEFTOVER_MARKDOWN_LINKS]:
        logger.debug("-------------------- MD LINKS REPLACE TEST ----------------------------")
        rst_directory_post_processor.search_replace_md_links()

    if config_toml[RUN]['replace_custom_strings']:
        logger.debug("-------------------- MD LINKS REPLACE TEST ----------------------------")
        rst_directory_post_processor.search_replace_custom_links(config_toml['replace_custom_strings_values'])

    if config_toml[RUN][REDIRECT_MARKDOWN]:
        logger.debug("------------------------------------------------")
        logger.debug("------------------------------------------------")
        logger.debug("-------------------- REDIRECT_MARKDOWN ----------------------------")
        markdown_redirector = MarkdownRedirector(config_toml[MARKDOWN][ROOT_DIRECTORY],
                                                 config_toml[MARKDOWN]['redirect_base_url'],
                                                 config_toml[MARKDOWN]['excluded_files_from_redirect'])
        markdown_redirector.traverse_insert_redirect_delete_content()

    if config_toml[TEST][RUN]:
        logger.debug("------------------------------------------------")
        logger.debug("------------------------------------------------")
        logger.debug("-------------------- RUN TEST ----------------------------")
        file_name = config_toml[TEST][FILE_NAME]
        file_name_converted = file_name + '.test'
        rst_directory = config_toml[RST][RST_DIRECTORY]
        run_single_rst_test(file_name, external_redirects_map, md_doc_permalinks_and_redirects_to_filepath_map,
                            md_pages_permalinks_and_redirects_to_filepath_map, md_sections_id_name_map, rst_directory)
        if config_toml[TEST][DOCUTILS_VALIDATE]:
            logger.debug("-------------------- VALIDATE TEST ----------------------------")
            validate_rst_file(file_name_converted)
        if config_toml[RUN][HANDLE_LEFTOVER_MARKDOWN_LINKS]:
            logger.debug("-------------------- MD LINKS REPLACE TEST ----------------------------")
            rst_directory_post_processor.search_replace_md_links_single(file_name_converted)


def run_single_rst_test(file_name: str, external_redirects_mappings: dict,
                        md_doc_permalinks_and_redirects_to_filepath_map: dict,
                        md_pages_permalinks_and_redirects_to_filepath_map: dict, md_sections_id_name_map: dict,
                        rst_directory: str) -> None:
    fileobj = open(file_name, 'r')
    # noinspection PyUnresolvedReferences
    default_settings = docutils.frontend.OptionParser(components=(docutils.parsers.rst.Parser,)).get_default_values()
    rst_document = docutils.utils.new_document(fileobj.name, default_settings)
    # noinspection PyUnresolvedReferences
    qubes_parser = docutils.parsers.rst.Parser()
    qubes_parser.parse(fileobj.read(), rst_document)
    fileobj.close()
    qubes_rst_links_checker = CheckRSTLinks('', md_doc_permalinks_and_redirects_to_filepath_map,
                                            md_pages_permalinks_and_redirects_to_filepath_map,
                                            external_redirects_mappings, md_sections_id_name_map)
    writer = QubesRstWriter(qubes_rst_links_checker, rst_directory)

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
