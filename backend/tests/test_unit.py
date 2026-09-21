"""
Unit Tests for Finnie AI Core Functionality
===========================================
Offline tests verifying math, simulations, security, compliance, and graph routing.
"""
import os
import unittest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

from langchain_core.messages import HumanMessage, AIMessage

from src.utils.simulations import run_monte_carlo
from src.agents.portfolio_analyst import compute_hhi_diversification
from src.auth.jwt import hash_password, verify_password, create_access_token, decode_access_token
from src.agents.compliance import compliance_guardian_node
from src.graph import route_decision, start_node


class TestSimulations(unittest.TestCase):
    def test_monte_carlo_positive_horizon(self):
        res = run_monte_carlo(
            initial_balance=10000.0,
            target_amount=50000.0,
            monthly_savings=500.0,
            years=5,
            expected_return=0.08,
            volatility=0.15,
            num_simulations=500
        )
        self.assertIn("confidence_score", res)
        self.assertIn("median_path", res)
        self.assertIn("p05_path", res)
        self.assertIn("p95_path", res)
        self.assertTrue(0.0 <= res["confidence_score"] <= 100.0)
        self.assertEqual(len(res["years_axis"]), 6)
        # Check percentile ordering at final step
        p05_end = res["p05_path"][-1]
        p50_end = res["median_path"][-1]
        p95_end = res["p95_path"][-1]
        self.assertLessEqual(p05_end, p50_end)
        self.assertLessEqual(p50_end, p95_end)

    def test_monte_carlo_zero_years(self):
        res = run_monte_carlo(
            initial_balance=10000.0,
            target_amount=50000.0,
            monthly_savings=500.0,
            years=0,
            expected_return=0.08,
            volatility=0.15
        )
        self.assertEqual(res["confidence_score"], 0)
        self.assertIn("error", res)


class TestPortfolioMath(unittest.TestCase):
    def test_compute_hhi_empty(self):
        score, sectors = compute_hhi_diversification([])
        self.assertEqual(score, 0.0)
        self.assertEqual(sectors, {})

    @patch("yfinance.Ticker")
    def test_compute_hhi_multi_sector(self, mock_ticker):
        # Mock 2 tickers in different sectors
        def ticker_side_effect(symbol):
            mock = MagicMock()
            if symbol == "AAPL":
                mock.info = {"sector": "Technology"}
            elif symbol == "JNJ":
                mock.info = {"sector": "Healthcare"}
            else:
                mock.info = {"sector": "Unknown"}
            return mock

        mock_ticker.side_effect = ticker_side_effect
        score, sectors = compute_hhi_diversification(["AAPL", "JNJ"], max_retries=1)
        self.assertIsNotNone(score)
        self.assertEqual(sectors, {"Technology": 1, "Healthcare": 1})
        self.assertGreater(score, 5.0)  # Diversified across 2 sectors should score well


class TestAuthentication(unittest.TestCase):
    def test_password_hash_and_verify(self):
        pwd = "SecureTestPassword123!"
        hashed = hash_password(pwd)
        self.assertNotEqual(pwd, hashed)
        self.assertTrue(verify_password(pwd, hashed))
        self.assertFalse(verify_password("WrongPassword", hashed))

    def test_jwt_create_and_decode(self):
        payload = {"sub": "user_12345", "email": "test@finnie.ai"}
        token = create_access_token(payload)
        self.assertIsInstance(token, str)
        decoded = decode_access_token(token)
        self.assertEqual(decoded["sub"], "user_12345")
        self.assertEqual(decoded["email"], "test@finnie.ai")
        self.assertIn("exp", decoded)

    def test_jwt_invalid_token(self):
        self.assertIsNone(decode_access_token("invalid.token.structure"))


class TestCompliance(unittest.TestCase):
    def test_appends_disclaimer(self):
        state = {"messages": [AIMessage(content="You should buy index funds.", id="msg_1")]}
        res = compliance_guardian_node(state)
        self.assertIn("messages", res)
        updated_msg = res["messages"][0]
        self.assertIn("$NFA", updated_msg.content)
        self.assertEqual(updated_msg.id, "msg_1")

    def test_idempotent_if_already_has_disclaimer(self):
        state = {"messages": [AIMessage(content="This is educational. $NFA applies.", id="msg_2")]}
        res = compliance_guardian_node(state)
        self.assertEqual(res, {})


