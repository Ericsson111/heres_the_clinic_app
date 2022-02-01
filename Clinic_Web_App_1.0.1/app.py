from clinic import app, db

if __name__ == '__main__':
    db.create_all()
    app.jinja_env.cache = {}
    app.run(debug=True)