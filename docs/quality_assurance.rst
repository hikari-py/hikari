Quality Assurance
#################

The following is produced by the most recent CI build on the current branch.


Version: |version|

Release: |release|


Changelog
...................................

`View the page here <CHANGELOG.html>`_

.. raw:: html

    <iframe src="CHANGELOG.html" style="border: 0;"
            onload="this.style.height=Math.min(this.contentDocument.body.scrollHeight, 400) +'px';this.style.width=Math.max(this.contentDocument.body.scrollWidth,1024) +'px';"></iframe>

Static application security testing
...................................

Produced using "bandit". `View the page here <bandit.html>`_

.. raw:: html

    <iframe src="bandit.html" style="border: 0;"
            onload="this.style.height=this.contentDocument.body.scrollHeight + 30 +'px';this.style.width=this.contentDocument.body.scrollWidth +'px';"></iframe>

Unit test coverage
........................

An aggregate combination of the coverage reports for all test environments. This takes into account differences between
different versions of Python, for example, whilst handing release-specific compatibility code.

`View the page here <coverage/index.html>`_

.. raw:: html

    <iframe src="coverage/index.html" width="auto" style="border: 0;"
            onload="this.style.height=this.contentDocument.body.scrollHeight + 30 +'px';this.style.width=this.contentDocument.body.scrollWidth +'px';"></iframe>


The difference in test coverage between this release and the previous master release is as follows (`View the page here <diff-cover.html>`_)

.. raw:: html

    <iframe src="diff-cover.html" width="auto" style="border: 0;"
            onload="this.style.height=this.contentDocument.body.scrollHeight + 1 +'px';this.style.width=this.contentDocument.body.scrollWidth + 10 + 'px';"></iframe>

If any documents are unavailable, it is likely due to the pipeline not running fully. This process is fully automated.
