"""Multi-agent orchestration.

Two entry points:

run_single_agent(db, client_id, role, task, shape) — one specialist, persisted
as an AgentRun.

run_council(db, client_id, kind, question, options_hint) — the full pipeline:

    1. PLAN        Planner decomposes the question.
    2. PROPOSE     Relevant specialists each produce a proposal (with RAG context).
    3. DEBATE      Each specialist critiques the others' proposals (1-2 rounds).
    4. VOTE        Every participant votes on the refined options with confidence.
    5. DECIDE      Decision Agent synthesizes the final strategy.
    6. REVIEW      Supervisor approves or annotates defects.

The full transcript, votes, decision, token usage and cost are persisted on the
AgentRun row, so the UI can replay how the team reached its answer.
"""
from __future__ import annotations

import datetime as dt
import logging
from typing import Any

from sqlalchemy.orm import Session

from app.agents.prompts import DEBATER_ADDENDUM, ROLE_PROMPTS
from app.ai.router import llm
from app.models.aether import AgentRun
from app.rag.store import build_context

log = logging.getLogger("aether.agents")

# Which specialists join the council for each kind of run.
COUNCIL_ROSTERS: dict[str, list[str]] = {
    "strategy_council": ["research", "strategy", "copy", "creative", "analytics", "optimization"],
    "campaign_plan": ["strategy", "creative", "analytics", "optimization"],
    "performance_review": ["analytics", "optimization", "strategy"],
    "creative_direction": ["research", "copy", "creative"],
    "default": ["research", "strategy", "analytics"],
}

DEBATE_ROUNDS = 1  # each extra round adds n_agents LLM calls


def _now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


class _RunTracker:
    """Accumulates transcript + usage onto an AgentRun row."""

    def __init__(self, db: Session, run: AgentRun):
        self.db = db
        self.run = run
        self.steps: list[dict[str, Any]] = []
        self.messages: list[dict[str, Any]] = []
        self.tokens_in = 0
        self.tokens_out = 0
        self.cost = 0.0

    def record(self, agent: str, action: str, result: Any) -> None:
        self.steps.append({"agent": agent, "action": action, "at": _now().isoformat()})
        self.messages.append({"agent": agent, "action": action, "content": result})
        self._flush()

    def track_usage(self, res: Any) -> None:
        self.tokens_in += res.tokens_in
        self.tokens_out += res.tokens_out
        self.cost += res.cost_usd

    def _flush(self) -> None:
        self.run.steps = self.steps
        self.run.messages = self.messages
        self.run.tokens_in = self.tokens_in
        self.run.tokens_out = self.tokens_out
        self.run.cost_usd = round(self.cost, 6)
        self.db.commit()


def _ask(tracker: _RunTracker, role: str, user: str, shape: Any | None = None,
         extra_system: str = "", client_id: str | None = None,
         temperature: float = 0.7) -> Any:
    res = llm.complete(
        role=role,
        system=ROLE_PROMPTS[role] + extra_system,
        user=user,
        shape=shape,
        client_id=client_id,
        temperature=temperature,
    )
    tracker.track_usage(res)
    return res.data if shape is not None else res.text


def run_single_agent(db: Session, client_id: str, role: str, task: str,
                     shape: Any | None = None, *, kind: str | None = None,
                     use_rag: bool = True) -> AgentRun:
    """One specialist, one task, persisted."""
    run = AgentRun(client_id=client_id, kind=kind or role, status="RUNNING",
                   input={"role": role, "task": task[:2000]}, started_at=_now())
    db.add(run)
    db.commit()
    tracker = _RunTracker(db, run)
    try:
        context = build_context(db, client_id, task) if use_rag else ""
        user = task if not context else f"CLIENT KNOWLEDGE BASE (retrieved):\n{context}\n\nTASK:\n{task}"
        result = _ask(tracker, role, user, shape, client_id=client_id)
        tracker.record(role, "answer", result)
        run.decision = result if isinstance(result, (dict, list)) else {"text": result}
        run.status = "DONE"
    except Exception as exc:
        log.exception("single agent run failed")
        run.status = "FAILED"
        run.error = str(exc)[:2000]
    run.finished_at = _now()
    db.commit()
    return run


