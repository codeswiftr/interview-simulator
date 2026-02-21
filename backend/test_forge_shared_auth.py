#!/usr/bin/env python3
"""Quick verification script for forge-shared auth migration.

Run this to verify the migration is working correctly:
    uv run python test_forge_shared_auth.py
"""

import sys


def test_imports():
    """Test that all imports work."""
    print("Testing imports...")
    try:
        from forge_shared.auth.jwt import JWTAuth, JWTConfig
        from forge_shared.auth.models import ForgeTokenPayload, Permission, PlanTier, UserRole

        from app.dependencies import get_current_user
        from app.security import (
            create_access_token,
            decode_token,
            get_jwt_auth_instance,
            hash_password,
            verify_password,
        )

        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


def test_jwt_creation():
    """Test JWT token creation."""
    print("\nTesting JWT token creation...")
    try:
        from app.security import create_access_token, get_jwt_auth_instance

        # Initialize JWT auth
        auth = get_jwt_auth_instance()
        print(f"✓ JWT auth initialized (issuer: {auth.config.issuer})")

        # Create a token
        token = create_access_token({"sub": "test-user-id"})
        print(f"✓ Token created: {token[:50]}...")

        return True
    except Exception as e:
        print(f"✗ Token creation failed: {e}")
        return False


def test_jwt_decoding():
    """Test JWT token decoding."""
    print("\nTesting JWT token decoding...")
    try:
        from app.security import create_access_token, decode_token

        # Create and decode a token
        token = create_access_token({"sub": "test-user-id-123"})
        payload = decode_token(token)

        if payload is None:
            print("✗ Token decode returned None")
            return False

        if payload.get("sub") != "test-user-id-123":
            print(f"✗ Token subject mismatch: {payload.get('sub')}")
            return False

        print(f"✓ Token decoded successfully: sub={payload.get('sub')}")
        return True
    except Exception as e:
        print(f"✗ Token decoding failed: {e}")
        return False


def test_invalid_token():
    """Test that invalid tokens are rejected."""
    print("\nTesting invalid token rejection...")
    try:
        from app.security import decode_token

        # Test with invalid token
        payload = decode_token("invalid.token.here")

        if payload is not None:
            print("✗ Invalid token was accepted (should be rejected)")
            return False

        print("✓ Invalid token correctly rejected")
        return True
    except Exception as e:
        print(f"✗ Invalid token test failed: {e}")
        return False


def test_password_hashing():
    """Test password hashing (should remain unchanged)."""
    print("\nTesting password hashing...")
    try:
        from app.security import hash_password, verify_password

        password = "test-password-123"
        hashed = hash_password(password)

        if not hashed.startswith("$2b$"):
            print(f"✗ Hash doesn't use bcrypt: {hashed[:10]}")
            return False

        if not verify_password(password, hashed):
            print("✗ Password verification failed")
            return False

        if verify_password("wrong-password", hashed):
            print("✗ Wrong password was accepted")
            return False

        print("✓ Password hashing works correctly")
        return True
    except Exception as e:
        print(f"✗ Password hashing test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 70)
    print("FORGE-SHARED AUTH MIGRATION VERIFICATION")
    print("=" * 70)

    tests = [
        test_imports,
        test_jwt_creation,
        test_jwt_decoding,
        test_invalid_token,
        test_password_hashing,
    ]

    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"\n✗ Test {test.__name__} crashed: {e}")
            results.append(False)

    print("\n" + "=" * 70)
    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"✓ ALL TESTS PASSED ({passed}/{total})")
        print("=" * 70)
        print("\nMigration verification successful!")
        print("\nNext steps:")
        print("1. Run full test suite: uv run pytest")
        print("2. Test login endpoint: POST /api/v1/users/login")
        print("3. Test protected endpoints with token")
        return 0
    else:
        print(f"✗ SOME TESTS FAILED ({passed}/{total} passed)")
        print("=" * 70)
        print("\nPlease review the failed tests above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
