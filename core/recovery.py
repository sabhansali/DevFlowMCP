from dataclasses import dataclass


@dataclass
class RecoveryDecision:
    retry: bool
    category: str
    reason: str


def classify(error: Exception | str, attempt: int, max_retries: int, tool_name: str = "") -> RecoveryDecision:
    message = str(error).lower()
    if any(term in message for term in ("outside", "policy", "approval", "sensitive", "invalid")):
        return RecoveryDecision(False, "policy_or_input", "Security and input errors are not retryable")
    if "timeout" in message or "timed out" in message:
        eligible = tool_name != "run_project_tests" and attempt < max_retries
        return RecoveryDecision(eligible, "timeout", "Retry only for eligible transient operations")
    if any(term in message for term in ("communication", "connection", "transport")) and attempt < max_retries:
        return RecoveryDecision(True, "mcp_communication", "Transient MCP communication failure")
    return RecoveryDecision(False, "tool_execution", "Operation failed without an eligible retry")