def run_council(db: Session, client_id: str, kind: str, question: str,
                context_hint: str = "") -> AgentRun:
    """Full multi-agent council: plan → propose → debate → vote → decide → review."""
    roster = COUNCIL_ROSTERS.get(kind, COUNCIL_ROSTERS["default"])
    run = AgentRun(client_id=client_id, kind=kind, status="RUNNING",
                   input={"question": question[:2000], "roster": roster},
                   started_at=_now())
    db.add(run)
    db.commit()
    tracker = _RunTracker(db, run)

    try:
        rag = build_context(db, client_id, question,
                            namespaces=["business", "research", "performance", "creatives"])
        base_ctx = (f"CLIENT KNOWLEDGE (retrieved):\n{rag}\n\n"
                    f"ADDITIONAL CONTEXT:\n{context_hint or '(none)'}\n\n"
                    f"QUESTION FOR THE COUNCIL:\n{question}")

        # 1 — PLAN
        plan = _ask(tracker, "planner", base_ctx, shape={
            "objective": "one-line restatement of what must be decided",
            "key_unknowns": ["unknown that most affects the answer"],
            "evaluation_criteria": ["criterion the final answer will be judged on"],
        }, client_id=client_id, temperature=0.4)
        tracker.record("planner", "plan", plan)

        # 2 — PROPOSE (each specialist)
        proposals: dict[str, Any] = {}
        for role in roster:
            p = _ask(tracker, role, base_ctx + "\n\nGive YOUR proposal from your specialty. "
                     f"Judging criteria: {plan.get('evaluation_criteria')}", shape={
                "proposal": "your recommended approach in 2-4 sentences",
                "reasoning": "the mechanism: why this beats alternatives",
                "risks": ["main risk"],
                "confidence": "confidence",
            }, client_id=client_id)
            proposals[role] = p
            tracker.record(role, "proposal", p)

        # 3 — DEBATE
        for round_no in range(DEBATE_ROUNDS):
            import json as _json
            board = _json.dumps(proposals, indent=1)[:6000]
            for role in roster:
                critique = _ask(tracker, role,
                                f"{base_ctx}\n\nALL PROPOSALS ON THE TABLE:\n{board}\n\n"
                                "Critique the strongest competing proposal and defend or amend yours.",
                                shape={
                                    "challenges": [{"target_agent": "role name", "challenge": "specific flaw"}],
                                    "amended_proposal": "your (possibly updated) proposal",
                                    "conceded_points": ["point you now accept from others"],
                                }, extra_system=DEBATER_ADDENDUM, client_id=client_id)
                proposals[role] = {**proposals[role], "proposal": critique.get("amended_proposal",
                                                                               proposals[role].get("proposal"))}
                tracker.record(role, f"debate_r{round_no + 1}", critique)

        # 4 — VOTE
        import json as _json
        options = {r: p.get("proposal") for r, p in proposals.items()}
        votes = []
        for role in roster:
            v = _ask(tracker, role,
                     f"Final proposals:\n{_json.dumps(options, indent=1)[:5000]}\n\n"
                     "Vote for the single best proposal (you may vote for your own only "
                     "if you genuinely believe it strongest).", shape={
                         "vote_for": "role name of the proposal you back",
                         "confidence": "confidence",
                         "reason": "one sentence",
                     }, client_id=client_id, temperature=0.3)
            v["voter"] = role
            votes.append(v)
            tracker.record(role, "vote", v)
        run.votes = votes
        db.commit()

        # 5 — DECIDE
        decision = _ask(tracker, "decision",
                        f"{base_ctx}\n\nPROPOSALS:\n{_json.dumps(options, indent=1)[:5000]}\n\n"
                        f"VOTES:\n{_json.dumps(votes, indent=1)[:2500]}\n\n"
                        "Synthesize the final decision.", shape={
                            "decision": "the chosen strategy, concrete and specific",
                            "why": "expected-value reasoning",
                            "risks": ["risk"],
                            "kill_criteria": ["measurable condition that means we were wrong"],
                            "first_48h_actions": [{"action": "specific action", "owner": "agent role"}],
                        }, client_id=client_id, temperature=0.3)
        tracker.record("decision", "decision", decision)

        # 6 — REVIEW
        review = _ask(tracker, "supervisor",
                      f"QUESTION: {question}\n\nFINAL DECISION:\n{_json.dumps(decision, indent=1)[:4000]}",
                      shape={"verdict": "APPROVED or REJECTED",
                             "defects": ["defect if any"],
                             "notes": "one-paragraph quality assessment"},
                      client_id=client_id, temperature=0.2)
        tracker.record("supervisor", "review", review)

        run.decision = {"plan": plan, "decision": decision, "review": review}
        run.status = "DONE"
    except Exception as exc:
        log.exception("council run failed")
        run.status = "FAILED"
        run.error = str(exc)[:2000]

    run.finished_at = _now()
    db.commit()
    return run