class TestGraphRouting(unittest.TestCase):
    def test_route_decision(self):
        self.assertEqual(route_decision({"next_step": "FINANCIAL_QA"}), "financial_qa")
        self.assertEqual(route_decision({"next_step": "PORTFOLIO_ANALYST"}), "portfolio_analyst")
        self.assertEqual(route_decision({"next_step": "MARKET_INSIGHTS"}), "market_insights")
        self.assertEqual(route_decision({"next_step": "GOAL_STRATEGIST"}), "goal_strategist")
        self.assertEqual(route_decision({"next_step": "FINISH"}), "compliance")
        self.assertEqual(route_decision({}), "compliance")

    def test_start_node_bypass(self):
        # Direct bypass when next_step is provided
        self.assertEqual(start_node({"next_step": "PORTFOLIO_ANALYST"}), "portfolio_analyst")
        # Route to supervisor when next_step is None
        self.assertEqual(start_node({}), "supervisor")


class TestModelIntegrityAndDatetimes(unittest.TestCase):
    def test_holding_unique_constraint(self):
        from src.models.portfolio import Holding
        from sqlalchemy import UniqueConstraint

        constraints = [
            c for c in Holding.__table__.constraints
            if isinstance(c, UniqueConstraint)
        ]
        self.assertTrue(len(constraints) >= 1)
        col_names = [col.name for col in constraints[0].columns]
        self.assertEqual(col_names, ["user_id", "ticker", "exchange"])

    def test_market_cache_tz_aware_expiration(self):
        from datetime import datetime, timezone, timedelta
        from src.models.market_cache import MarketCache

        # 1. Fresh cache entry (UTC aware)
        cache_fresh = MarketCache(
            key="TEST:FRESH",
            data_json="{}",
            timestamp=datetime.now(timezone.utc)
        )
        self.assertFalse(cache_fresh.is_expired(ttl_minutes=30))

        # 2. Expired cache entry (UTC aware)
        cache_old = MarketCache(
            key="TEST:OLD",
            data_json="{}",
            timestamp=datetime.now(timezone.utc) - timedelta(minutes=45)
        )
        self.assertTrue(cache_old.is_expired(ttl_minutes=30))

        # 3. Naive datetime fallback (legacy SQLite storage compatibility)
        cache_naive = MarketCache(
            key="TEST:NAIVE",
            data_json="{}",
            timestamp=(datetime.now(timezone.utc) - timedelta(minutes=45)).replace(tzinfo=None)
        )
        # Must not raise TypeError: can't subtract offset-naive and offset-aware datetimes
        self.assertTrue(cache_naive.is_expired(ttl_minutes=30))
        self.assertIn("key=TEST:NAIVE", repr(cache_naive))

    def test_financial_goal_tz_aware(self):
        from src.models.goal import FinancialGoal

        goal = FinancialGoal(
            user_id="user_test",
            goal_name="Vacation Fund",
            target_amount=15000.0,
            target_year=2028,
            monthly_contribution=300.0,
        )
        # Evaluates default callable
        default_created = FinancialGoal.created_at.default.arg(None)
        self.assertIsNotNone(default_created.tzinfo)
        self.assertEqual(default_created.tzinfo, timezone.utc)


