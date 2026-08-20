from hypothesis.stateful import RuleBasedStateMachine, invariant, rule

from nexus_core.policy import ActionApproval, ActionIntent, evaluate_action


class AuthorizationGateMachine(RuleBasedStateMachine):
    """Exercise approval reuse and intent changes across a sequence of gate decisions.

    The critical invariant is action-scoped authorization: approval for one consequential
    action must never bleed into another action merely because the action kind or actor
    context is similar.
    """

    def __init__(self):
        super().__init__()
        self.intent = ActionIntent(
            action_id="send:thread-a",
            kind="send_external_message",
            description="Send the reviewed response for thread A.",
        )
        self.approval = None
        self.last_decision = evaluate_action(self.intent, approval=self.approval)

    @rule()
    def approve_current_action(self):
        self.approval = ActionApproval(self.intent.action_id, approved=True)
        self.last_decision = evaluate_action(self.intent, approval=self.approval)

    @rule()
    def switch_to_different_send(self):
        self.intent = ActionIntent(
            action_id="send:thread-b",
            kind="send_external_message",
            description="Send the reviewed response for thread B.",
        )
        self.last_decision = evaluate_action(self.intent, approval=self.approval)

    @rule()
    def switch_to_payment(self):
        self.intent = ActionIntent(
            action_id="payment:po-1",
            kind="payment",
            description="Release payment for PO-1.",
            reversible=False,
        )
        self.last_decision = evaluate_action(self.intent, approval=self.approval)

    @rule()
    def switch_to_safe_read(self):
        self.intent = ActionIntent(
            action_id="read:mailbox",
            kind="read",
            description="Read the mailbox for decision-relevant changes.",
        )
        self.last_decision = evaluate_action(self.intent, approval=self.approval)

    @invariant()
    def approval_scope_is_never_implicit(self):
        matched = (
            isinstance(self.approval, ActionApproval)
            and self.approval.approved is True
            and self.approval.action_id == self.intent.action_id
        )
        consequential = self.intent.kind in {
            "send_external_message",
            "merge_code",
            "production_deploy",
            "change_access",
            "delete_or_archive",
            "contract_or_po",
            "payment",
            "signature",
        } or not self.intent.reversible

        if consequential and not matched:
            assert self.last_decision.allowed_now is False
            assert self.last_decision.requires_human_approval is True
        elif consequential and matched:
            assert self.last_decision.allowed_now is True
        else:
            assert self.last_decision.allowed_now is True


TestAuthorizationGateMachine = AuthorizationGateMachine.TestCase
