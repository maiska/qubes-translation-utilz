# redacted from https://github.com/sphinx-contrib/restbuilder
from __future__ import absolute_import
import re
import os
import textwrap
from logging import basicConfig, getLogger, DEBUG

import docutils
from docutils import nodes, writers
from docutils.nodes import Node

from sphinx.writers.text import MAXWIDTH, STDINDENT

from config_constants import PATTERN_STRIKEOUT_1, PATTERN_STRIKEOUT_2
from docutils_rst_writer.writer import RstTranslator
from utilz import CheckRSTLinks

PUNCTUATION_SET = {'!', ',', '.', ':', ';', '?', '__'}

basicConfig(level=DEBUG)
logger_qubes_rst = getLogger(__name__)


class QubesRstWriter(writers.Writer):
    supported = ('text',)
    settings_spec = ('No options here.', '', ())
    settings_defaults = {}

    output = None

    def __init__(self, qubes_rst_links_checker: CheckRSTLinks):
        writers.Writer.__init__(self)
        self.qubes_rst_links_checker = qubes_rst_links_checker

    def translate(self):
        visitor = QubesRstTranslator(self.document, self.qubes_rst_links_checker)
        # visitor = RstTranslator(self.document) new rsttranslator
        self.document.walkabout(visitor)
        self.output = visitor.body


SPACE = ' '
CODE_BLOCK_IDENT = SPACE * STDINDENT * 2
LIST_ITEM_IDENT = SPACE * STDINDENT


def is_python_code_block(code_as_string):
    return ' class ' in code_as_string or ' self.' in code_as_string or \
           ' for modname in' in code_as_string or re.findall(' def.*.\):',
                                                             code_as_string) or ' import ' in code_as_string


def is_shell_session_original_code_block(node):
    return node.hasattr('classes') and len(node['classes']) == 2 and node['classes'][0] == 'code' and \
           (node['classes'][1] == 'shell_session' or node['classes'][1] == 'bash_session')


def is_html_original_code_block(node):
    return node.hasattr('classes') and len(node['classes']) == 2 and node['classes'][0] == 'code' and node['classes'][
        1] == 'html'


def is_python_original_code_block(node):
    return node.hasattr('classes') and len(node['classes']) == 2 and node['classes'][0] == 'code' and node['classes'][
        1] == 'python'


def is_video_tours_original_code_block(node):
    return node.hasattr('classes') and len(node['classes']) == 2 and node['classes'][0] == 'container' and \
           node['classes'][
               1] == 'video'


def is_lua_original_code_block(node):
    return node.hasattr('classes') and len(node['classes']) == 2 and node['classes'][0] == 'code' and node['classes'][
        1] == 'lua'


def is_c_original_code_block(node):
    return node.hasattr('classes') and len(node['classes']) == 2 and node['classes'][0] == 'code' and node['classes'][
        1] == 'c'


def is_bash_original_code_block(node):
    return node.hasattr('classes') and len(node['classes']) == 2 and node['classes'][0] == 'code' and \
           (node['classes'][1] == 'bash' or node['classes'][1] == 'shell' or node['classes'][1] == 'sh')


def is_c_code_block(code_as_string):
    return ' while(' in code_as_string or ' for(' in code_as_string or \
           ' while (' in code_as_string or ' for (' in code_as_string or \
           ' #if ' in code_as_string or ' #endif ' in code_as_string or \
           ' int ' in code_as_string or ' struct ' in code_as_string or \
           ' #include <' in code_as_string or '.h>' in code_as_string or \
           ' int main(int argc, char* argv[])' in code_as_string or \
           ' uint32_t ' in code_as_string


def is_file_with_c_code_blocks(filename):
    return 'coding-style' in filename


def is_node_a_code_block(node):
    return (isinstance(node, docutils.nodes.literal_block) and node.hasattr('language')) or \
           (node.hasattr('classes') and 'code' in node['classes']) or \
           (node.hasattr('xml:space') and node['xml:space'] == 'preserve')


