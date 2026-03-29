"""
ai/query.py — Natural language query interface.

Lets the user ask free-form questions about their simulation in plain English.
Maintains full conversation history so follow-up questions work correctly.

Usage:
    from ai.query import QueryInterface
    qi = QueryInterface(ctx)
    qi.run()          # interactive REPL
    qi.ask("Why is month 4 the insolvency point?")   # programmatic
"""

from __future__ import annotations

from ai.client import SimulationContext, _stream_response

# ─────────────────────────────────────────────────────────────────────────────
# Query interface
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_SUFFIX = """
You are in an interactive Q&A session. The user will ask questions about this
simulation. Guidelines:
- Always ground your answer in specific numbers from the data above.
- When referencing a month, give its dollar figures.
- If the user asks "what if" questions, reason through the impact step by step.
- Keep answers concise but complete — use bullet points for multi-part answers.
- If you don't have enough data to answer confidently, say so clearly.
- Never make up numbers that aren't in the simulation data.
"""

WELCOME = """
┌─────────────────────────────────────────────────────────┐
│          💬  Financial Simulation Query Interface        │
│                                                         │
│  Ask anything about your simulation in plain English.   │
│  Type 'exit' or 'quit' to leave.                        │
│  Type 'clear' to reset conversation history.            │
└─────────────────────────────────────────────────────────┘

Example questions:
  • Why does the EXPECTED scenario hit insolvency so early?
  • What's driving the cash cliff in month 3?
  • How much does the Acme contract help?
  • Compare BEST and WORST runway — what's the difference?
  • What would happen if we delayed hiring by 2 months?
"""


class QueryInterface:
    def __init__(self, ctx: SimulationContext):
        self.ctx = ctx
        self._system = ctx.to_system_prompt() + "\n\n" + SYSTEM_SUFFIX

    def ask(self, question: str) -> str:
        """Ask a single question and get a response (maintains history)."""
        self.ctx.chat_history.append({"role": "user", "content": question})
        response = _stream_response(self._system, self.ctx.chat_history, max_tokens=600)
        self.ctx.chat_history.append({"role": "assistant", "content": response})
        return response

    def run(self) -> None:
        """Start interactive REPL."""
        print(WELCOME)

        while True:
            try:
                user_input = input("\n🧑 You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n\nExiting query interface.")
                break

            if not user_input:
                continue

            if user_input.lower() in {"exit", "quit", "q"}:
                print("Leaving query interface.")
                break

            if user_input.lower() == "clear":
                self.ctx.chat_history.clear()
                print("✅ Conversation history cleared.")
                continue

            if user_input.lower() == "help":
                print(WELCOME)
                continue

            print("\n🤖 CFO Assistant:\n")
            self.ask(user_input)
