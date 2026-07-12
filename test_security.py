from backend.config.security import (
    hash_password,
    verify_password,
    create_access_token,
)

password = "Admin@123"

hashed = hash_password(password)

print(hashed)
print(verify_password(password, hashed))
print(create_access_token({"sub": "admin"}))