import os

from flask import Flask
from flask_appbuilder import AppBuilder
from flask_sqlalchemy import SQLAlchemy
from app.admin.views import SourceAIPromtView, SourceFilterView, SourceRssView, SourceTgView
from app import DB_PATH

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{DB_PATH}"
app.config['SECRET_KEY'] = 'your-secure-key'
app.config['CSRF_ENABLED'] = True
app.config['APP_NAME'] = "TeleReposter админка"



def start_admin_app():
    db = SQLAlchemy(app)

    with app.app_context():
        appbuilder = AppBuilder(app, db.session) # type: ignore

        appbuilder.add_view(SourceTgView, "Источники Telegram", category="Источники")
        appbuilder.add_view(SourceRssView, "Источники RSS", category="Источники")
        appbuilder.add_view(SourceAIPromtView, "AI промпты", category="Дополнительно")
        appbuilder.add_view(SourceFilterView, "Фильтры", category="Дополнительно")

        if not appbuilder.sm.find_user(username="admin"):
            role_admin = appbuilder.sm.find_role("Admin")
            appbuilder.sm.add_user(
                    username="admin",
                    first_name="Admin",
                    last_name="User",
                    email="admin@example.com",
                    role=role_admin,
                    password="password123")
            print("Администратор создан: логин 'admin', пароль 'password123'")

    app.run(host="0.0.0.0", port=8080, debug=False)

if __name__ == "__main__":
    start_admin_app()  