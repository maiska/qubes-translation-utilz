# qubes-translation-utilz
Utilities for translation of the Qubes OS site

Here you can find scripts for a translation workflow based on the current jekyll website hosting the documentation in Markdown

and a script for post processing the conversion of the existing Markdown documentation to ReStructured Text.


# translating qubes-doc

```
tx --traceback config mapping-bulk  --project "qubes" --file-extension '.pot' --source-file-dir _build/gettext --source-lang en --type PO --expression '_translated/<lang>/LC_MESSAGES/{filepath}/{filename}.po' --execute
sed -e 's/_build_gettext/doc/' -i .tx/config
```
