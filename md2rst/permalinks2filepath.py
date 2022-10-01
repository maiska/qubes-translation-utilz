import fnmatch
import io
import os
from logging import basicConfig, getLogger, DEBUG

from frontmatter import load

from config_constants import PERMALINK_KEY, REDIRECT_FROM_KEY, REDIRECT_TO_KEY

basicConfig(level=DEBUG)
logger = getLogger(__name__)


class Permalinks2Filepath:

    def __init__(self, root_qubes_directory: str, skip_md: list) -> None:
        if os.path.isdir(root_qubes_directory):
            self.root_qubes_directory = root_qubes_directory
        else:
            raise ValueError("Directory parameter containing the markdown documentation does not point to a directory")
        if not os.access(self.root_qubes_directory, os.R_OK):
            raise PermissionError("Directory parameter containing the markdown documentation could not be read")
        # skip those files
        self.skip_md = skip_md
        # holds _doc mappings for official Qubes OS documenation
        self.md_permalinks_and_redirects_to_filepath_mapping = None
        # holds pages mappings for official Qubes OS documenation
        self.md_permalinks_and_redirects_to_filepath_mapping_pages = None
        # holds the external documentation redirects mapping
        self.external_mappings = None

    def traverse_md_directory_and_create_mapping(self, exclude_pattern: str = '/external',
                                                 file_patterns: list = ['*.md'],
                                                 subdir: str = '_doc') -> dict:
        self.md_permalinks_and_redirects_to_filepath_mapping = {}

        for path, dirs, files in os.walk(os.path.join(self.root_qubes_directory, subdir)):
            for file_pattern in file_patterns:
                for file_name in fnmatch.filter(files, file_pattern):
                    logger.info('\t%s' % file_name)
                    if file_name == 'README.md' or file_name == 'CONTRIBUTING.md':
                        continue
                    file_path = os.path.join(path, file_name)
                    relative_path = file_path[file_path.index(subdir) + len(subdir):file_path.index(
                        file_pattern[1:len(file_pattern)])]
                    if relative_path.lstrip('/') + '.md' in self.skip_md:
                        continue
                    if relative_path.startswith(exclude_pattern):
                        continue
                    with io.open(file_path) as fp:
                        md = load(fp)
                        if not md.metadata:
                            continue

                        perm = md.get(PERMALINK_KEY)
                        redirect_from = md.get(REDIRECT_FROM_KEY)
                        self.md_permalinks_and_redirects_to_filepath_mapping[perm] = relative_path
                        if redirect_from is not None:
                            if isinstance(redirect_from, list):
                                for rf in redirect_from:
                                    self.md_permalinks_and_redirects_to_filepath_mapping[rf] = relative_path
                            if isinstance(redirect_from, str):
                                self.md_permalinks_and_redirects_to_filepath_mapping[redirect_from] = relative_path
        return self.md_permalinks_and_redirects_to_filepath_mapping

    def collect_external_redirects(self, single_dir: str = '/external', file_patterns: list = ['*.md'],
                                   subdir: str = '_doc') -> dict:
        self.external_mappings = {}
        for path, dirs, files in os.walk(os.path.join(self.root_qubes_directory, subdir)):
            for file_pattern in file_patterns:
                for file_name in fnmatch.filter(files, file_pattern):
                    logger.info('\t%s' % file_name)
                    file_path = os.path.join(path, file_name)
                    relative_path = file_path[file_path.index(subdir) + len(subdir):file_path.index(
                        file_pattern[1:len(file_pattern)])]
                    if relative_path.lstrip('/') + '.md' in self.skip_md:
                        continue
                    if relative_path.startswith(single_dir):
                        with io.open(file_path) as fp:
                            md = load(fp)
                            if not md.metadata:
                                continue
                            perm = md.get(PERMALINK_KEY)
                            redirect_from = md.get(REDIRECT_FROM_KEY)
                            redirect_to = md.get(REDIRECT_TO_KEY)
                            self.external_mappings[perm] = redirect_to
                            if redirect_from is not None:
                                if isinstance(redirect_from, list):
                                    for rf in redirect_from:
                                        self.external_mappings[rf] = redirect_to
                                if isinstance(redirect_from, str):
                                    self.external_mappings[redirect_from] = redirect_to
        return self.external_mappings

    def get_external_mapppings(self) -> dict:
        if self.external_mappings is None:
            return self.collect_external_redirects()
        return self.external_mappings

    def get_md_permalinks_and_redirects_to_filepath_mapping(self) -> dict:
        if self.md_permalinks_and_redirects_to_filepath_mapping is None:
            self.md_permalinks_and_redirects_to_filepath_mapping = self.traverse_md_directory_and_create_mapping()
        return self.md_permalinks_and_redirects_to_filepath_mapping

    def get_md_permalinks_and_redirects_to_filepath_mapping_pages(self, file_patterns: list = ['*.md', '*.html'],
                                                                  subdir: str = 'pages') -> dict:
        if self.md_permalinks_and_redirects_to_filepath_mapping_pages is None:
            self.md_permalinks_and_redirects_to_filepath_mapping_pages = \
                self.traverse_md_directory_and_create_mapping(file_patterns=file_patterns, subdir=subdir)
        return self.md_permalinks_and_redirects_to_filepath_mapping_pages
