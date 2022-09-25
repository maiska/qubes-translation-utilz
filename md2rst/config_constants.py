MARKDOWN = 'markdown'
# ------
ROOT_DIRECTORY = 'root_directory'

RST = 'rst'
# ------
RST_DIRECTORY = 'rst_directory'
COPY_FROM_DIR = 'copy_from_dir'
MD_FILE_NAMES = 'md_file_names'
RST_CONFIG_FILES = "rst_config_files"
RST_FILES = 'rst_files'
DIRECTORY_TO_REMOVE = "directory_to_remove"
FILES_TO_REMOVE = 'files_to_remove'
SKIP_FILES = 'skip_files'

SVG = 'svg'
# ------
SVG_FILES_TO_PNG = 'svg_files_to_png'
PNG_IN_RST_FILES = 'replace_svg_with_png_in_rst_files'


RUN = 'run'
# ------
PYPANDOC = 'pypandoc'
COPY_MD_FILES = "copy_md_files"
COPY_RST_FILES = "copy_rst_files"
REMOVE_RST_DIRECTORY = "remove_rst_directory"
REMOVE_RST_FILES = "remove_rst_files"
DOCUTILS_VALIDATE = 'docutils_validate'
QUBES_RST = 'qubes_rst'

SVG_PNG_CONVERSION_REPLACEMENT = 'svg_png_conversion_replacement'
HANDLE_LEFTOVER_MARKDOWN_LINKS = 'markdown_links_leftover'

REDIRECT_MARKDOWN = 'redirect_markdown'


URL_MAPPING = 'url_mapping'
# ------
SAVE_TO_JSON = 'save_to_json'
DUMP_DIRECTORY = 'dump_directory_name'
DUMP_PAGES_FILENAME = 'dump_pages_filename'
DUMP_DOCS_FILENAME = 'dump_docs_filename'
DUMP_EXTERNAL_FILENAME = 'dump_external_filename'

TEST = 'test'
# ------
FILE_NAME = 'file_name'

# ------
LOGFILE = 'logfile'

MD_MAP = 'md_map'

# ---------------------------------------
# MARKDOWN CONSTANTS
PERMALINK_KEY = 'permalink'
REDIRECT_FROM_KEY = 'redirect_from'
REDIRECT_TO_KEY = 'redirect_to'

# URL CONSTANTS

QUBESOS_SITE = 'https://www.qubes-os.org/'
INTERNAL_BASE_PATH = '/home/'
DOC_BASE_PATH = '/doc/'
FEED_XML = '/feed.xml'



# REGEX

PATTERN_MD_INTERNAL_LINKS = '(\[[\w\d\s#@\“\”\_\)\(/\.\’&:,\\-]{1,50}\])(\((/[\w]{1,50}){1,8}/\))'
PATTERN_MD_INTERNAL_LINKS_SPACEY = '(\[[\w\d\s#@\“\”\_\)\(/\.\’&:,\\-]{1,50}\])(\((/[\w]{1,50}){1,8}/\s\))'

PATTERN_MD_EXTERNAL_LINKS = '(\[[\w#@\d\s\“\”\[\]\_\)\(/\.\’&:,\\-]{1,50}\])(\(https{0,1}:/(/[\w\.\-\/\d]{1,50}){1,10}\))'
PATTERN_MD_EXTERNAL_LINKS_SPACEY = '(\[[\w#@\d\s\“\”\[\]\_\)\(/\.\’&:,\\-]{1,50}\])(\(https{0,1}:/(/[\w\.\-\/\d]{1,50}){1,10}\s\))'

PATTERN_MD_MAILTO_LINKS = '(\[[\w\d\s#@\“\”\_\)\(/\.\’&:,\\-]{1,50}\])(mailto:\((/[\w]{1,50}){1,8}/\))'


