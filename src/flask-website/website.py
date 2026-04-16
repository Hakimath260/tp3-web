from flask import Flask, render_template, redirect, url_for, request, session, flash, Response
import urllib.request
import json
from functools import wraps
from werkzeug.security import check_password_hash
import re

app = Flask(__name__)
app.secret_key = "tp-web-secret-key-2026"

API_URL = "http://127.0.0.1:5000"


def get_api_data(path):
    with urllib.request.urlopen(API_URL + path) as response:
        data = response.read().decode("utf-8")
        return json.loads(data)


def post_api_data(path, payload):
    json_data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        API_URL + path,
        data=json_data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(req) as response:
        data = response.read().decode("utf-8")
        return json.loads(data)


def delete_api_data(path):
    req = urllib.request.Request(
        API_URL + path,
        method="DELETE"
    )

    with urllib.request.urlopen(req) as response:
        data = response.read().decode("utf-8")
        return json.loads(data)


def read_local_json(name):
    with open(f"data/{name}.json", encoding="utf-8") as f:
        return json.load(f)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


def is_valid_name(value):
    return re.fullmatch(r"[A-Za-z0-9 _-]{2,50}", value) is not None


def is_valid_upstream_name(value):
    return re.fullmatch(r"[A-Za-z0-9 _-]{2,50}", value) is not None


def is_valid_lb_method(value):
    return value in ["least_conn", "ip_hash", "round_robin"]


def is_valid_server(value):
    return re.fullmatch(r"[A-Za-z0-9.-]{3,100}", value) is not None


def is_valid_proxy_pass(value):
    return re.fullmatch(r"https?://[A-Za-z0-9._/-]+", value) is not None


def is_valid_path(value):
    return re.fullmatch(r"/[A-Za-z0-9_./-]+", value) is not None


def is_valid_index(value):
    return re.fullmatch(r"[A-Za-z0-9_. -]+", value) is not None


def is_valid_error_page(value):
    return re.fullmatch(r"(\d{3}\s+)+/[A-Za-z0-9_./-]+", value) is not None


def is_valid_ipv4(value):
    if re.fullmatch(r"(\d{1,3}\.){3}\d{1,3}", value) is None:
        return False
    parts = value.split(".")
    return all(0 <= int(part) <= 255 for part in parts)


def safe_filename(value):
    return re.sub(r"[^A-Za-z0-9_-]", "_", value)


def generate_loadbalancer_config(data):
    return f"""http {{
    server {{
        location / {{
            proxy_bind {data['ip_bind']};
            proxy_pass {data['pass']};
        }}
    }}
}}
"""


def generate_webserver_config(data):
    return f"""http {{
    server {{
        root {data['root']};

        location / {{
            index {data['index']};
        }}

        error_page {data['error_page']};
        location = /error-page.html {{
            root {data['error_root']};
            internal;
        }}
    }}
}}
"""


def generate_reverseproxy_config(data):
    return f"""http {{
    upstream {data['upstream_name']} {{
        {data['lb_strategy_method']};
        server {data['server1']};
        server {data['server2']};
    }}

    server {{
        location / {{
            proxy_pass {data['proxy_pass']};
        }}
    }}
}}
"""


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        users = read_local_json("users")

        for user in users:
            if user["username"] == username and check_password_hash(user["password"], password):
                session["user"] = username
                return redirect(url_for("start"))

        flash("Identifiants invalides", "danger")
        return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))


@app.route("/")
@login_required
def start():
    return redirect(url_for("loadbalancers"))


@app.route("/loadbalancers")
@login_required
def loadbalancers():
    data = get_api_data("/loadbalancers")
    return render_template("loadbalancers.html", data=data)


@app.route("/loadbalancers/<int:lb_id>")
@login_required
def loadbalancer_detail(lb_id):
    data = get_api_data(f"/loadbalancers/{lb_id}")
    return render_template("loadbalancer_detail.html", data=data)


@app.route("/loadbalancers/add", methods=["GET", "POST"])
@login_required
def add_loadbalancer():
    if request.method == "POST":
        name = request.form["name"].strip()
        ip_bind = request.form["ip_bind"].strip()
        proxy_pass = request.form["pass"].strip()

        if not is_valid_name(name):
            flash("Nom invalide. Utilisez lettres, chiffres, espaces, tirets ou underscores.", "danger")
            return redirect(url_for("add_loadbalancer"))

        if not is_valid_ipv4(ip_bind):
            flash("IP Bind invalide. Entrez une adresse IPv4 correcte.", "danger")
            return redirect(url_for("add_loadbalancer"))

        if not is_valid_proxy_pass(proxy_pass):
            flash("Proxy Pass invalide. Il doit commencer par http:// ou https://", "danger")
            return redirect(url_for("add_loadbalancer"))

        payload = {
            "name": name,
            "ip_bind": ip_bind,
            "pass": proxy_pass
        }

        post_api_data("/loadbalancers", payload)
        return redirect(url_for("loadbalancers"))

    return render_template("add_loadbalancer.html")


@app.route("/loadbalancers/delete/<int:lb_id>", methods=["POST"])
@login_required
def delete_loadbalancer(lb_id):
    delete_api_data(f"/loadbalancers/{lb_id}")
    return redirect(url_for("loadbalancers"))


