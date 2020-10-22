from application import create_app

app = create_app(testing=False, debug=False)

if __name__ == "__main__":
    app.run()


# eof
