from app import create_app

app = create_app()
app.app_context().push()


app.run(host='127.0.0.1',port=8000,debug=True)
