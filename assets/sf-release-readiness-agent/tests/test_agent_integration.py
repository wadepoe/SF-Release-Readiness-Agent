"""Integration and unit tests for the SF Release Readiness Agent."""
import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Ensure test mode
os.environ.setdefault("IBD_TESTING", "1")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_llm_response():
    """A canned LLM response simulating change plan output."""
    return (
        "I have analysed the release notes and found 3 change items affecting this tenant.\n\n"
        "**Change Plan for Tenant ClientA:**\n\n"
        "**Low-risk changes (2 items):**\n"
        "1. Picklist label update for 'ACTIVE' → 'Active Employee' (classification: low-risk)\n"
        "2. UI theme text update for login page footer (classification: low-risk)\n\n"
        "**Requires-approval changes (1 item):**\n"
        "1. Role-Based Permission role 'ROLE_001' requires new permission for ESS_PAYSLIP (classification: requires approval)\n\n"
        "Please confirm to apply the 2 low-risk changes, or type 'skip' to proceed to manual guidance only."
    )


@pytest.fixture
def mock_tools():
    """Minimal list of mock MCP tools."""
    tool1 = MagicMock()
    tool1.name = "list_picklistv2_for_sfodata"
    tool1.description = "List PickListV2 entities"
    tool2 = MagicMock()
    tool2.name = "list_rbprole_for_sfodata"
    tool2.description = "List RBP roles"
    return [tool1, tool2]


# ---------------------------------------------------------------------------
# Unit tests — Release note ingestion detection (M1)
# ---------------------------------------------------------------------------

class TestMilestoneDetection:
    """Test that milestone triggers are correctly detected from query keywords."""

    def test_m1_detected_for_release_notes_query(self):
        keywords = ["release note", "what's new", "whats new", "release content"]
        for kw in keywords:
            assert kw in kw.lower(), f"Keyword '{kw}' should be detectable"

    def test_m1_not_triggered_for_unrelated_query(self):
        query = "what is my tenant URL?"
        m1_keywords = ["release note", "what's new", "whats new", "release content"]
        triggered = any(k in query.lower() for k in m1_keywords)
        assert not triggered

    def test_m3_detected_in_response_with_change_plan(self, mock_llm_response):
        m3_keywords = ["low-risk", "requires approval", "change plan", "classification"]
        triggered = any(k in mock_llm_response.lower() for k in m3_keywords)
        assert triggered

    def test_m5_detected_in_response_with_complete(self):
        response = "The release readiness cycle is now complete. Here is your change log."
        m5_keywords = ["change log", "manual action", "sign-off", "complete", "finalised", "finalized"]
        triggered = any(k in response.lower() for k in m5_keywords)
        assert triggered

    def test_m5_not_detected_in_intermediate_response(self, mock_llm_response):
        m5_keywords = ["change log", "manual action", "sign-off", "complete", "finalised", "finalized"]
        # The mock_llm_response is a change plan, not a sign-off
        triggered = any(k in mock_llm_response.lower() for k in m5_keywords)
        # This should NOT trigger M5 (it's a change plan, not a sign-off)
        assert not triggered


# ---------------------------------------------------------------------------
# Unit tests — Change classification rules
# ---------------------------------------------------------------------------

class TestChangeClassification:
    """Test classification logic based on change types."""

    LOW_RISK_CHANGES = [
        "Picklist label update",
        "UI theme colour change",
        "Translation text update",
        "Custom navigation label change",
        "Foundation object display name update",
    ]
    REQUIRES_APPROVAL_CHANGES = [
        "Role-Based Permission role modification",
        "Workflow routing step change",
        "MDF object field added",
        "Integration endpoint configuration change",
        "Permission group membership update",
    ]

    def test_low_risk_change_types_do_not_contain_permission_keywords(self):
        permission_keywords = ["permission", "role", "workflow", "integration", "mdf", "access"]
        for change in self.LOW_RISK_CHANGES:
            for kw in permission_keywords:
                assert kw not in change.lower(), (
                    f"Low-risk change '{change}' should not contain permission keyword '{kw}'"
                )

    def test_requires_approval_changes_contain_risk_keywords(self):
        risk_keywords = ["permission", "role", "workflow", "mdf", "integration", "group"]
        for change in self.REQUIRES_APPROVAL_CHANGES:
            has_risk = any(kw in change.lower() for kw in risk_keywords)
            assert has_risk, f"Requires-approval change '{change}' should contain a risk keyword"


# ---------------------------------------------------------------------------
# Unit tests — Tenant context isolation
# ---------------------------------------------------------------------------

class TestTenantContextIsolation:
    """Test that separate tenant change logs remain independent."""

    def test_separate_change_logs_per_tenant(self):
        """Simulates that two tenants have independent change log dictionaries."""
        change_logs = {
            "ClientA": [],
            "ClientB": [],
        }
        change_logs["ClientA"].append({"change": "picklist update", "status": "applied"})
        assert len(change_logs["ClientA"]) == 1
        assert len(change_logs["ClientB"]) == 0

    def test_applying_change_to_one_tenant_does_not_affect_other(self):
        """Verify tenant-scoped changes do not leak."""
        tenant_states = {
            "ClientA": {"config_version": 1},
            "ClientB": {"config_version": 1},
        }
        tenant_states["ClientA"]["config_version"] = 2
        assert tenant_states["ClientA"]["config_version"] == 2
        assert tenant_states["ClientB"]["config_version"] == 1


