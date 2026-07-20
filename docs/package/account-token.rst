.. _access token:

Configuring Access Token
###########################


*fairly* can be used to access datasets owned by a user of a data repository. For 4TU.ResearchData and Zenodo, we can do that by configuring access tokens.

Creating a personal access token
=====================================

A personal access toke allows to connect to a user account remotely without the need to a *username* and *password*.

Zenodo
-------------

1. Register for a Zenodo account if you do not already have one.
#. Go to your :guilabel:`Applications`, and click on :guilabel:`New token` under **Personal access tokens**.
#. Enter a name for your token.
#. Select the OAuth scopes you need (:guilabel:`deposit:write` and :guilabel:`deposit:actions`).
#. Click :guilabel:`Create`
#. An access token will be shown, copy it and store it. **The token will only be shown once.**
#. Click on :guilabel:`Save`


4TU.ResearchData
-------------------

1. Register for a Zenodo account if you do not already have one.
#. Go to your :guilabel:`Applications`, and click on :guilabel:`Create Personal Token`.
#. Enter short description for your token, for example a name, and click on :guilabel:`Save`
#. An access token will be shown, copy it and store it. **The token will only be shown once.**
#. Click on :guilabel:`Done`

Connecting to an Account
============================

Connecting to an account is a simple as passing a token when creating a 4TU.ResearchData or Zenodo client.

.. code-block:: python

   import fairly

   # For 4TU.ResearchData
   fourtu = fairly.client("figshare", token="<my-4tu-token>")

   # For Zenodo
   zenodo = fairly.client("zenodo", token="<my-zenodo-token>" )

Storing Tokens
================

Token can be stored on a user configuration files at `~/.fairly/config.json`. You can add/modify tokens to repositories as follows. Stored tokens will be used by the Python API, CLI and JupyterLab extension, unless a different topen is passed when performing a task.

To store a token using the CLI, use:

.. code-block:: shell

   fairly repository token <reposiotry-id> <your-token>

To check which repositories and token are configured, use:

.. code-block:: shell

   fairly repository list
