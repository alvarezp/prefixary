#
# Derechos Reservados (C) 2025, Octavio Alvarez Piza <octalgh@alvarezp.org>
# Copyright (C) 2025, Octavio Alvarez Piza. All rights reserved.
#
# This program is free software: you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public
# License as published by the Free Software Foundation, either
# version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public
# License version 3 along with this program. If not, see
# <https://www.gnu.org/licenses/>.
#
# Dependencies: flask, psycopg2, jinja2
#
# Execute (debug):
#   flask run [--debug] [--reload]
#

import os
import psycopg2
from flask import Flask, request, redirect, url_for, render_template
from jinja2 import DictLoader

app = Flask(__name__)

# --------------------------------------------------------------------------
# Database connection
# --------------------------------------------------------------------------

# For now it's just unix sockets. Not ideal because if multiple apps run as
# the same user, this app would have some privileges to the others and
# viceversa. But, for now, it allows for publishing without passwords.
# Adjust accordingly.

def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv("PGDATABASE", "prefixary"),
        #user=os.getenv("PGUSER", None),
        #password=os.getenv("PGPASSWORD", None),
        #host=os.getenv("PGHOST", "localhost"),
        #port=os.getenv("PGPORT", 5432),
    )

# --------------------------------------------------------------------------
# Jinja templates
# --------------------------------------------------------------------------

BASE_TEMPLATE = """
<!doctype html>
<html>
<head>
    <meta charset="utf-8">
    <title>{{ title }}</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='stylesheet.css') }}">
</head>
<body>
    {% block body %}{% endblock %}
</body>
</html>
"""

PREFIX_VIEW = """
<!doctype html>
<html>
<head>
    <meta charset="utf-8">
    <title>{{ title }}</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='stylesheet.css') }}">
</head>
<body>

<div class='nav' id='nav_goto'>
  Go to - <a href="{{ url_for('index', prefix='0.0.0.0/0' )}}">IPv4 root</a> | <a href="{{ url_for('index', prefix='0::/0' )}}">IPv6 root</a> | <a href='fixed_prefixes/'>Fixed prefixes</a>
</div>
<div class='nav' id='nav_search'>
  Search - <form action='' method='GET'>By prefix: <input name='prefix' value='{{ prefix }}'></input></form> |
  <form action='descsearch' method='GET'>By description or device name: <input name='keyword' value=''></input></form>
</div>

<h2>Prefix hierarchy</h2>

<table class="prefix-table">
  <thead>
    <tr>
      <th>Record type</th>
      <th></th>
      <th>Prefix</th>
      <th>Description</th>
    </tr>
  </thead>
  <tbody>

{# Ancestors #}
  {% for a in ancestors %}
    <tr class="ancestor" style="font-weight: {{ "bold" if a.record_type|string|trim|upper == "FIXED" else "normal" }};">
      <td>{{ a.record_type }}</td>
      <td></td>
      <td><a href="{{ baseaddress }}{{ a.prefix }}">{{ a.prefix }}</a></td>
      <td>{{ a.description }}</td>
    </tr>
  {% endfor %}

{# Matches #}
  {% if matches %}
    {% for m in matches %}
      <tr class="found" style="font-weight: {{ "bold" if m.record_type|string|trim|upper == "FIXED" else "normal" }};">
        <td>{{ m.record_type }}</td>
        <td>You are here</td>
        <td><a href="{{ baseaddress }}{{ m.prefix }}">{{ m.prefix }}</a></td>
        <td>{{ m.description }}</td>
      </tr>
    {% endfor %}
  {% else %}
      <tr class="not-found">
        <td></td>
        <td>NOT FOUND</td>
        <td>{{ prefix }}</td>
        <td></td>
      </tr>
  {% endif %}

{# Direct children #}
  {% for c in direct_children %}
    <tr class="direct-child" style="font-weight: {{ "bold" if c.record_type|string|trim|upper == "FIXED" else "normal" }};">
      <td>{{ c.record_type }}</td>
      <td></td>
      <td>└─ <a href="{{ baseaddress }}{{ c.prefix }}">{{ c.prefix }}</a></td>
      <td>{{ c.description }}</td>
    </tr>
  {% endfor %}

  </tbody>
</table>


<h2>Occurrences</h2>
<p>The following table shows the devices where {{ prefix }} is being defined.</p>

{% if seen_in_devices and seen_in_devices_headers %}
<table id="instances" border="1">
    <thead>
        <tr>
        {% for h in seen_in_devices_headers %}
            <th>{{ h }}</th>
        {% endfor %}
        </tr>
    </thead>
    <tbody>
    {% for row in seen_in_devices %}
        <tr>
        {% for v in row %}
            <td>{{ v }}</td>
        {% endfor %}
        </tr>
    {% endfor %}
    </tbody>
</table>
{% else %}
<p>No instances found.</p>
{% endif %}

</body>
</html>
"""

