# based on https://github.com/sphinx-contrib/restbuilder
from __future__ import absolute_import
import re
import os
from logging import basicConfig, getLogger, DEBUG

import docutils
from docutils import nodes, writers
from docutils.nodes import Node

from config_constants import PATTERN_STRIKEOUT_1, PATTERN_STRIKEOUT_2

from typing import List

PUNCTUATION_SET = {'!', ',', '.', ':', ';', '?', '__'}
ADVANCED_WARNING = ".. warning::" + "\n\n      " + 'This page is intended for advanced users.'

basicConfig(level=DEBUG)
logger_qubes_rst = getLogger(__name__)
from sphinx.writers.text import STDINDENT

from utilz import CheckRSTLinks

from docutils_rst_writer.writer import RstTranslator


basicConfig(level=DEBUG)
logger = getLogger(__name__)


class QubesRstWriter(writers.Writer):
  supported = ('text',)
  settings_spec = ('No options here.', '', ())
  settings_defaults = {}

  output = None

  def __init__(self, qubes_rst_links_checker: CheckRSTLinks, rst_directory: str, advanced_warning_files: List[str]) -> None:
    writers.Writer.__init__(self)
    self.qubes_rst_links_checker = qubes_rst_links_checker
    self.rst_directory = rst_directory
    self.advanced_warning_files = advanced_warning_files

  def translate(self) -> None:
    visitor = QubesRstTranslator(self.document, self.qubes_rst_links_checker, self.rst_directory, self.advanced_warning_files)
    self.document.walkabout(visitor)
    self.output = visitor.body


SPACE = ' '
CODE_BLOCK_IDENT = SPACE * STDINDENT * 2
LIST_ITEM_IDENT = SPACE * STDINDENT


def is_python_code_block(code_as_string: str) -> str:
  return ' class ' in code_as_string or ' self.' in code_as_string or \
       ' for modname in' in code_as_string or re.findall(' def.*.\):',
                               code_as_string) or ' import ' in code_as_string


def is_shell_session_original_code_block(node: Node) -> bool:
  return node.hasattr('classes') and len(node['classes']) == 2 and node['classes'][0] == 'code' and \
       (node['classes'][1] == 'shell_session' or node['classes'][1] == 'bash_session')


def is_html_original_code_block(node: Node) -> bool:
  return node.hasattr('classes') and len(node['classes']) == 2 and node['classes'][0] == 'code' and \
       node['classes'][1] == 'html'


def is_python_original_code_block(node: Node) -> bool:
  return node.hasattr('classes') and len(node['classes']) == 2 and node['classes'][0] == 'code' and \
       node['classes'][1] == 'python'


def is_video_tours_original_code_block(node: Node) -> bool:
  return node.hasattr('classes') and len(node['classes']) == 2 and node['classes'][0] == 'container' and \
       node['classes'][1] == 'video'


def is_lua_original_code_block(node: Node) -> bool:
  return node.hasattr('classes') and len(node['classes']) == 2 and node['classes'][0] == 'code' and \
       node['classes'][1] == 'lua'


def is_c_original_code_block(node: Node) -> bool:
  return node.hasattr('classes') and len(node['classes']) == 2 and node['classes'][0] == 'code' and \
       node['classes'][1] == 'c'


def is_bash_original_code_block(node: Node) -> bool:
  return node.hasattr('classes') and len(node['classes']) == 2 and node['classes'][0] == 'code' and \
       (node['classes'][1] == 'bash' or node['classes'][1] == 'shell' or node['classes'][1] == 'sh')

def get_basename(filename: str):
  return os.path.basename(filename)

def is_c_code_block(code_as_string: str) -> bool:
  return ' while(' in code_as_string or ' for(' in code_as_string or \
       ' while (' in code_as_string or ' for (' in code_as_string or \
       ' #if ' in code_as_string or ' #endif ' in code_as_string or \
       ' int ' in code_as_string or ' struct ' in code_as_string or \
       ' #include <' in code_as_string or '.h>' in code_as_string or \
       ' int main(int argc, char* argv[])' in code_as_string or \
       ' uint32_t ' in code_as_string


def is_file_with_c_code_blocks(filename: str) -> bool:
  return 'coding-style' in filename


def is_node_a_code_block(node: Node) -> bool:
  return (isinstance(node, docutils.nodes.literal_block) and node.hasattr('language')) or \
       (node.hasattr('classes') and 'code' in node['classes']) or \
       (node.hasattr('xml:space') and node['xml:space'] == 'preserve')


