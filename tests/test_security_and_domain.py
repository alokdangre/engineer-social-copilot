from __future__ import annotations

import pytest
from pydantic import SecretStr

from social_manager.config import Settings
from social_manager.domain.enums import (
    ActionType,
    ConnectorStatus,
    EvidenceStatus,
    MemoryCategory,
    Platform,
    RecommendationStatus,
    ReviewDecision,
    Visibility,
    WorkflowKind,
)
from social_manager.domain.schemas import MemoryCreate, UserCreate
from social_manager.security import (
    AuthenticationError,
    TokenCipher,
    create_access_token,
    decode_access_token,
    digest_oauth_state,
    generate_oauth_state,
    generate_pkce_pair,
    hash_password,
    verify_password,
)


def test_password_hashing() -> None:
    password = "SuperSecretPassword123!"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword123!", hashed) is False


def test_jwt_access_token() -> None:
    settings = Settings(app_secret_key=SecretStr("my-test-secret-key-32-chars-long!"))
    user_id = "user_123456"
    token = create_access_token(user_id, settings=settings)
    decoded_user_id = decode_access_token(token, settings=settings)
    assert decoded_user_id == user_id

    # Test invalid token
    with pytest.raises(AuthenticationError):
        decode_access_token("invalid.token.here", settings=settings)


def test_token_cipher() -> None:
    settings = Settings(app_secret_key=SecretStr("my-test-secret-key-32-chars-long!"))
    cipher = TokenCipher(settings)
    secret_data = "gho_test_access_token_value_abc123"

    encrypted = cipher.encrypt(secret_data)
    assert encrypted != secret_data

    decrypted = cipher.decrypt(encrypted)
    assert decrypted == secret_data

    with pytest.raises(ValueError):
        cipher.decrypt("not_valid_ciphertext")


def test_pkce_and_oauth_state() -> None:
    verifier, challenge = generate_pkce_pair()
    assert len(verifier) >= 43
    assert len(challenge) >= 43
    assert verifier != challenge

    state = generate_oauth_state()
    assert len(state) >= 32

    digest = digest_oauth_state(state)
    assert digest is not None
    assert len(digest) == 64  # SHA256 hex


def test_domain_enums() -> None:
    assert Platform.GITHUB.value == "github"
    assert Platform.X.value == "x"
    assert Platform.LINKEDIN.value == "linkedin"
    assert ConnectorStatus.CONNECTED.value == "connected"
    assert MemoryCategory.TECHNICAL_KNOWLEDGE.value == "technical_knowledge"
    assert EvidenceStatus.USER_CONFIRMED.value == "user_confirmed"
    assert Visibility.APPROVED_PUBLIC.value == "approved_public"
    assert ActionType.ORIGINAL_POST.value == "original_post"
    assert RecommendationStatus.AWAITING_REVIEW.value == "awaiting_review"
    assert ReviewDecision.APPROVE.value == "approve"
    assert WorkflowKind.PROFILE.value == "profile"


def test_domain_schemas_validation() -> None:
    user = UserCreate(
        email="test@domain.com",
        display_name="Dev User",
        password="PassWord123!",
    )
    assert user.email == "test@domain.com"

    mem = MemoryCreate(
        category=MemoryCategory.PROJECT_CONTRIBUTION,
        title="Built async vector engine",
        statement="Engineered an async vector processing module with 99% accuracy.",
        evidence_status=EvidenceStatus.USER_CONFIRMED,
        visibility=Visibility.APPROVED_PUBLIC,
        confidence=1.0,
    )
    assert mem.confidence == 1.0
