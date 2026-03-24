from app.admin.views import SourceAIPromtView, SourceFilterView, SourceRssView, SourceTgView

def add_all_views1(appbuilder):
    appbuilder.add_view(SourceTgView, "Источники Telegram", category="Источники")
    appbuilder.add_view(SourceRssView, "Источники RSS", category="Источники")
    appbuilder.add_view(SourceAIPromtView, "AI промпты", category="Дополнительно")
    appbuilder.add_view(SourceFilterView, "Фильтры", category="Дополнительно")

def create_admin(appbuilder, admin_name, admin_pass):
    if not appbuilder.sm.find_user(username="admin"):
        role_admin = appbuilder.sm.find_role("Admin")
        appbuilder.sm.add_user(
            username=admin_name,
            first_name="Admin",
            last_name="Adminov",
            email="admin@example.com",
            role=role_admin,
            password=admin_pass)
        print(f"Администратор создан: {admin_name}")