# From Markdown to ReStructuredText

This is a helper script to convert the current Qubes OS markdown documentation.
It is to be executed only once and forgotten about.
The output should be the ReStructuredText (RST) variant of it.
Will be hosted on ReadTheDocs and rendered using [sphinx](https://www.sphinx-doc.org/en/master/)

## Config

All the relevant configuration can be found in config.toml.

The script takes the repository containing the current markdown documentation, 
gathering permalinks and relative paths, so that cross-referencing
can later be done in converted RST documentation and copying its 
documentation contents to a new directory that will serve as the new
RST documentation repository.

### Preparation

To be aware of the many files that are provided in the preparation folder.
It contains:

1. RST relevant configuration such as:

- requirements.txt - dependencies for serving sphinx locally with all the extensions needed
- conf.py - initial sphinx configuration with strike role for strikeout text and redirects,
  [see](https://www.sphinx-doc.org/en/master/usage/configuration.html)
- .readthedocs.yml - ReadTheDocs conf, [see](https://docs.readthedocs.io/en/stable/config-file/v2.html)

2. Markdown files to be copied prior conversion such as 
- doc.md - written out documentation index containing references to the separate doc files and external documentation 
  Be careful before converting, make sure the contents is up to date and satisfies the requirements 

3. RST specific files for which it was easier to create a manual representation

4. Certain RST files to skip from post processing and cross referencing links because either they do not have any (gui.rst) 
  or are already converted and prepared (the rest of the files). These files will be skipped ALWAYS

5. Directories and files to remove such as the markdown documentation configuration or mere redirects to external docs

#### TODO

- TODO requirements - new one
- TODO redirects does not work atm
1. test links with sphinx
2. fix links
3. fix broken links in config files 
4. pdf latex builds 
5. new jekyll site test with new
6. developer/general/gsoc.rst - remove the commented out section 
7. how to edit the documentation, documentation style guide, website style guide (remove from index?? )
8. visually style guide - manually convert??
9. http://127.0.0.1:8000/developer/services/qrexec.html - comment

```commandline
grep -r "</doc/"
--- user/how-to-guides/how-to-use-usb-devices.rst:pass it to the ```qvm-pci`` tool </doc/how-to-use-pci-devices/>`__ to
user/how-to-guides/how-to-use-pci-devices.rst:```qvm-device pci`` </doc/how-to-use-devices/#general-qubes-device-widget-behavior-and-handling>`__.
user/advanced-topics/bind-dirs.rst:  using ```/rw/config/rc.local`` </doc/config-files>`__
introduction/faq.rst:intend to use from ```sys-usb`` </doc/usb/>`__ to another qube via
developer/system/template-implementation.rst:``/home`` </doc/templates/#inheritance-and-persistence>`__. The child  
```
```commandline
grep -r "\`\`\`"
```

```commandline
grep -r ":title-reference"
user/how-to-guides/how-to-update.rst:30::title-reference:`Qubes Security Pack (``qubes-secpack``) </security/pack/>`__. It is
user/how-to-guides/how-to-update.rst:108:instructions to this effect. See the relevant QSB and the :title-reference:`AEM
user/how-to-guides/how-to-use-devices.rst:70:But be careful: There is a :title-reference:`bug in ``qvm-device block`` or
user/advanced-topics/bind-dirs.rst:24:For example, in Whonix, :title-reference:`Tor’s data dir ``/var/lib/tor`` has been made
introduction/support.rst:39:5. Try :title-reference:`searching the ``qubes-users``
developer/system/template-implementation.rst:36:``/home`` directory of its parent TemplateVM :title-reference:`are not copied to the
```
### Submodule

THe new RST documentatoin expects the attachment Qubes OS repo to be available
either just copied or as a submodule
There is a way to configure automatically adding the attachment repo as a submodule
and performs ONLY initial commit after pandoc conversion and rst cross linkings.
Expects signed commits preconfigured

### SVG Conversion

Originally there was a problem with svg images when rendering latex offline documentation
so there is the option to generate pngs on the fly and replace them in the RST docs

# Run configurations

The script should be run in 3 stages

## 1-st stage

- initially converts markdown to rst via `pypandoc = true`
- copies the markdown files from md_file_names via `copy_md_files = true`
- copies the rst files from rst_files via `copy_rst_files = true`
- deletes rst dirs from directories_to_remove via `remove_rst_directory = true`
- deletes the rst files from files_to_remove via `remove_rst_files = true`

## 2nd stage

- prior to further processing the converted rst documentation via pandoc should be parsed and validated first
via `docutils_validate = true`. The usual suspects are 2 files:
   1. developer/building/development-workflow.rst, l. 168, l. 241, l. 321 with
      with a needed modification from -------- to ~~~~~~~ for the section separators
   2. developer/system/template-implementation.rst, l. 111, l. 132 with
      with a needed modification from ~~~~~~~ to -------- for the section separators
- fix the broken cross-referencing links between the different documentation files via `qubes_rst = true`
- whether or not to initialize the newly converted rst documentation repository
and add the attachment submodule via `git_init = true`
(either way attachment should be present in the rst-doc repository
so that all the referenced images can be found and displayed see svg above)
- whether or not to convert certain svg to png (see git above) via `svg_png_conversion_replacement = true`
- handle several leftovers with regular expressions (see config_constants.py) via `markdown_links_leftover = true`
- simple search and replace custom strings (see replace_custom_strings_values) via `replace_custom_strings = true`

### Tips

1. to be on the safe side do grep for SYSTEM / ERROR inside the rst doc directory for system errors 
(will be written in the files if there is one)
2. servce the documentation locally and manually fix warnings, such as
    - Title underline too short.
    - Bullet list ends without a blank line; unexpected unindent. or
    - etc.
3. toctree errors
    - decide if the index should contain the external urls (to https://qubes-os.org/hcl f.ex.) or to internal empty rst 
 dummy file but handled via redirects

## 3rd stage

- empty all relevant markdown files and add a redirection to the current rst documentation (see redirect_base_url)
via `redirect_markdown = true`


# Contents of rst documentation

In preparation folder there are two files with initial content suggestions: 
1. `how-to-edit-the-rst-documentation.rst` as additional sections to the already
existing how-to-edit-the-documentation.md or as a separate file. The first option does not require changing cross-reference
 linking and wording in other documents, but it is not a clear differentiation either as the second one. 
2. `privacy.rst` with a reference to the privacy policy of RTD at the end of the file.

## New TODO

1. style guide for RST documentation  

## Serve jekyll website locally

```commandline
qvm-clone debian-11-minimal jekyll-tvm

in jekyll-tvm:
apt install qubes-core-agent-networking
apt install ruby-full build-essential zlib1g-dev vim
apt install qubes-core-agent-passwordless-root
apt install firefox-esr git

in jekyll-app-vm:
echo '# Install Ruby Gems to ~/gems' >> ~/.bashrc
echo 'export GEM_HOME="$HOME/gems"' >> ~/.bashrc
echo 'export PATH="$HOME/gems/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
gem install jekyll bundler
find . -name gem
bundle config set --local path '/home/user/.local/share/gem/'
git clone -b new-master --recursive https://github.com/QubesOS/qubesos.github.io.git; cd qubesos.github.io.rtd/
bundle install
bundle exec jekyll serve --incremental
```
