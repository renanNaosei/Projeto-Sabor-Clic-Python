from dotenv import load_dotenv

load_dotenv()  # precisa vir antes de importar a aplicação (lê SECRET_KEY, DATABASE_URL...)

from app import create_app

app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=app.config.get("DEBUG", False))
