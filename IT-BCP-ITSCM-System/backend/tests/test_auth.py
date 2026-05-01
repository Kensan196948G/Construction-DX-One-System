import pytest


REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"


# ---------------------------------------------------------------------------
# register
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_register_success(client):
    """New user can register and receives id/username/role."""
    payload = {
        "username": "testuser",
        "password": "secret123",
        "email": "testuser@example.com",
        "role": "user",
    }
    resp = await client.post(REGISTER_URL, json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == "testuser"
    assert data["role"] == "user"
    assert "id" in data


@pytest.mark.asyncio
async def test_register_default_role(client):
    """Role defaults to 'user' when not specified."""
    payload = {
        "username": "noroler",
        "password": "pass1234",
        "email": "noroler@example.com",
    }
    resp = await client.post(REGISTER_URL, json=payload)
    assert resp.status_code == 201
    assert resp.json()["role"] == "user"


@pytest.mark.asyncio
async def test_register_custom_role(client):
    """Admin role is accepted."""
    payload = {
        "username": "adminuser",
        "password": "adminpass",
        "email": "admin@example.com",
        "role": "admin",
    }
    resp = await client.post(REGISTER_URL, json=payload)
    assert resp.status_code == 201
    assert resp.json()["role"] == "admin"


@pytest.mark.asyncio
async def test_register_duplicate_username(client):
    """Registering the same username twice returns 409."""
    payload = {
        "username": "dupuser",
        "password": "pass1234",
        "email": "dup@example.com",
    }
    resp1 = await client.post(REGISTER_URL, json=payload)
    assert resp1.status_code == 201

    payload2 = {**payload, "email": "dup2@example.com"}
    resp2 = await client.post(REGISTER_URL, json=payload2)
    assert resp2.status_code == 409
    assert "already exists" in resp2.json()["detail"].lower()


# ---------------------------------------------------------------------------
# login
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_login_success(client):
    """Registered user can login and receives a bearer token."""
    reg_payload = {
        "username": "loginuser",
        "password": "mypassword",
        "email": "loginuser@example.com",
    }
    await client.post(REGISTER_URL, json=reg_payload)

    login_payload = {"username": "loginuser", "password": "mypassword"}
    resp = await client.post(LOGIN_URL, json=login_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 0


@pytest.mark.asyncio
async def test_login_invalid_password(client):
    """Wrong password returns 401."""
    reg_payload = {
        "username": "pwduser",
        "password": "correctpwd",
        "email": "pwduser@example.com",
    }
    await client.post(REGISTER_URL, json=reg_payload)

    resp = await client.post(LOGIN_URL, json={"username": "pwduser", "password": "wrongpwd"})
    assert resp.status_code == 401
    assert "invalid credentials" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_unknown_user(client):
    """Login with non-existent username returns 401."""
    resp = await client.post(LOGIN_URL, json={"username": "ghost", "password": "any"})
    assert resp.status_code == 401
    assert "invalid credentials" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_empty_password(client):
    """Empty password returns 401 (not a server error)."""
    reg_payload = {
        "username": "emptypwd",
        "password": "realpassword",
        "email": "emptypwd@example.com",
    }
    await client.post(REGISTER_URL, json=reg_payload)

    resp = await client.post(LOGIN_URL, json={"username": "emptypwd", "password": ""})
    assert resp.status_code == 401
