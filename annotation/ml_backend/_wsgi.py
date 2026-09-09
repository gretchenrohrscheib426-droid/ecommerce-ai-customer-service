import importlib
import logging
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault("MODEL_DIR", str(ROOT / "artifacts/local/ml-backend"))
Path(os.environ["MODEL_DIR"]).mkdir(parents=True, exist_ok=True)
logging.basicConfig(level=logging.WARNING)
flask = importlib.import_module("flask")
jsonify, request = flask.jsonify, flask.request
init_app = importlib.import_module("label_studio_ml.api").init_app
model = importlib.import_module("model")
InferenceUnavailable, TagBackend = model.InferenceUnavailable, model.TagBackend

app = init_app(TagBackend)
app.config["MAX_CONTENT_LENGTH"] = 128 * 1024


def predict_endpoint():
    """Keep SDK models/response protocol, without its traceback-leaking decorator."""
    data = request.get_json()
    if not isinstance(data, dict):
        raise ValueError("JSON object required")
    model = TagBackend(
        project_id=str(data.get("project", "")).split(".")[0], label_config=data.get("label_config", "")
    )
    response = model.predict(data.get("tasks"), context=(data.get("params") or {}).get("context"))
    response.update_predictions_version()
    return jsonify({"results": response.model_dump()["predictions"]})


app.view_functions["_predict"] = predict_endpoint


@app.after_request
def remove_internal_errors(response):
    if response.status_code >= 500 and response.status_code != 503:
        safe = jsonify({"error": "backend_failure", "detail": "See local redacted backend log"})
        safe.status_code = response.status_code
        return safe
    return response


@app.errorhandler(InferenceUnavailable)
def unavailable(error):
    return jsonify({"error": "inference_blocked", "detail": str(error)}), 503


@app.errorhandler(ValueError)
def bad_input(error):
    return jsonify({"error": "invalid_input", "detail": str(error)}), 400


if __name__ == "__main__":
    from waitress import serve

    serve(
        app,
        host="127.0.0.1",
        port=int(os.environ.get("ML_BACKEND_PORT", "9092")),
        threads=2,
        channel_timeout=35,
    )
