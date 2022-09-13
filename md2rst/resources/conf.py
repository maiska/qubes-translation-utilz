

# -- Project information -----------------------------------------------------

project = 'qubes-docs'
copyright = '2022, test'
author = 'test'

title = "Qubes Docs"
html_title = "Qubes Docs"

# The full version, including alpha/beta/rc tags
release = '0.1'

# -- General configuration ---------------------------------------------------

html_static_path = ['attachment/doc']
extensions = [
        'sphinx.ext.autosectionlabel',
]
autosectionlabel_prefix_document = True

source_suffix = {
    '.rst': 'restructuredtext',
}
templates_path = ['_templates']

root_doc = "index"
exclude_patterns = [
            '_dev/*', 
            'attachment/*',
            '**/*.txt'
            ]


html_theme = 'default'
#html_theme = 'classic'

html_theme_options = {
    'externalrefs': True, 
    'bgcolor': 'white',
    'linkcolor': '#99bfff',
    'textcolor': '#000000',
    'visitedlinkcolor': '#7b7b7b',
    'bodyfont': '"Open Sans", Arial, sans-serif',
    'codebgcolor': '$color-qube-light',
    'codebgcolor': 'grey',
    'body_min_width': '50%',
    'body_max_width': '90%',
}

gettext_uuid=True
gettext_compact=False


#epub_show_urls = 'footnote'
#latex_show_urls ='footnote'


locale_dirs = ['_translated']
