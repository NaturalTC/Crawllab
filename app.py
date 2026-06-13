import os
from flask import Flask, jsonify, render_template
from dotenv import load_dotenv
from benchmark.runner import start_benchmark, get_state, load_saved_results

load_dotenv()

app = Flask(__name__)

SEED      = os.getenv("SEED_URL", "https://en.wikipedia.org/wiki/Main_Page")
MAX_PAGES = int(os.getenv("MAX_PAGES", 50))
WORKERS   = int(os.getenv("WORKERS", 10))
REPEATS   = int(os.getenv("REPEATS", 3))
MONGO_URI = os.getenv("MONGODB_URI")
DB_NAME   = os.getenv("MONGODB_DBNAME", "webCrawlerArchive")


@app.route("/")
def index():
    return render_template("index.html",
        results=load_saved_results(),
        mongo_configured=bool(MONGO_URI),
        config={"seed": SEED, "max_pages": MAX_PAGES, "workers": WORKERS, "repeats": REPEATS},
    )


@app.route("/api/run", methods=["POST"])
def run():
    started = start_benchmark(SEED, MAX_PAGES, WORKERS, REPEATS, MONGO_URI, DB_NAME)
    if not started:
        return jsonify({"error": "Benchmark already running"}), 409
    return jsonify({"status": "started"})


@app.route("/api/status")
def status():
    state = get_state()
    return jsonify({"running": state["running"], "progress": state["progress"], "error": state["error"]})


@app.route("/api/results")
def results():
    state = get_state()
    data = state["results"] or load_saved_results()
    if not data:
        return jsonify({"error": "No results yet"}), 404
    return jsonify(data)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
