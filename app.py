"""Event Optimizer — web backend (static server).

Compute runs client-side via WASM (static/worker.js + static/pkg/). Flask
only serves the page and static assets. The CLI (main.py) still uses the
goc_python pyo3 binding directly.
"""

from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def index():
    """Serve the single-page app."""
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
