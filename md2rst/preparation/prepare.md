# Step by step guide

## Prepare master

### RST

1. prepare doc.md which files are retained and need to refer to the qubes os website? admin-api-*.md
configuration in config.toml
stage 1
2. pypandoc convert
3. rst validation
4. qubes-links-convert
5. figures with attachment to static
5. build sphinx log error fixes
6. incorporate _dev into the new documentation (nice to have)
6. conf.py, requirements.txt, readthedocs.yml
7. see fixed rst files perhaps prepare them also
8. copy them to a new branch in repo
9. svg convert
inkscape admin-api-architecture.svg -w 1000 -h 1000 -o admin-api-architecture.png
inkscape update_table-20140424-170010.svg  -w 1000 -h 1000 -o update_table-20140424-170010.png
inkscape release-cycle.svg -w 1000 -h 1000 -o release-cycle.png

10. edit RST documentation new file
11. privacy policy 2 times
12. toctree for latex epub pdf -> test
13. change and new files in index as in an example of markdown index
### General

[How to edit the documentation](https://www.qubes-os.org/doc/how-to-edit-the-documentation/)
[Documentation style guide](https://www.qubes-os.org/doc/documentation-style-guide/)
[Website style guide](https://www.qubes-os.org/doc/website-style-guide/)

SHOULD BE

### General

[How to edit the RST/RTD documentation](TODO)
[How to edit the markdownn documentation](https://www.qubes-os.org/doc/how-to-edit-the-documentation/)
[Markdown documentation style guide](https://www.qubes-os.org/doc/documentation-style-guide/)
[Website style guide](https://www.qubes-os.org/doc/website-style-guide/)



### Jekyll

1. script for converting redirects
2. test jekyll serve 


### Localization

1. Warning for untrusted doc on rst translation