DESCSEARCH_VIEW = """
{% extends "base" %}
{% block body %}

<h1>Search: {{ keyword }}</h1>

{% if results %}
<table border="1">
    <thead>
        <tr>
            <th>observed / fixed</th>
            <th>prefix</th>
            <th>description</th>
            <th>device</th>
            <th>entry type</th>
        </tr>
    </thead>
    <tbody>
    {% for r in results %}
        <tr>
            <td>{{ r.record_type }}</td>
            <td><a href="{{ baseaddress }}{{ r.prefix }}">{{ r.prefix }}</a></td>
            <td>{{ r.description }}</td>
            <td>{{ r.device }}</td>
            <td>{{ r.entry_type }}</td>
        </tr>
    {% endfor %}
    </tbody>
</table>
{% else %}
<p>No matches.</p>
{% endif %}

{% endblock %}
"""

FIXED_PREFIXES_LIST_VIEW = """
<!doctype html>
<html>
<head>
    <meta charset="utf-8">
    <title>Fixed prefixes</title>
</head>
<body>
    <a href="..">Go back to main view</a>
    <h1>Fixed prefixes</h1>
    <p><a href="{{ url_for('fixed_prefix_new') }}">New prefix</a></p>

    {% if rows %}
    <table border="1">
        <thead>
            <tr>
                <th>prefix</th>
                <th>description</th>
                <th>actions</th>
            </tr>
        </thead>
        <tbody>
        {% for r in rows %}
            <tr>
                <td>{{ r.prefix }}</td>
                <td>{{ r.description or '' }}</td>
                <td>
                    <a href="{{ url_for('fixed_prefix_edit', prefix=r.prefix) }}">edit</a>
                    |
                    <a href="{{ url_for('fixed_prefix_delete', prefix=r.prefix) }}">del</a>                    
                </td>
            </tr>
        {% endfor %}
        </tbody>
    </table>
    {% else %}
        <p>No prefixes found.</p>
    {% endif %}
</body>
</html>
"""

FIXED_PREFIXES_FORM_VIEW = """
<!doctype html>
<html>
<head>
    <meta charset="utf-8">
    <title>{{ 'Edit' if editing else 'New' }} fixed prefix</title>
</head>
<body>
    <h1>{{ 'Edit' if editing else 'New' }} fixed prefix</h1>

    <form method="post">
        <div>
            <label>prefix (CIDR):</label><br>
            <input type="text" name="prefix" value="{{ prefix or '' }}"
                   {{ 'readonly' if editing else '' }} required>
        </div>

        <div>
            <label>description:</label><br>
            <input type="text" name="description" value="{{ description or '' }}">
        </div>

        <div style="margin-top: 1em;">
            <button type="submit">Save</button>
            <a href="{{ url_for('fixed_prefixes_list') }}">Cancel</a>
        </div>
    </form>
</body>
</html>
"""

FIXED_PREFIXES_DELETE_CONFIRM_VIEW = """
<!doctype html>
<html>
<head>
    <meta charset="utf-8">
    <title>Delete fixed prefix</title>
</head>
<body>
    <h1>Delete fixed prefix</h1>

    <p>Are you sure you want to delete fixed prefix <strong>{{ prefix }}</strong>?</p>

    {% if description %}
    <p>
        <strong>Description:</strong> {{ description or '' }}<br>
    </p>
    {% endif %}

    <form method="post">
        <button type="submit" name="confirm" value="yes">
            Yes, delete
        </button>

        <button type="submit" name="confirm" value="no">
            No, go back
        </button>
    </form>

</body>
</html>
"""

