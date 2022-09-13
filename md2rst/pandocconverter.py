import fnmatch
import io
import os
import shutil
from logging import basicConfig, getLogger, DEBUG

from frontmatter import load
from pypandoc import convert_file

from utilz import is_not_readable

# TODO Maya configure logging centrally
basicConfig(level=DEBUG)
logger = getLogger(__name__)


class PandocConverter:

    def __init__(self, directory):
        if os.path.isdir(directory):
            self.directory_to_convert = directory
        else:
            raise ValueError("Directory parameter does not point to a directory")
        if is_not_readable(self.directory_to_convert):
            raise PermissionError("Directory could not be read")

    def traverse_directory_and_convert(self, file_pattern='*.md'):
        for path, dirs, files in os.walk(os.path.abspath(self.directory_to_convert)):
            for filename in fnmatch.filter(files, file_pattern):
                filepath = os.path.join(path, filename)
                if filename == 'README.md' or filename == 'CONTRIBUTING.md':
                    continue
                rst_name = os.path.splitext(filepath)[0] + '.rst'
                logger.info('Converting [%s] to [%s]', filepath, rst_name)
                with io.open(filepath, 'r') as fp:
                    md = load(fp)
                    title = md.get('title')
                convert_file(filepath, outputfile=rst_name, to='rst', format='md')
                with io.open(rst_name, 'r+') as fp:
                    lines = fp.readlines()
                    fp.seek(0)
                    header = "=" * len(title)
                    fp.write(header + '\n' + title + '\n' + header + '\n')
                    for line in lines:
                        fp.write(line)

    def remove_obsolete_files(self, file_patterns=['*.md']):
        for file_pattern in file_patterns:
            for path, dirs, files in os.walk(os.path.abspath(self.directory_to_convert)):
                for filename in fnmatch.filter(files, file_pattern):
                    filepath = os.path.join(path, filename)
                    os.remove(filepath)

    def remove_whole_directory(self, path_pattern='/external/'):
        # TODO Maya test
        filepath = os.path.join(self.directory_to_convert, path_pattern)
        shutil.rmtree(filepath)

    def prepare_convert(self, copy_from_dir='/home/user/md2rst/preparation/',
                        md_file_names=['admin-api-table.md', 'admin-api.md', 'doc.md']):
        # TODO Maya test
        for file_name in md_file_names:
            for path, dirs, files in os.walk(os.path.abspath(self.directory_to_convert)):
                for filename in fnmatch.filter(files, file_name):
                    filepath = os.path.join(path, filename)
                    file_to_copy = os.path.join(copy_from_dir, file_name)
                    print(file_to_copy)
                    print(filepath)
                    shutil.copy(file_to_copy, filepath)

    def post_convert(self, copy_from_dir='/home/user/md2rst/preparation/',
                     rst_file_names=['requirements.txt', 'conf.py', '.readthedocs.yaml']):
        # TODO Maya test
        shutil.move(os.path.join(self.directory_to_convert, "doc.rst"),
                    os.path.join(self.directory_to_convert, "index.rst"))
        for file_name in rst_file_names:
            file_to_copy = os.path.join(copy_from_dir, file_name)
            shutil.copy(file_to_copy, self.directory_to_convert)
