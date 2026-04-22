import os
import requests
from flask import Flask, render_template, request, redirect, url_for


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates")

    workflow_base_url = os.getenv("WORKFLOW_BASE_URL", "http://workflow-service:8081")

    @app.get("/")
    def index():
        return render_template("form.html")

    @app.post("/submit")
    def submit():
        form_data = {
            "title": request.form.get("title", "").strip(),
            "description": request.form.get("description", "").strip(),
            "location": request.form.get("location", "").strip(),
            "date": request.form.get("date", "").strip(),
            "organiser": request.form.get("organiser", "").strip(),
        }

        try:
            response = requests.post(
                f"{workflow_base_url}/api/submissions",
                json=form_data,
                timeout=5
            )
        except requests.RequestException:
            return render_template(
                "error.html",
                message="Workflow service is unavailable."
            ), 503

        if response.status_code not in (200, 201):
            return render_template(
                "error.html",
                message=f"Submission failed. Status code: {response.status_code}"
            ), 500

        data = response.json()
        submission_id = data.get("submission_id")

        if not submission_id:
            return render_template(
                "error.html",
                message="No submission ID returned by workflow service."
            ), 500

        return redirect(url_for("status_page", submission_id=submission_id))

    @app.get("/status/<submission_id>")
    def status_page(submission_id: str):
        try:
            response = requests.get(
                f"{workflow_base_url}/api/submissions/{submission_id}",
                timeout=5
            )
        except requests.RequestException:
            return render_template(
                "error.html",
                message="Unable to retrieve submission status."
            ), 503

        if response.status_code == 404:
            return render_template(
                "error.html",
                message="Submission not found."
            ), 404

        if response.status_code != 200:
            return render_template(
                "error.html",
                message=f"Failed to load result. Status code: {response.status_code}"
            ), 500

        data = response.json()
        return render_template(
            "status.html",
            submission_id=data.get("submission_id"),
            input_data=data.get("input", {}),
            result=data.get("result", {}),
        )

    @app.get("/health")
    def health() -> str:
        return "ok"

    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=8080)
