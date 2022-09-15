# redacted from https://github.com/sphinx-contrib/restbuilder
import codecs
import logging
import os
import sys
import textwrap
from logging import basicConfig, getLogger, DEBUG

import docutils
from docutils import nodes, writers
from docutils.io import StringOutput
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


def get_path_from(perm, mapping):
    path = ''
    if perm in mapping.keys():
        path = mapping[perm]
    elif perm + '/' in mapping.keys():
        path = mapping[perm + '/']
    elif perm[0:len(perm) - 1] in mapping.keys():
        path = mapping[perm[0:len(perm) - 1]]
    return path


def replace_page_aux(perm_match, path):
    return BASE_SITE + path + '/' + perm_match[perm_match.index('#'):len(perm_match)] if not path.startswith(
        '/') else BASE_SITE[0:len(BASE_SITE) - 1] + path + '/' + perm_match[perm_match.index('#'):len(perm_match)]


SPACE = ' '
CODE_BLOCK_IDENT = SPACE * STDINDENT * 2
LIST_ITEM_IDENT = SPACE * STDINDENT


def is_c_code_block(codestr):
    return ' while(' in codestr or ' for(' in codestr or \
           ' while (' in codestr or ' for (' in codestr or \
           ' #if ' in codestr or ' #endif ' in codestr or \
           ' int ' in codestr or ' struct ' in codestr


def is_node_a_code_block(parent):
    return isinstance(parent, docutils.nodes.literal_block) and parent.hasattr('language') or parent.hasattr(
        'classes') and 'code' in parent['classes']