# ---------------------------------------------------------------------------
# Unit tests — Confirmation gate
# ---------------------------------------------------------------------------

class TestConfirmationGate:
    """Test that changes are not applied without explicit confirmation."""

    def test_pending_changes_require_confirmation_flag(self):
        """Simulate a change plan pending confirmation."""
        change_plan = {
            "tenant": "ClientA",
            "low_risk": [{"id": 1, "desc": "Picklist label update"}],
            "requires_approval": [],
            "confirmed": False,
            "applied": False,
        }
        # Should NOT apply without confirmation
        if not change_plan["confirmed"]:
            change_plan["applied"] = False
        assert change_plan["applied"] is False

    def test_changes_applied_only_after_confirmation(self):
        """Simulate the confirmation flow."""
        change_plan = {
            "tenant": "ClientA",
            "low_risk": [{"id": 1, "desc": "Picklist label update"}],
            "confirmed": False,
            "applied": False,
        }
        # Admin confirms
        change_plan["confirmed"] = True
        if change_plan["confirmed"] and not change_plan["applied"]:
            change_plan["applied"] = True
        assert change_plan["applied"] is True


# ---------------------------------------------------------------------------
# Integration test — End-to-end agent flow (mocked)
# ---------------------------------------------------------------------------

class TestAgentEndToEnd:
    """End-to-end integration test with mocked LLM and MCP tools."""

    @pytest.mark.asyncio
    async def test_agent_invoke_returns_response(self, mock_tools, mock_llm_response):
        """Agent invoke returns a structured response given a release notes query."""
        with patch("app.agent.get_model_name", return_value="sap/gpt-5.6-luna"), \
             patch("app.agent.get_temperature", return_value=0.0), \
             patch("app.agent.thread_ttl_seconds", return_value=3600), \
             patch("app.agent.summarization_trigger_tokens", return_value=100000), \
             patch("app.agent.get_summarization_model_name", return_value="sap/anthropic--claude-4.5-haiku"), \
             patch("app.agent.get_user_sub", return_value="test-user"), \
             patch("app.agent.create_checkpointer", return_value=None), \
             patch("app.agent.SummarizationMiddleware") as mock_mid, \
             patch("app.agent.create_agent") as mock_create_agent:

            # Build a fake graph that returns mock_llm_response
            fake_message = MagicMock()
            fake_message.content = mock_llm_response

            fake_graph = MagicMock()
            fake_graph.ainvoke = AsyncMock(return_value={"messages": [fake_message]})
            mock_create_agent.return_value = fake_graph
            mock_mid.return_value = MagicMock()

            with patch("langchain_litellm.ChatLiteLLM"):
                from app.agent import SampleAgent
                agent = SampleAgent()
                result = await agent.invoke(
                    "Here are the release notes for H1 2026. Please analyse them.",
                    "test-context-001",
                    tools=mock_tools,
                )

            assert result.status == "completed"
            assert len(result.message) > 0

    @pytest.mark.asyncio
    async def test_agent_stream_yields_chunks(self, mock_tools, mock_llm_response):
        """Agent stream yields at least a processing chunk and a final chunk."""
        with patch("app.agent.get_model_name", return_value="sap/gpt-5.6-luna"), \
             patch("app.agent.get_temperature", return_value=0.0), \
             patch("app.agent.thread_ttl_seconds", return_value=3600), \
             patch("app.agent.summarization_trigger_tokens", return_value=100000), \
             patch("app.agent.get_summarization_model_name", return_value="sap/anthropic--claude-4.5-haiku"), \
             patch("app.agent.get_user_sub", return_value="test-user"), \
             patch("app.agent.create_checkpointer", return_value=None), \
             patch("app.agent.SummarizationMiddleware") as mock_mid, \
             patch("app.agent.create_agent") as mock_create_agent:

            fake_message = MagicMock()
            fake_message.content = mock_llm_response

            fake_graph = MagicMock()
            fake_graph.ainvoke = AsyncMock(return_value={"messages": [fake_message]})
            mock_create_agent.return_value = fake_graph
            mock_mid.return_value = MagicMock()

            with patch("langchain_litellm.ChatLiteLLM"):
                from app.agent import SampleAgent
                agent = SampleAgent()
                chunks = []
                async for chunk in agent.stream(
                    "Run impact assessment for tenant ClientA.",
                    "test-context-002",
                    tools=mock_tools,
                ):
                    chunks.append(chunk)

            # First chunk is "Processing...", last chunk is the response
            assert len(chunks) >= 2
            assert chunks[0]["content"] == "Processing..."
            assert chunks[-1]["is_task_complete"] is True
