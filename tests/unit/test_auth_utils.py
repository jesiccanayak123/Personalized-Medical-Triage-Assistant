"""
Unit tests for authentication utilities.
"""
import pytest
from modules.auth.utils import (
    hash_password,
    verify_password,
    generate_token,
    generate_id,
    is_valid_email,
    is_valid_password,
)


class TestPasswordHashing:
    """Tests for password hashing functions."""

    def test_hash_password(self):
        """Test password hashing."""
        password = "securepassword123"
        hashed = hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 20

    def test_hash_different_for_same_password(self):
        """Test that same password produces different hashes (salt)."""
        password = "securepassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        # bcrypt uses random salt, so hashes should differ
        assert hash1 != hash2

    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "securepassword123"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "securepassword123"
        hashed = hash_password(password)
        
        assert verify_password("wrongpassword", hashed) is False

    def test_verify_empty_password(self):
        """Test verification with empty password."""
        hashed = hash_password("somepassword")
        
        assert verify_password("", hashed) is False


class TestTokenGeneration:
    """Tests for token generation."""

    def test_generate_token(self):
        """Test token generation."""
        token = generate_token()
        
        assert token is not None
        assert len(token) > 30
        assert isinstance(token, str)

    def test_generate_unique_tokens(self):
        """Test that tokens are unique."""
        tokens = [generate_token() for _ in range(100)]
        
        assert len(set(tokens)) == 100


class TestIdGeneration:
    """Tests for ID generation."""

    def test_generate_id(self):
        """Test ID generation."""
        id_ = generate_id()
        
        assert id_ is not None
        assert len(id_) == 24  # ObjectId-style hex string
        assert all(c in '0123456789abcdef' for c in id_)

    def test_generate_unique_ids(self):
        """Test that IDs are unique."""
        ids = [generate_id() for _ in range(100)]
        
        assert len(set(ids)) == 100


class TestEmailValidation:
    """Tests for email validation."""

    def test_valid_email(self):
        """Test valid email addresses."""
        valid_emails = [
            "test@example.com",
            "user.name@domain.org",
            "user+tag@example.co.uk",
            "first.last@subdomain.example.com",
        ]
        
        for email in valid_emails:
            assert is_valid_email(email) is True, f"Should be valid: {email}"

    def test_invalid_email(self):
        """Test invalid email addresses."""
        invalid_emails = [
            "notanemail",
            "@nodomain.com",
            "noat.com",
            "spaces in@email.com",
            "",
            "missing@.com",
        ]
        
        for email in invalid_emails:
            assert is_valid_email(email) is False, f"Should be invalid: {email}"


class TestPasswordValidation:
    """Tests for password validation."""

    def test_valid_password(self):
        """Test valid passwords."""
        valid_passwords = [
            "password123",
            "SecurePass!23",
            "abcdefghij",
            "verylongpasswordwithmanycharacters",
        ]
        
        for password in valid_passwords:
            assert is_valid_password(password) is True, f"Should be valid: {password}"

    def test_invalid_password_too_short(self):
        """Test password that's too short."""
        assert is_valid_password("12345") is False
        assert is_valid_password("abc") is False

    def test_empty_password(self):
        """Test empty password."""
        assert is_valid_password("") is False

