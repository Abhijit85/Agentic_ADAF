from src.model.mula_tabpro.agent.simple_agent import parse_between_flag, Agent, List, InitOP, TQAData, cut_log, TABLELLM_VERSION, TASK_TYPE, DEFAULT_ROW_CUT, df_to_cotable_old, cal_tokens, MAX_INPUT_LIMIT, MAX_OUTPUT_LIMIT, parse_any_string, LLM_NAME

from src.model.autotqa.prompt import DEMO_CRITIC, QUERY_CRITIC, QUERY_REACT_STEP_CRITIC


class AutoTQACritic(Agent):
    def __init__(self, llm_name=LLM_NAME, chains: List = [InitOP()], PROMPT = None, agent_name='critic', logger_root='tmp/autotqa_log', logger_file=f'autotqa_v{TABLELLM_VERSION}.log'):
        super().__init__(llm_name=llm_name, chains=chains, PROMPT=PROMPT, agent_name=agent_name, logger_root=logger_root, logger_file=logger_file)

    def process(self, data:TQAData, react_records:List, fewshot=True):
        self.err_raise_cnt = 0
        self.last_log = None
        while True:
            try:
                prompt = self._ans_gen_prompt(data, react_records, fewshot)
                self.logger.log_message(line_limit=cut_log, level='debug', msg='Prompt: ' + prompt)
                out = self.gpt.query(prompt)
                self.logger.log_message(line_limit=cut_log, level='debug', msg=f'Output: {out}')
                preliminary_evaluation, summarize_the_result, final_report = self.parse_answer(out)
                break
            except Exception as e:
                self._record_error_raise(e)
                continue

        return preliminary_evaluation, summarize_the_result, final_report

    def parse_answer(self, ans: str):
        # use <preliminary_evaluation> your preliminary evaluation </preliminary_evaluation>, <summarize_the_result> summarize the result </summarize_the_result>, and <final_report> the final report </final_report> to structure the report
        # parse the answer
        preliminary_evaluation = parse_between_flag(ans, flag='preliminary_evaluation')
        summarize_the_result = parse_between_flag(ans, flag='summarize_the_result')
        final_report = parse_between_flag(ans, flag='final_report')
        return preliminary_evaluation, summarize_the_result, final_report

    def _ans_gen_prompt(self, data:TQAData, react_records:List, fewshot=True):
        tbl, question = data.tbl, data.question

        demo = DEMO_CRITIC if fewshot else ''

        row_len = DEFAULT_ROW_CUT

        prompt = ''

        table = df_to_cotable_old(tbl, row_len)

        react_records_strs = []
        for i in range(len(react_records)):
            record = react_records[i]
            input_table = record['input_table']
            engineer_plan = record['engineer_plan']
            action_type = record['action_type']
            action = record['action']
            agent_name = 'NL2SQL' if action_type == 'SQL' else 'NL2Code'

            if i == 0:
                initial_instruction=f'Title: {data.title}'
                question_or_not= f'\nQuestion: {question}' if TASK_TYPE == 'tableqa' else f'\nStatement: {question}'
            else:
                initial_instruction=f'Get new table after invoke the Executor({agent_name}) tool:'
                question_or_not=''
            
            cur_react_str = QUERY_REACT_STEP_CRITIC.format(initial_instruction=initial_instruction,
                            table=input_table, question_or_not=question_or_not,
                            engineer_plan=engineer_plan, code_type=action_type, code=action)
            
            react_records_strs.append(cur_react_str)

        react_records_str = '\n'.join(react_records_strs)

        query = QUERY_CRITIC.format(react_records_str=react_records_str, error=str(self.last_log))


        prompt = demo + '\n\n' + query
        
        if cal_tokens(prompt) > MAX_INPUT_LIMIT-MAX_OUTPUT_LIMIT:
            raise ValueError(f'E: The prompt is too long!')
        
        return prompt