# Register templates in memory
templates = {
    "base": BASE_TEMPLATE,
    "index": PREFIX_VIEW,
    "descsearch": DESCSEARCH_VIEW,
    "fixed_prefixes_list": FIXED_PREFIXES_LIST_VIEW,
    "fixed_prefixes_form": FIXED_PREFIXES_FORM_VIEW,
    "fixed_prefixes_del": FIXED_PREFIXES_DELETE_CONFIRM_VIEW
}
app.jinja_loader = DictLoader(templates)

# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------

@app.route("/")
def index():
    prefix = request.args.get("prefix")
    if not prefix:
        # Equivalent to "Location: ?prefix=0.0.0.0/0" (HTTP header)
        return redirect(url_for("index", prefix="0.0.0.0/0"))

    baseaddress = url_for("index") + "?prefix="

    ancestors = []
    matches = []
    direct_children = []
    seen_in_devices = []
    seen_in_devices_headers = []

    conn = get_db_connection()
    try:
        cur = conn.cursor()

        # ----------------- Ancestors -----------------
        ancestors_sql = """
          SELECT record_type, prefix, description
          FROM all_prefixes_with_best_description
          WHERE prefix >> %(prefix)s
          ORDER BY masklen(prefix);
        """
        cur.execute(ancestors_sql, {'prefix': prefix})
        rows = cur.fetchall()
        for row in rows:
            ancestors.append(
                {
                    "record_type": row[0],
                    "prefix": row[1],
                    "description": row[2],
                }
            )
        print(ancestors)

        # ----------------- Matches -----------------
        matches_sql = """
          SELECT record_type, prefix, description
          FROM all_prefixes_with_best_description
          WHERE prefix = %(prefix)s;
        """
        cur.execute(matches_sql, {'prefix': prefix})
        rows = cur.fetchall()
        for row in rows:
            matches.append(
                {
                    "record_type": row[0],
                    "prefix": row[1],
                    "description": row[2],
                }
            )

        # ----------------- Direct children -----------------
        direct_children_sql = """
          SELECT apwbd.record_type, dc.child as prefix, apwbd.description
          FROM get_direct_children(
               %(prefix)s::cidr,
               (SELECT array_agg(prefixs)
                FROM (SELECT prefix FROM fixed_prefixes
                      UNION
                      SELECT prefix FROM observed_prefixes
                     ) s(prefixs)
               )
               ) dc(child)
            LEFT JOIN all_prefixes_with_best_description apwbd ON dc.child = apwbd.prefix;
        """
        cur.execute(direct_children_sql, {'prefix': prefix})
        rows = cur.fetchall()
        for row in rows:
            direct_children.append(
                {
                    "record_type": row[0],
                    "prefix": row[1],
                    "description": row[2],
                }
            )

        # ----------------- Seen in devices -----------------
        seen_in_devices_sql = """
          SELECT DISTINCT description, device, entry_type
          FROM observed_prefixes
          WHERE prefix = %(prefix)s
          ORDER BY device ASC, entry_type ASC;
        """
        cur.execute(seen_in_devices_sql, {'prefix': prefix})
        rows = cur.fetchall()
        seen_in_devices_headers = [desc[0] for desc in cur.description] if cur.description else []
        for row in rows:
            seen_in_devices.append(row)

        cur.close()
    finally:
        conn.close()
        
    return render_template(
        "index",
        title=prefix,
        prefix=prefix,
        baseaddress=baseaddress,
        ancestors=ancestors,
        matches=matches,
        direct_children=direct_children,
        seen_in_devices=seen_in_devices,
        seen_in_devices_headers=seen_in_devices_headers,
    )

@app.route("/descsearch")
def descsearch():
    keyword = request.args.get("keyword", "")
    baseaddress = url_for("index") + "?prefix="
    results = []

    if keyword:
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            search_sql = """
              SELECT record_type, prefix, description, device, entry_type, %(keyword)s
              FROM all_prefixes
              WHERE description ILIKE %(pattern)s OR device ILIKE %(pattern)s
              ORDER BY device ASC, entry_type ASC;
            """
            cur.execute(search_sql, {'keyword': keyword, 'pattern': '%' + keyword + '%'})
            rows = cur.fetchall()
            for row in rows:
                results.append(
                    {
                        "record_type": row[0],
                        "prefix": row[1],
                        "description": row[2],
                        "device": row[3],
                        "entry_type": row[4],
                        "search": row[5],
                    }
                )
            cur.close()
        finally:
            conn.close()

    return render_template(
        "descsearch",
        title=keyword or "Search",
        keyword=keyword,
        baseaddress=baseaddress,
        results=results,
    )

