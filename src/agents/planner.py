from .base_agent import BaseAgent

class StrategyAgent(BaseAgent):
    def act(self, insured_info, current_policies):
        prompt = f"""
        你是一位资深保险顾问，请基于以下受保人信息与当前保单信息，
        制定一个最优的保险策略，并给出理由。
        
        受保人信息：{insured_info}
        当前保单信息：{current_policies}
        """
        return self.llm.generate(prompt)

