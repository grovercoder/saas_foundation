import pytest
import os
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from src.web_service.app import initialize_web_service, get_web_service
from src.web_service.routes import public as public_routes
from src.web_service.auth import create_access_token, decode_access_token
from src.templating.manager import TemplatingManager
from src.logging_system.manager import LogManager
from datetime import datetime, timedelta

@pytest.fixture
def mock_logger():
    return Mock()

@pytest.fixture
def mock_templating_manager(mock_logger):
    manager = TemplatingManager(mock_logger)
    manager.env.get_template = Mock(return_value=Mock(render=Mock(side_effect=lambda context: f"Template: {context['request'].url.path}, Context: {context}")))
    return manager

@pytest.fixture
def web_service_client(mock_logger, mock_templating_manager):
    # Mock the uvicorn.Server instance
    mock_server = Mock()
    mock_server.should_exit = False

    web_service = initialize_web_service(mock_logger, mock_templating_manager, mock_server, mode="dev")
    web_service.get_app().include_router(public_routes.router)

    # Mock the TemplateResponse method on the Jinja2Templates instance
    # This is needed because Jinja2Templates.TemplateResponse is a method, not an attribute
    # and we want to control its behavior during testing.
    web_service.templates.TemplateResponse = Mock(side_effect=lambda name, context: f"Template: {name}, Context: {context}")

    with TestClient(web_service.get_app()) as client:
        yield client

@pytest.fixture
def jwt_secret_key_env():
    with patch.dict(os.environ, {"JWT_SECRET_KEY": "test-secret-key"}):
        yield

# Test Cases for Public Routes

def test_home_route_returns_200_ok_and_template(web_service_client):
    response = web_service_client.get("/")
    assert response.status_code == 200
    assert "Template: public/home.html" in response.text

def test_login_route_returns_200_ok_and_template(web_service_client):
    response = web_service_client.get("/login")
    assert response.status_code == 200
    assert "Template: public/login.html" in response.text

def test_logout_route_returns_200_ok_and_template(web_service_client):
    response = web_service_client.get("/logout")
    assert response.status_code == 200
    assert "Template: public/logout.html" in response.text

def test_pricing_route_returns_200_ok_and_template(web_service_client):
    response = web_service_client.get("/pricing")
    assert response.status_code == 200
    assert "Template: public/pricing.html" in response.text

def test_signup_route_returns_200_ok_and_template(web_service_client):
    response = web_service_client.get("/signup")
    assert response.status_code == 200
    assert "Template: public/signup.html" in response.text

# Test Case for /stop route

def test_stop_route_shuts_down_server(web_service_client):
    response = web_service_client.get("/stop")
    assert response.status_code == 200
    assert "Server shutdown initiated." in response.text
    # Verify that the server's should_exit flag was set
    web_service = get_web_service()
    assert web_service.server.should_exit is True

# Test Cases for JWT

def test_create_access_token(jwt_secret_key_env):
    data = {"sub": "testuser"}
    token = create_access_token(data)
    assert isinstance(token, str)
    assert len(token) > 0

def test_decode_access_token_valid(jwt_secret_key_env):
    data = {"sub": "testuser"}
    token = create_access_token(data, expires_delta=timedelta(minutes=5))
    decoded_payload = decode_access_token(token)
    assert decoded_payload is not None
    assert decoded_payload["sub"] == "testuser"
    assert "exp" in decoded_payload

def test_decode_access_token_invalid(jwt_secret_key_env):
    invalid_token = "invalid.jwt.token"
    decoded_payload = decode_access_token(invalid_token)
    assert decoded_payload is None

def test_decode_access_token_expired(jwt_secret_key_env):
    data = {"sub": "testuser"}
    # Create an expired token
    expired_token = create_access_token(data, expires_delta=timedelta(minutes=-1))
    decoded_payload = decode_access_token(expired_token)
    assert decoded_payload is None
