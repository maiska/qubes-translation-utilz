import fnmatch
import io
import re
import os
import shutil
from logging import basicConfig, getLogger, DEBUG

from frontmatter import load
from pypandoc import convert_file

from utilz import read_from
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
          with io.open(filepath, 'r', encoding='utf-8') as fp:
            md = load(fp)
            title = md.get('title')
          #if filename == "how-to-back-up-restore-and-migrate.md":
          convert_file(filepath, outputfile=rst_name, to='rst', extra_args=['--wrap=none'])#, format='md')
          #else:
          #  convert_file(filepath, outputfile=rst_name, to='rst')#, format='md')

          with io.open(rst_name, 'r+', encoding='utf-8') as fp:
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

  def convert_link_to_markdown(self, match):
    href = match.group(1)
    text = match.group(2)
    return f'[{text}]({href})'

  def convert_links_in_div(self, div_content):
    modified_div_content = re.sub(
        r'<a href="([^"]+)">([^<]+)</a>',
        self.convert_link_to_markdown,
        div_content
    )
    return modified_div_content

  def convert_html_links_to_markdown(self, md_dir: str, file_pattern="*.md"):
    for path, dirs, files in os.walk(os.path.abspath(self.directory_to_convert)):
      for filename in fnmatch.filter(files, file_pattern):
        filepath = os.path.join(path, filename)
        markdown_content = read_from(filepath)
        div_blocks = re.findall(r'(<div class="alert.*?<\/div>)', markdown_content, flags=re.DOTALL)
        modified_content = markdown_content
        for div_block in div_blocks:
          hrefs = re.findall(r'<a href="([^"]+)">([^<]+)</a>', div_block, flags=re.DOTALL)
          logger.info(hrefs)
          modified_div = self.convert_links_in_div(div_block)

          logger.info(div_block)
          logger.info(modified_div)
          if modified_div != div_block:
            logger.info("Replacing links in html blocks with markdown ones")
            modified_content = modified_content.replace(div_block, modified_div)

        if modified_content != markdown_content:
          with open(filepath, 'w', encoding='utf-8') as file:
            file.write(modified_content)

