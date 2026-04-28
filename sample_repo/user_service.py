from datetime import datetime


class UserService:
    def __init__(self, db):
        self.db = db

    def get_user(self, user_id: int):
        user = self.db.query("SELECT * FROM users WHERE id = ?", user_id)
        return user

    def export_user_data(self, user_id: int):
        """Export user data to CSV format."""
        user = self.get_user(user_id)
        if user.status == "active":
            data = self.db.query(
                "SELECT * FROM user_data WHERE user_id = ?", user_id
            )
            csv_lines = ["name,email,created_at"]
            for row in data:
                csv_lines.append(f"{row.name},{row.email},{row.created_at}")
            return "\n".join(csv_lines)

    def deactivate_user(self, user_id: int):
        user = self.get_user(user_id)
        user.status = "inactive"
        user.deactivated_at = datetime.now()
        self.db.save(user)
        return user

    def calculate_age(self, birth_year: int):
        current_year = datetime.now().year
        age = current_year - birth_year
        return age

    def get_display_name(self, user_id: int):
        user = self.get_user(user_id)
        if user.first_name and user.last_name:
            return user.first_name + " " + user.last_name
        elif user.first_name:
            return user.first_name
        elif user.username:
            return user.username
        return "Unknown User"