class TestPasswordRecovery(unittest.TestCase):
    def setUp(self):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from src.database import Base
        from src.models.user import User
        from main import _forgot_password_rate_limit

        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()
        _forgot_password_rate_limit.clear()

        # Seed test user
        self.test_user = User(
            id="user_reset_test",
            email="reset.tester@finnie.ai",
            hashed_password=hash_password("OldPassword123!"),
            full_name="Reset Tester",
            token_version=1
        )
        self.db.add(self.test_user)
        self.db.commit()

        self.mock_request = MagicMock()
        self.mock_request.client.host = "127.0.0.1"
        self.mock_request.headers = {
            "X-Forwarded-For": "198.51.100.42",
            "User-Agent": "TestAgent/1.0",
            "CF-IPCountry": "US"
        }

    def tearDown(self):
        self.db.close()
        from src.database import Base
        Base.metadata.drop_all(bind=self.engine)
        self.engine.dispose()

    def test_forgot_password_registered_user(self):
        from main import forgot_password
        from src.models.auth_schemas import ForgotPasswordRequest
        from src.models.password_reset import PasswordResetAudit

        req = ForgotPasswordRequest(email="reset.tester@finnie.ai")
        res = forgot_password(req, self.mock_request, self.db)
        self.assertEqual(res.expires_in_minutes, 15)
        self.assertIn("verification code has been sent", res.message)

        # Confirm audit record in database
        audit = self.db.query(PasswordResetAudit).filter(PasswordResetAudit.user_id == self.test_user.id).first()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.status, "PENDING")
        self.assertEqual(audit.attempts, 0)
        self.assertEqual(audit.request_ip, "198.51.100.42")
        self.assertIn("198.51.100.42", audit.request_location)

    def test_forgot_password_unregistered_email_enumeration_defense(self):
        from main import forgot_password
        from src.models.auth_schemas import ForgotPasswordRequest
        from src.models.password_reset import PasswordResetAudit

        req = ForgotPasswordRequest(email="unknown@finnie.ai")
        res = forgot_password(req, self.mock_request, self.db)
        # Identical message returned
        self.assertEqual(res.expires_in_minutes, 15)
        self.assertIn("verification code has been sent", res.message)

        # Zero audit records created
        audits = self.db.query(PasswordResetAudit).all()
        self.assertEqual(len(audits), 0)

    @patch("secrets.randbelow")
    def test_reset_password_success(self, mock_rand):
        from main import forgot_password, reset_password
        from src.models.auth_schemas import ForgotPasswordRequest, ResetPasswordRequest
        from src.models.password_reset import PasswordResetAudit

        # Mock OTP generation: 23456 + 100000 = 123456
        mock_rand.return_value = 23456

        forgot_password(ForgotPasswordRequest(email="reset.tester@finnie.ai"), self.mock_request, self.db)

        # Perform password reset
        reset_req = ResetPasswordRequest(
            email="reset.tester@finnie.ai",
            code="123456",
            new_password="NewSecurePassword123!"
        )
        res = reset_password(reset_req, self.mock_request, self.db)
        self.assertIn("successfully reset", res.message)

        # Verify DB updates
        self.db.refresh(self.test_user)
        self.assertTrue(verify_password("NewSecurePassword123!", self.test_user.hashed_password))
        self.assertEqual(self.test_user.token_version, 2)

        audit = self.db.query(PasswordResetAudit).first()
        self.assertEqual(audit.status, "COMPLETED")
        self.assertIsNotNone(audit.completed_at)
        self.assertEqual(audit.completed_ip, "198.51.100.42")

    def test_session_revocation_on_token_version(self):
        from fastapi import HTTPException
        from src.auth.jwt import create_access_token, get_current_user

        # Token created with version 1
        valid_token = create_access_token({"sub": self.test_user.id, "v": 1})
        user = get_current_user(token=valid_token, db=self.db)
        self.assertEqual(user.id, self.test_user.id)

        # Invalidate by incrementing version
        self.test_user.token_version = 2
        self.db.commit()

        # Token with version 1 must now be rejected
        with self.assertRaises(HTTPException) as ctx:
            get_current_user(token=valid_token, db=self.db)
        self.assertEqual(ctx.exception.status_code, 401)

    def test_reset_password_expired_code(self):
        from fastapi import HTTPException
        from main import reset_password
        from src.models.auth_schemas import ResetPasswordRequest
        from src.models.password_reset import PasswordResetAudit

        # Create expired code
        expired_audit = PasswordResetAudit(
            user_id=self.test_user.id,
            code_hash=hash_password("123456"),
            status="PENDING",
            attempts=0,
            requested_at=datetime.now(timezone.utc) - timedelta(minutes=20),
            expires_at=datetime.now(timezone.utc) - timedelta(minutes=5)
        )
        self.db.add(expired_audit)
        self.db.commit()

        reset_req = ResetPasswordRequest(
            email="reset.tester@finnie.ai",
            code="123456",
            new_password="NewSecurePassword123!"
        )
        with self.assertRaises(HTTPException) as ctx:
            reset_password(reset_req, self.mock_request, self.db)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("expired", ctx.exception.detail.lower())

        self.db.refresh(expired_audit)
        self.assertEqual(expired_audit.status, "EXPIRED")

    def test_reset_password_attempt_capping_3_attempts(self):
        from fastapi import HTTPException
        from main import reset_password
        from src.models.auth_schemas import ResetPasswordRequest
        from src.models.password_reset import PasswordResetAudit

        audit = PasswordResetAudit(
            user_id=self.test_user.id,
            code_hash=hash_password("654321"),
            status="PENDING",
            attempts=0,
            requested_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=15)
        )
        self.db.add(audit)
        self.db.commit()

        reset_req = ResetPasswordRequest(
            email="reset.tester@finnie.ai",
            code="000000",
            new_password="NewSecurePassword123!"
        )

        # Attempt 1: 2 attempts remaining
        with self.assertRaises(HTTPException) as ctx1:
            reset_password(reset_req, self.mock_request, self.db)
        self.assertEqual(ctx1.exception.status_code, 400)
        self.assertIn("2 attempts remaining", ctx1.exception.detail)

        # Attempt 2: 1 attempt remaining
        with self.assertRaises(HTTPException) as ctx2:
            reset_password(reset_req, self.mock_request, self.db)
        self.assertEqual(ctx2.exception.status_code, 400)
        self.assertIn("1 attempts remaining", ctx2.exception.detail)

        # Attempt 3: Locked out, status FAILED
        with self.assertRaises(HTTPException) as ctx3:
            reset_password(reset_req, self.mock_request, self.db)
        self.assertEqual(ctx3.exception.status_code, 400)
        self.assertIn("Too many failed attempts", ctx3.exception.detail)

        self.db.refresh(audit)
        self.assertEqual(audit.status, "FAILED")
        self.assertEqual(audit.attempts, 3)

    def test_reset_password_same_password_rejected(self):
        from fastapi import HTTPException
        from main import reset_password
        from src.models.auth_schemas import ResetPasswordRequest
        from src.models.password_reset import PasswordResetAudit

        audit = PasswordResetAudit(
            user_id=self.test_user.id,
            code_hash=hash_password("111222"),
            status="PENDING",
            attempts=0,
            requested_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=15)
        )
        self.db.add(audit)
        self.db.commit()

        reset_req = ResetPasswordRequest(
            email="reset.tester@finnie.ai",
            code="111222",
            new_password="OldPassword123!"  # Reusing current password
        )
        with self.assertRaises(HTTPException) as ctx:
            reset_password(reset_req, self.mock_request, self.db)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("cannot be the same as your current password", ctx.exception.detail)

    def test_forgot_password_rate_limiting(self):
        from fastapi import HTTPException
        from main import forgot_password
        from src.models.auth_schemas import ForgotPasswordRequest

        req = ForgotPasswordRequest(email="reset.tester@finnie.ai")

        # First 3 calls succeed
        for _ in range(3):
            res = forgot_password(req, self.mock_request, self.db)
            self.assertEqual(res.expires_in_minutes, 15)

        # 4th call within 15 minutes triggers rate limit
        with self.assertRaises(HTTPException) as ctx:
            forgot_password(req, self.mock_request, self.db)
        self.assertEqual(ctx.exception.status_code, 429)
        self.assertIn("Too many password reset requests", ctx.exception.detail)


