# redacted from https://github.com/sphinx-contrib/restbuilder
import codecs
import logging
import os
import sys
import textwrap
from logging import basicConfig, getLogger, DEBUG

from docutils import nodes, writers
from docutils.io import StringOutput
from docutils.nodes import fully_normalize_name
from sphinx import addnodes
from sphinx.locale import admonitionlabels, _
from sphinx.util import ensuredir
from sphinx.writers.text import MAXWIDTH, STDINDENT

from config_constants import INTERNAL_BASE_PATH, BASE_SITE, DOC_BASE_PATH, FEED_XML
from utilz import is_dict_empty

basicConfig(level=DEBUG)
logger = getLogger(__name__)


class QubesRstWriter(writers.Writer):
    supported = ('text',)
    settings_spec = ('No options here.', '', ())
    settings_defaults = {}

    output = None

    def __init__(self, builder, md_doc_permalinks_and_redirects_to_filepath_map,
                 md_pages_permalinks_and_redirects_to_filepath_map,
                 external_redirects_map):
        writers.Writer.__init__(self)
        self.builder = builder
        if is_dict_empty(md_pages_permalinks_and_redirects_to_filepath_map):
            raise ValueError("md_pages_permalinks_and_redirects_to_filepath_mapping is not set")
        self.md_pages_permalinks_and_redirects_to_filepath_map = md_pages_permalinks_and_redirects_to_filepath_map

        if is_dict_empty(md_doc_permalinks_and_redirects_to_filepath_map):
            raise ValueError("md_doc_permalinks_and_redirects_to_filepath_mapping is not set")
        self.md_doc_permalinks_and_redirects_to_filepath_map = md_doc_permalinks_and_redirects_to_filepath_map

        if is_dict_empty(external_redirects_map):
            raise ValueError("external_url_mapping is not set")
        self.external_redirects_map = external_redirects_map
        self.md_pages_permalinks_and_redirects_to_filepath_map = md_pages_permalinks_and_redirects_to_filepath_map
        self.md_doc_permalinks_and_redirects_to_filepath_map = md_doc_permalinks_and_redirects_to_filepath_map

    def translate(self):
        visitor = QubesRstTranslator(self.document, self.builder,
                                     self.md_doc_permalinks_and_redirects_to_filepath_map,
                                     self.md_pages_permalinks_and_redirects_to_filepath_map,
                                     self.external_redirects_map)
        self.document.walkabout(visitor)
        self.output = visitor.body


def log_warning(message):
    logger = logging.getLogger("sphinxcontrib.writers.rst")
    if len(logger.handlers) == 0:
        # Logging is not yet configured. Configure it.
        logging.basicConfig(level=logging.INFO, stream=sys.stderr, format='%(levelname)-8s %(message)s')
        logger = logging.getLogger("sphinxcontrib.writers.rst")
    logger.warning(message)


def log_unknown(typed, node):
    log_warning("%s(%s) unsupported formatting" % (typed, node))

    # TODO Maya eigene sphinx extension fuer :role: :doc; beim bauen einbauen
    # def escape_uri(self,uri):
    #     if uri.endswith('_'):
    #         uri = uri[:-1] + '\\_'
    #     return uri


def get_url(path):
    logger.debug('>>>> pages path %s ' % path)
    if path.startswith('/'):
        url = BASE_SITE + path[1:len(path)] + '/'
    else:
        url = BASE_SITE + path + '/'
    return url


def get_cross_referencing_role(uri):
    
    if uri.startswith('/') and '#' in uri and not uri.startswith('/attachment'):
        return ':ref:'
    elif uri.startswith('/') and not uri.startswith('/attachment'):
        return ':doc:'
    elif uri.startswith('#'):
        return 'inline-section'
    else:
        return ''
    return ''


def replace_page_aux(perm_match, path):
    return BASE_SITE + path + '/' + perm_match[perm_match.index('#'):len(perm_match)] if not path.startswith(
        '/') else BASE_SITE[0:len(BASE_SITE) - 1] + path + '/' + perm_match[perm_match.index('#'):len(perm_match)]


