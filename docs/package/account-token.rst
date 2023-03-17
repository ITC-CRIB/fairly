.. _access token:

Configuring Access Token
###########################


*fairly* can be used to access datasets owened by a user of a data repository. For 4TU.ReaseachData and Zenodo, we can do data by configuring access tokens.

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
#. An access token will be showned, copy it and store it. **The token will only be showned once.** 
#. Click on :guilabel:`Save`


4TU.ReaseachData
-------------------

1. Register for a Zenodo account if you do not already have one.
#. Go to your :guilabel:`Applications`, and click on :guilabel:`Create Personal Token`.
#. Enter short description for your token, for example a namem, and click on :guilabel:`Save`
#. An access token will be showned, copy it and store it. **The token will only be showned once.** 
#. Click on :guilabel:`Done`

Connecting to an Account
============================

Connecting to an account is a simple as passign a token when creating a 4TU.ResearchDaata or Zenodo client.

.. code-block:: python

   from fairly import client

   # For 4TU.ReseachData 
   fourtu = client(id="figshare", token="<my-tu-token>" )

   # For Zenodo
   fourtu = client(id="zenodo", token="<my-zenodo-token>" )

Storing Tokens
================

To store your Tokens, create a JSON file like the one below and store it at `~/.fairly/repositories.json` You can store tokens for other repositories by addding them to this file as `"<repository-ID>": {"token": <the-token>}`

.. code-block:: json

   {
      "4tu": {
         "token": "<4tu-token>"
      }
   }

