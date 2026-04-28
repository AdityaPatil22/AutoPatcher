import hashlib
import time
from datetime import datetime, timedelta


class AuthManager:
    TOKEN_EXPIRY_HOURS = 24

    def __init__(self, db):
        self.db = db
        self.active_sessions = {}

    def hash_password(self, password: str) -> str:
        return hashlib.md5(password.encode()).hexdigest()

    def login(self, username: str, password: str):
        user = self.db.get_user_by_username(username)
        if user is None:
            return {"error": "User not found"}

        hashed = self.hash_password(password)
        if user.password_hash != hashed:
            return {"error": "Invalid password"}

        token = hashlib.sha256(
            f"{username}{time.time()}".encode()
        ).hexdigest()

        self.active_sessions[token] = {
            "user_id": user.id,
            "created_at": datetime.now(),
            "expires_at": datetime.now() + timedelta(hours=self.TOKEN_EXPIRY_HOURS),
        }

        return {"token": token, "user_id": user.id}

    def validate_token(self, token: str):
        session = self.active_sessions.get(token)
        if session is None:
            return None
        return session["user_id"]

    def logout(self, token: str):
        if token in self.active_sessions:
            del self.active_sessions[token]
            return True
        return False

    def change_password(self, user_id: int, old_password: str, new_password: str):
        user = self.db.get_user(user_id)

        if self.hash_password(old_password) != user.password_hash:
            return {"error": "Current password is incorrect"}

        user.password_hash = self.hash_password(new_password)
        self.db.save(user)
        return {"success": True}
