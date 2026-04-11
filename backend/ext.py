from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

# 在 app.py 中统一 init_app
db = SQLAlchemy()
bcrypt = Bcrypt()