# noinspection PyPep8Naming,PyMethodMayBeStatic
def is_code_block_to_convert_to_bash(node_as_text):
    return "shell_session" in node_as_text or "bash_session" in node_as_text or '[user@dom0 ~]$' in node_as_text


# noinspection PyMethodMayBeStatic,PyPep8Naming,PyRedeclaration,PyUnusedLocal
def is_node_inside_emphasis_strong_literal(parent):
    return True if isinstance(parent, docutils.nodes.emphasis) or \
                   isinstance(parent, docutils.nodes.strong) or \
                   isinstance(parent, docutils.nodes.literal) else False


def get_title_text_length(child):
    length = len(child.astext())
    if isinstance(child, docutils.nodes.literal) or isinstance(child, docutils.nodes.strong):
        length += 4
    if isinstance(child, docutils.nodes.emphasis):
        length += 2
    return length


class QubesRstTranslator(nodes.NodeVisitor):
    sectionchars = '*=-~"+`'

    def __init__(self, document, qubes_rst_links_checker: CheckRSTLinks):
        nodes.NodeVisitor.__init__(self, document)
        self.qubes_rst_links_checker = qubes_rst_links_checker
        self.body = ""
        self.document = document
        self.title_count = 0
        self.section_count = 0
        self.enumerated_count = 0
        self.enumerated_lists_count = 0
        self.ident_count = 0
        self.video_container_summit_count = 0

        newlines = 'native'
        if newlines == 'windows':
            self.nl = '\r\n'
        elif newlines == 'native':
            self.nl = os.linesep
        else:
            self.nl = '\n'
        self.sectionchars = '=-~"+`'
        self.indent = STDINDENT
        self.wrapper = textwrap.TextWrapper(width=MAXWIDTH, break_long_words=False, break_on_hyphens=False)

    def wrap(self, text, width=MAXWIDTH):
        self.wrapper.width = width
        return self.wrapper.wrap(text)

    def visit_document(self, node):
        pass

    def depart_document(self, node):
        pass

    def visit_block_quote(self, node):
        pass

    def depart_block_quote(self, node):
        pass

    def visit_comment(self, node):
        pass

    def depart_comment(self, node):
        pass

    def visit_raw(self, node):
        pass

    def depart_raw(self, node):
        pass

    def visit_container(self, node):
        if node.hasattr('classes') and node['classes'][0] == 'focus' and \
                isinstance(node.children[0], docutils.nodes.paragraph):
            self.body += self.nl + '**' + node.children[0].astext() + '**' + self.nl
            raise nodes.SkipNode

        if node.hasattr('classes') and len(node['classes']) == 2 and \
                node['classes'][0] == 'alert' and \
                node['classes'][1] == 'alert-warning' and \
                isinstance(node.children[0], docutils.nodes.paragraph):
            self.body += self.nl + '.. warning::' + self.nl + CODE_BLOCK_IDENT + self.get_code_text_block(
                node.children[0].astext()) + self.nl
            raise nodes.SkipNode
        if node.hasattr('classes') and len(node['classes']) == 2 and \
                node['classes'][0] == 'alert' and \
                node['classes'][1] == 'alert-danger' and \
                isinstance(node.children[0], docutils.nodes.paragraph):
            self.body += self.nl + '.. DANGER::' + self.nl + CODE_BLOCK_IDENT + self.get_code_text_block(
                node.children[0].astext()) + self.nl
            raise nodes.SkipNode
        if node.hasattr('classes') and len(node['classes']) == 2 and \
                node['classes'][0] == 'alert' and \
                (node['classes'][1] == 'alert-success' or node['classes'][1] == 'alert-info') and \
                isinstance(node.children[0], docutils.nodes.paragraph):
            self.body += self.nl + '.. note::' + self.nl + CODE_BLOCK_IDENT + self.get_code_text_block(
                node.children[0].astext()) + self.nl
            raise nodes.SkipNode

    def depart_container(self, node):
        pass

    def visit_transition(self, node):
        pass

    def depart_transition(self, node):
        pass

    def visit_system_message(self, node):
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
        self.body += 'SYSTEM MESSAGE  for: ' + node_as_text

    def depart_system_message(self, node):
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

    def get_custom_videotours_directive(self, directive_name, vidid):
        spacing = self.nl + SPACE * len(directive_name)
        return self.nl + directive_name + vidid + spacing + \
               ':height: 315' + spacing + \
               ':width: 560' + spacing + \
               ':align: left' + self.nl

    # TODO refactor...
    def visit_literal_block(self, node):
        node_as_text = node.astext()
        if node_as_text.lstrip().rstrip().startswith('.. figure::'):
            self.body += self.nl + node_as_text
            raise nodes.SkipNode
        if node_as_text.lstrip().rstrip() == '.. container:: center-block more-bottom' and \
                self.document['source'].endswith('statistics.rst'):
            self.body += self.nl + '.. figure:: '
            self.body += 'https://tools.qubes-os.org/counter/stats.png' + self.nl + LIST_ITEM_IDENT
            self.body += ':alt: ' + 'Estimated Qubes OS userbase graph' + self.nl
            raise nodes.SkipNode
        if node_as_text.lstrip().rstrip() == '.. container:: video more-bottom' and \
                self.document['source'].endswith('video-tours.rst') and \
                isinstance(node.parent, docutils.nodes.system_message) and \
                isinstance(node.parent.parent, docutils.nodes.section) and \
                'Qubes OS Summit 2022' in node.parent.parent.astext():
            youtube_directive = '.. youtube:: '
            if self.video_container_summit_count == 0:
                self.body += self.get_custom_videotours_directive(youtube_directive, 'hkWWz3xGqS8')
                self.body += self.get_custom_videotours_directive(youtube_directive, 'A9GrlQsQc7Q')
                self.body += self.get_custom_videotours_directive(youtube_directive, 'gnWHjv-9_YM')
                self.video_container_summit_count += 1
            raise nodes.SkipNode
        if node_as_text.lstrip().rstrip() == '.. container:: video more-bottom' and \
                self.document['source'].endswith('video-tours.rst') and \
                isinstance(node.parent, docutils.nodes.system_message) and \
                isinstance(node.parent.parent, docutils.nodes.section) and \
                'Micah Lee' in node.parent.parent.astext():
            generalvid_directive = '.. generalvid:: '
            self.body += self.get_custom_videotours_directive(generalvid_directive,
                                                              'https://livestream.com/accounts/9197973/events/8286152/videos/178431606/player?autoPlay=false')
            raise nodes.SkipNode
        if node_as_text.lstrip().rstrip() == '.. container:: video' and \
                self.document['source'].endswith('video-tours.rst') and \
                isinstance(node.parent, docutils.nodes.system_message) and \
                isinstance(node.parent.parent, docutils.nodes.section) and \
                'Explaining Computers' in node.parent.parent.astext():
            youtube_directive = '.. youtube:: '
            self.body += self.get_custom_videotours_directive(youtube_directive, 'hWDvS_Mp6gc')
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
            if is_python_code_block(node_as_text):  # or is_file_with_c_code_blocks(self.document['source']):
                node['language'] = 'python'
                self.ident_coding_block_for(node, 'python')
                raise nodes.SkipNode
            elif is_c_code_block(node_as_text) or is_file_with_c_code_blocks(self.document['source']):
                node['language'] = 'c'
                self.body += self.nl + '.. code:: c' + self.nl + self.nl
            elif node.hasattr('language') and node['language'] == 'bash':
                pass
            elif is_code_block_to_convert_to_bash(node_as_text):
                for i in ['shell_session', 'bash_session', '.. code::']:
                    node_as_text = node_as_text.replace(i, '').lstrip()
                self.body += self.nl + '.. code:: bash' + self.nl + self.nl
                get_code_text_block = self.get_code_text_block(node_as_text)
                self.body += CODE_BLOCK_IDENT + get_code_text_block
                self.body += self.nl
                raise nodes.SkipNode
            elif not node.hasattr('language') or node['language'] in ["shell_session", "bash_session"]:
                node['language'] = 'bash'
                self.body += self.nl + '.. code:: bash' + self.nl + self.nl
            else:
                self.body += self.nl + '.. code:: ' + node['language'] + self.nl + self.nl

    def ident_coding_block_for(self, node, language):
        self.body += self.nl + '.. code:: ' + language + self.nl + self.nl + CODE_BLOCK_IDENT
        get_code_text_block = self.get_code_text_block(node.astext())
        self.add_space_to_body_if_needed(get_code_text_block, node)
        self.body += self.nl

    def depart_literal_block(self, node):
        self.body += self.nl + self.nl

    def visit_subsection(self, node):
        pass

    def visit_problematic(self, node):
        pass

    def depart_problematic(self, node):
        pass

    def visit_title_reference(self, node):
        pass

    def depart_title_reference(self, node):
        pass

    def visit_line(self, node):
        pass

    def depart_line(self, node):
        pass

    def visit_substitution_reference(self, node):
        self.body += '|'

    def depart_substitution_reference(self, node):
        self.body += '|'

    def visit_substitution_definition(self, node):
        assert len(node.children) > 0
        first_child = node.children[0]
        if isinstance(first_child, docutils.nodes.reference):
            assert len(first_child.children) > 0
            image = first_child.children[0]
            assert isinstance(image, docutils.nodes.image)

            self.body += self.nl + '.. |' + node['names'][0] + '| image:: ' + image['uri'] \
                         + self.nl + LIST_ITEM_IDENT + \
                         ':target: ' + first_child['refuri'] + self.nl
            raise nodes.SkipNode
        if isinstance(first_child, docutils.nodes.image):
            self.body += self.nl + '.. |' + node['names'][0] + '| image:: ' + first_child['uri'] \
                         + self.nl
            raise nodes.SkipNode

    def depart_substitution_definition(self, node):
        raise nodes.SkipNode

    # noinspection PyMethodMayBeStatic
    def visit_line_block(self, node):
        pass

    # noinspection PyMethodMayBeStatic
    def depart_line_block(self, node):
        pass

    # noinspection PyMethodMayBeStatic
    def visit_target(self, node):
        pass

    # noinspection PyMethodMayBeStatic
    def depart_target(self, node):
        pass

    # noinspection PyMethodMayBeStatic
    def visit_section(self, node):
        pass

    def depart_section(self, node):
        self.section_count += 1

    def visit_title(self, node):
        if self.title_count == 0:
            length = 0
            for child in node.children:
                length += get_title_text_length(child)
            self.body += '=' * length + self.nl
        else:
            self.body += self.nl

    def depart_title(self, node):
        parent = node.parent
        length = 0
        for child in node.children:
            length += get_title_text_length(child)
        # section title
        if self.title_count >= 0 and isinstance(parent, docutils.nodes.section) and not (
                isinstance(parent.parent, docutils.nodes.section)):
            self.body += self.nl + '=' * length + self.nl + self.nl
        # subsubsection title
        elif self.title_count >= 0 and isinstance(parent, docutils.nodes.section) and \
                isinstance(parent.parent, docutils.nodes.section) and \
                isinstance(parent.parent.parent, docutils.nodes.section):
            self.body += self.nl + '^' * length + self.nl + self.nl
        # subsection title
        elif self.title_count >= 0 and isinstance(parent, docutils.nodes.section) and \
                isinstance(parent.parent, docutils.nodes.section):
            self.body += self.nl + '-' * length + self.nl + self.nl
        else:
            pass
        self.title_count += 1

    # noinspection PyMethodMayBeStatic
    def visit_line_block(self, node):
        pass

    def visit_Text(self, node):
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
            if self.body[len(self.body) - 1] in [self.nl]:
                self.body += CODE_BLOCK_IDENT
            else:
                self.body += self.nl + CODE_BLOCK_IDENT
        elif isinstance(parent, docutils.nodes.reference):
            self.body += node.astext().replace(self.nl, ' ')
            raise nodes.SkipNode
        elif isinstance(parent.parent, docutils.nodes.list_item):
            self.body += self.get_list_item_ident(node.astext(), self.ident_count)
            raise nodes.SkipNode
        elif isinstance(parent, docutils.nodes.list_item) or \
                isinstance(parent.parent, docutils.nodes.list_item) or \
                isinstance(parent.parent.parent, docutils.nodes.list_item):
            self.body += self.get_list_item_ident(node.astext())
            raise nodes.SkipNode
        elif isinstance(parent, docutils.nodes.paragraph) and \
                isinstance(parent.parent, docutils.nodes.entry) and \
                isinstance(parent.parent.parent, docutils.nodes.row):
            # table is handled in entry element
            pass

    def depart_Text(self, node):
        parent = node.parent
        node_as_text = node.astext()
        if is_node_inside_emphasis_strong_literal(parent):
            self.body += node_as_text.replace(self.nl, ' ')
        elif isinstance(parent, docutils.nodes.title):
            self.body += node.astext().replace('’', '\'').replace('”', '"').replace('“', '"')
            # raise nodes.SkipNode
        elif is_node_a_code_block(parent):
            code_as_indented_text = self.get_code_text_block(node_as_text)
            self.add_space_to_body_if_needed(code_as_indented_text, node)
        elif isinstance(parent, docutils.nodes.caption):
            pass
        elif isinstance(parent, docutils.nodes.paragraph) and \
                isinstance(parent.parent, docutils.nodes.entry) and \
                isinstance(parent.parent.parent, docutils.nodes.row):
            # table is handled in the entry element
            pass
        elif node_as_text.lstrip() == '{% raw %}' or node_as_text.lstrip() == '{% endraw %}':
            self.body += ''
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
            self.body += node_as_text
        else:
            strikeout1 = re.findall(PATTERN_STRIKEOUT_1, node_as_text)
            if len(strikeout1) > 0:
                for item in strikeout1:
                    to_replace = item[0]
                    replacing = to_replace.replace('~[STRIKEOUT:', ' ``')
                    replacing = replacing.replace(']~', '`` ')
                    node_as_text = node_as_text.replace(to_replace, replacing)
                self.body += node_as_text
                return
            strikeout2 = re.findall(PATTERN_STRIKEOUT_2, node_as_text)
            if len(strikeout2) > 0:
                for item in strikeout2:
                    to_replace = item[0]
                    replacing = to_replace.replace('[STRIKEOUT:', ' :strike:`')
                    replacing = replacing.replace(']', '` ')
                    node_as_text = node_as_text.replace(to_replace, replacing)
                self.body += node_as_text
                return
            self.add_space_to_body_if_needed(node_as_text, node)

    def get_code_text_block(self, node_as_string):
        x = node_as_string.splitlines()
        ident = self.nl + CODE_BLOCK_IDENT
        return ident.join(x) + self.nl

    def get_list_item_ident(self, node_as_string, level=1):
        x = node_as_string.splitlines()
        ident = self.nl + LIST_ITEM_IDENT * level
        return ident.join(x)

    def visit_enumerated_list(self, node):
        if self.enumerated_lists_count > 2:
            logger_qubes_rst.debug('no more enumerated list spiral')
            self.visit_system_message(node)
        self.enumerated_lists_count += 1
        self.ident_count += 1
        self.body += self.nl

    def depart_enumerated_list(self, node):
        self.enumerated_lists_count -= 1
        self.enumerated_count = 0
        self.body += self.nl + self.nl
        self.ident_count -= 1

    def visit_bullet_list(self, node):
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
            toctree_directive = self.nl + '.. toctree::' + self.nl + LIST_ITEM_IDENT + ':maxdepth: 1'
            self.body += toctree_directive + self.nl
        self.body += self.nl
        self.ident_count += 1

    def depart_bullet_list(self, node):
        self.body += self.nl + self.nl
        self.ident_count -= 1

    def visit_list_item(self, node):
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
            self.body += LIST_ITEM_IDENT
        elif isinstance(parent, docutils.nodes.list_item) or isinstance(parent.parent, docutils.nodes.list_item):
            self.body += LIST_ITEM_IDENT + '-  '
        elif isinstance(parent, docutils.nodes.bullet_list):
            self.body += '-  '
        elif isinstance(parent, docutils.nodes.enumerated_list):
            self.enumerated_count += 1
            self.body += self.nl + str(self.enumerated_count) + '.' + SPACE

    # noinspection PyMethodMayBeStatic
    def depart_list_item(self, node):
        pass

    def visit_inline(self, node):
        parent = node.parent
        if is_node_a_code_block(parent) and node.hasattr('classes') and 'single' in node['classes']:
            self.body += self.nl + CODE_BLOCK_IDENT

    # noinspection PyMethodMayBeStatic
    def depart_inline(self, node):
        pass

    def visit_table(self, node):
        self.body += self.nl + '.. list-table:: ' + self.nl + LIST_ITEM_IDENT
        tgroup_child = node.children[0]
        if isinstance(tgroup_child, docutils.nodes.tgroup) and tgroup_child.hasattr('cols'):
            colspec_child = tgroup_child.children[0]
            if isinstance(colspec_child, docutils.nodes.colspec) and colspec_child.hasattr('colwidth'):
                colspec = str(colspec_child['colwidth']) + ' '
                nr_columns = int(tgroup_child['cols'])
                self.body += ':widths: ' + colspec * nr_columns + self.nl + LIST_ITEM_IDENT
        self.body += ':align: center' + self.nl + LIST_ITEM_IDENT
        self.body += ':header-rows: 1' + self.nl + self.nl + LIST_ITEM_IDENT

    def depart_table(self, node):
        self.body += self.nl + self.nl

    def visit_entry(self, node):
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
                self.body += '* - ' + node_as_text + self.nl + LIST_ITEM_IDENT
            else:
                self.body += '  - ' + node_as_text + self.nl + LIST_ITEM_IDENT
        raise nodes.SkipNode

    # noinspection PyMethodMayBeStatic
    def depart_entry(self, node):
        pass

    # noinspection PyMethodMayBeStatic
    def visit_row(self, node):
        pass

    # noinspection PyMethodMayBeStatic
    def depart_row(self, node):
        pass

    # noinspection PyMethodMayBeStatic
    def visit_math(self, node):
        pass

    # noinspection PyMethodMayBeStatic
    def depart_math(self, node):
        pass

    # noinspection PyMethodMayBeStatic
    def visit_tbody(self, node):
        pass

    # noinspection PyMethodMayBeStatic
    def depart_tbody(self, node):
        pass

    # noinspection PyMethodMayBeStatic
    def visit_thead(self, node):
        pass

    # noinspection PyMethodMayBeStatic
    def depart_thead(self, node):
        pass

    def visit_tgroup(self, node):
        pass

    def depart_tgroup(self, node):
        pass

    def visit_colspec(self, node):
        pass

    def depart_colspec(self, node):
        pass

    def visit_paragraph(self, node):
        parent = node.parent
        if not isinstance(parent, docutils.nodes.list_item):
            self.body += self.nl
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
            self.body += real_table
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
                self.body += "ERROR when parsing a table please check!!!"
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
            self.body += real_table
            raise nodes.SkipNode

    def depart_paragraph(self, node):
        self.body += self.nl

    def visit_image(self, node):
        self.body += node['uri'] + self.nl + LIST_ITEM_IDENT
        self.body += ':alt: ' + node['alt'] + self.nl

    def depart_image(self, node):
        pass

    def visit_caption(self, node):
        self.body += self.nl + LIST_ITEM_IDENT + node.astext()

    def depart_caption(self, node):
        self.body += self.nl

    def visit_figure(self, node):
        self.body += self.nl + '.. figure:: '

    def depart_figure(self, node):
        pass

    def add_space_to_body_if_needed(self, text, node):
        if self.body[len(self.body) - 1] in [self.nl, SPACE, CODE_BLOCK_IDENT, LIST_ITEM_IDENT, '(', ':', '/'] or \
                (self.body[len(self.body) - 1] in ['`', '>'] and isinstance(node, docutils.nodes.reference)) or \
                (self.body[len(self.body) - 1] in ['`'] and isinstance(node.parent, docutils.nodes.reference)) or \
                (len(text) > 0 and text[0] in PUNCTUATION_SET) or \
                isinstance(node.parent, docutils.nodes.strong) or isinstance(node.parent, docutils.nodes.emphasis) or \
                isinstance(node.parent, docutils.nodes.literal):
            self.body += text
        else:
            self.body += SPACE + text

    def visit_reference(self, node):
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
            self.body += refuri
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
            if not self.body[len(self.body) - 1] in \
                   [self.nl, SPACE, CODE_BLOCK_IDENT, LIST_ITEM_IDENT, '(', ':', '/', "", '\'', '“']:
                self.body += ' '
            self.add_space_to_body_if_needed(role + '`', node)

    def depart_reference(self, node):
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
            self.add_space_to_body_if_needed('<' + refuri + '>', node)
            self.body += '`__'
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
        self.add_space_to_body_if_needed(url_to_add, node)
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
            self.body += '`' + underscore

    def visit_strong(self, node):
        self.add_space_to_body_if_needed('**', node)

    def depart_strong(self, node):
        self.body += '**'

    def visit_emphasis(self, node):
        self.add_space_to_body_if_needed('*', node)

    def depart_emphasis(self, node):
        self.body += '*'

    def visit_term(self, node: Node) -> None:
        pass

    def visit_definition(self, node: Node) -> None:
        self.indent += 3

    def depart_definition(self, node: Node) -> None:
        self.indent -= 3

    def depart_term(self, node: Node) -> None:
        self.body += self.nl

    def visit_definition_list(self, node: Node) -> None:
        pass

    def depart_definition_list(self, node: Node) -> None:
        pass

    def visit_definition_list_item(self, node: Node) -> None:
        pass

    def depart_definition_list_item(self, node: Node) -> None:
        pass

    def visit_literal(self, node):
        parent = node.parent
        if not (isinstance(parent, docutils.nodes.reference) and parent.hasattr('name') and
                node.astext().lstrip() == parent['name']):
            self.add_space_to_body_if_needed('``', node)

    def depart_literal(self, node):
        parent = node.parent
        # TODO regular expressions
        # ```openqa_investigator``
        # < https://github.com/QubesOS/openqa-tests-qubesos/blob/master/utils/openqa_investigator.py>`__
        # < literal > `openqa_investigator < / literal > << reference
        # refuri = "https://github.com/QubesOS/openqa-tests-qubesos/blob/master/utils/openqa_investigator.py" >
        if not (isinstance(parent, docutils.nodes.reference) and parent.hasattr('name') and
                node.astext().lstrip() == parent['name']):
            self.body += '``'

    # def unknown_visit(self, node):
    #     print(node)
    #     print("unknown_visit end")
    #     self.add_text('[UNKNOWN NODE %s]' % node.astext())
    #     log_unknown(node.__class__.__name__, node)
    #
    # def unknown_departure(self, node):
    #     print(node)
    #     pass