@app.route("/loadbalancers/<int:lb_id>/download")
@login_required
def download_loadbalancer_config(lb_id):
    data = get_api_data(f"/loadbalancers/{lb_id}")
    config_text = generate_loadbalancer_config(data)
    filename = f"{safe_filename(data['name'])}.conf"

    return Response(
        config_text,
        mimetype="text/plain",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.route("/webservers")
@login_required
def webservers():
    data = get_api_data("/webservers")
    return render_template("webservers.html", data=data)


@app.route("/webservers/<int:web_id>")
@login_required
def webserver_detail(web_id):
    data = get_api_data(f"/webservers/{web_id}")
    return render_template("webserver_detail.html", data=data)


@app.route("/webservers/add", methods=["GET", "POST"])
@login_required
def add_webserver():
    if request.method == "POST":
        name = request.form["name"].strip()
        root = request.form["root"].strip()
        index = request.form["index"].strip()
        error_page = request.form["error_page"].strip()
        error_root = request.form["error_root"].strip()

        if not is_valid_name(name):
            flash("Nom invalide. Utilisez lettres, chiffres, espaces, tirets ou underscores.", "danger")
            return redirect(url_for("add_webserver"))

        if not is_valid_path(root):
            flash("Root invalide. Entrez un chemin absolu commençant par /", "danger")
            return redirect(url_for("add_webserver"))

        if not is_valid_index(index):
            flash("Index invalide. Entrez un ou plusieurs noms de fichiers séparés par des espaces.", "danger")
            return redirect(url_for("add_webserver"))

        if not is_valid_error_page(error_page):
            flash("Error Page invalide. Format attendu : codes HTTP suivis d’un chemin, par exemple 404 500 /error-page.html", "danger")
            return redirect(url_for("add_webserver"))

        if not is_valid_path(error_root):
            flash("Error Root invalide. Entrez un chemin absolu commençant par /", "danger")
            return redirect(url_for("add_webserver"))

        payload = {
            "name": name,
            "root": root,
            "index": index,
            "error_page": error_page,
            "error_root": error_root
        }

        post_api_data("/webservers", payload)
        return redirect(url_for("webservers"))

    return render_template("add_webserver.html")


@app.route("/webservers/delete/<int:web_id>", methods=["POST"])
@login_required
def delete_webserver(web_id):
    delete_api_data(f"/webservers/{web_id}")
    return redirect(url_for("webservers"))


@app.route("/webservers/<int:web_id>/download")
@login_required
def download_webserver_config(web_id):
    data = get_api_data(f"/webservers/{web_id}")
    config_text = generate_webserver_config(data)
    filename = f"{safe_filename(data['name'])}.conf"

    return Response(
        config_text,
        mimetype="text/plain",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.route("/reverseproxies")
@login_required
def reverseproxies():
    data = get_api_data("/reverseproxies")
    return render_template("reverseproxies.html", data=data)


@app.route("/reverseproxies/<int:proxy_id>")
@login_required
def reverseproxy_detail(proxy_id):
    data = get_api_data(f"/reverseproxies/{proxy_id}")
    return render_template("reverseproxy_detail.html", data=data)


@app.route("/reverseproxies/add", methods=["GET", "POST"])
@login_required
def add_reverseproxy():
    if request.method == "POST":
        name = request.form["name"].strip()
        upstream_name = request.form["upstream_name"].strip()
        lb_strategy_method = request.form["lb_strategy_method"].strip()
        server1 = request.form["server1"].strip()
        server2 = request.form["server2"].strip()
        proxy_pass = request.form["proxy_pass"].strip()

        if not is_valid_name(name):
            flash("Nom invalide. Utilisez lettres, chiffres, espaces, tirets ou underscores.", "danger")
            return redirect(url_for("add_reverseproxy"))

        if not is_valid_upstream_name(upstream_name):
            flash("Nom Upstream invalide. Utilisez lettres, chiffres, espaces, tirets ou underscores.", "danger")
            return redirect(url_for("add_reverseproxy"))

        if not is_valid_lb_method(lb_strategy_method):
            flash("Méthode d'équilibrage invalide. Valeurs autorisées : least_conn, ip_hash, round_robin.", "danger")
            return redirect(url_for("add_reverseproxy"))

        if not is_valid_server(server1):
            flash("Server 1 invalide. Entrez un nom de serveur ou de domaine valide.", "danger")
            return redirect(url_for("add_reverseproxy"))

        if not is_valid_server(server2):
            flash("Server 2 invalide. Entrez un nom de serveur ou de domaine valide.", "danger")
            return redirect(url_for("add_reverseproxy"))

        if not is_valid_proxy_pass(proxy_pass):
            flash("Proxy Pass invalide. Il doit commencer par http:// ou https://", "danger")
            return redirect(url_for("add_reverseproxy"))

        payload = {
            "name": name,
            "upstream_name": upstream_name,
            "lb_strategy_method": lb_strategy_method,
            "server1": server1,
            "server2": server2,
            "proxy_pass": proxy_pass
        }

        post_api_data("/reverseproxies", payload)
        return redirect(url_for("reverseproxies"))

    return render_template("add_reverseproxy.html")


@app.route("/reverseproxies/delete/<int:proxy_id>", methods=["POST"])
@login_required
def delete_reverseproxy(proxy_id):
    delete_api_data(f"/reverseproxies/{proxy_id}")
    return redirect(url_for("reverseproxies"))


@app.route("/reverseproxies/<int:proxy_id>/download")
@login_required
def download_reverseproxy_config(proxy_id):
    data = get_api_data(f"/reverseproxies/{proxy_id}")
    config_text = generate_reverseproxy_config(data)
    filename = f"{safe_filename(data['name'])}.conf"

    return Response(
        config_text,
        mimetype="text/plain",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )