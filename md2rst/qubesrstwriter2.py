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
from utilz import is_dict_empty, CheckRSTLinks

from docutils_rst_writer.writer import RstTranslator

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


# def get_path_from(perm, mapping):
#     path = ''
#     if perm in mapping.keys():
#         path = mapping[perm]
#     elif perm + '/' in mapping.keys():
#         path = mapping[perm + '/']
#     elif perm[0:len(perm) - 1] in mapping.keys():
#         path = mapping[perm[0:len(perm) - 1]]
#     return path


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


class QubesRstTranslator(RstTranslator):
    sectionchars = '*=-~"+`'

    def __init__(self, document, builder,
                 md_doc_permalinks_and_redirects_to_filepath_map,
                 md_pages_permalinks_and_redirects_to_filepath_map,
                 external_redirects_map):
        super().__init__(document)

        self.checkRSTLinks = CheckRSTLinks(md_doc_permalinks_and_redirects_to_filepath_map,
                                      md_pages_permalinks_and_redirects_to_filepath_map,
                                      external_redirects_map)
        # self.md_pages_permalinks_and_redirects_to_filepath_map = md_pages_permalinks_and_redirects_to_filepath_map
        # self.external_redirects_map = external_redirects_map
        # self.md_doc_permalinks_and_redirects_to_filepath_map = md_doc_permalinks_and_redirects_to_filepath_map
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
        self.wrapper = textwrap.TextWrapper(width=MAXWIDTH, break_long_words=False, break_on_hyphens=False)

    # def get_cross_referencing_role(self, uri):
    #     role = ''
    #     if uri.startswith('/news'):
    #         role = ''
    #     elif uri.startswith('/') and '#' in uri and not uri.startswith('/attachment'):
    #         role = ':ref:'
    #     elif uri.startswith('/') and not uri.startswith(
    #             '/attachment') and uri not in self.external_redirects_map.keys():
    #         role = ':doc:'
    #     elif BASE_SITE in uri:
    #         role = ''
    #
    #     return role

    def depart_document(self, node):
        # print(node.astext())
        super().depart_document(node)
        self.body += '\n'.join(self.lines)

    def visit_system_message(self, node):
        print('SYSTEM MESSAGE: ' + str(node))
        raise nodes.SkipNode

    def depart_system_message(self, node):
        print(node)
        pass


    def visit_literal_block(self, node, language=None):
        print(node)
        print(f'attrs {node.attributes!r}, lang {language}')
        # if node['classes'] in ['code bash', 'code shell']:
        #     print(node)

        # if only children with the baove classes fix for last code block in qubes-builder
        # children = node.children
        # classes = [i.__class__.__name__ for i in children]
        # if is_node_a_code_block(node) and set(classes) == set('inline', 'Text'):
        #     self.body += self.get_code_text_block(node.astext())
        #     pass
        if language is None:
            language = node.get('language')
        if language is None:
            classes = node.get('classes') or []
            classes = [c for c in classes if c not in ('code',)]
            if len(classes) == 1:
                language = classes[0]

        if node.hasattr('xml:space') or language is not None:
            astext = node.astext()
            if is_shell_code_block(astext):
                for i in ['shell_session', 'bash_session', '.. code::']:
                    code_section = astext.replace(i, '')
                    code_section = code_section.lstrip()
                self.write(self.nl + self.get_code_text_block(code_section))
                raise nodes.SkipNode
            if is_c_code_block(astext):
                language = 'c'
            elif False and language is None:
                language = 'bash'
            elif language in ["shell_session", "bash_session"]:
                language = 'shell-session'
        super().visit_literal_block(node, language=language)

    def get_code_text_block(self, nodeasstr):
        x = nodeasstr.splitlines()
        ident = self.nl + CODE_BLOCK_IDENT
        return ident.join(x)

    def visit_reference(self, node):
        refname = node.get('name')
        refbody = node.astext()
        refid = node.get('refid')
        refuri = node.get('refuri')
        if refname is None and refuri.startswith('http'):
            # the case of license.rst and markdown link with qubes os have to be converted manually
            # perhaps with the bash skript TODO
            super().visit_reference(node)
        else:
            self.checkRSTLinks.set_uri(refuri)
            role = self.checkRSTLinks.get_cross_referencing_role()
            self.write(SPACE + role + '`')
        pass

    def depart_reference(self, node):
        result = ""
        refname = node.get('name')
        refuri = node.get('refuri')
        self.checkRSTLinks.set_uri(refuri)
        role = self.checkRSTLinks.get_cross_referencing_role()
        # role = self.get_cross_referencing_role(refuri)
        if refname is None and refuri.startswith('http'):
            return super().depart_reference(node)

            # self.body += refuri
            url = self.checkRSTLinks.check_cross_referencing_escape_uri()
            # url = self.check_cross_referencing_escape_uri(refuri)
            result += (SPACE + '<' + url + '>')
        else:
            url = self.checkRSTLinks.check_cross_referencing_escape_uri()
            # url = self.check_cross_referencing_escape_uri(refuri)
            if role == ':ref:':
                result += (SPACE + '<' + url.lstrip('/') + '>')
            else:
                result += (SPACE + '<' + url + '>')
        underscore = ''
        if len(role) == 0:
            underscore = '__'

        result += ('`' + underscore + SPACE)
        # self.write(result)
        node['refuri'] = url
        self.write(result)
        # super().depart_reference(node)

    def visit_figure(self, node):
        # there is 'image' node inside, that will be actually handled
        pass

    def depart_figure(self, node):
        pass

    def visit_caption(self, node):
        # TODO: caption to a fiture
        pass

    def depart_caption(self, node):
        pass

    def visit_container(self, node):
        attrs = ''
        if 'alert-warning' in node.get('classes'):
            directive = 'warning'
        elif 'alert-info' in node.get('classes'):
            directive = 'note'
        else:
            directive = 'container'
            attrs = ' ' + ' '.join(node['classes'])
        self.write(f'.. {directive}::{attrs}\n')
        self.indent += 4

    def depart_container(self, node):
        self.write('\n\n')
        self.indent -= 4

    def visit_raw(self, node):
        self.write(f'.. raw:: {node["format"]}')
        self.indent += 4

    def depart_raw(self, node):
        self.indent -= 4

    def unknown_visit(self, node):
        print(node)
        super().unknown_visit(node)
    #     print("unknown_visit end")
    #     self.write('[UNKOWN NODE (%s) %s]' % (node.__class__.__name__, node.astext()))
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
