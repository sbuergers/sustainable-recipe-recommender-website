from application import create_app
from config import DevConfig

app = create_app(cfg=DevConfig)

if __name__ == "__main__":
    app.run()


# eof