# noinspection PyPep8Naming,PyMethodMayBeStatic
class QubesRstTranslator(nodes.NodeVisitor):
    sectionchars = '*=-~"+`'

    def __init__(self, document, builder,
                 md_doc_permalinks_and_redirects_to_filepath_map,
                 md_pages_permalinks_and_redirects_to_filepath_map,
                 external_redirects_mappings):
        nodes.NodeVisitor.__init__(self, document)

        self.md_pages_permalinks_and_redirects_to_filepath_map = md_pages_permalinks_and_redirects_to_filepath_map
        self.external_redirects_mappings = external_redirects_mappings
        self.md_doc_permalinks_and_redirects_to_filepath_map = md_doc_permalinks_and_redirects_to_filepath_map
        self._li_has_classifier = None
        self._citlabel = None
        self._firstoption = None
        self._footnote = None
        self.first_param = None
        self._title_char = None
        self.body = None
        self.document = document
        self.builder = builder

        newlines = 'native'
        if newlines == 'windows':
            self.nl = '\r\n'
        elif newlines == 'native':
            self.nl = os.linesep
        else:
            self.nl = '\n'
        self.sectionchars = '*=-~"+`'
        self.states = [[]]
        self.stateindent = [0]
        self.list_counter = []
        self.list_formatter = []
        self.sectionlevel = 0
        self.table = None
        self.indent = STDINDENT
        self.wrapper = textwrap.TextWrapper(width=MAXWIDTH, break_long_words=False, break_on_hyphens=False)

    def wrap(self, text, width=MAXWIDTH):
        self.wrapper.width = width
        return self.wrapper.wrap(text)

    def add_text(self, text):
        print("self.states[-1]")
        print(self.states[-1])
        self.states[-1].append((-1, text))

    def new_state(self, indent=STDINDENT):
        self.states.append([])
        self.stateindent.append(indent)

    def end_state(self, wrap=True, end=None, first=None):
        if end is None:
            end = ['']
        content = self.states.pop()
        width = max(MAXWIDTH // 3, MAXWIDTH - sum(self.stateindent))
        indent = self.stateindent.pop()
        result = []
        toformat = []

        def do_format():
            if not toformat:
                return
            if wrap:
                res = self.wrap(''.join(toformat), width=width)
            else:
                res = ''.join(toformat).splitlines()
            if end:
                res += end
            result.append((indent, res))

        for itemindent, item in content:
            if itemindent == -1:
                toformat.append(item)
            else:
                do_format()
                result.append((indent + itemindent, item))
                toformat = []
        do_format()
        if first is not None and result:
            itemindent, item = result[0]
            if item:
                result.insert(0, (itemindent - indent, [first + item[0]]))
                result[1] = (itemindent, item[1:])
        self.states[-1].extend(result)

    def visit_document(self, node):
        self.new_state(0)

    def depart_document(self, node):
        self.end_state()
        self.body = self.nl.join(line and (' ' * indent + line)
                                 for indent, lines in self.states[0]
                                 for line in lines)
        # TODO: add header/footer?

    def visit_highlightlang(self, node):
        print('VISIT_HIGHLIGHTLANG')
        print(node)
        raise nodes.SkipNode

    def visit_section(self, node):
        self._title_char = self.sectionchars[self.sectionlevel]
        self.sectionlevel += 1

    def depart_section(self, node):
        self.sectionlevel -= 1

    def visit_topic(self, node):
        self.new_state(0)

    def depart_topic(self, node):
        self.end_state()

    visit_sidebar = visit_topic
    depart_sidebar = depart_topic

    def visit_rubric(self, node):
        self.new_state(0)
        self.add_text('-[ ')

    def depart_rubric(self, node):
        self.add_text(' ]-')
        self.end_state()

    def visit_container(self, node):
        # self.log_unknown("compound", node)
        pass

    def depart_container(self, node):
        pass

    # def visit_compound(self, node):
    #     # self.log_unknown("compound", node)
    #     pass
    #
    # def depart_compound(self, node):
    #     pass

    def visit_glossary(self, node):
        # self.log_unknown("glossary", node)
        pass

    def depart_glossary(self, node):
        pass

    def visit_title(self, node):
        if isinstance(node.parent, nodes.Admonition):
            self.add_text(node.astext() + ': ')
            raise nodes.SkipNode
        self.new_state(0)

    def depart_title(self, node):
        if isinstance(node.parent, nodes.section):
            char = self._title_char
        else:
            char = '^'
        text = ''.join(x[1] for x in self.states.pop() if x[0] == -1)
        self.stateindent.pop()
        self.states[-1].append((0, ['', text, '%s' % (char * len(text)), '']))

    # def visit_subtitle(self, node):
    #     # self.log_unknown("subtitle", node)
    #     pass
    #
    # def depart_subtitle(self, node):
    #     pass

    def visit_attribution(self, node):
        self.add_text('-- ')

    def depart_attribution(self, node):
        pass

    def visit_desc(self, node):
        self.new_state(0)

    def depart_desc(self, node):
        self.end_state()

    def visit_desc_signature(self, node):
        if node.parent['objtype'] in ('class', 'exception', 'method', 'function'):
            self.add_text('**')
        else:
            self.add_text('``')

    def depart_desc_signature(self, node):
        if node.parent['objtype'] in ('class', 'exception', 'method', 'function'):
            self.add_text('**')
        else:
            self.add_text('``')

    # def visit_desc_name(self, node):
    #     # self.log_unknown("desc_name", node)
    #     pass
    #
    # def depart_desc_name(self, node):
    #     pass

    # def visit_desc_addname(self, node):
    #     # self.log_unknown("desc_addname", node)
    #     pass
    #
    # def depart_desc_addname(self, node):
    #     pass

    def visit_desc_type(self, node):
        # self.log_unknown("desc_type", node)
        pass

    def depart_desc_type(self, node):
        pass

    def visit_desc_returns(self, node):
        self.add_text(' -> ')

    def depart_desc_returns(self, node):
        pass

    def visit_desc_parameterlist(self, node):
        self.add_text('(')
        self.first_param = 1

    def depart_desc_parameterlist(self, node):
        self.add_text(')')

    def visit_desc_parameter(self, node):
        if not self.first_param:
            self.add_text(', ')
        else:
            self.first_param = 0
        self.add_text(node.astext())
        raise nodes.SkipNode

    def visit_desc_optional(self, node):
        self.add_text('[')

    def depart_desc_optional(self, node):
        self.add_text(']')

    def visit_desc_annotation(self, node):
        content = node.astext()
        if len(content) > MAXWIDTH:
            h = int(MAXWIDTH / 3)
            content = content[:h] + " ... " + content[-h:]
            self.add_text(content)
            raise nodes.SkipNode

    def depart_desc_annotation(self, node):
        pass

    # def visit_refcount(self, node):
    #     pass
    #
    # def depart_refcount(self, node):
    #     pass

    def visit_desc_content(self, node):
        self.new_state(self.indent)

    def depart_desc_content(self, node):
        self.end_state()

    def visit_figure(self, node):
        print(node)
        self.new_state(self.indent)

    def depart_figure(self, node):
        self.end_state()

    #
    def depart_image(self, node):
        self.end_state()

    def visit_caption(self, node):
        # self.log_unknown("caption", node)
        pass

    def depart_caption(self, node):
        pass

    def visit_productionlist(self, node):
        self.new_state(self.indent)
        names = []
        for production in node:
            names.append(production['tokenname'])
        maxlen = max(len(name) for name in names)
        lastname = ''
        for production in node:
            if production['tokenname']:
                self.add_text(production['tokenname'].ljust(maxlen) + ' ::=')
                lastname = production['tokenname']
            else:
                self.add_text('%s    ' % (' ' * len(lastname)))
            self.add_text(production.astext() + self.nl)
        self.end_state(wrap=False)
        raise nodes.SkipNode

    def visit_seealso(self, node):
        self.new_state(self.indent)

    def depart_seealso(self, node):
        self.end_state(first='')

    def visit_footnote(self, node):
        self._footnote = node.children[0].astext().strip()
        self.new_state(len(self._footnote) + self.indent)

    def depart_footnote(self, node):
        self.end_state(first='[%s] ' % self._footnote)

    def visit_citation(self, node):
        if len(node) and isinstance(node[0], nodes.label):
            self._citlabel = node[0].astext()
        else:
            self._citlabel = ''
        self.new_state(len(self._citlabel) + self.indent)

    def depart_citation(self, node):
        self.end_state(first='[%s] ' % self._citlabel)

    def visit_label(self, node):
        raise nodes.SkipNode

    # TODO: option list could use some better styling

    def visit_option_list(self, node):
        # self.log_unknown("option_list", node)
        pass

    def depart_option_list(self, node):
        pass

    def visit_option_list_item(self, node):
        self.new_state(0)

    def depart_option_list_item(self, node):
        self.end_state()

    def visit_option_group(self, node):
        self._firstoption = True

    def depart_option_group(self, node):
        self.add_text('     ')

    def visit_option(self, node):
        if self._firstoption:
            self._firstoption = False
        else:
            self.add_text(', ')

    def depart_option(self, node):
        pass

    # def visit_option_string(self, node):
    #     pass
    #
    # def depart_option_string(self, node):
    #     pass

    def visit_option_argument(self, node):
        self.add_text(node['delimiter'])

    def depart_option_argument(self, node):
        pass

    # def visit_description(self, node):
    #     # self.log_unknown("description", node)
    #     pass
    #
    # def depart_description(self, node):
    #     pass

    def visit_tabular_col_spec(self, node):
        raise nodes.SkipNode

    def visit_colspec(self, node):
        self.table[0].append(round(node['colwidth']))
        raise nodes.SkipNode

    def visit_tgroup(self, node):
        # self.log_unknown("tgroup", node)
        pass

    def depart_tgroup(self, node):
        pass

    def visit_thead(self, node):
        # self.log_unknown("thead", node)
        pass

    def depart_thead(self, node):
        pass

    def visit_tbody(self, node):
        self.table.append('sep')

    def depart_tbody(self, node):
        pass

    def visit_row(self, node):
        self.table.append([])

    def depart_row(self, node):
        pass

    def visit_entry(self, node):
        if 'morerows' in node or 'morecols' in node:
            log_warning('Column or row spanning cells are not implemented.')
        self.new_state(0)

    def depart_entry(self, node):
        text = self.nl.join(self.nl.join(x[1]) for x in self.states.pop())
        self.stateindent.pop()
        self.table[-1].append(text)

    def visit_table(self, node):
        # TODO MAYA tbale
        if self.table:
            log_warning('Nested tables are not supported.')
        self.new_state(0)
        self.table = [[]]

    def depart_table(self, node):
        # TODO Maya CONVERT TABLE
        lines = self.table[1:]
        fmted_rows = []
        colwidths = self.table[0]
        realwidths = colwidths[:]
        separator = 0
        # don't allow paragraphs in table cells for now
        for line in lines:
            if line == 'sep':
                separator = len(fmted_rows)
            else:
                cells = []
                for i, cell in enumerate(line):
                    par = self.wrap(cell, width=colwidths[i])
                    if par:
                        maxwidth = max(list(map(len, par)))
                    else:
                        maxwidth = 0
                    realwidths[i] = max(realwidths[i], maxwidth)
                    cells.append(par)
                fmted_rows.append(cells)

        def writesep(char='-'):
            out = ['+']
            for width in realwidths:
                out.append(char * (width + 2))
                out.append('+')
            self.add_text(''.join(out) + self.nl)

        def writerow(row):
            lines_tmp = list(zip(*row))
            for line_tmp in lines_tmp:
                out = ['|']
                for i_t, cell_tmp in enumerate(line_tmp):
                    if cell_tmp:
                        out.append(' ' + cell_tmp.ljust(realwidths[i_t] + 1))
                    else:
                        out.append(' ' * (realwidths[i_t] + 2))
                    out.append('|')
                self.add_text(''.join(out) + self.nl)

        for i, row in enumerate(fmted_rows):
            if separator and i == separator:
                writesep('=')
            else:
                writesep('-')
            writerow(row)
        writesep('-')
        self.table = None
        self.end_state(wrap=False)

    # def visit_acks(self, node):
    #     self.new_state(0)
    #     self.add_text(', '.join(n.astext() for n in node.children[0].children)
    #                   + '.')
    #     self.end_state()
    #     raise nodes.SkipNode

    def visit_image(self, node):
        # TODO Maya this does not function
        self.new_state(0)
        if 'uri' in node:
            self.add_text(_('.. image:: %s') % self.check_cross_referencing_escape_uri(node['uri']))
        elif 'target' in node.attributes:
            self.add_text(_('.. image: %s') % node['target'])
        elif 'alt' in node.attributes:
            self.add_text(_('[image: %s]') % node['alt'])
        else:
            self.add_text(_('[image]'))
        self.end_state(wrap=False)
        raise nodes.SkipNode

    def visit_transition(self, node):
        indent = sum(self.stateindent)
        self.new_state(0)
        self.add_text('=' * (MAXWIDTH - indent))
        self.end_state()
        raise nodes.SkipNode

    def visit_bullet_list(self, node):
        def bullet_list_format(counter):
            return '*'

        self.list_counter.append(-1)  # TODO: just 0 is fine.
        self.list_formatter.append(bullet_list_format)

    def depart_bullet_list(self, node):
        self.list_counter.pop()
        self.list_formatter.pop()

    def visit_enumerated_list(self, node):
        def enumerated_list_format(counter):
            return str(counter) + '.'

        self.list_counter.append(0)
        self.list_formatter.append(enumerated_list_format)

    def depart_enumerated_list(self, node):
        self.list_counter.pop()
        self.list_formatter.pop()

    def visit_list_item(self, node):
        self.list_counter[-1] += 1
        bullet_formatter = self.list_formatter[-1]
        bullet = bullet_formatter(self.list_counter[-1])
        indent = max(self.indent, len(bullet) + 1)
        self.new_state(indent)

    def depart_list_item(self, node):
        # formatting to make the string `self.stateindent[-1]` chars long.
        format_tmp = '%%-%ds' % (self.stateindent[-1])
        bullet_formatter = self.list_formatter[-1]
        bullet = format_tmp % bullet_formatter(self.list_counter[-1])
        self.end_state(first=bullet, end=None)

    def visit_definition_list(self, node):
        pass

    def depart_definition_list(self, node):
        pass

    def visit_definition_list_item(self, node):
        self._li_has_classifier = len(node) >= 2 and \
                                  isinstance(node[1], nodes.classifier)

    def depart_definition_list_item(self, node):
        pass

    def visit_term(self, node):
        self.new_state(0)

    def depart_term(self, node):
        if not self._li_has_classifier:
            self.end_state(end=None)

    def visit_termsep(self, node):
        self.add_text(', ')
        raise nodes.SkipNode

    def visit_classifier(self, node):
        self.add_text(' : ')

    def depart_classifier(self, node):
        self.end_state(end=None)

    def visit_definition(self, node):
        self.new_state(self.indent)

    def depart_definition(self, node):
        self.end_state()

    # def visit_field_list(self, node):
    #     # self.log_unknown("field_list", node)
    #     pass
    #
    # def depart_field_list(self, node):
    #     pass

    def visit_field(self, node):
        self.new_state(0)

    def depart_field(self, node):
        self.end_state(end=None)

    def visit_field_name(self, node):
        self.add_text(':')

    def depart_field_name(self, node):
        self.add_text(':')
        content = node.astext()
        self.add_text((16 - len(content)) * ' ')

    def visit_field_body(self, node):
        self.new_state(self.indent)

    def depart_field_body(self, node):
        self.end_state()

    # def visit_centered(self, node):
    #     pass
    #
    # def depart_centered(self, node):
    #     pass
    #
    # def visit_hlist(self, node):
    #     # self.log_unknown("hlist", node)
    #     pass
    #
    # def depart_hlist(self, node):
    #     pass
    #
    # def visit_hlistcol(self, node):
    #     pass
    #
    # def depart_hlistcol(self, node):
    #     pass

    def visit_admonition(self, node):
        self.new_state(0)

    def depart_admonition(self, node):
        self.end_state()

    def _visit_admonition(self, node):
        self.new_state(self.indent)

    def _make_depart_admonition(name):
        def depart_admonition(node):
            self.end_state(first=admonitionlabels[name] + ': ')

        return depart_admonition

    visit_attention = _visit_admonition
    depart_attention = _make_depart_admonition('attention')
    visit_caution = _visit_admonition
    depart_caution = _make_depart_admonition('caution')
    visit_danger = _visit_admonition
    depart_danger = _make_depart_admonition('danger')
    visit_error = _visit_admonition
    depart_error = _make_depart_admonition('error')
    visit_hint = _visit_admonition
    depart_hint = _make_depart_admonition('hint')
    visit_important = _visit_admonition
    depart_important = _make_depart_admonition('important')
    visit_note = _visit_admonition
    depart_note = _make_depart_admonition('note')
    visit_tip = _visit_admonition
    depart_tip = _make_depart_admonition('tip')
    visit_warning = _visit_admonition
    depart_warning = _make_depart_admonition('warning')

    def visit_versionmodified(self, node):
        self.new_state(0)

    def depart_versionmodified(self, node):
        self.end_state()

    def visit_literal_block(self, node):
        print("visit_literal_block")
        print(node)
        print(type(node))
        # TODO Maya here later for comparison between coding sections translation vs original
        is_image_block = False
        is_figure_block = False
        if 'image' in node.get('classes', []):
            is_image_block = True
            print(node.get('href'))
            print('&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&')
        if 'figure' in node.get('classes', []):
            print('&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&')
            print(node.get('href'))

            is_figure_block = True

        is_code_block = False
        # Support for Sphinx < 2.0, which defines classes['code', 'language']
        if 'code' in node.get('classes', []):
            is_code_block = True
            if node.get('language', 'default') == 'default' and len(node['classes']) >= 2:
                node['language'] = node['classes'][1]
        # highlight_args is the only way to distinguish between :: and .. code:: in Sphinx 2 or higher.
        if node.get('highlight_args') is not None:
            is_code_block = True
        if is_code_block:
            if node.get('language', 'default') == 'default':
                directive = ".. code::"
            else:
                # TODO Maya hier code shell_session warning
                lang = node['language']
                if node['language'] == 'shell_session' or node['language'] == 'bash_session':
                    lang = 'bash'
                    node['language'] = lang
                directive = ".. code:: %s" % lang
            if node.get('linenos'):
                indent = self.indent * ' '
                directive += "%s%s:number-lines:" % (self.nl, indent)
            # else:
            #     directive = "::"
            self.new_state(0)
            self.add_text(directive)
            self.end_state(wrap=False)
            self.new_state(self.indent)
        else:

            self.new_state(0)

    def depart_literal_block(self, node):
        print(node)
        self.end_state(wrap=False)

    def visit_doctest_block(self, node):
        print(node)
        self.new_state(0)

    def depart_doctest_block(self, node):
        print(node)
        self.end_state(wrap=False)

    def visit_line_block(self, node):
        print(node)
        self.new_state(0)

    def depart_line_block(self, node):
        print("depart_line_block")
        print(node)
        self.end_state(wrap=False)

    def visit_line(self, node):
        # self.log_unknown("line", node)
        print(node)
        pass

    def depart_line(self, node):
        print(node)
        pass

    def visit_block_quote(self, node):
        print("visit_block_quote")
        print(node)
        self.new_state(self.indent)

    def depart_block_quote(self, node):
        print("depart_block_quote")
        print(node)
        self.end_state()

    def visit_compact_paragraph(self, node):
        print(node)
        self.visit_paragraph(node)

    def depart_compact_paragraph(self, node):
        print(node)
        self.depart_paragraph(node)

    def visit_paragraph(self, node):
        print(node)
        if not isinstance(node.parent, nodes.Admonition) or \
                isinstance(node.parent, addnodes.seealso):
            self.new_state(0)

    def depart_paragraph(self, node):
        if not isinstance(node.parent, nodes.Admonition) or \
                isinstance(node.parent, addnodes.seealso):
            self.end_state()

    def visit_target(self, node):
        print(node)
        is_inline = node.parent.tagname in ('paragraph',)
        if is_inline or node.get('anonymous'):
            return
        refid = node.get('refid')
        # refuri = node.get('refuri')
        if refid:
            self.new_state(0)
            if node.get('ids'):
                self.add_text(self.nl.join(
                    '.. _%s: %s_' % (id_tmp, refid) for id_tmp in node['ids']
                ))
            else:
                self.add_text('.. _' + node['refid'] + ':')
            self.end_state(wrap=False)
        raise nodes.SkipNode

    def depart_target(self, node):
        print(node)
        pass

    def visit_index(self, node):
        print(node)
        raise nodes.SkipNode

    def visit_substitution_definition(self, node):
        print("subst", node)
        print(node.children)
        if len(node)==1:
            child_tmp = node.children[0]
            if isinstance(child_tmp, nodes.reference):
                refuri = child_tmp.get('refuri')
                self.add_text(_('|%s| image:: %s') % (refuri[refuri.rfind('/') + 1:len(refuri)], refuri))
        raise nodes.SkipNode

    def depart_substitution_definition(self, node):
        print(node)
        raise nodes.SkipNode

    # def visit_pending_xref(self, node):
    #     print(node)
    #     pass
    #
    # def depart_pending_xref(self, node):
    #     print(node)
    #     pass

    def visit_reference(self, node):
        print(node)
        print(type(node))
        # TODO Maya debug

        refname = node.get('name')
        refbody = node.astext()
        refuri = node.get('refuri')
        refid = node.get('refid')

        if node.get('anonymous'):
            underscore = '__'
        else:
            underscore = '_'
        if not refname:
            refname = refbody

        if refid:
            print('@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ REFID @@@@@@@@@@@@@@@@@@@@@@@')
            if refid == self.document.nameids.get(fully_normalize_name(refname)):
                self.add_text('`%s`%s' % (refname, underscore))
            else:
                self.add_text('`%s <%s_>`%s' % (refname, refid, underscore))
            raise nodes.SkipNode
        elif refuri:
            if refuri == refname:
                self.add_text(self.check_cross_referencing_escape_uri(refuri))
            else:
                role = get_cross_referencing_role(refuri)
                ref_tmp = self.check_cross_referencing_escape_uri(refuri)
                if refuri.startswith('/attachment') and "png" in refuri:
                    self.add_text(_('|%s| image:: %s') % (refuri[refuri.rfind('/') + 1:len(refuri)], refuri))
                    return
                if role == ':doc:' or role == ':ref:':
                    underscore = ''
                if role == ':ref:' and ref_tmp.startswith('/'):
                    ref_tmp = ref_tmp[1:len(ref_tmp)]
                if role == 'inline-section':
                    underscore = '_'
                    self.add_text('`%s`%s' % (ref_tmp, underscore))
                else:
                    uri = self.check_cross_referencing_escape_uri(refuri)
                    if role == ':ref:':
                        uri = uri.lstrip('/')
                    self.add_text(
                        '%s`%s <%s>`%s' % (role, refname, uri, underscore))
            print('raise2')
            raise nodes.SkipNode

    def get_path_from_md_internal_mapping(self, perm, map='doc'):
        path = ''
        if map is 'doc':
            perm_mappings = self.md_doc_permalinks_and_redirects_to_filepath_map
        if map is 'pages':
            perm_mappings = self.md_pages_permalinks_and_redirects_to_filepath_map
        if perm in perm_mappings.keys():
            path = perm_mappings[perm]
        elif perm + '/' in perm_mappings.keys():
            path = perm_mappings[perm + '/']
        elif perm[0:len(perm) - 1] in perm_mappings.keys():
            path = perm_mappings[perm[0:len(perm) - 1]]
        return path

    def check_cross_referencing_escape_uri(self, uri: str) -> str:
        if uri.startswith('#'):
            # inline section
            section = uri[uri.index('#') + 1:len(uri)]
            uri = section.replace('-', ' ').replace('#', '')
        if '#' in uri and uri.startswith('/') and not uri.startswith('/attachment'):
            # sections
            # perm_match = uri
            perm = uri[0:uri.index('#')]
            section = uri[uri.index('#') + 1:len(uri)]
            internal_section = section.replace('#', '')
            if internal_section == 'how-to-guides':
                internal_section = 'how-to guides'
            elif internal_section not in (
            'qubes-devel', 'qubes-users', 'qubes-announce', 'qubes-project', 'qubes-translation'):
                internal_section = internal_section.replace('-', ' ')
            if perm in DOC_BASE_PATH:
                uri = 'index:' + internal_section
            elif perm.startswith('/news/'):
                uri = BASE_SITE + uri[1:len(uri)]
            else:
                path = self.get_path_from_md_internal_mapping(perm, 'pages')
                if len(path) > 0:
                    uri = replace_page_aux(uri, path)
                else:
                    path = self.get_path_from_md_internal_mapping(perm, 'doc')
                    if len(path) > 0:
                        uri = path + ':' + internal_section
            # print('sections')
            # print(uri)
        elif '/attachment/' in uri and '.pdf' in uri:
            to_replace = uri[uri.find('/'):uri.rfind('/') + 1]
            uri = uri.replace(to_replace, '/_static/')
        elif uri in INTERNAL_BASE_PATH:
            uri = BASE_SITE
        elif uri.startswith('/news/'):
            uri = BASE_SITE + uri[1:len(uri)]
        elif uri in DOC_BASE_PATH:
            uri = '/index'
        elif uri in FEED_XML:
            uri = BASE_SITE + FEED_XML[1:len(FEED_XML)]
        elif uri in self.md_pages_permalinks_and_redirects_to_filepath_map.keys():
            path = self.md_pages_permalinks_and_redirects_to_filepath_map[uri]
            uri = get_url(path)
        elif uri + '/' in self.md_pages_permalinks_and_redirects_to_filepath_map.keys():
            path = self.md_pages_permalinks_and_redirects_to_filepath_map[uri + '/']
            uri = get_url(path)
        elif uri[0:len(uri) - 1] in self.md_pages_permalinks_and_redirects_to_filepath_map.keys():
            path = self.md_pages_permalinks_and_redirects_to_filepath_map[uri[0:len(uri) - 1]]
            uri = get_url(path)
        elif uri.startswith('/') and not uri.startswith('/attachment'):
            # print('doc')
            # print(uri)
            tmp_uri = self.get_path_from_md_internal_mapping(uri)
            # print(uri)
            if len(tmp_uri) == 0:
                logger.debug('nothing found')
            else:
                uri = tmp_uri
        elif uri.endswith('_'):
            logger.debug('ends with uri %s', uri)
            uri = uri[:-1] + '\\_'
        else:
            logger.debug(uri)
            logger.debug("NOTHING should be refactored AGAIN")
        return uri

    def depart_reference(self, node):
        print(node)
        pass

    # def visit_download_reference(self, node):
    #     pass
    #
    # def depart_download_reference(self, node):
    #     pass

    def visit_emphasis(self, node):
        print(node)
        self.add_text('*')

    def depart_emphasis(self, node):
        print(node)
        self.add_text('*')

    def visit_literal_emphasis(self, node):
        print(node)
        self.add_text('*')

    def depart_literal_emphasis(self, node):
        print(node)
        self.add_text('*')

    def visit_strong(self, node):
        print(node)
        self.add_text('**')

    def depart_strong(self, node):
        print(node)
        self.add_text('**')

    def visit_abbreviation(self, node):
        print(node)
        self.add_text('')

    def depart_abbreviation(self, node):
        print(node)
        if node.hasattr('explanation'):
            self.add_text(' (%s)' % node['explanation'])

    def visit_title_reference(self, node):
        print(node)
        self.add_text('*')

    def depart_title_reference(self, node):
        print(node)
        self.add_text('*')

    def visit_literal(self, node):
        print(node)
        self.add_text('``')

    def depart_literal(self, node):
        print(node)
        self.add_text('``')

    def visit_subscript(self, node):
        print(node)
        self.add_text(':sub:`')

    def depart_subscript(self, node):
        print(node)
        self.add_text('`')

    def visit_superscript(self, node):
        print(node)
        self.add_text(':sup:`')

    def depart_superscript(self, node):
        print(node)
        self.add_text('`')

    # def visit_footnote_reference(self, node):
    #     print(node)
    #     self.add_text('[%s]' % node.astext())
    #     raise nodes.SkipNode
    #
    # def visit_citation_reference(self, node):
    #     print(node)
    #     self.add_text('[%s]' % node.astext())
    #     raise nodes.SkipNode

    def visit_math_block(self, node):
        print(node)
        self.add_text(".. math::")
        self.new_state(self.indent)

    def depart_math_block(self, node):
        print(node)
        self.end_state(wrap=False)

    def visit_math(self, node):
        print(node)
        self.add_text(".. math::")
        self.new_state(self.indent)

    def depart_math(self, node):
        print(node)
        self.end_state(wrap=False)

    def visit_code_block(self, node):
        print(node)
        print("visit_code_block")
        print(node)
        self.new_state(self.indent)

    def visit_Text(self, node):
        print(node)
        self.add_text(node.astext())

    def depart_Text(self, node):
        print(node)
        pass

    def visit_inline(self, node):
        print(node)
        pass

    def depart_inline(self, node):
        print(node)
        pass

    #
    def visit_problematic(self, node):
        print('2385785873')
        print(node)
        pass

    def depart_problematic(self, node):
        print(node)
        pass

    def visit_system_message(self, node):
        print(node)
        self.new_state(0)
        # TODO ERRROR MESSAGES
        self.add_text('[ERROR MESSAGE: %s]' % node.astext())
        self.end_state()
        raise nodes.SkipNode

    def visit_comment(self, node):
        print(node)
        raise nodes.SkipNode

    # def visit_meta(self, node):
    #     print(node)
    #     raise nodes.SkipNode

    def visit_raw(self, node):
        print(node)
        if 'text' in node.get('format', '').split():
            self.body.append(node.astext())
        raise nodes.SkipNode

    # def visit_docinfo(self, node):
    #     print(node)
    #     raise nodes.SkipNode
    def visit_substitution_reference(self, node):
        print(node)
        print("****")
        refname = node.get('refname')
        self.add_text(_('|%s|') % (refname))
        raise nodes.SkipNode

    def depart_substitution_reference(self, node):
        pass
    # def unknown_visit(self, node):
    #     print(node)
    #     print("unknown_visit end")
    #     self.add_text('[UNKOWN NODE %s]' % node.astext())
    #     log_unknown(node.__class__.__name__, node)
    #
    # def unknown_departure(self, node):
    #     print(node)
    #     pass

    # default_visit = unknown_visit


# noinspection PyBroadException,PyAttributeOutsideInit,PyUnresolvedReferences
class RstBuilder():
    name = 'rst'
    format = 'rst'
    file_suffix = '.rst'
    link_suffix = None  # defaults to file_suffix
    config = {
        # general options
        'project': ('Python', 'env', []),
        'author': ('unknown', 'env', []),
        'project_copyright': ('', 'html', [str]),
        'copyright': (lambda c: c.project_copyright, 'html', [str]),
        'version': ('', 'env', []),
        'release': ('', 'env', []),
        'today': ('', 'env', []),
        # the real default is locale-dependent
        'today_fmt': (None, 'env', [str]),

        'language': (None, 'env', [str]),
        'locale_dirs': (['locales'], 'env', []),
        'figure_language_filename': ('{root}.{language}{ext}', 'env', [str]),
        'gettext_allow_fuzzy_translations': (False, 'gettext', []),

        'master_doc': ('index', 'env', []),
        'root_doc': (lambda config: config.master_doc, 'env', []),
        'source_suffix': ({'.rst': 'restructuredtext'}, 'env', any),
        'source_encoding': ('utf-8-sig', 'env', []),
        'exclude_patterns': ([], 'env', []),
        'default_role': (None, 'env', [str]),
        'add_function_parentheses': (True, 'env', []),
        'add_module_names': (True, 'env', []),
        'trim_footnote_reference_space': (False, 'env', []),
        'show_authors': (False, 'env', []),
        'pygments_style': (None, 'html', [str]),
        'highlight_language': ('default', 'env', []),
        'highlight_options': ({}, 'env', []),
        'templates_path': ([], 'html', []),
        'template_bridge': (None, 'html', [str]),
        'keep_warnings': (False, 'env', []),
        'suppress_warnings': ([], 'env', []),
        'modindex_common_prefix': ([], 'html', []),
        'rst_epilog': (None, 'env', [str]),
        'rst_prolog': (None, 'env', [str]),
        'trim_doctest_flags': (True, 'env', []),
        'primary_domain': ('py', 'env', [None]),
        'needs_sphinx': (None, None, [str]),
        'needs_extensions': ({}, None, []),
        'manpages_url': (None, 'env', []),
        'nitpicky': (False, None, []),
        'nitpick_ignore': ([], None, []),
        'nitpick_ignore_regex': ([], None, []),
        'numfig': (False, 'env', []),
        'numfig_secnum_depth': (1, 'env', []),
        'numfig_format': ({}, 'env', []),  # will be initialized in init_numfig_format()

        'math_number_all': (False, 'env', []),
        'math_eqref_format': (None, 'env', [str]),
        'math_numfig': (True, 'env', []),
        'tls_verify': (True, 'env', []),
        'tls_cacerts': (None, 'env', []),
        'user_agent': (None, 'env', [str]),
        'smartquotes': (True, 'env', []),
        'smartquotes_action': ('qDe', 'env', []),
        'smartquotes_excludes': ({'languages': ['ja'],
                                  'builders': ['man', 'text']},
                                 'env', []),
        'text_newlines': ('\n', 'env', [str]),
    }

    def init(self):
        """Load necessary templates and perform initialization."""

        # if self.config.rst_file_suffix is not None:
        #     self.file_suffix = .config.rst_file_suffix
        # if self.config.rst_link_suffix is not None:
        #     self.link_suffix = self.config.rst_link_suffix
        # elif self.link_suffix is None:
        #     self.link_suffix = self.file_suffix

        # Function to convert the docname to a reST file name.
        def file_transform(docname):
            return docname + '.rst'
            # return docname + self.file_suffix

        # Function to convert the docname to a relative URI.
        def link_transform(docname):
            # generated reST files. The default is ".rst". rst_link_suffix, Suffix for generated links to reST files.
            # The default is whatever rst_file_suffix is set to. rst_file_transform,
            return docname + '.rst'
            # return docname + self.link_suffix

        if self.config.rst_file_transform is not None:
            self.file_transform = self.config.rst_file_transform
        else:
            self.file_transform = file_transform
        if self.config.rst_link_transform is not None:
            self.link_transform = self.config.rst_link_transform
        else:
            self.link_transform = link_transform

    def get_outdated_docs(self):
        """
        Return an iterable of input files that are outdated.
        """
        # This method is taken from TextBuilder.get_outdated_docs()
        # with minor changes to support :confval:`rst_file_transform`.
        for docname in self.env.found_docs:
            if docname not in self.env.all_docs:
                yield docname
                continue
            sourcename = os.path.join(self.env.srcdir, docname +
                                      self.file_suffix)
            targetname = os.path.join(self.outdir, self.file_transform(docname))
            # print (sourcename, targetname)

            try:
                targetmtime = os.path.getmtime(targetname)
            except Exception:
                targetmtime = 0
            try:
                srcmtime = os.path.getmtime(sourcename)
                if srcmtime > targetmtime:
                    yield docname
            except EnvironmentError:
                # source doesn't exist anymore
                pass

    def get_target_uri(self, docname, typ=None):
        return self.link_transform(docname)

    def prepare_writing(self, docnames):
        self.writer = QubesRstWriter(self)

    def write_doc(self, docname, doctree):
        # TODO Maya delete
        # This method is taken from TextBuilder.write_doc()
        # with minor changes to support :confval:`rst_file_transform`.
        destination = StringOutput(encoding='utf-8')
        # print "write(%s,%s)" % (type(doctree), type(destination))

        self.writer.write(doctree, destination)
        outfilename = '/tmp/bla.rst'
        # outfilename = path.join(self.outdir, self.file_transform(docname))
        # print "write(%s,%s) -> %s" % (type(doctree), type(destination), outfilename)
        ensuredir(os.path.dirname(outfilename))
        try:
            f = codecs.open(outfilename, 'w', 'utf-8')
            try:
                f.write(self.writer.output)
            finally:
                f.close()
        except (IOError, OSError) as err:
            self.warn("error writing file %s: %s" % (outfilename, err))

    def finish(self):
        pass
