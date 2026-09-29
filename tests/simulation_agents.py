"""Deterministic user personas for repeatable application simulations."""


class PersonaAgent:
    name = "base"

    def ask(self, question: str) -> str:
        raise NotImplementedError


class SkepticalFarmerAgent(PersonaAgent):
    name = "skeptical_farmer"

    def ask(self, question: str) -> str:
        return f"Não acredito que o aplicativo saiba isso. {question} Responda sem enrolar."


class ProfessionalAgent(PersonaAgent):
    name = "professional"

    def ask(self, question: str) -> str:
        return f"{question} Informe também a fonte e as condições técnicas usadas."


class CasualUserAgent(PersonaAgent):
    name = "casual_user"

    def ask(self, question: str) -> str:
        return f"Oi, pode me explicar de um jeito simples? {question}"


AGENTS = (
    SkepticalFarmerAgent(),
    ProfessionalAgent(),
    CasualUserAgent(),
)
