import fnmatch
import os
from logging import basicConfig, getLogger, DEBUG

from config_constants import REDIRECT_TO_KEY
from frontmatter import load, dump

from utilz import is_base_url_available, create_rtd_url

basicConfig(level=DEBUG)
logger = getLogger(__name__)


# noinspection PyDefaultArgument
class MarkdownRedirector:

    def __init__(self, root_markdown_directory: str, base_site: str,
                 excluded_files_to_redirect=['README.md', 'CONTRIBUTING.md', 'hcl.md', 'downloads.md',
                                             'visual-style-guide.md', 'website-style-guide.md',
                                             'how-to-edit-the-documentation.md',
                                             'documentation-style-guide.md']) -> None:
        if os.path.isdir(root_markdown_directory):
            self.root_markdown_directory = root_markdown_directory
        else:
            raise ValueError("Directory parameter containing the markdown documentation does not point to a directory")
        if not os.access(self.root_markdown_directory, os.R_OK):
            raise PermissionError("Directory parameter containing the markdown documentation could not be read")
        self.excluded_files_to_redirect = excluded_files_to_redirect
        # ping the site
        if is_base_url_available(base_site):
            self.base_site = base_site
        else:
            raise ValueError("There is a problem with reaching the RTD doc site " + base_site)

    def traverse_insert_redirect_delete_content(self, subdir='_doc', file_extension='*.md'):
        for path, dirs, files in os.walk(os.path.join(self.root_markdown_directory, subdir)):
            for file_name in fnmatch.filter(files, file_extension):
                file_path = os.path.join(path, file_name)
                logger.info(
                    'Inserting redirect_to base site [%s] and removing markdown content for \t%s' % (self.base_site,
                                                                                                     file_path))
                if file_name in self.excluded_files_to_redirect or 'external/' in file_name:
                    continue

                relative_path = file_path[file_path.index(subdir) + len(subdir):file_path.index(
                    file_extension[1:len(file_extension)])]

                with open(file_path) as fp:
                    md = load(fp)
                if not md.metadata:
                    continue

                redirect_to = md.get(REDIRECT_TO_KEY)
                if redirect_to is None:
                    md[REDIRECT_TO_KEY] = create_rtd_url(self.base_site, relative_path)
                md.content = ''

                with open(file_path, 'wb') as f:
                    dump(md, f)
