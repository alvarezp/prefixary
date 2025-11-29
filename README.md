PREFIXARY
=========

A lightweight Flask application to keep track of network prefixes,
whether observed or fixed.

"Observed" means that some audit program saw the prefix in the
network. "Fixed" means that the user manually set it in Prefixary.

It supports IPv4 and IPv6.

Observed
--------

For now, the "observed" part is up to the user. Just insert them into
the `observed_prefixes` table. Prefixary will integrate them into the
main prefix view.

The `observed_prefixes` table assigns semantic to the following
values. This is internal and the values may change in the future, so,
unless you are adding data into the `observed_prefixes` table, you may
just want to skip the rest of this section.

* entry_type beginning with "interface " (including the space):
  * it gives it a weight of 600

* entry_type beginning with "route":
  * it gives it a weight of 300

* entry_type beginning with "specification":
  * it gives it a weight of 100 -- it does not really mean that it was
    found in the network, but if we were to default it to "fixed" then
    they would show in bold, causing even more noise.

This "weight" is used to choose which description to prefer when a
prefix is found multiple times in the `observed_prefixes` table (maybe
the prefix is observed in multiple devices).

Fixed prefixes
--------------

If you have a better description or want to declare a prefix by
yourself, click on "Fixed prefixes" and add them to the table. Fixed
prefixes have an operator-given description and are shown in bold in
the main prefix view. Use them if you want to keep them regardless of
whether the prefix is seen in the network or not.

For example, if you want to reserve a prefix for future use, just add
it as a fixed prefix with description "Reserved for future use" and it
will be shown with that message. You know that when you click on it,
you expect to see no children. If you do, it means there's some work
to do until the prefix is no longer observed in the network.


Dependencies
============

Jinja2, Psycopg, PostgreSQL


How to run
==========

The simplest way is to use:

`flask run`

It will run it on port 5000, but this is not recommended for
production use. It should be enough for occassional use by a single
user, though.

You should be able to integrate it to your Web server using your
favorite WSGI interface.


Database
========

Setup
-----

Create a new database in PostgreSQL and load `prefixary.sql`. This
will vary from system to system depending on distro, user account,
superuser access, current `pg_hba.conf` setup, etc. However, the core
of it is something like this:

```
createdb prefixary
psql prefixary < prefixary.sql
```

Connection details
------------------

You can modify them yourself in the code or set the following
variables:

```
export PGDATABASE=prefixary
export PGUSER=youruser
export PGPASSWORD=yourpass
export PGHOST=localhost
export PGPORT=5432
```

The code, as it is now, just connects locally to a database named
`prefixary` through Unix sockets.


Security disclaimers
====================

Handle with care. Not enough work has been put into security yet.
If you find any security vulnerabilities please open an issue.


Copyright statements
====================

Derechos Reservados © 2025, Octavio Alvarez Piza <octalgh@alvarezp.org>

Copyright © 2025, Octavio Alvarez Piza <octalgh@alvarezp.org>

It is released under the Affero General Public License version 3. Read
the LICENSE file for the license terms.

Read as: all rights non explicitly provided by the license are
reserved according to corresponding Copyright laws.
