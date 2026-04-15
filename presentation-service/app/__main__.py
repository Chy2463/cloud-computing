from flask import Flask


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/")
    def health() -> str:
        return "ok"

    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=8080)