# --------------------------------------------------------------------------

# -------------------------------------------------------------------
# LIST: GET /fixed_prefixes/
# -------------------------------------------------------------------
@app.route("/fixed_prefixes/")
def fixed_prefixes_list():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT prefix::text, description
            FROM fixed_prefixes
            ORDER BY prefix;
        """)
        rows = cur.fetchall()
        cur.close()
    finally:
        conn.close()

    rows_dict = [
        {"prefix": r[0], "description": r[1]}
        for r in rows
    ]

    return render_template(
        "fixed_prefixes_list",
        rows=rows_dict,
    )

# -------------------------------------------------------------------
# CREATE: GET/POST /fixed_prefixes/new
# -------------------------------------------------------------------
@app.route("/fixed_prefixes/new", methods=["GET", "POST"])
def fixed_prefix_new():
    if request.method == "POST":
        prefix = request.form.get("prefix", "").strip()
        description = request.form.get("description", "").strip() or None

        if not prefix:
            abort(400, "prefix is mandatory")

        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO fixed_prefixes (prefix, description)
                VALUES (%s::cidr, %s);
            """, (prefix, description))
            conn.commit()
            cur.close()
        finally:
            conn.close()

        return redirect(url_for("fixed_prefixes_list"))

    # GET
    return render_template(
        "fixed_prefixes_form",
        editing=False,
        prefix="",
        description="",
    )

# -------------------------------------------------------------------
# EDIT: GET/POST /fixed_prefixes/<prefix>/edit
# We use <path:prefix> because CIDRs have a slash (ex: 10.0.0.0/8)
# -------------------------------------------------------------------
@app.route("/fixed_prefixes/<path:prefix>/edit", methods=["GET", "POST"])
def fixed_prefix_edit(prefix):
    if request.method == "POST":
        # prefix is readonly in the form while updating
        description = request.form.get("description", "").strip() or None

        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                UPDATE fixed_prefixes
                SET description = %s
                WHERE prefix = %s::cidr;
            """, (description, prefix))
            if cur.rowcount == 0:
                conn.rollback()
                cur.close()
                abort(404, "Prefix not found")
            conn.commit()
            cur.close()
        finally:
            conn.close()

        return redirect(url_for("fixed_prefixes_list"))

    # GET: load current record
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT prefix::text, description
            FROM fixed_prefixes
            WHERE prefix = %s::cidr;
        """, (prefix,))
        row = cur.fetchone()
        cur.close()
    finally:
        conn.close()

    if not row:
        abort(404, "Prefix not found")

    return render_template(
        "fixed_prefixes_form",
        editing=True,
        prefix=row[0],
        description=row[1],
    )

# -------------------------------------------------------------------
# DELETE: POST /fixed_prefixes/<prefix>/delete
# -------------------------------------------------------------------
@app.route("/fixed_prefixes/<path:prefix>/delete", methods=["GET", "POST"])
def fixed_prefix_delete(prefix):
    # POST
    if request.method == "POST":
        if request.form.get("confirm") == "yes":
            conn = get_db_connection()
            try:
                cur = conn.cursor()
                cur.execute("""
                    DELETE FROM fixed_prefixes
                    WHERE prefix = %s::cidr;
                """, (prefix,))
                if cur.rowcount == 0:
                    conn.rollback()
                    cur.close()
                    abort(404, "Prefix not found")
                conn.commit()
                cur.close()
            finally:
                conn.close()

        return redirect(url_for("fixed_prefixes_list"))

    # GET
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT prefix::text, description
            FROM fixed_prefixes
            WHERE prefix = %s::cidr;
        """, (prefix,))
        row = cur.fetchone()
        cur.close()
    finally:
        conn.close()

    if not row:
        abort(404, "Prefix not found")

    return render_template(
        "fixed_prefixes_del",
        prefix=row[0],
        description=row[1],
    )

if __name__ == "__main__":
    app.run(debug=False)