# noinspection PyPep8Naming,PyMethodMayBeStatic
def is_code_block_to_convert_to_bash(node_as_text: str) -> bool:
  return "shell_session" in node_as_text or "bash_session" in node_as_text or '[user@dom0 ~]$' in node_as_text


# noinspection PyMethodMayBeStatic,PyPep8Naming,PyRedeclaration,PyUnusedLocal
def is_node_inside_emphasis_strong_literal(parent: Node) -> bool:
  return True if isinstance(parent, docutils.nodes.emphasis) or \
           isinstance(parent, docutils.nodes.strong) or \
           isinstance(parent, docutils.nodes.literal) else False


def get_title_text_length(child: Node) -> int:
  length = len(child.astext())
  if isinstance(child, docutils.nodes.literal) or isinstance(child, docutils.nodes.strong):
    length += 4
  if isinstance(child, docutils.nodes.emphasis):
    length += 2
  return length


class QubesRstTranslator(RstTranslator):

  def __init__(self, document: docutils.nodes.document, qubes_rst_links_checker: CheckRSTLinks,
         rst_directory: str, advanced_warning_files = List[str]) -> None:
    super().__init__(document)
    self.qubes_rst_links_checker = qubes_rst_links_checker
    self.rst_directory = rst_directory
    self.docname = self.get_self_docname()
    self.body = ""
    self.document = document
    self.title_count = 0
    self.enumerated_count = 0
    self.enumerated_lists_count = 0
    self.ident_count = 0
    self.video_container_summit_count = 0
    self.indentation = STDINDENT
    self.advanced_warning_files = advanced_warning_files

  def get_self_docname(self) -> str:

    source = self.document['source']
    return source.replace(self.rst_directory + '/', '').replace('.rst', '') \
      if source.startswith(self.rst_directory + '/') and source.endswith('.rst') \
      else None

  def visit_document(self, node: Node) -> None:
    pass

  def depart_document(self, node: Node) -> None:
    super().depart_document(node)
    self.body += '\n'.join(self.lines)

  def visit_comment(self, node: Node) -> None:
    pass

  def depart_comment(self, node: Node) -> None:
    pass

  def visit_raw(self, node: Node) -> None:
    pass

  def depart_raw(self, node: Node) -> None:
    pass

  def visit_container(self, node: Node) -> None:
    source = self.document['source']

    if node.hasattr('classes') and node['classes'][0] == 'focus' and \
        isinstance(node.children[0], docutils.nodes.paragraph):
      self.write(self.nl + '.. important::' + self.nl + CODE_BLOCK_IDENT)

    if node.hasattr('classes') and len(node['classes']) == 2 and \
        node['classes'][0] == 'alert' and \
        node['classes'][1] == 'alert-warning' and \
        isinstance(node.children[0], docutils.nodes.paragraph):
      self.write(self.nl + '.. warning::' + self.nl + CODE_BLOCK_IDENT)
    if node.hasattr('classes') and len(node['classes']) == 2 and \
        node['classes'][0] == 'alert' and \
        node['classes'][1] == 'alert-danger' and \
        isinstance(node.children[0], docutils.nodes.paragraph):
      self.write(self.nl + '.. DANGER::' + self.nl + CODE_BLOCK_IDENT)
    if node.hasattr('classes') and len(node['classes']) == 2 and \
        node['classes'][0] == 'alert' and \
        (node['classes'][1] == 'alert-success' or node['classes'][1] == 'alert-info') and \
        isinstance(node.children[0], docutils.nodes.paragraph):
      self.write(self.nl + '.. note::' + self.nl + CODE_BLOCK_IDENT)

  def depart_container(self, node: Node) -> None:
    pass

  def visit_system_message(self, node: Node) -> None:


    if isinstance(node.parent, docutils.nodes.section):
      pass

    logger_qubes_rst.info("=====================================================================")
    logger_qubes_rst.info("===================== SYSTEM MESSAGE: ===============================")
    node_as_text = node.astext()
    logger_qubes_rst.info("%s", node_as_text)
    logger_qubes_rst.info("______")
    parent = node.parent
    for child in parent.children:
      logger_qubes_rst.info("------------------------------------------------------------------")
      logger_qubes_rst.info("Child: %s", child)
    logger_qubes_rst.info("=====================================================================")
    if len([i for i in [
      'Cannot analyze code. No Pygments lexer found for "shell_session".',
      'Cannot analyze code. No Pygments lexer found for "bash_session".',
      'Enumerated list start value not ordinal',
      'Duplicate implicit target name',
      'Error in "figure" directive:',
      'Content block expected for the "container" directive; none found.',
      'Possible title underline, too short for the title',
      'Treating it as ordinary text because it',
      'Inline emphasis start-string without end-string.'
    ] if i in node.astext()]) > 0:
      return
    self.write('SYSTEM MESSAGE  for: ' + node_as_text)

  def depart_system_message(self, node: Node) -> None:
    node_as_text = node.astext()
    if len([i for i in [
      'Cannot analyze code. No Pygments lexer found for "shell_session".',
      'Cannot analyze code. No Pygments lexer found for "bash_session".',
      'Enumerated list start value not ordinal',
      'Duplicate implicit target name:',
      'Error in "figure" directive:',
      'Content block expected for the "container" directive; none found.',
      'Possible title underline, too short for the title.',
      'Treating it as ordinary text because it',
      'Inline emphasis start-string without end-string.'
    ] if i in node_as_text]) > 0:
      return

  def get_custom_videotours_directive(self, directive_name: str, vidid: str) -> str:
    spacing = self.nl + SPACE * len(directive_name)
    return '----' + self.nl + self.nl + self.nl + directive_name + vidid + spacing + \
         ':height: 315' + spacing + \
         ':width: 560' + spacing + \
         ':align: left' + self.nl

  # TODO refactor...
  def visit_literal_block(self, node: Node) -> None:
    node_as_text = node.astext()
    if node_as_text.lstrip().rstrip().startswith('.. figure::'):
      self.write(self.nl + node_as_text)
      raise nodes.SkipNode
    if node_as_text.lstrip().rstrip() == '.. container:: center-block more-bottom' and \
        self.document['source'].endswith('statistics.rst'):
      self.write(self.nl + '.. figure:: ')
      self.write('https://tools.qubes-os.org/counter/stats.png' + self.nl + LIST_ITEM_IDENT)
      self.write(':alt: ' + 'Estimated Qubes OS userbase graph' + self.nl)
      raise nodes.SkipNode
    if node_as_text.lstrip().rstrip() == '.. container:: video more-bottom' and \
        self.document['source'].endswith('video-tours.rst') and \
        isinstance(node.parent, docutils.nodes.system_message) and \
        isinstance(node.parent.parent, docutils.nodes.section) and \
        'Qubes OS Summit 2022' in node.parent.parent.astext():
      youtube_directive = '.. youtube:: '
      if self.video_container_summit_count == 0:
        self.write(self.get_custom_videotours_directive(youtube_directive, 'hkWWz3xGqS8'))
        self.write(self.get_custom_videotours_directive(youtube_directive, 'A9GrlQsQc7Q'))
        self.write(self.get_custom_videotours_directive(youtube_directive, 'gnWHjv-9_YM'))
        self.video_container_summit_count += 1
      raise nodes.SkipNode
    if node_as_text.lstrip().rstrip() == '.. container:: video more-bottom' and \
        self.document['source'].endswith('video-tours.rst') and \
        isinstance(node.parent, docutils.nodes.system_message) and \
        isinstance(node.parent.parent, docutils.nodes.section) and \
        'Micah Lee' in node.parent.parent.astext():
      generalvid_directive = '.. generalvid:: '
      self.write(self.get_custom_videotours_directive(generalvid_directive,
                              'https://livestream.com/accounts/9197973/events/8286152/videos/178431606/player?autoPlay=false'))
      raise nodes.SkipNode
    if node_as_text.lstrip().rstrip() == '.. container:: video' and \
        self.document['source'].endswith('video-tours.rst') and \
        isinstance(node.parent, docutils.nodes.system_message) and \
        isinstance(node.parent.parent, docutils.nodes.section) and \
        'Explaining Computers' in node.parent.parent.astext():
      youtube_directive = '.. youtube:: '
      self.write(self.get_custom_videotours_directive(youtube_directive, 'hWDvS_Mp6gc'))
      raise nodes.SkipNode
    if is_bash_original_code_block(node) or is_shell_session_original_code_block(node):
      self.ident_coding_block_for(node, 'bash')
      raise nodes.SkipNode
    if is_python_original_code_block(node):
      self.ident_coding_block_for(node, 'python')
      raise nodes.SkipNode
    if is_lua_original_code_block(node):
      self.ident_coding_block_for(node, 'lua')
      raise nodes.SkipNode
    if is_c_original_code_block(node):
      self.ident_coding_block_for(node, 'c')
      raise nodes.SkipNode
    if is_html_original_code_block(node):
      self.ident_coding_block_for(node, 'html')
      raise nodes.SkipNode

    if node.hasattr('xml:space'):
      node_as_text = node_as_text
      if is_python_code_block(node_as_text):
        node['language'] = 'python'
        self.ident_coding_block_for(node, 'python')
        raise nodes.SkipNode
      elif is_c_code_block(node_as_text) or is_file_with_c_code_blocks(self.document['source']):
        node['language'] = 'c'
        self.write(self.nl + '.. code:: c' + self.nl + self.nl)
      elif node.hasattr('language') and node['language'] == 'bash':
        pass
      elif is_code_block_to_convert_to_bash(node_as_text):
        for i in ['shell_session', 'bash_session', '.. code::']:
          node_as_text = node_as_text.replace(i, '').lstrip()
        self.write(self.nl + '.. code:: bash' + self.nl + self.nl)
        get_code_text_block = self.get_code_text_block(node_as_text)
        self.write(CODE_BLOCK_IDENT + get_code_text_block + self.nl)
        raise nodes.SkipNode
      elif not node.hasattr('language') or node['language'] in ["shell_session", "bash_session"]:
        node['language'] = 'bash'
        self.write(self.nl + '.. code:: bash' + self.nl + self.nl)
      else:
        self.write(self.nl + '.. code:: ' + node['language'] + self.nl + self.nl)

  def ident_coding_block_for(self, node: Node, language: str) -> None:
    self.write(self.nl + '.. code:: ' + language + self.nl + self.nl + CODE_BLOCK_IDENT)
    get_code_text_block = self.get_code_text_block(node.astext())
    self.write(get_code_text_block + self.nl)

  def depart_literal_block(self, node: Node) -> None:
    self.write(self.nl + self.nl)

  def visit_substitution_definition(self, node: Node) -> None:
    assert len(node.children) > 0
    first_child = node.children[0]
    if isinstance(first_child, docutils.nodes.reference):
      assert len(first_child.children) > 0
      image = first_child.children[0]
      assert isinstance(image, docutils.nodes.image)

      self.write(self.nl + '.. |' + node['names'][0] + '| image:: ' + image['uri'] + \
             self.nl + LIST_ITEM_IDENT + \
             ('' if first_child['refuri'].startswith('/attachment') else ':target: ' + first_child['refuri']) + self.nl)
      raise nodes.SkipNode
    if isinstance(first_child, docutils.nodes.image):
      self.write(self.nl + '.. |' + node['names'][0] + '| image:: ' + first_child['uri'] + \
             self.nl)
      raise nodes.SkipNode

  def depart_substitution_definition(self, node: Node) -> None:
    raise nodes.SkipNode

  def visit_target(self, node: Node) -> None:
    self.write(self.nl)
    super().visit_target(node)

  def visit_title(self, node: Node) -> None:
    if self.title_count == 0:
      length = 0
      for child in node.children:
        length += get_title_text_length(child)
      self.write('=' * length + self.nl)
    else:
      self.write(self.nl)

  def depart_title(self, node: Node) -> None:
    parent = node.parent
    length = 0
    for child in node.children:
      length += get_title_text_length(child)

    # section title
    if self.title_count >= 0 and isinstance(parent, docutils.nodes.section) and not (
        isinstance(parent.parent, docutils.nodes.section)):
      self.write(self.nl + '=' * length + self.nl + self.nl)
      # only with title
      if self.title_count == 0 and get_basename(self.document['source']) in self.advanced_warning_files:
        self.write(ADVANCED_WARNING + self.nl)
    # subsubsection title
    elif self.title_count >= 0 and isinstance(parent, docutils.nodes.section) and \
        isinstance(parent.parent, docutils.nodes.section) and \
        isinstance(parent.parent.parent, docutils.nodes.section):
      self.write(self.nl + '^' * length + self.nl + self.nl)
    # subsection title
    elif self.title_count >= 0 and isinstance(parent, docutils.nodes.section) and \
        isinstance(parent.parent, docutils.nodes.section):
      self.write(self.nl + '-' * length + self.nl + self.nl)
    else:
      pass
    self.title_count += 1

  def visit_strong(self, node):
    parent = node.parent
    if isinstance(parent, docutils.nodes.paragraph) and \
        isinstance(parent.parent, docutils.nodes.container):
      self.write(CODE_BLOCK_IDENT)

    super().visit_strong(node)

  def visit_Text(self, node: Node) -> None:
    parent = node.parent

    if len([i for i in [
      'Cannot analyze code. No Pygments lexer found for "shell_session".',
      'Cannot analyze code. No Pygments lexer found for "bash_session".',
      'Enumerated list start value not ordinal',
      'Inline emphasis start-string without end-string.',
      'Duplicate implicit target name:',
      'Content block expected for the "container" directive; none found.',
      'Error in "figure" directive:',
      'Treating it as ordinary text because it',
      'Possible title underline, too short for the title.',
    ] if i in node.astext()]) > 0:
      pass
    elif is_node_a_code_block(parent):
      self.write(CODE_BLOCK_IDENT)
    elif isinstance(parent, docutils.nodes.reference):
      self.write(node.astext().replace(self.nl, ' '))
      raise nodes.SkipNode

    elif isinstance(parent, docutils.nodes.paragraph) and \
        isinstance(parent.parent, docutils.nodes.container):
      self.write(CODE_BLOCK_IDENT)
      self.write(node.astext().replace(self.nl, ' '))
      raise nodes.SkipNode
    elif isinstance(parent, docutils.nodes.paragraph) and \
        isinstance(parent.parent, docutils.nodes.entry) and \
        isinstance(parent.parent.parent, docutils.nodes.row):
      # table is handled in entry element
      pass

  def depart_Text(self, node: Node) -> None:
    parent = node.parent
    node_as_text = node.astext()
    if is_node_inside_emphasis_strong_literal(parent):
      self.write(node_as_text.replace(self.nl, ' '))
    elif isinstance(parent, docutils.nodes.title):
      self.write(node.astext().replace('’', '\'').replace('”', '"').replace('“', '"'))
    elif is_node_a_code_block(parent):
      code_as_indented_text = self.get_code_text_block(node_as_text)
      self.write(code_as_indented_text)
    elif isinstance(parent, docutils.nodes.caption):
      pass
    elif isinstance(parent, docutils.nodes.paragraph) and \
        isinstance(parent.parent, docutils.nodes.entry) and \
        isinstance(parent.parent.parent, docutils.nodes.row):
      # table is handled in the entry element
      pass
    elif node_as_text.lstrip() == '{% raw %}' or node_as_text.lstrip() == '{% endraw %}':
      self.write('')
    elif len([i for i in [
      'Cannot analyze code. No Pygments lexer found for "shell_session".',
      'Cannot analyze code. No Pygments lexer found for "bash_session".',
      'Enumerated list start value not ordinal',
      'Inline emphasis start-string without end-string.',
      'Duplicate implicit target name:',
      'Error in "figure" directive:',
      'Content block expected for the "container" directive; none found.',
      'Possible title underline, too short for the title.',
      'Treating it as ordinary text because',
    ] if i in node.astext()]) > 0:
      pass
    elif isinstance(node.parent, docutils.nodes.substitution_reference):
      self.write(node_as_text)
    else:
      strikeout1 = re.findall(PATTERN_STRIKEOUT_1, node_as_text)
      if len(strikeout1) > 0:
        for item in strikeout1:
          to_replace = item[0]
          replacing = to_replace.replace('~[STRIKEOUT:', ' ``')
          replacing = replacing.replace(']~', '`` ')
          node_as_text = node_as_text.replace(to_replace, replacing)
        self.write(node_as_text)
        return
      strikeout2 = re.findall(PATTERN_STRIKEOUT_2, node_as_text)
      if len(strikeout2) > 0:
        for item in strikeout2:
          to_replace = item[0]
          replacing = to_replace.replace('[STRIKEOUT:', ' :strike:`')
          replacing = replacing.replace(']', '` ')
          node_as_text = node_as_text.replace(to_replace, replacing)
        self.write(node_as_text)
        return
      self.write(node_as_text)


  def get_code_text_block(self, node_as_string: str) -> str:

    x = node_as_string.splitlines()
    ident = self.nl + CODE_BLOCK_IDENT
    return ident.join(x) + self.nl

  def get_list_item_ident(self, node_as_string: str, level: int = 1) -> str:
    x = node_as_string.splitlines()
    ident = self.nl + LIST_ITEM_IDENT * level
    return ident.join(x)

  def visit_enumerated_list(self, node: Node) -> None:
    self.write(self.nl)
    super().visit_enumerated_list(node)

  def depart_enumerated_list(self, node: Node) -> None:
    super().depart_enumerated_list(node)


  def visit_bullet_list(self, node: Node) -> None:
    if self.document["source"].endswith('index.rst') or \
        self.document["source"].endswith('releases/notes.rst') or \
        self.document["source"].endswith('releases/schedules.rst') or \
        self.document["source"].endswith('downloading-installing-upgrading/upgrade/upgrade.rst') or \
        (self.document["source"].endswith('how-to-back-up-restore-and-migrate.rst') and
         (
             'Qubes R4 or newer' in node.astext() or
             'Qubes R3' in node.astext() or
             'Qubes R2 or older' in node.astext()
         )
        ):
      toctree_directive = self.nl + '.. toctree::' + self.nl + LIST_ITEM_IDENT + ':maxdepth: 1' + self.nl
      self.write(toctree_directive)
    self.write(self.nl)
    super().visit_bullet_list(node)

  def depart_bullet_list(self, node: Node) -> None:
    super().depart_bullet_list(node)

  def visit_list_item(self, node: Node) -> None:
    parent = node.parent
    if isinstance(parent, docutils.nodes.bullet_list) and \
        (self.document["source"].endswith('index.rst') or
         self.document["source"].endswith('releases/notes.rst') or
         self.document["source"].endswith('releases/schedules.rst') or
         self.document["source"].endswith('downloading-installing-upgrading/upgrade/upgrade.rst') or
         (self.document["source"].endswith('how-to-back-up-restore-and-migrate.rst') and
          (
              'Qubes R4 or newer' in node.astext() or
              'Qubes R3' in node.astext() or
              'Qubes R2 or older' in node.astext()
          )
         )):
      self.write(LIST_ITEM_IDENT)
      return
    super().visit_list_item(node)

  # noinspection PyMethodMayBeStatic
  def depart_list_item(self, node: Node) -> None:
    super().depart_list_item(node)

  def visit_table(self, node: Node) -> None:
    self.write(self.nl + '.. list-table:: ' + self.nl + LIST_ITEM_IDENT)
    tgroup_child = node.children[0]
    if isinstance(tgroup_child, docutils.nodes.tgroup) and tgroup_child.hasattr('cols'):
      colspec_child = tgroup_child.children[0]
      if isinstance(colspec_child, docutils.nodes.colspec) and colspec_child.hasattr('colwidth'):
        colspec = str(colspec_child['colwidth']) + ' '
        nr_columns = int(tgroup_child['cols'])
        self.write(':widths: ' + colspec * nr_columns + self.nl + LIST_ITEM_IDENT)
    self.write(':align: center' + self.nl + LIST_ITEM_IDENT)
    self.write(':header-rows: 1' + self.nl + self.nl + LIST_ITEM_IDENT)

  def depart_table(self, node: Node) -> None:
    self.write(self.nl + self.nl)

  def visit_entry(self, node: Node) -> None:
    if isinstance(node.parent, docutils.nodes.row):
      node_as_text = node.astext().replace(self.nl, ' ').lstrip()
      # it is a quick fix for tables and a STRIKEOUT markdown directive
      # remove all children that are system messages
      strikeout2 = re.findall(PATTERN_STRIKEOUT_2, node_as_text)
      if len(strikeout2) > 0:
        for child in node.children:
          if isinstance(child, docutils.nodes.system_message):
            node.children.remove(child)
        node_as_text = node.astext().replace(self.nl, ' ').lstrip()
        strikeout_again = re.findall(PATTERN_STRIKEOUT_2, node_as_text)
        if len(strikeout_again) > 0:
          for item in strikeout_again:
            to_replace = item[0]
            replacing = to_replace.replace('[STRIKEOUT:', ' :strike:`')
            replacing = replacing.replace(']', '` ')
            node_as_text = node_as_text.replace(to_replace, replacing)
      if node.parent.children[0] == node:
        self.write('* - ' + node_as_text + self.nl + LIST_ITEM_IDENT)
      else:
        self.write('  - ' + node_as_text + self.nl + LIST_ITEM_IDENT)
    raise nodes.SkipNode

  # noinspection PyMethodMayBeStatic
  def depart_entry(self, node: Node) -> None:
    pass

  # noinspection PyMethodMayBeStatic
  def visit_row(self, node: Node) -> None:
    pass

  # noinspection PyMethodMayBeStatic
  def depart_row(self, node: Node) -> None:
    pass

  # noinspection PyMethodMayBeStatic
  def visit_tbody(self, node: Node) -> None:
    pass

  # noinspection PyMethodMayBeStatic
  def depart_tbody(self, node: Node) -> None:
    pass

  # noinspection PyMethodMayBeStatic
  def visit_thead(self, node: Node) -> None:
    pass

  # noinspection PyMethodMayBeStatic
  def depart_thead(self, node: Node) -> None:
    pass

  def visit_tgroup(self, node: Node) -> None:
    pass

  def depart_tgroup(self, node: Node) -> None:
    pass

  def visit_colspec(self, node: Node) -> None:
    pass

  def depart_colspec(self, node: Node) -> None:
    pass

  def visit_paragraph(self, node: Node) -> None:
    parent = node.parent
    if not isinstance(parent, docutils.nodes.list_item):
      self.write(self.nl)
    node_as_text = node.astext()
    if node_as_text.startswith('|| |'):
      start_fg = '|| |'
      node_as_text = node_as_text[len(start_fg):len(node_as_text)]
      fake_table = node_as_text.split(self.nl)
      start = True
      for rows_tmp in fake_table:
        rows = rows_tmp.split('|')
        if '' in rows:
          rows.remove('')
        if start:
          var = str(int(80 / len(rows))) + ' '
          real_table = '.. list-table::  ' + self.nl + CODE_BLOCK_IDENT + \
                 ':widths: ' + (var * len(rows)) + self.nl + CODE_BLOCK_IDENT + \
                 ':align: center' + self.nl + CODE_BLOCK_IDENT + \
                 ':header-rows: 1' + self.nl + self.nl + CODE_BLOCK_IDENT
          start = False
        first_element = 1
        for row in rows:
          if '' in rows:
            rows.remove('')
          if first_element:
            real_table += '* - ' + row + self.nl + CODE_BLOCK_IDENT
            first_element = 0
          else:
            real_table += '  - ' + row + self.nl + CODE_BLOCK_IDENT

      real_table += self.nl
      self.write(real_table)
      raise nodes.SkipNode

    if '————————————————————————' in node_as_text and '|' in node_as_text:
      # TODO it is hedious but it works to be refactored
      fake_table = node_as_text.split('|')
      header = 0
      headers = []
      rows = []
      real_table = ''
      for item in fake_table:
        if '————————————' in item and header == 0:
          header += 1
        elif '————————————' in item and header == 1:
          new_headers = [i for i in headers if len(i) > 0]
          var = str(int(80 / len(new_headers))) + ' '
          real_table += '.. list-table::  ' + self.nl + CODE_BLOCK_IDENT + \
                  ':widths: ' + (var * len(new_headers)) + self.nl + CODE_BLOCK_IDENT + \
                  ':align: center' + self.nl + CODE_BLOCK_IDENT + \
                  ':header-rows: 1' + self.nl + self.nl + CODE_BLOCK_IDENT
          start = 0
          for i in range(0, len(new_headers)):
            if len(new_headers[i]) > 0:
              if start == 0:
                real_table += '* - ' + new_headers[i] + self.nl + CODE_BLOCK_IDENT
                start = 1
              else:
                real_table += '  - ' + new_headers[i] + self.nl + CODE_BLOCK_IDENT
          header = 3
        elif header == 1:
          if len(item) > 0:
            headers.append(item.lstrip().replace(self.nl, ''))
        else:
          if len(item) > 0:
            rows.append(item.lstrip().replace(self.nl, ''))
      if new_headers is None:
        self.write("ERROR when parsing a table please check!!!")
        return
      col_count = len(new_headers)
      start = 0
      if '' in rows:
        rows.remove('')

      new_rows = [i for i in rows if len(i) > 0]
      for i in range(0, len(new_rows)):
        if '——————————' in new_rows[i]:
          pass
        elif len(new_rows[i]) > 0 or '—————' not in new_rows[i]:
          if start == 0 or i % col_count == 0:
            real_table += '* - ' + new_rows[i] + self.nl + CODE_BLOCK_IDENT
            start = 1
          else:
            real_table += '  - ' + new_rows[i] + self.nl + CODE_BLOCK_IDENT
      real_table += self.nl
      self.write(real_table)
      raise nodes.SkipNode

  def depart_paragraph(self, node: Node) -> None:
    self.write(self.nl)

  def visit_figure(self, node: Node) -> None:
    self.write(self.nl + '.. figure:: ')

  def depart_figure(self, node: Node) -> None:
    pass

  def visit_image(self, node: Node) -> None:
    self.write(node['uri'] + self.nl + LIST_ITEM_IDENT)
    self.write(':alt: ' + node['alt'] + self.nl)

  def visit_caption(self, node: Node) -> None:
    self.write(self.nl + LIST_ITEM_IDENT + node.astext())

  def depart_caption(self, node: Node) -> None:
    self.write(self.nl)

  def visit_reference(self, node: Node) -> None:
    refname = node.get('name')
    refuri = node.get('refuri')

    if self.document['source'].endswith('index.rst') or \
        self.document["source"].endswith('releases/notes.rst') or \
        self.document["source"].endswith('releases/schedules.rst') or \
        self.document["source"].endswith('downloading-installing-upgrading/upgrade/upgrade.rst') or \
        (self.document["source"].endswith('how-to-back-up-restore-and-migrate.rst') and
         (
             'Qubes R4 or newer' in node.astext() or
             'Qubes R3' in node.astext() or
             'Qubes R2 or older' in node.astext()
         )
        ):
      return
    if refname is None and refuri.startswith('http'):
      self.write(refuri)
      raise nodes.SkipNode
    else:
      if refuri.startswith('/') and '#' in refuri:
        perm = refuri[0:refuri.index('#')]
        section = refuri[refuri.index('#') + 1:len(refuri)]
        self.qubes_rst_links_checker.set_uri(perm)
        self.qubes_rst_links_checker.set_section(section)
      else:
        self.qubes_rst_links_checker.set_section('')
        self.qubes_rst_links_checker.set_uri(refuri)
      # TODO refactor, just one time check for the role no in visit AND depart
      role = self.qubes_rst_links_checker.get_cross_referencing_role()
      l = len(self.lines[-1])
      prefix = role + '`'
      if l > 0 and self.lines[-1][l - 1] in ['*', '`', '.', '!', ',', ':', ';', '?']:
        prefix = ' ' + prefix
      elif l > 0 and self.lines[-1][l - 1] in [' ', '\n', '(', ' ', '/', '“']:
        prefix = prefix
      elif l == 0 and len(self.lines) > 0:
        prefix = prefix
      else:
        prefix = ' ' + prefix
      self.write(prefix)

  def depart_reference(self, node: Node) -> None:
    refname = node.get('name')
    refuri = node.get('refuri')
    if refname is None and refuri.startswith('http'):
      # the case of license.rst and Markdown link with qubes os have to be converted manually
      return

    if refuri.startswith('/doc/#'):
      section = refuri[refuri.index('#') + 1:len(refuri)]
      self.qubes_rst_links_checker.set_section(section)
      self.qubes_rst_links_checker.set_uri(refuri)
    elif refuri.startswith('/') and '#' in refuri:
      perm = refuri[0:refuri.index('#')]
      section = refuri[refuri.index('#') + 1:len(refuri)]
      self.qubes_rst_links_checker.set_uri(perm)
      self.qubes_rst_links_checker.set_section(section)
    elif refuri.startswith('#'):
      # this is here it is an internal link
      # TODO this should be done in check_cross_referencing_escape_uri
      self.write(' <' + refuri + '>')
      self.write('`__')
      return
    else:
      self.qubes_rst_links_checker.set_section('')
      self.qubes_rst_links_checker.set_uri(refuri)
    # TODO refactor, just one time check for the role not in visit AND depart
    role = self.qubes_rst_links_checker.get_cross_referencing_role()
    if len(role) == 0:
      url = self.qubes_rst_links_checker.check_cross_referencing_escape_uri()
      url_to_add = '<' + url + '>'
    else:
      url = self.qubes_rst_links_checker.check_cross_referencing_escape_uri()
      url_to_add = '<' + url + '>'
      if role == ':ref:' and url.startswith('/'):
        url_to_add = '<' + url[1:len(url)] + '>'
    self.write(' ' + url_to_add)
    underscore = ''
    if len(role) == 0:
      underscore = '__'

    if not (self.document['source'].endswith('index.rst') or
        self.document["source"].endswith('releases/notes.rst') or
        self.document["source"].endswith('releases/schedules.rst') or
        self.document["source"].endswith('downloading-installing-upgrading/upgrade/upgrade.rst') or \
        (self.document["source"].endswith('how-to-back-up-restore-and-migrate.rst') and
         (
             'Qubes R4 or newer' in node.astext() or
             'Qubes R3' in node.astext() or
             'Qubes R2 or older' in node.astext()
         )
        )):
      self.write('`' + underscore)
