"""
Unit Tests for Finnie AI Core Functionality
===========================================
Offline tests verifying math, simulations, security, compliance, and graph routing.
"""
import unittest
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


if __name__ == "__main__":
    unittest.main()
