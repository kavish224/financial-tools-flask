from app import create_app

app = create_app()
app.config.from_object("config.DevelopmentConfig")
