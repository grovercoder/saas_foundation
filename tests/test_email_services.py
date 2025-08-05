import pytest
import os
from unittest.mock import Mock, patch
import smtplib
from src.email_services.manager import EmailManager
from src.templating.manager import TemplatingManager

@pytest.fixture
def mock_logger():
    return Mock()

@pytest.fixture
def mock_templating_manager(mock_logger):
    manager = TemplatingManager(mock_logger)
    manager.get_environment = Mock()
    manager.get_environment().get_template.return_value.render.side_effect = lambda context: f"Rendered: {context}"
    return manager

@pytest.fixture
def mock_smtp_env_vars():
    with patch.dict(os.environ, {
        "SMTP_SERVER": "smtp.test.com",
        "SMTP_PORT": "587",
        "SMTP_USERNAME": "testuser",
        "SMTP_PASSWORD": "testpass",
        "SMTP_USE_TLS": "True",
        "SMTP_SENDER_EMAIL": "sender@test.com",
    }):
        yield

@pytest.fixture
def email_manager(mock_logger, mock_templating_manager, mock_smtp_env_vars):
    with patch('smtplib.SMTP') as mock_smtp_class:
        manager = EmailManager(mock_logger, mock_templating_manager)
        manager.smtp_use_tls = True # Force TLS for testing
        manager.mock_smtp_class = mock_smtp_class # Store the mock for assertions
        # Configure the mock SMTP instance returned by the context manager
        mock_smtp_instance = mock_smtp_class.return_value
        mock_smtp_instance.starttls = Mock()
        mock_smtp_instance.login = Mock()
        mock_smtp_instance.sendmail = Mock()
        
        # Configure the context manager behavior
        mock_smtp_class.return_value.__enter__.return_value = mock_smtp_instance
        mock_smtp_class.return_value.__exit__.return_value = False # Don't suppress exceptions
        yield manager

def test_email_manager_initialization(email_manager):
    assert email_manager.smtp_server == "smtp.test.com"
    assert email_manager.smtp_port == 587
    assert email_manager.smtp_username == "testuser"
    assert email_manager.smtp_password == "testpass"
    assert email_manager.smtp_use_tls is True
    assert email_manager.smtp_sender_email == "sender@test.com"

def test_email_manager_initialization_missing_env_vars(mock_logger, mock_templating_manager):
    with patch.dict(os.environ, {}, clear=True):
        manager = EmailManager(mock_logger, mock_templating_manager)
        mock_logger.warning.assert_called_with("SMTP environment variables are not fully configured. Email sending may fail.")

def test_send_email_text_content(email_manager, mock_logger):
    to_email = "recipient@test.com"
    subject = "Test Subject"
    text_content = "This is a test email."

    email_manager.send_email(to_email, subject, text_content=text_content)

    email_manager.mock_smtp_class.assert_called_once_with("smtp.test.com", 587)
    instance = email_manager.mock_smtp_class.return_value
    instance.starttls.assert_called_once()
    instance.login.assert_called_once_with("testuser", "testpass")
    instance.sendmail.assert_called_once()
    args, kwargs = instance.sendmail.call_args
    assert args[0] == "sender@test.com"
    assert args[1] == "recipient@test.com"
    assert "This is a test email." in args[2]
    mock_logger.info.assert_called_with(f"Email sent successfully to {to_email} with subject '{subject}'.")

def test_send_email_html_content(email_manager, mock_logger):
    to_email = "recipient@test.com"
    subject = "Test Subject"
    html_content = "<h1>This is a test email.</h1>"

    email_manager.send_email(to_email, subject, html_content=html_content)

    email_manager.mock_smtp_class.assert_called_once_with("smtp.test.com", 587)
    instance = email_manager.mock_smtp_class.return_value
    instance.starttls.assert_called_once()
    instance.login.assert_called_once_with("testuser", "testpass")
    instance.sendmail.assert_called_once()
    args, kwargs = instance.sendmail.call_args
    assert args[0] == "sender@test.com"
    assert args[1] == "recipient@test.com"
    assert "<h1>This is a test email.</h1>" in args[2]
    mock_logger.info.assert_called_with(f"Email sent successfully to {to_email} with subject '{subject}'.")

def test_send_email_with_template(email_manager, mock_logger, mock_templating_manager):
    to_email = "recipient@test.com"
    subject = "Password Reset"
    template_context = {"username": "testuser", "reset_link": "http://reset.link", "expiration_minutes": 60, "app_name": "TestApp"}

    email_manager.send_email(
        to_email,
        subject,
        text_content="email/forgot_password.txt",
        html_content="email/forgot_password.html",
        template_context=template_context
    )

    mock_templating_manager.get_environment().get_template.assert_any_call("email/forgot_password.txt")
    mock_templating_manager.get_environment().get_template.assert_any_call("email/forgot_password.html")
    mock_templating_manager.get_environment().get_template.return_value.render.assert_called_with(template_context)

    email_manager.mock_smtp_class.assert_called_once_with("smtp.test.com", 587)
    instance = email_manager.mock_smtp_class.return_value
    instance.starttls.assert_called_once()
    instance.login.assert_called_once_with("testuser", "testpass")
    instance.sendmail.assert_called_once()
    args, kwargs = instance.sendmail.call_args
    assert args[0] == "sender@test.com"
    assert args[1] == "recipient@test.com"
    assert "Rendered: {'username': 'testuser', 'reset_link': 'http://reset.link', 'expiration_minutes': 60, 'app_name': 'TestApp'}" in args[2]
    mock_logger.info.assert_called_with(f"Email sent successfully to {to_email} with subject '{subject}'.")

def test_send_email_failure(email_manager, mock_logger):
    email_manager.mock_smtp_class.side_effect = Exception("SMTP Connection Error")
    to_email = "recipient@test.com"
    subject = "Test Subject"
    text_content = "This is a test email."

    with pytest.raises(Exception, match="SMTP Connection Error"):
        email_manager.send_email(to_email, subject, text_content=text_content)

    mock_logger.error.assert_called_with(f"Failed to send email to {to_email} with subject '{subject}': SMTP Connection Error")