# noinspection PyPep8Naming,PyMethodMayBeStatic
def is_shell_code_block(node):
    return "shell_session" in node or "bash_session" in node


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
        self.body = ""
        self.document = document
        self.builder = builder
        self.title_count = 0
        self.section_count = 0
        self.enumerated_count = 0
        self.enumerated_lists_count = 0

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

    def get_cross_referencing_role(self, uri):
        role = ''
        if uri.startswith('/news'):
            role = ''
        elif uri.startswith('/') and '#' in uri and not uri.startswith('/attachment'):
            role = ':ref:'
        elif uri.startswith('/') and not uri.startswith(
                '/attachment') and uri not in self.external_redirects_mappings.keys():
            role = ':doc:'
        elif BASE_SITE in uri:
            role = ''

        return role

    def wrap(self, text, width=MAXWIDTH):
        self.wrapper.width = width
        return self.wrapper.wrap(text)

    def visit_document(self, node):
        # print(node)
        pass

    def depart_document(self, node):
        # print(node.astext())
        pass

    def visit_block_quote(self, node):
        print(node)
        pass

    def depart_block_quote(self, node):
        print(node)
        pass

    def visit_comment(self, node):
        print(node)
        pass

    def depart_comment(self, node):
        print(node)
        pass

    def visit_system_message(self, node):
        # print(node)
        self.body += 'SYSTEM MESSAGE  for: ' + node.astext()
        pass

    def depart_system_message(self, node):
        print(node)
        pass

    def visit_literal(self, node):
        self.body += ' ``'
        pass

    def depart_literal(self, node):
        self.body += '`` '
        pass

    def visit_literal_block(self, node):
        print(node)
        print(node.attributes)
        # if node['classes'] in ['code bash', 'code shell']:
        #     print(node)

        # if only children with the baove classes fix for last code block in qubes-builder
        # children = node.children
        # classes = [i.__class__.__name__ for i in children]
        # if is_node_a_code_block(node) and set(classes) == set('inline', 'Text'):
        #     self.body += self.get_code_text_block(node.astext())
        #     pass

        if node.hasattr('xml:space'):
            astext = node.astext()
            if is_shell_code_block(astext):
                for i in ['shell_session', 'bash_session', '.. code::']:
                    code_section = astext.replace(i, '')
                    code_section = code_section.lstrip()
                    self.body += self.nl + self.get_code_text_block(code_section)
                    raise nodes.SkipNode
            if is_c_code_block(astext):
                node['language'] = 'c'
                self.body += self.nl + '.. code:: c' + self.nl + self.nl  # + SPACE * STDINDENT * 2
            elif not node.hasattr('language'):
                node['language'] = 'bash'
                self.body += self.nl + '.. code:: bash' + self.nl + self.nl  # + SPACE * STDINDENT * 2
            elif node['language'] in ["shell_session", "bash_session"]:
                node['language'] = 'bash'
                self.body += self.nl + '.. code:: bash' + self.nl + self.nl
                # + SPACE * STDINDENT * 2
            else:
                self.body += self.nl + '.. code:: ' + node['language'] + self.nl + self.nl \
                    # + SPACE * STDINDENT * 2

        pass

    def depart_literal_block(self, node):
        print("depart")
        # print(node)
        self.body += self.nl + self.nl
        pass

    # def visit_target(self, node):
    #     pass
    # def depart_target(self, node):elf,
    #     pass
    def visit_subsection(self, node):
        print(node)
        pass

    def visit_section(self, node):
        print(node)
        pass

    def depart_section(self, node):
        self.section_count += 1
        print(node)
        pass

    # def depart_section(self, node):
    #     pass
    def visit_title(self, node):
        parent = node.parent
        # subsections TODO
        if self.title_count == 0:
            self.body += '=' * len(node.astext()) + self.nl
        else:
            self.body += self.nl
        pass

    def depart_title(self, node):
        # self.body += node.astext() + self.nl
        parent = node.parent
        if self.title_count >= 0 or isinstance(parent, docutils.nodes.section):
            self.body += self.nl + '=' * len(node.astext()) + self.nl + self.nl
        self.title_count += 1
        pass

    def visit_line_block(self, node):
        print("line 123")
        print(node)
        pass

    def visit_Text(self, node):
        print('visit text')
        parent = node.parent
        if is_node_a_code_block(parent):
            self.body += CODE_BLOCK_IDENT
        print(node)  # Qubes ISO building
        # print(node.parent) #<title>Qubes ISO building</title>
        pass

    def get_code_text_block(self, nodeasstr):
        x = nodeasstr.splitlines()
        ident = self.nl + CODE_BLOCK_IDENT
        return ident.join(x)

    def get_list_item_ident(self, nodeasstr):
        x = nodeasstr.splitlines()
        ident = self.nl + LIST_ITEM_IDENT
        return ident.join(x)

    def depart_Text(self, node):
        print('depart text')
        parent = node.parent
        print(type(parent))
        print(node)  # Qubes ISO building
        if is_node_a_code_block(parent):
            self.body += self.get_code_text_block(node.astext())
        else:
            self.body += node.astext().lstrip()
        pass

    def visit_enumerated_list(self, node):
        print(node)
        if self.enumerated_lists_count > 2:
            logger.debug('no more verschlachtelung')
            self.visit_system_message(node)
        self.enumerated_lists_count += 1
        pass

    def depart_enumerated_list(self, node):
        print(node)
        self.enumerated_lists_count -= 1
        self.enumerated_count = 0
        self.body += self.nl
        pass

    def visit_bullet_list(self, node):
        print(node)
        self.body += self.nl
        pass

    def depart_bullet_list(self, node):
        print(node)
        self.body += self.nl + self.nl
        pass

    def visit_list_item(self, node):
        parent = node.parent
        if isinstance(parent, docutils.nodes.bullet_list):
            self.body += '-  '
        if isinstance(parent, docutils.nodes.enumerated_list):
            self.enumerated_count += 1
            self.body += self.nl + str(self.enumerated_count) + '.' + SPACE
        print(node)
        pass

    def depart_list_item(self, node):
        parent = node.parent
        print(node)
        if isinstance(parent, docutils.nodes.bullet_list):
            self.body += self.nl
        pass

    def visit_inline(self, node):
        parent = node.parent
        if is_node_a_code_block(parent) and node.hasattr('classes') and 'single' in node['classes']:
            self.body += self.nl + CODE_BLOCK_IDENT  # + self.get_code_text_block(node.astext())
        print(node)

        pass

    def depart_inline(self, node):
        print(node)
        pass

    def visit_paragraph(self, node):
        parent = node.parent
        if not isinstance(parent, docutils.nodes.list_item):
            self.body += self.nl
        # print(node)
        pass

    def depart_paragraph(self, node):
        self.body += self.nl
        pass

    # def visit_role(self, node):
    #     print(node)
    #     pass

    def visit_refui(self, node):
        t = 'd'
        pass

    def visit_Refuri(self, node):
        t = 'd'
        pass

    def visit_reference(self, node):
        refname = node.get('name')
        refbody = node.astext()
        refid = node.get('refid')
        refuri = node.get('refuri')
        if refname is None and refuri.startswith('http'):
            # the case of license.rst and markdown link with qubes os have to be converted manually
            # perhaps with the bash skript TODO
            pass
        else:
            role = self.get_cross_referencing_role(refuri)
            self.body += SPACE + role + '`'
        pass

    def depart_reference(self, node):
        refname = node.get('name')
        refuri = node.get('refuri')
        if refname is None and refuri.startswith('http'):
            # the case of license.rst and markdown link with qubes os have to be converted manually
            # perhaps with the bash skript TODO
            pass
            # raise nodes.SkipNode
        else:
            refuri = node.get('refuri')
            role = self.get_cross_referencing_role(refuri)
            if len(role) == 0:
                # self.body += refuri
                url = self.check_cross_referencing_escape_uri(refuri)
                self.body += SPACE + '<' + url + '>'
            else:
                url = self.check_cross_referencing_escape_uri(refuri)
                if role == ':ref:':
                    self.body += SPACE + '<' + url[1:len(url)] + '>'
                else:
                    self.body += SPACE + '<' + url + '>'
            underscore = ''
            if len(role) == 0:
                underscore = '__'
            self.body += '`' + underscore + SPACE
        pass

    def visit_strong(self, node):
        self.body += '**'
        #     print(node)
        pass

    def depart_strong(self, node):
        #     self.body += node.astext()
        self.body += '** '
        pass

    def visit_emphasis(self, node):
        #     print(node)
        self.body += '*'
        pass

    def depart_emphasis(self, node):
        self.body += '* '
        pass

    # def visit_substitution_reference(self, node):
    #     print(node)
    #     pass
    #
    # def depart_substitution_reference(self, node):
    #     pass

    # def get_path_from_md_internal_mapping(self, perm, map='doc'):
    #     path = ''
    #     if map is 'doc':
    #         perm_mappings = self.md_doc_permalinks_and_redirects_to_filepath_map
    #     if map is 'pages':
    #         perm_mappings = self.md_pages_permalinks_and_redirects_to_filepath_map
    #     if perm in perm_mappings.keys():
    #         path = perm_mappings[perm]
    #     elif perm + '/' in perm_mappings.keys():
    #         path = perm_mappings[perm + '/']
    #     elif perm[0:len(perm) - 1] in perm_mappings.keys():
    #         path = perm_mappings[perm[0:len(perm) - 1]]
    #     return path
    #
    def get_path_from_md_internal_mapping(self, perm, map='all'):
        path = ''
        if map == 'pages':
            return get_path_from(perm, self.md_pages_permalinks_and_redirects_to_filepath_map)
        if map == 'doc':
            return get_path_from(perm, self.md_doc_permalinks_and_redirects_to_filepath_map)
        if map == 'all':
            path = get_path_from(perm, self.md_doc_permalinks_and_redirects_to_filepath_map)
            if len(path) == 0:
                path = get_path_from(perm, self.external_redirects_mappings)
        return path

    def check_cross_referencing_escape_uri(self, uri: str) -> str:
        if uri.startswith('/news/'):
            uri = BASE_SITE + uri[1:len(uri)]
        elif uri.startswith('#'):
            uri = uri.replace('-', ' ')
            # TODO inline section
        elif uri in INTERNAL_BASE_PATH:
            uri = BASE_SITE
        elif uri in DOC_BASE_PATH:
            uri = 'index'
        elif uri in FEED_XML:
            uri = BASE_SITE + FEED_XML[1:len(FEED_XML)]
        elif '#' in uri and uri.startswith('/') and not uri.startswith('/attachment'):
            # sections
            # perm_match = uri
            perm = uri[0:uri.index('#')]
            section = uri[uri.index('#') + 1:len(uri)]
            if perm in DOC_BASE_PATH:
                uri = '/' + uri[uri.index('#'):len(uri)]
            else:
                path = self.get_path_from_md_internal_mapping(perm, 'pages')
                if len(path) > 0:
                    uri = replace_page_aux(uri, path)
                else:
                    path = self.get_path_from_md_internal_mapping(perm, 'doc')
                    internal_section = section.replace('-', ' ').replace('#', '')

                    if len(path) > 0:
                        uri = path + ':' + internal_section
            # print('sections')
            # print(uri)
        elif '/attachment/' in uri and '.pdf' in uri and uri.startswith('/'):
            to_replace = uri[uri.find('/'):uri.rfind('/') + 1]
            uri = uri.replace(to_replace, '/_static/')
        elif uri.startswith('/'):
            path = self.get_path_from_md_internal_mapping(uri, 'pages')
            if len(path) > 0:
                uri = get_url(path)
            else:
                uri = self.get_path_from_md_internal_mapping(uri, 'all')
        elif uri.endswith('_'):
            logger.debug('ends with uri %s', uri)
            uri = uri[:-1] + '\\_'
        else:
            logger.debug(uri)
            logger.debug(" it should be an external link")
        return uri

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
