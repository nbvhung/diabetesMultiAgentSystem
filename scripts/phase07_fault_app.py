"""Isolated local QA/demo entry point. Never imported by the production application."""
from backend.app.main import create_app
from backend.app.knowledge.store import KnowledgeUnavailable


class DownGraph:
    def candidates(self,*args):raise KnowledgeUnavailable('SYNTHETIC_FAULT_INJECTION')
    def summary(self):raise KnowledgeUnavailable('SYNTHETIC_FAULT_INJECTION')


def knowledge_down():
    return create_app(knowledge_store=DownGraph())
