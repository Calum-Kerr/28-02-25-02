# run.py
from app import create_app

app = create_app()

if __name__ == '__main__':
    # Running on host 0.0.0.0 to be accessible externally (Heroku requirement)
    app.run(host='0.0.0.0', port=5000)