from passlib.context import CryptContext

# Create a CryptContext instance with bcrypt as the hashing scheme
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify if the provided plain password matches the hashed password.

    Args:
    - plain_password: The password provided by the user during login.
    - hashed_password: The stored hashed password in the database.

    Returns:
    - bool: True if passwords match, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
    - password: The plain password to hash.

    Returns:
    - str: The hashed password.
    """
    return pwd_context.hash(password)
