from cryptography.fernet import Fernet, InvalidToken


class Cryptographer:
    def __init__(self, fernet: Fernet):
        self.fernet = fernet

    def create_token(self, data: str):
        return self.fernet.encrypt(data.encode())

    def verify_token(self, token: bytes, ttl: int = 3600) -> str:
        try:
            return self.fernet.decrypt(token, ttl=ttl).decode()
        except InvalidToken:
            raise ValueError("Provided token is invalid")
