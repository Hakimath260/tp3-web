from flask import Flask, jsonify, request
import json

app = Flask(__name__)

def read_json(name):
    with open(f"data/{name}.json", encoding="utf-8") as f:
        return json.load(f)

def write_json(name, data):
    with open(f"data/{name}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.route("/")
def hello():
    return "Hello, API!"

@app.route("/loadbalancers")
def get_loadbalancers():
    data = read_json("loadbalancer")
    return jsonify(data)

@app.route("/loadbalancers/<int:lb_id>")
def get_loadbalancer(lb_id):
    data = read_json("loadbalancer")
    for item in data:
        if item["id"] == lb_id:
            return jsonify(item)
    return jsonify({"error": "Load balancer introuvable"}), 404

@app.route("/loadbalancers", methods=["POST"])
def add_loadbalancer():
    data = read_json("loadbalancer")
    payload = request.get_json()

    new_id = max(item["id"] for item in data) + 1 if data else 1

    new_item = {
        "id": new_id,
        "name": payload["name"],
        "ip_bind": payload["ip_bind"],
        "pass": payload["pass"]
    }

    data.append(new_item)
    write_json("loadbalancer", data)

    return jsonify(new_item), 201

@app.route("/loadbalancers/<int:lb_id>", methods=["DELETE"])
def delete_loadbalancer(lb_id):
    data = read_json("loadbalancer")
    new_data = [item for item in data if item["id"] != lb_id]

    if len(new_data) == len(data):
        return jsonify({"error": "Load balancer introuvable"}), 404

    write_json("loadbalancer", new_data)
    return jsonify({"message": "Load balancer supprimé"})

@app.route("/webservers")
def get_webservers():
    data = read_json("webserver")
    return jsonify(data)

@app.route("/webservers/<int:web_id>")
def get_webserver(web_id):
    data = read_json("webserver")
    for item in data:
        if item["id"] == web_id:
            return jsonify(item)
    return jsonify({"error": "Web server introuvable"}), 404

@app.route("/webservers", methods=["POST"])
def add_webserver():
    data = read_json("webserver")
    payload = request.get_json()

    new_id = max(item["id"] for item in data) + 1 if data else 1

    new_item = {
        "id": new_id,
        "name": payload["name"],
        "root": payload["root"],
        "index": payload["index"],
        "error_page": payload["error_page"],
        "error_root": payload["error_root"]
    }

    data.append(new_item)
    write_json("webserver", data)

    return jsonify(new_item), 201

@app.route("/webservers/<int:web_id>", methods=["DELETE"])
def delete_webserver(web_id):
    data = read_json("webserver")
    new_data = [item for item in data if item["id"] != web_id]

    if len(new_data) == len(data):
        return jsonify({"error": "Web server introuvable"}), 404

    write_json("webserver", new_data)
    return jsonify({"message": "Web server supprimé"})

@app.route("/reverseproxies")
def get_reverseproxies():
    data = read_json("reverseproxy")
    return jsonify(data)

@app.route("/reverseproxies/<int:proxy_id>")
def get_reverseproxy(proxy_id):
    data = read_json("reverseproxy")
    for item in data:
        if item["id"] == proxy_id:
            return jsonify(item)
    return jsonify({"error": "Reverse proxy introuvable"}), 404

@app.route("/reverseproxies", methods=["POST"])
def add_reverseproxy():
    data = read_json("reverseproxy")
    payload = request.get_json()

    new_id = max(item["id"] for item in data) + 1 if data else 1

    new_item = {
        "id": new_id,
        "name": payload["name"],
        "upstream_name": payload["upstream_name"],
        "lb_strategy_method": payload["lb_strategy_method"],
        "server1": payload["server1"],
        "server2": payload["server2"],
        "proxy_pass": payload["proxy_pass"]
    }

    data.append(new_item)
    write_json("reverseproxy", data)

    return jsonify(new_item), 201

@app.route("/reverseproxies/<int:proxy_id>", methods=["DELETE"])
def delete_reverseproxy(proxy_id):
    data = read_json("reverseproxy")
    new_data = [item for item in data if item["id"] != proxy_id]

    if len(new_data) == len(data):
        return jsonify({"error": "Reverse proxy introuvable"}), 404

    write_json("reverseproxy", new_data)
    return jsonify({"message": "Reverse proxy supprimé"})