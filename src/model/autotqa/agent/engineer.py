from src.model.mula_tabpro.agent.simple_agent import copy, post_process_sql, Agent, List, InitOP, TQAData, cut_log, TABLELLM_VERSION, LLM_NAME, DEFAULT_ROW_CUT, df_to_cotable_old, cal_tokens, MAX_INPUT_LIMIT, MAX_OUTPUT_LIMIT, parse_any_string

from .executor import AutoTQAExecutor
from src.model.autotqa.prompt import DEMO_ENGINEER, QUERY_ENGINEER, QUERY_REACT_ENGINEER

class AutoTQAEngineer(Agent):
    def __init__(self, llm_name=LLM_NAME, chains: List = [InitOP()], PROMPT = None, agent_name='engineer', logger_root='tmp/autotqa_log', logger_file=f'autotqa_v{TABLELLM_VERSION}.log'):
        super().__init__(llm_name=llm_name, chains=chains, PROMPT=PROMPT, agent_name=agent_name, logger_root=logger_root, logger_file=logger_file)
        self.executor = AutoTQAExecutor(llm_name=llm_name)

        self.MAX_REACT_ROUND = 10

    def process(self, data:TQAData, reasoning_plan:str, fewshot=True):

        agent_name = None
        prompt = None
        react_records = []
        self.cur_round = 0

        for _ in range(self.MAX_REACT_ROUND):

            self.err_raise_cnt = 0
            self.last_log = None
            comein_prompt = copy.deepcopy(prompt)
            react_record = {}
            while True:
                try:
                    prompt = self._ans_gen_prompt(data, reasoning_plan, fewshot=True, prompt=prompt, agent_name=agent_name)
                    self.logger.log_message(line_limit=cut_log, level='debug', msg='Prompt: ' + prompt)
                    out = self.gpt.query(prompt.replace('Engineering Plan:', 'Only Output One Sub-plan of the Engineer Plan, DO NOT OUTPUT SQL or PYTHON or ANYTHING ELSE!\nEngineering Plan:'))
                    self.cur_round += 1
                    self.logger.log_message(line_limit=cut_log, level='debug', msg=f'Outputed Engineer Plan: {out}')
                    agent_name, engineer_plan = self.parse_answer(out)
                    self.logger.log_message(line_limit=cut_log, level='debug', msg=f'Agent Name: {agent_name}, Engineer Plan: {engineer_plan}')
                    
                    input_tbl_str = df_to_cotable_old(data.tbl, DEFAULT_ROW_CUT)

                    react_record['input_table'] = input_tbl_str
                    react_record['engineer_plan'] = engineer_plan

                    if agent_name == 'NL2SQL':
                        prompt = prompt + f' ```{engineer_plan}```'
                        prompt = prompt + '\n' + f'SQL:'
                        self.logger.log_message(line_limit=cut_log, level='debug', msg='Prompt: ' + prompt)


                        sql_out = self.gpt.query(prompt.replace('SQL:', 'Only Output the SQL, DO NOT OUTPUT ENGINEER PLAN or ANYTHING ELSE!\nSQL:'))
                        self.cur_round += 1
                        self.logger.log_message(line_limit=cut_log, level='debug', msg=f'SQL: {sql_out}')
                        sql = parse_any_string(sql_out, code_type='SQL')

                        sql, _ = post_process_sql(sql, data.tbl, data.title)
                        data.tbl = self.executor.exe_sql(sql, data)
                        output_tbl_str = df_to_cotable_old(data.tbl, DEFAULT_ROW_CUT)
                        self.logger.log_message(line_limit=cut_log, level='debug', msg=f'tbl: {output_tbl_str}')
                        
                        react_record['action_type'] = 'SQL'
                        react_record['action'] = sql
                        react_record['output_table'] = output_tbl_str

                        prompt = prompt + f' ```{sql}```'

                    elif agent_name == 'NL2Code':
                        prompt = prompt + f' ```{engineer_plan}```'
                        prompt = prompt + '\n' + f'Python:'
                        self.logger.log_message(line_limit=cut_log, level='debug', msg='Prompt: ' + prompt)

                        code_out = self.gpt.query(prompt.replace('Python:', 'Only Output the Python, DO NOT OUTPUT ENGINEER PLAN or ANYTHING ELSE!\nPython:'))
                        self.cur_round += 1
                        self.logger.log_message(line_limit=cut_log, level='debug', msg=f'Python: {code_out}')
                        code = parse_any_string(code_out, code_type='Python')
                        
                        code = "import pandas as pd\nimport numpy as np\nimport re\n" + code

                        data.tbl = self.executor.exe_code(code, data)
                        output_tbl_str = df_to_cotable_old(data.tbl, DEFAULT_ROW_CUT)
                        self.logger.log_message(line_limit=cut_log, level='debug', msg=f'tbl: {output_tbl_str}')

                        react_record['action_type'] = 'Python'
                        react_record['action'] = code
                        react_record['output_table'] = output_tbl_str

                        prompt = prompt + f' ```{code}```'

                    elif agent_name == '[FINISH]':
                        react_record['action_type'] = 'END'
                        react_record['action'] = 'END'
                        react_record['output_table'] = 'As_Before'
                        break
                    else:
                        raise ValueError(f'E: Unknown agent name: {agent_name}')
                    break
                except Exception as e:
                    prompt = comein_prompt
                    self._record_error_raise(e)
                    continue
            
            react_records.append(react_record)
            
            if agent_name == '[FINISH]':
                break
            
        return react_records
    
    def parse_answer(self, out: str):
        engineer_plan = parse_any_string(out, hard_replace='Engineering Plan:')
        engineer_plan = engineer_plan.replace('```', '')
        if len(engineer_plan) > 0 and engineer_plan[-1] == '.':
            engineer_plan = engineer_plan[:-1]
        engineer_plan = engineer_plan.strip()
        if 'NL2SQL' in engineer_plan or 'nl2sql' in engineer_plan:
            return 'NL2SQL', engineer_plan
        elif 'NL2Code' in engineer_plan or 'nl2code' in engineer_plan:
            return 'NL2Code', engineer_plan
        elif '[FINISH]' in engineer_plan or '[FINISH]' in engineer_plan:
            return '[FINISH]', engineer_plan
        else:
            raise ValueError(f'E: Unknown agent name in the engineer plan: {engineer_plan}')

    def _ans_gen_prompt(self, data:TQAData, reasoning_plan:str, fewshot=True, prompt=None, agent_name='nl2sqler'):
        tbl, question = data.tbl, data.question
        demo = DEMO_ENGINEER if fewshot else ''

        row_len = DEFAULT_ROW_CUT
        table = df_to_cotable_old(tbl, row_len)

        if prompt is None:
            prompt = demo
            query = QUERY_ENGINEER.format(table=table, question=question, title=data.title, reasoning_plan=reasoning_plan, error=str(self.last_log))
        else:
            query = QUERY_REACT_ENGINEER.format(agent=agent_name, table=table, question=question, reasoning_plan=reasoning_plan, error=str(self.last_log))
        
        prompt = prompt + '\n\n' + query
        if cal_tokens(prompt) > MAX_INPUT_LIMIT-MAX_OUTPUT_LIMIT:
            raise ValueError(f'E: The prompt is too long!')

        return prompt
