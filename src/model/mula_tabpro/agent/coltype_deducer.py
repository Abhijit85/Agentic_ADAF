from .simple_agent import *

class ColTypeDeducer(Agent):
    def __init__(self, llm_name=LLM_NAME, chains: List = [InitOP()], PROMPT = None, agent_name='coltype_deducer', logger_root='tmp/table_llm_log', logger_file=f'mula_tabpro_v{TABLELLM_VERSION}.log'):
        super().__init__(llm_name=llm_name, chains=chains, PROMPT=PROMPT, agent_name=agent_name, logger_root=logger_root, logger_file=logger_file)

    def process(self, data:TQAData, related_columns:List[str], sql: str):
        self.last_log = None
        self.err_raise_cnt = 0
        self.self_corr_inses = []
        self.icl_inses = []
        if len(related_columns) == 0:
            raise ValueError(f'E: No related columns found in the SQL: {sql}')

        while True:
            try:
                prompt = self._ans_gen_prompt(data, related_columns, sql)
                out = self.gpt.query(prompt)

                self.logger.log_message(line_limit=cut_log, level='debug', msg='Prompt: ' + prompt)
                self.logger.log_message(line_limit=cut_log, level='debug', msg=f'Output: {out}')
                
                coltype_dict = parse_coltype_dict(out)
                if len(coltype_dict) == 0:
                    raise ValueError(f'E: No column type deduced from the output: {out}')
                
                for col in related_columns:
                    if col not in coltype_dict:
                        raise ValueError(f'E: Column {col} not found in the output: {out}')
                    t = coltype_dict[col]
                    if t not in ['string', 'numerical', 'datetime']:
                        raise ValueError(f'E: Column type {t} not supported!')
                break
            except Exception as e:
                self._record_error_raise(data.id + '(ID)' + str(e))
        
        if self.last_log is not None:
            self.last_log = None
            
            self.logger.log_message(msg=f'[DEBUG_CORRECT_FLAG]---- ID: {data.id}, SUCCESSFULLY DEBUG IN {self.err_raise_cnt} times! ----')
        else:
            self.logger.log_message(msg=f'[NO_BUG_FLAG]---- ID: {data.id}, NO BUGS! ----')
        
        
        return coltype_dict
    
    def exe_sql(self, sql: str, data:TQAData):
        tbl = data.tbl
        tbl.to_sql('w', self.conn, index=False, if_exists='replace')
        ans = pd.read_sql(sql, self.conn)
        return ans

    def _ans_gen_prompt(self, data:TQAData, related_columns: List[str], sql: str):
        tbl = data.tbl
        exclude_cols = [col for col in tbl.columns if col not in related_columns]

        head = HEAD_COLTYPE_DEDUCER

        row_len = len(tbl)
        row_len = min(row_len, DEFAULT_ROW_CUT)
        prompt = ''
        for row_lim in range(row_len, 0, -2):
            demo = copy.deepcopy(DEMO_COLTYPE_DEDUCER)
            table = df_to_str_columns(df=tbl, cut_line=row_lim, exclude_cols=exclude_cols)
            related_col_str = ', '.join(related_columns)
            query = QUERY_COLTYPE_DEDUCER.format(table=table, sql=sql, columns=related_col_str)

            if self.self_correction and self.last_log != None:
                query = query.replace('Column Type Dict:', 'Last Error: ' + self.last_log + '\nColumn Type Dict:')
            
            prompt = head + '\n\n' + demo + '\n\n' + query
            
            if cal_tokens(prompt) <= MAX_INPUT_LIMIT-MAX_OUTPUT_LIMIT:
                break
        if len(prompt) == 0:
            raise ValueError(f'E: The prompt is empty, the first row is too long!')
        return prompt
