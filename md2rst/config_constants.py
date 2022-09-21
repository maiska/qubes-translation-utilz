MARKDOWN = 'markdown'
# ------
ROOT_DIRECTORY = 'root_directory'

RST = 'rst'
# ------
RST_DIRECTORY = 'rst_directory'
COPY_FROM_DIR = 'copy_from_dir'
MD_FILE_NAMES = 'md_file_names'
RST_FILE_NAMES = "rst_file_names"
DIRECTORY_TO_REMOVE = "directory_to_remove"
HIDDEN_FILES_TO_REMOVE = 'hidden_files_to_remove'

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
REMOVE_HIDDEN_FILES = "remove_hidden_files"
DOCUTILS_VALIDATE = 'docutils_validate'
QUBES_RST = 'qubes_rst'

SVG_PNG_CONVERSION_REPLACEMENT = 'svg_png_conversion_replacement'


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

BASE_SITE = 'https://www.qubes-os.org/'
INTERNAL_BASE_PATH = '/home/'
DOC_BASE_PATH = '/doc/'
FEED_XML = '/feed.xml'


# REGEX

PATTERN_MD_INTERNAL_LINKS = '(\[[\w\d\s#@\“\”\_\)\(/\.\’&:,\\-]{1,50}\])(\((/[\w]{1,50}){1,8}/\))'

PATTERN_MD_EXTERNAL_LINKS = '(\[[\w#@\d\s\“\”\[\]\_\)\(/\.\’&:,\\-]{1,50}\])(\(https{0,1}:/(/[\w\.\-\/\d]{1,50}){1,10}\))'

