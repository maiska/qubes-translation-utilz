import fnmatch
import io
import os
import shutil
from logging import basicConfig, getLogger, DEBUG

from frontmatter import load
from pypandoc import convert_file

from distutils.dir_util import copy_tree

basicConfig(level=DEBUG)
logger = getLogger(__name__)


# noinspection PyDefaultArgument
class PandocConverter:

    def __init__(self, directory: str) -> None:
        self.directory_to_convert = directory

    def traverse_directory_and_convert(self, file_pattern: str = '*.md') -> None:
        for path, dirs, files in os.walk(os.path.abspath(self.directory_to_convert)):
            for filename in fnmatch.filter(files, file_pattern):
                filepath = os.path.join(path, filename)
                if filename == 'README.md' or filename == 'CONTRIBUTING.md' or filename == 'COPYRIGHT.md':
                    logger.warning('Not converting file [%s]', filename)
                else:
                    # continue
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

    def remove_obsolete_files(self, file_patterns: list = ['*.md']) -> None:
        for file_pattern in file_patterns:
            for path, dirs, files in os.walk(os.path.abspath(self.directory_to_convert)):
                for filename in fnmatch.filter(files, file_pattern):
                    filepath = os.path.join(path, filename)
                    logger.info('Removing file [%s]', filepath)
                    os.remove(filepath)

    def remove_whole_directory(self, path_patterns: list = ['/external/']) -> None:
        for path_pattern in path_patterns:
            filepath = os.path.join(self.directory_to_convert, path_pattern)
            logger.info('Removing directory [%s]', filepath)
            if os.path.exists(filepath):
                shutil.rmtree(filepath)

    def prepare_convert(self, md_dir: str, copy_from_dir: str = '/home/user/md2rst/preparation/',
                        md_file_names: list = ['admin-api.md', 'doc.md']) -> None:
        if os.path.exists(self.directory_to_convert):
            shutil.rmtree(self.directory_to_convert)
        logger.info(md_dir)
        logger.info(os.path.join(md_dir, '_doc'))
        copy_tree(os.path.join(md_dir, '_doc'), self.directory_to_convert)
        logger.info('copied original markdown directory')

        for file_name in md_file_names:
            for path, dirs, files in os.walk(os.path.abspath(self.directory_to_convert)):
                for filename in fnmatch.filter(files, file_name):
                    filepath = os.path.join(path, filename)
                    file_to_copy = os.path.join(copy_from_dir, file_name)
                    logger.info('Copying [%s] to [%s]', file_to_copy, filepath)
                    shutil.copy(file_to_copy, filepath)

    def post_convert(self, copy_from_dir: str = '/home/user/md2rst/preparation/',
                     rst_config_files: list = ['requirements.txt', 'conf.py', '.readthedocs.yaml'],
                     rst_files: list = ['intro.rst']) -> None:

        if os.path.exists(os.path.join(self.directory_to_convert, "doc.rst")):
            shutil.move(os.path.join(self.directory_to_convert, "doc.rst"),
                        os.path.join(self.directory_to_convert, "index.rst"))

        for f in rst_files:
            existing_files = [os.path.join(path, name) for path, subdirs, files in
                              os.walk(self.directory_to_convert) for name in files if name == f]
            assert len(existing_files) == 1
            shutil.copy(os.path.join(copy_from_dir, f), existing_files[0])

        for file_name in rst_config_files:
            file_to_copy = os.path.join(copy_from_dir, file_name)
            logger.info('Copying [%s] to [%s]', file_to_copy, self.directory_to_convert)
            shutil.copy(file_to_copy, self.directory_to_convert)
