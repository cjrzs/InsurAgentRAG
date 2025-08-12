class BaseAgent:
    def __init__(self, name, llm, tools=None, memory=None):
        self.name = name
        self.llm = llm
        self.tools = tools or []
        self.memory = memory

    def act(self, **kwargs):
        raise NotImplementedError

