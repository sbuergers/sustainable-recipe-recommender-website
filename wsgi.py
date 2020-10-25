from application import create_app

app = create_app(testing=True, debug=True)

if __name__ == "__main__":
    app.run()


# eof
