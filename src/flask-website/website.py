from flask import Flask, render_template, redirect, url_for, request
import urllib.request
import json

app = Flask(__name__)

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

@app.route("/")
def start():
    return redirect(url_for("loadbalancers"))

@app.route("/loadbalancers")
def loadbalancers():
    data = get_api_data("/loadbalancers")
    return render_template("loadbalancers.html", data=data)

@app.route("/loadbalancers/<int:lb_id>")
def loadbalancer_detail(lb_id):
    data = get_api_data(f"/loadbalancers/{lb_id}")
    return render_template("loadbalancer_detail.html", data=data)

@app.route("/loadbalancers/add", methods=["GET", "POST"])
def add_loadbalancer():
    if request.method == "POST":
        payload = {
            "name": request.form["name"],
            "ip_bind": request.form["ip_bind"],
            "pass": request.form["pass"]
        }

        post_api_data("/loadbalancers", payload)
        return redirect(url_for("loadbalancers"))

    return render_template("add_loadbalancer.html")

def delete_api_data(path):
    req = urllib.request.Request(
        API_URL + path,
        method="DELETE"
    )

    with urllib.request.urlopen(req) as response:
        data = response.read().decode("utf-8")
        return json.loads(data)

@app.route("/loadbalancers/delete/<int:lb_id>", methods=["POST"])
def delete_loadbalancer(lb_id):
    delete_api_data(f"/loadbalancers/{lb_id}")
    return redirect(url_for("loadbalancers"))


@app.route("/webservers")
def webservers():
    data = get_api_data("/webservers")
    return render_template("webservers.html", data=data)

@app.route("/webservers/<int:web_id>")
def webserver_detail(web_id):
    data = get_api_data(f"/webservers/{web_id}")
    return render_template("webserver_detail.html", data=data)

@app.route("/webservers/add", methods=["GET", "POST"])
def add_webserver():
    if request.method == "POST":
        payload = {
            "name": request.form["name"],
            "root": request.form["root"],
            "index": request.form["index"],
            "error_page": request.form["error_page"],
            "error_root": request.form["error_root"]
        }

        post_api_data("/webservers", payload)
        return redirect(url_for("webservers"))

    return render_template("add_webserver.html")

@app.route("/webservers/delete/<int:web_id>", methods=["POST"])
def delete_webserver(web_id):
    delete_api_data(f"/webservers/{web_id}")
    return redirect(url_for("webservers"))


@app.route("/reverseproxies")
def reverseproxies():
    data = get_api_data("/reverseproxies")
    return render_template("reverseproxies.html", data=data)

@app.route("/reverseproxies/<int:proxy_id>")
def reverseproxy_detail(proxy_id):
    data = get_api_data(f"/reverseproxies/{proxy_id}")
    return render_template("reverseproxy_detail.html", data=data)

@app.route("/reverseproxies/add", methods=["GET", "POST"])
def add_reverseproxy():
    if request.method == "POST":
        payload = {
            "name": request.form["name"],
            "upstream_name": request.form["upstream_name"],
            "lb_strategy_method": request.form["lb_strategy_method"],
            "server1": request.form["server1"],
            "server2": request.form["server2"],
            "proxy_pass": request.form["proxy_pass"]
        }

        post_api_data("/reverseproxies", payload)
        return redirect(url_for("reverseproxies"))

    return render_template("add_reverseproxy.html")

@app.route("/reverseproxies/delete/<int:proxy_id>", methods=["POST"])
def delete_reverseproxy(proxy_id):
    delete_api_data(f"/reverseproxies/{proxy_id}")
    return redirect(url_for("reverseproxies"))