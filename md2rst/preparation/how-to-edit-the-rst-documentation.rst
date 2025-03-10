==============================================
How to edit the ReStructuredText documentation
==============================================

Most of the Qubes OS documentation pages are stored as ReStructuredText files in
the `qubes-rst-doc <https://github.com/QubesOS/qubes-doc>`__ repository on branch TODO.
By cloning and regularly pulling from this repo, users can maintain their
own up-to-date offline copy of all Qubes documentation rather than
relying solely on the web.

The documentation is a volunteer community effort. People like you are
constantly working to make it better. If you notice something that can
be fixed or improved, please follow the steps below to open a pull
request!

How to submit a pull request
============================

We keep all the ReStructuredText documentation in `qubes-doc <https://github.com/QubesOS/qubes-doc>`__,
a dedicated Git repository hosted on `GitHub <https://github.com/>`__. Thanks to
GitHub’s easy web interface, you can edit the documentation even if
you’re not familiar with Git or the command line! All you need is a free
GitHub account.

A few notes before we get started:

-  Since Qubes is a security-oriented project, every documentation
   change will be :ref:`reviewed <developer/general/how-to-edit-the-documentation:security>` before it’s accepted. This
   allows us to maintain quality control and protect our users.

-  To give your contribution a better chance of being accepted, please
   follow our TODO ReStrucutredText Style Guide. 

-  We don’t want you to spend time and effort on a contribution that we
   can’t accept. If your contribution would take a lot of time, please
   :doc:`file an issue </introduction/issue-tracking>` for it first so that we can
   make sure we’re on the same page before significant works begins.

-  Alternatively, you may already have written content that doesn’t
   conform to these guidelines, but you’d be willing to modify it so
   that it does. In this case, you can still submit it by following the
   instructions below. Just make a note in your pull request (PR) that
   you’re aware of the changes that need to be made and that you’re just
   asking for the content to be reviewed before you spend time making
   those changes.

-  Finally, if you’ve written something that doesn’t belong in qubes-doc
   but that would be beneficial to the Qubes community, please consider
   adding it to the :ref:`external documentation <developer/general/documentation-style-guide:core vs external documentation>`.

(**Advanced users:** If you’re already familiar with GitHub or wish to
work from the command line, you can skip the rest of this section. All
you need to do to contribute is to `fork and clone <https://guides.github.com/activities/forking/>`__ the `qubes-doc <https://github.com/QubesOS/qubes-rst-doc>`__ repo, make your changes, then `submit a pull request <https://help.github.com/articles/using-pull-requests/>`__.)

Ok, let’s begin. Every documentation page has a “Page Source on GitHub”
button. Depending on the size of your screen, it may either be on the
side (larger screens) or on the bottom (smaller screens).

|page-source-button|

When you click on it, you’ll be taken to the source file — a ReStructuredText (``.rst``) file — on GitHub. On this page, there will be a
button to edit the file.

|github-edit|

You’ll be prompted to sign in with your GitHub username and password (if
you aren’t already logged in). You can also create a free account from
here.

|github-sign-in|

If this is your first contribution to the documentation, you need to
“fork” the repository (make your own copy). It’s easy — just click the
big green button on the next page. This step is only needed the first
time you make a contribution.

|fork|

Now you can make your modifications. You can also preview the changes to
see how they’ll be formatted by clicking the “Preview changes” tab. If
you want to add images, please see :ref:`How to add images <developer/general/how-to-edit-the-rst-documentation:how to add images>`. 
If you’re making formatting changes, please render the RST documentation locally using sphinx TODO link to erify that everything looks correct before submitting any changes.

|edit|

Once you’re finished, describe your changes at the bottom and click
“Propose file change”.

|commit|

After that, you’ll see exactly what modifications you’ve made. At this
stage, those changes are still in your own copy of the documentation
(“fork”). If everything looks good, send those changes to us by pressing
the “Create pull request” button.

|pull-request|

You will be able to adjust the pull request message and title there. In
most cases, the defaults are ok, so you can just confirm by pressing the
“Create pull request” button again. However, if you’re not ready for
your PR to be reviewed or merged yet, please `make a draft PR instead <https://github.blog/2019-02-14-introducing-draft-pull-requests/>`__.

|pull-request-confirm|

If any of your changes should be reflected in the `documentation index (a.k.a. table of contents) </>`__ — for example, if you’re adding a
new page, changing the title of an existing page, or removing a page —
please see :ref:`How to edit the documentation index <developer/general/how-to-edit-the-rst-documentation:how to edit the documentation index>`.

That’s all! We will review your changes. If everything looks good, we’ll
pull them into the official documentation. Otherwise, we may have some
questions for you, which we’ll post in a comment on your pull request.
(GitHub will automatically notify you if we do.) If, for some reason, we
can’t accept your pull request, we’ll post a comment explaining why we
can’t.

|done|

How to edit the documentation index
===================================

The source file for the `documentation index (a.k.a. table of contents) </>`__ is index.rst TODO link to file

Editing this file will change what appears on the documentation index.
If your pull request (PR) adds, removes, or edits anything that should
be reflected in the documentation index, please make sure you also
submit an associated pull request against this file.

How to add images
=================


TODO 
To add an image to a page, use the following syntax in the main document

::

   [![Image Title](/attachment/doc/image.png)](/attachment/doc/image.png)

To add an image this would look something like

.. code-block:: rst
    :caption: Adding image to ReStructredText

    .. figure:: /attachment/doc/r4.0-snapshot12.png
      :alt: Qubes desktop screenshot

Then, submit your image(s) in a separate pull request to the `qubes-attachment <https://github.com/QubesOS/qubes-attachment>`__
repository using the same path and filename. This is the only permitted
way to include images. Do not link to images on other websites.

Cross-referencing
=================

When referencing to an existing RST file use the ``:doc:`` role as in 

.. code-block:: rst
   :caption: Add a link to an existing internal rst documenation file

   text :doc:`contribute code </introduction/contributing>` text


When referencing to a section in an existing RST file use the ``:ref:`` role as in 

.. code-block:: rst
   :caption: Add a link to a section in an existing internal rst documenation file. Pay attention to the missing leading slash in contrast to the doc role.

   text :ref:`USB Troubleshooting guide <user/troubleshooting/usb-troubleshooting:usb vm does not boot after creating and assigning usb controllers to it>`. text

Tips & Tricks
=============

WIP

See https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html for formatting text, it is either bold or italic, cannot be bold, if using out of the box.


> https://qubes-doc-rst.readthedocs.io/en/latest/user/downloading-installing-upgrading/testing.html

> * [ ]  `?` Im Abschnitt „Providing feedback“ fehlen die Symbole für „Daumen-hoch“ und „Daumen-runter“.
- LATER TODO
https://stackoverflow.com/questions/1862472/symbols-in-restructuredtext



Serving the RST documentation locally
=====================================

You can serve the ReStrucutedText offline on your local machine by using sphinx.
The following commands should do the trick:

.. code-block:: sh
    :caption: Sphinx-View

    virtualenv -v .venv;
    source .venv/bin/activate;
    pip3 install sphinx-view;
    sphinx-view _doc/ -c _doc/conf.py
   


This can be useful for making sure that your changes render the way you
expect, especially when your changes affect formatting, images, tables,
styling, etc.

Security
========

*Also see:*\ :ref:`Should I trust this website? <introduction/faq:should i trust this website>`

All pull requests (PRs) against `qubes-doc <https://github.com/QubesOS/qubes-doc>`__ must pass review
prior to be merged, except in the case of :ref:`external documentation <developer/general/how-to-edit-the-documentation:external documentation>` (see `#4693 <https://github.com/QubesOS/qubes-issues/issues/4693>`__). This
process is designed to ensure that contributed text is accurate and
non-malicious. This process is a best effort that should provide a
reasonable degree of assurance, but it is not foolproof. For example,
all text characters are checked for ANSI escape sequences. However,
binaries, such as images, are simply checked to ensure they appear or
function the way they should when the website is rendered. They are not
further analyzed in an attempt to determine whether they are malicious.

Once a pull request passes review, the reviewer should add a signed
comment stating, “Passed review as of ``<LATEST_COMMIT>`` (or similar).
The documentation maintainer then verifies that the pull request is
mechanically sound (no merge conflicts, broken links, ANSI escapes,
etc.). If so, the documentation maintainer then merges the pull request,
adds a PGP-signed tag to the latest commit (usually the merge commit),
then pushes to the remote. In cases in which another reviewer is not
required, the documentation maintainer may review the pull request (in
which case no signed comment is necessary, since it would be redundant
with the signed tag).

Questions, problems, and improvements
=====================================

If you have a question about something you read in the documentation or
about how to edit the documentation, please post it on the `forum <https://forum.qubes-os.org/>`__ or send it to the appropriate :doc:`mailing list </introduction/support>`. If you see that something in the
documentation should be fixed or improved, please :ref:`contribute <developer/general/how-to-edit-the-documentation:how to submit a pull request>` the change yourself. To
report an issue with the documentation, please follow our standard :doc:`issue reporting guidelines </introduction/issue-tracking>`. (If you report an
issue with the documentation, you will likely be asked to submit a pull
request for it, unless there is a clear indication in your report that
you are not willing or able to do so.)

.. |page-source-button| image:: /attachment/doc/doc-pr_01_page-source-button.png
   :target: /attachment/doc/doc-pr_01_page-source-button.png
.. |github-edit| image:: /attachment/doc/doc-pr_02_github-edit.png
   :target: /attachment/doc/doc-pr_02_github-edit.png
.. |github-sign-in| image:: /attachment/doc/doc-pr_03_sign-in.png
   :target: /attachment/doc/doc-pr_03_sign-in.png
.. |fork| image:: /attachment/doc/doc-pr_04_fork.png
   :target: /attachment/doc/doc-pr_04_fork.png
.. |edit| image:: /attachment/doc/doc-pr_05_edit.png
   :target: /attachment/doc/doc-pr_05_edit.png
.. |commit| image:: /attachment/doc/doc-pr_06_commit-msg.png
   :target: /attachment/doc/doc-pr_06_commit-msg.png
.. |pull-request| image:: /attachment/doc/doc-pr_07_review-changes.png
   :target: /attachment/doc/doc-pr_07_review-changes.png
.. |pull-request-confirm| image:: /attachment/doc/doc-pr_08_create-pull-request.png
   :target: /attachment/doc/doc-pr_08_create-pull-request.png
.. |done| image:: /attachment/doc/doc-pr_09_done.png
   :target: /attachment/doc/doc-pr_09_done.png