class TestEmailService(unittest.TestCase):
    """SPEC-09: Reusable Email Notification Engine & Mailgun Dispatch Test Suite."""

    def test_email_masking(self):
        from src.utils.email_service import mask_email

        self.assertEqual(mask_email("investor@finnie.ai"), "in***@finnie.ai")
        self.assertEqual(mask_email("uthircloudnative@gmail.com"), "ut***@gmail.com")
        self.assertEqual(mask_email("a@b.com"), "a***@b.com")
        self.assertEqual(mask_email("invalid"), "***")
        self.assertEqual(mask_email(""), "***")

    def test_provider_selection(self):
        from src.utils.email_service import EmailService, ConsoleEmailProvider, MailgunEmailProvider

        with patch.dict(os.environ, {}, clear=True):
            provider = EmailService.get_provider()
            self.assertIsInstance(provider, ConsoleEmailProvider)

        with patch.dict(os.environ, {"MAILGUN_API_KEY": "key-12345", "MAILGUN_DOMAIN": "sandbox.test"}, clear=True):
            provider = EmailService.get_provider()
            self.assertIsInstance(provider, MailgunEmailProvider)
            self.assertEqual(provider.domain, "sandbox.test")

    def test_template_rendering(self):
        from src.utils.email_service import EmailService

        context = {
            "otp_code": "987654",
            "expiry_minutes": 15,
            "request_location": "New York, US",
            "user_name": "Alice Investor",
            "recipient_email": "alice@finnie.ai"
        }
        html = EmailService.render_template("otp_reset.html", context)
        text = EmailService.render_template("otp_reset.txt", context)

        self.assertIn("987654", html)
        self.assertIn("New York, US", html)
        self.assertIn("15 minutes", html)
        self.assertNotIn("{{otp_code}}", html)

        self.assertIn("987654", text)
        self.assertIn("New York, US", text)
        self.assertNotIn("{{otp_code}}", text)

    @patch("requests.post")
    def test_mailgun_dispatch_mock(self, mock_post):
        from src.utils.email_service import MailgunEmailProvider, EmailMessage

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '{"id": "<2026.mailgun.org>", "message": "Queued. Thank you."}'
        mock_post.return_value = mock_resp

        provider = MailgunEmailProvider(
            api_key="mock-api-key",
            domain="sandbox123.mailgun.org",
            base_url="https://api.mailgun.net"
        )
        msg = EmailMessage(
            to_email="test@finnie.ai",
            subject="Test Subject",
            html_body="<p>Test</p>",
            text_body="Test"
        )

        success = provider.send_email(msg)
        self.assertTrue(success)
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], "https://api.mailgun.net/v3/sandbox123.mailgun.org/messages")
        self.assertEqual(kwargs["auth"], ("api", "mock-api-key"))
        self.assertEqual(kwargs["data"]["to"], "test@finnie.ai")

    @patch("requests.post")
    def test_mailgun_sandbox_rejection_resilience(self, mock_post):
        from src.utils.email_service import MailgunEmailProvider, EmailMessage

        # Simulate Mailgun's HTTP 400 rejection for unauthorized sandbox recipients
        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.text = "Sandbox subdomains are for test purposes only, and can only send to authorized recipients."
        mock_post.return_value = mock_resp

        provider = MailgunEmailProvider(
            api_key="mock-api-key",
            domain="sandbox123.mailgun.org"
        )
        msg = EmailMessage(
            to_email="unauthorized@example.com",
            subject="Verification Code",
            html_body="<p>Code</p>",
            text_body="Code"
        )

        # Must return False and not throw an uncaught exception
        success = provider.send_email(msg)
        self.assertFalse(success)

    def test_console_email_provider_dispatch(self):
        from src.utils.email_service import ConsoleEmailProvider, EmailMessage

        provider = ConsoleEmailProvider()
        msg = EmailMessage(
            to_email="console.tester@finnie.ai",
            subject="Offline Test",
            html_body="<p>Body</p>",
            text_body="Body"
        )
        self.assertTrue(provider.send_email(msg))

    def test_email_service_send_otp_reset(self):
        from src.utils.email_service import EmailService

        # Should dispatch cleanly via console provider in test environment
        success = EmailService.send_otp_reset_email(
            to_email="investor.test@finnie.ai",
            otp_code="123456",
            expiry_minutes=15,
            location="Chicago, US",
            user_name="Test Investor"
        )
        self.assertTrue(success)


if __name__ == "__main__":
    unittest.main()



