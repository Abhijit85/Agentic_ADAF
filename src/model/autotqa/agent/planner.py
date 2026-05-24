from src.model.mula_tabpro.agent.simple_agent import Agent, List, InitOP, TQAData, cut_log, TABLELLM_VERSION, DEFAULT_ROW_CUT, df_to_cotable_old, cal_tokens, MAX_INPUT_LIMIT, MAX_OUTPUT_LIMIT, parse_any_string, LLM_NAME

from src.model.autotqa.prompt import DEMO_PLANNER, QUERY_PLANNER, DEMO_MODIFY_PLANNER, QUERY_MODIFY_PLANNER


class AutoTQAPlanner(Agent):
    def __init__(self, llm_name=LLM_NAME, chains: List = [InitOP()], PROMPT = None, agent_name='planner', logger_root='tmp/autotqa_log', logger_file=f'autotqa_v{TABLELLM_VERSION}.log'):
        super().__init__(llm_name=llm_name, chains=chains, PROMPT=PROMPT, agent_name=agent_name, logger_root=logger_root, logger_file=logger_file)

    def modify_plan_from_critic(self, data:TQAData, historical_reasoning_plan:str, critic_report:str):
        self.err_raise_cnt = 0
        self.last_log = None
        while True:
            try:
                prompt = self._modify_plan_prompt(data, historical_reasoning_plan, critic_report)
                self.logger.log_message(line_limit=cut_log, level='debug', msg='Prompt: ' + prompt)
                out = self.gpt.query(prompt)
                self.logger.log_message(line_limit=cut_log, level='debug', msg=f'Output: {out}')
                new_reasoning_plan = self.parse_answer(out)
                break
            except Exception as e:
                self._record_error_raise(e)
                continue

        return new_reasoning_plan

    def process(self, data:TQAData, fewshot=True):
        self.err_raise_cnt = 0
        self.last_log = None
        while True:
            try:
                prompt = self._ans_gen_prompt(data, fewshot)
                self.logger.log_message(line_limit=cut_log, level='debug', msg='Prompt: ' + prompt)
                out = self.gpt.query(prompt)
                self.logger.log_message(line_limit=cut_log, level='debug', msg=f'Output: {out}')
                ans = self.parse_answer(out)
                break
            except Exception as e:
                self._record_error_raise(e)
                continue
            
        return ans
    
    def parse_answer(self, ans: str):
        ans = parse_any_string(ans, hard_replace='Reasoning Plan:')
        if len(ans) > 0 and ans[-1] == '.':
            ans = ans[:-1]
        ans = ans.strip()
        return ans

    def _modify_plan_prompt(self, data:TQAData, historical_reasoning_plan:str, critic_report:str, fewshot=True):
        tbl, question = data.tbl, data.question

        demo = DEMO_MODIFY_PLANNER if fewshot else ''

        row_len = DEFAULT_ROW_CUT
        prompt = ''

        table = df_to_cotable_old(tbl, row_len)
        query = QUERY_MODIFY_PLANNER.format(table=table, question=question, title=data.title,
                                          old_reasoning_plan=historical_reasoning_plan,
                                          critic_report=critic_report, error=str(self.last_log))
        prompt = demo + '\n\n' + query
        prompt = prompt.strip()
        
        if cal_tokens(prompt) > MAX_INPUT_LIMIT-MAX_OUTPUT_LIMIT:
            raise ValueError(f'E: The prompt is empty, the first row is too long!')
        return prompt

    def _ans_gen_prompt(self, data:TQAData, fewshot=True):
        tbl, question = data.tbl, data.question

        demo = DEMO_PLANNER if fewshot else ''

        row_len = DEFAULT_ROW_CUT
        prompt = ''

        table = df_to_cotable_old(tbl, row_len)
        query = QUERY_PLANNER.format(table=table, question=question, title=data.title, error=str(self.last_log))
        prompt = demo + '\n\n' + query
        prompt = prompt.strip()
        
        if cal_tokens(prompt) > MAX_INPUT_LIMIT-MAX_OUTPUT_LIMIT:
            raise ValueError(f'E: The prompt is empty, the first row is too long!')
        return prompt
