#!/usr/bin/env python3
"""Quick JWT test to verify forge-shared integration works."""

import sys


def test_jwt():
    """Test JWT token creation and decoding."""
    try:
        from app.security import create_access_token, decode_token

        print("1. Creating token...")
        user_id = "test-user-123"
        email = "test@example.com"
        token = create_access_token({"sub": user_id, "email": email})
        print(f"   Token created: {token[:50]}...")

        print("\n2. Decoding token...")
        payload = decode_token(token)
        print(f"   Decoded payload: {payload}")

        print("\n3. Validating payload...")
        assert payload is not None, "Payload should not be None"
        assert payload["sub"] == user_id, f"Expected sub={user_id}, got {payload['sub']}"
        assert payload["email"] == email, f"Expected email={email}, got {payload['email']}"
        assert "exp" in payload, "Missing 'exp' claim"
        assert "iat" in payload, "Missing 'iat' claim"

        print("\n✓ All tests passed!")
        return 0

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(test_jwt())
