from .simple_agent import *

class ViewGenerator(SimpleAgent):
    def __init__(self, llm_name=LLM_NAME, chains: List = [InitOP()], PROMPT = PROMPT_VIEW_GENERATOR, agent_name='view_generator', logger_root='tmp/table_llm_log', logger_file=f'mula_tabpro_v{TABLELLM_VERSION}.log'):
        super().__init__(llm_name=llm_name, chains=chains, agent_name=agent_name, PROMPT=PROMPT, logger_root=logger_root, logger_file=logger_file)

        self.MAX_ERR_RAISE_CNT = 4
    
    def _generate_column_from_columns_prompt(self, data:TQAData, cols:str, require:str):
        head = self.PROMPT['head']
        op_desc = self.PROMPT[NAMES['GEN_NEW_COL']]
        query_temp = self.PROMPT[f"query_{NAMES['GEN_NEW_COL']}_from_column"]
        prompt = ''
        row_len = len(data.tbl)
        row_len = min(row_len, DEFAULT_ROW_CUT)
        for row_lim in range(row_len, 0, -2):
            op_demo = copy.deepcopy(self.PROMPT[f"demo_{NAMES['GEN_NEW_COL']}_from_column"])
            table = df_to_str_columns_add_quo(df=data.tbl, exclude_cols=[c for c in data.tbl.columns if c not in cols], cut_line=row_lim)
            col_str = ', '.join([f'`{col}`' for col in cols])
            query = query_temp.format(table=table, col=col_str, question=require)

            if self.self_correction and self.last_log != None:
                query = query.replace('Operator:', 'Last Error: ' + self.last_log + '\n' + 'Operator:')
            
            prompt = head + '\n\n' + op_desc + '\n\n' + op_demo + '\n\n' + query
            if cal_tokens(prompt) <= MAX_INPUT_LIMIT-MAX_OUTPUT_LIMIT:
                break

        if cal_tokens(prompt) > MAX_INPUT_LIMIT-MAX_OUTPUT_LIMIT:
            raise ValueError(f'E: The prompt is too long, the first row is too long!')

        return prompt
    
    def generate_column_from_columns(self, data:TQAData, cols:List[str], require:str):
        self.last_log = None
        self.err_raise_cnt = 0
        self.self_corr_inses = []
        self.icl_inses = []
        
        for col in cols:
            if col not in data.tbl.columns:
                raise ValueError(f'E: The column {col} does not exist in the table!')
        while True:
            prompt = self._generate_column_from_columns_prompt(data, cols, require)
            out = self.gpt.query(prompt)

            self.logger.log_message(msg='Prompt: ' + prompt)
            self.logger.log_message(msg=f'Output: {out}')

            try:
                OpClass = AutoOP.deduce_op(out)
                op = OpClass(llm_model=self.gpt.model, log_root=self.logger.root, log_file=self.logger.log_file)
                op.complete_args_with_output(data, out)
                data = op.execute(data)
                self.logger.log_message(msg=f'New Table is:\n{data.tbl}')
                break
            except Exception as e:
                self._record_error_raise(data.id + '(ID)' + str(e))
        
        if self.last_log is not None:
            self.last_log = None
            
            self.logger.log_message(msg=f'[DEBUG_CORRECT_FLAG]---- ID: {data.id}, SUCCESSFULLY DEBUG IN {self.err_raise_cnt} times! ----')
        else:
            self.logger.log_message(msg=f'[NO_BUG_FLAG]---- ID: {data.id}, NO BUGS! ----')

        return data, op
