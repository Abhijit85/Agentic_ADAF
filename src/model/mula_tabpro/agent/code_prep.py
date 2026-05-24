from .simple_agent import *

def execute_code_from_string(code_string, df, glo = globals(), loc = locals(), ret_variable='df'):
    try:
        loc['df'] = df
        exec(code_string, glo, loc)
        return loc[ret_variable]
    except Exception as e:
        raise ValueError(f"Error executing code: {e}")

class CodePrep(Agent):
    def __init__(self, llm_name=LLM_NAME, chains: List = [InitOP()], PROMPT = None, agent_name='code_prep', logger_root='tmp/table_llm_log', logger_file=f'mula_tabpro_v{TABLELLM_VERSION}.log'):
        super().__init__(llm_name=llm_name, chains=chains, PROMPT=PROMPT, agent_name=agent_name, logger_root=logger_root, logger_file=logger_file)
        

    def process(self, data:TQAData):
        self.last_log = None
        self.self_corr_inses = []
        self.icl_inses = []
        self.err_raise_cnt = 0
        self.data = data
        self.log_info = {}

        self.data.tbl, _ = base_clean_dataframe(self.data.tbl)
        self.data.tbl = add_row_number_to_df(self.data.tbl, col_name='row_id')
        self.data = update_TData_col_type(self.data, col_type={'row_id': 'numerical'})
        
        while True:
            prompt = self._ans_gen_prompt(self.data)
            out = self.gpt.query(prompt)
            self.logger.log_message(line_limit=cut_log, level='debug', msg='Prompt: ' + prompt)
            self.logger.log_message(line_limit=cut_log, level='debug', msg=f'Output: {out}')
            try:
                code = parse_any_string(out, hard_replace='Code:')
                self.log_info['code'] = code
                new_df = self.exe_code(code, self.data)
                self.logger.log_message(line_limit=cut_log, level='debug', msg=f'Old tbl: {df_to_cotable(self.data.tbl)}')
                self.logger.log_message(line_limit=cut_log, level='debug', msg=f'New tbl: {df_to_cotable(new_df)}')
                self.data.tbl = new_df
                break
            except Exception as e:
                self.code = code
                self._record_error_raise(data.id + '(ID)' + str(e))
        
        if self.last_log is not None:
            self.last_log = None
            
            self.logger.log_message(msg=f'[DEBUG_CORRECT_FLAG]---- ID: {data.id}, SUCCESSFULLY DEBUG IN {self.err_raise_cnt} times! ----')
        else:
            self.logger.log_message(msg=f'[NO_BUG_FLAG]---- ID: {data.id}, NO BUGS! ----')

        return self.data, self.log_info

    def exe_code(self, code: str, data:TQAData):
        df = copy.deepcopy(data.tbl)
        df = execute_code_from_string(code, df)
        # if len(df) != len(data.tbl):
        #     raise ValueError(f'Error: The number of rows in the table is changed after executing the code! you should not select relevant row!!!')

        return df

    def _ans_gen_prompt(self, data:TQAData):

        tbl, question, title = data.tbl, data.question, data.title

        row_len = len(tbl)
        row_len = min(row_len, DEFAULT_ROW_CUT)
        prompt = ''
        for row_lim in range(row_len, 0, -2):
            demo = copy.deepcopy(DEMO_CODE_PREP)
            create_table, table_ret = binder_nl2sql_prompt(data, cut_line=row_lim)
            query = QUERY_CODE_PREP.format(table=table_ret, question=question, title=title)

            if self.self_correction and self.last_log is not None:
                query = query.replace('Code:', 'Last Error: ' + self.last_log + '\n' + 'Code:')
            
            prompt = demo + '\n\n' + query
            if cal_tokens(prompt) <= MAX_INPUT_LIMIT-MAX_OUTPUT_LIMIT:
                break
        if len(prompt) == 0:
            raise ValueError(f'E: The prompt is empty, the first row is too long!')
        return prompt
