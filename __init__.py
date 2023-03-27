from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flaskext.markdown import Markdown
import os

db = SQLAlchemy()
#IMAGE_FOLDER = os.path.join('static', 'images')


def create_app():
    app_b = Flask(__name__,
                  static_url_path='',
                  static_folder='flask_auth_app/static',)
    app_b.config['SECRET_KEY'] = 'secret-key-goes-here'
    app_b.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
#    app_b.config['UPLOAD_FOLDER'] = IMAGE_FOLDER
    db.init_app(app_b)

    from .auth import auth as auth_blueprint
    app_b.register_blueprint(auth_blueprint)

    from .main import main as main_blueprint
    app_b.register_blueprint(main_blueprint)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app_b)

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        # since the user_id is just the primary key of our user table, use it in the query for the user
        return User.query.get(int(user_id))

    with app_b.app_context():
        db.create_all()

    return app_b


app = create_app()
Markdown(app)
