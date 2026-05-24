from .simple_agent import *
import sqlite3

class NL2SQLer(Agent):
    def __init__(self, llm_name=LLM_NAME, chains: List = [InitOP()], PROMPT = None, agent_name='nl2sqler', logger_root='tmp/table_llm_log', logger_file=f'mula_tabpro_v{TABLELLM_VERSION}.log', mode='base'):
        super().__init__(llm_name=llm_name, chains=chains, PROMPT=PROMPT, agent_name=agent_name, logger_root=logger_root, logger_file=logger_file)
        self.mode = mode
        self.conn = sqlite3.connect(':memory:')

    def process(self, data:TQAData):
        self.last_log = None
        self.self_corr_inses = []
        self.icl_inses = []
        self.err_raise_cnt = 0
        self.sql, self.ans = 'INIT', 'INIT'

        data.tbl = add_row_number_to_df(data.tbl, col_name='row_id')
        data = update_TData_col_type(data, col_type={'row_id': 'numerical'})
        
        if self.mode == 'base':
            data.tbl, _ = base_clean_dataframe(data.tbl, True, True, True)

        start_time = time.time()
        while True:
            prompt = self._ans_gen_prompt(data)
            out = self.gpt.query(prompt)
            self.logger.log_message(line_limit=cut_log, level='debug', msg='Prompt: ' + prompt)
            self.logger.log_message(line_limit=cut_log, level='debug', msg=f'Output: {out}')
            try:
                sql = parse_any_string(out, hard_replace='SQL:')
                sql, _ = post_process_sql(sql, data.tbl, data.title)
                ans = self.exe_sql(sql, data)
                self.logger.log_message(line_limit=cut_log, level='debug', msg=f'tbl: {df_to_cotable(ans)}')
                break
            except Exception as e:
                self.sql = sql
                self.ans = str(e)
                data.tbl = shuffle_columns(data.tbl)
                self._record_error_raise(data.id + '(ID)' + str(e))
        
        if self.last_log is not None:
            self.last_log = None
        
        return sql, ans

    def exe_sql(self, sql: str, data:TQAData):
        tbl = data.tbl
        tbl.to_sql('w', self.conn, index=False, if_exists='replace')
        ans = pd.read_sql(sql, self.conn)

        ret_lis = extract_answers(ans)
        if TASK_TYPE == 'tableqa':
            if ret_lis is None or len(ret_lis) == 0:
                raise ValueError(f'E: The answer is empty!')
            elif len(ret_lis) == 1:
                val = ret_lis[0]
                if val == 'None' or val == '' or val == 'none' or val == None:
                    raise ValueError(f'E: The answer is empty!')

        return ans

    def _ans_gen_prompt(self, data:TQAData):
        
        DEMO_NL2SQLER = DEMO_NL2SQLER_COMPLETE if self.mode=='base' else DEMO_NL2SQLER_PREP
        QUERY_NL2SQLER = QUERY_NL2SQLER_COMPLETE if self.mode=='base' else QUERY_NL2SQLER_PREP
        SELF_CORREC_INS_NL2SQLER = SELF_CORREC_INS_NL2SQLER_COMPLETE if self.mode=='base' else SELF_CORREC_INS_NL2SQLER_PREP

        tbl, question, title = data.tbl, data.question, data.title

        row_len = len(tbl)
        row_len = min(row_len, DEFAULT_ROW_CUT)
        prompt = ''
        for row_lim in range(row_len, 0, -2):
            demo = copy.deepcopy(DEMO_NL2SQLER)
            create_table, table_ret = binder_nl2sql_prompt(data, cut_line=row_lim)
            query = QUERY_NL2SQLER.format(create_table_text=create_table, table=table_ret, question=question, title=title)

            if self.self_correction and self.last_log is not None:
                query = query.replace('SQL:', 'Last Error: ' + self.last_log + '\n' + 'SQL:')
            
            prompt = demo + '\n\n' + query
            if cal_tokens(prompt) <= MAX_INPUT_LIMIT-MAX_OUTPUT_LIMIT:
                break
        if len(prompt) == 0:
            raise ValueError(f'E: The prompt is empty, the first row is too long!')
        return prompt
