from .simple_agent import *

def execute_code_from_string(code_string, df, glo = globals(), loc = locals(), ret_variable='result'):
    try:
        loc['df'] = df
        exec(code_string, glo, loc)
        return loc[ret_variable]
    except Exception as e:
        raise ValueError(f"Error executing code: {e}")

class NL2Coder(Agent):
    def __init__(self, llm_name=LLM_NAME, chains: List = [InitOP()], PROMPT = None, agent_name='nl2coder', logger_root='tmp/table_llm_log', logger_file=f'mula_tabpro_v{TABLELLM_VERSION}.log', mode='base'):
        super().__init__(llm_name=llm_name, chains=chains, PROMPT=PROMPT, agent_name=agent_name, logger_root=logger_root, logger_file=logger_file)
        self.mode = mode
        

    def process(self, data:TQAData):
        self.last_log = None
        self.self_corr_inses = []
        self.icl_inses = []
        self.err_raise_cnt = 0
        self.code, self.ans = 'INIT', 'INIT'

        data.tbl = add_row_number_to_df(data.tbl, col_name='row_id')
        data = update_TData_col_type(data, col_type={'row_id': 'numerical'})
        
        while True:
            prompt = self._ans_gen_prompt(data)
            out = self.gpt.query(prompt)
            self.logger.log_message(line_limit=cut_log, level='debug', msg='Prompt: ' + prompt)
            self.logger.log_message(line_limit=cut_log, level='debug', msg=f'Output: {out}')
            try:
                code = parse_any_string(out, hard_replace='Code:')
                ans = self.exe_code(code, data)
                self.logger.log_message(line_limit=cut_log, level='debug', msg=f'tbl: {df_to_cotable(data.tbl)}')
                break
            except Exception as e:
                self.code = code
                self.ans = str(e)
                self._record_error_raise(data.id + '(ID)' + str(e))
        
        if self.last_log is not None:
            self.last_log = None

        return code, ans

    def exe_code(self, code: str, data:TQAData):
        df = data.tbl
        result = execute_code_from_string(code, df)
        if TASK_TYPE == 'tableqa':
            if type(result) == list:
                result = '|'.join([str(r) for r in result])
        elif TASK_TYPE == 'tablefact':
            # if result is None:
            #     result = False
            try:
                result = bool(result)
            except:
                raise ValueError(f'E: The result of the code is not boolean: {result}')
            
            result = 1 if result else 0

        return str(result)

    def _ans_gen_prompt(self, data:TQAData):
        DEMO_NL2CODE = DEMO_NL2CODE_COMPLETE if self.mode=='base' else DEMO_NL2CODE_PREP
        QUERY_NL2CODE = QUERY_NL2CODE_COMPLETE if self.mode=='base' else QUERY_NL2CODE_PREP
        SELF_CORREC_INS_NL2CODE = SELF_CORREC_INS_NL2CODE_COMPLETE if self.mode=='base' else SELF_CORREC_INS_NL2CODE_PREP

        tbl, question, title = data.tbl, data.question, data.title

        row_len = len(tbl)
        row_len = min(row_len, DEFAULT_ROW_CUT)
        prompt = ''
        for row_lim in range(row_len, 0, -2):
            demo = copy.deepcopy(DEMO_NL2CODE)
            create_table, table_ret = binder_nl2sql_prompt(data, cut_line=row_lim)
            query = QUERY_NL2CODE.format(table=table_ret, question=question, title=title)


            if self.self_correction and self.last_log is not None:
                query = query.replace('Code:', 'Last Error: ' + self.last_log + '\n' + 'Code:')

            
            prompt = demo + '\n\n' + query
            if cal_tokens(prompt) <= MAX_INPUT_LIMIT-MAX_OUTPUT_LIMIT:
                break
        if len(prompt) == 0:
            raise ValueError(f'E: The prompt is empty, the first row is too long!')
        return prompt
