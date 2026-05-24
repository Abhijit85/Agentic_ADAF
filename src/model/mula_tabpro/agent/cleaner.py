from .simple_agent import *

class Cleaner(SimpleAgent):
    def __init__(self, llm_name=LLM_NAME, chains: List = [InitOP()], PROMPT = PROMPT_CLEANER, agent_name='cleaner', logger_root='tmp/table_llm_log', logger_file=f'mula_tabpro_v{TABLELLM_VERSION}.log'):
        super().__init__(llm_name=llm_name, chains=chains, agent_name=agent_name, PROMPT=PROMPT, logger_root=logger_root, logger_file=logger_file)
        self.MAX_ERR_RAISE_CNT = 4

    def _standardize_prompt(self, data:TQAData, col:str, coltype:str, key:str):

        op_desc = self.PROMPT[NAMES[key]]

        query_temp = self.PROMPT['standardize_query']
        op_name = NAMES[key]
        column = col
        format = coltype

        prompt = ''
        for row_lim in range(DEFAULT_ROW_CUT, 0, -2):
            op_demo = copy.deepcopy(self.PROMPT[f'demo_{NAMES[key]}'])
            cot_tbl = df_to_str_columns_add_quo(df=data.tbl, exclude_cols=[c for c in data.tbl.columns if c != col], cut_line=row_lim)
            query = query_temp.format(cot_tbl=cot_tbl, column=column, format=format, op_name=op_name)
            
            if self.self_correction and self.last_log != None and len(self.last_log)!=0:

                query = query.replace('Operator:', 'Last Error: ' + self.last_log + '\n' + 'Operator:')

            prompt = op_desc + '\n\n' + op_demo + '\n\n' + query
            if cal_tokens(prompt) <= MAX_INPUT_LIMIT-MAX_OUTPUT_LIMIT:
                break

        if len(prompt) == 0:
            raise ValueError(f'E: The prompt is empty, the first row is too long!')

        return prompt

    def standardize_coltype(self, data:TQAData, col:str, coltype:str):
        self.last_log = None
        self.err_raise_cnt = 0
        self.self_corr_inses = []
        self.icl_inses = []

        if coltype == 'datetime':
            key = 'STAND_DATETIME'
            OP = StandDatetime
        elif coltype == 'numerical':
            key = 'STAND_NUMERICAL'
            OP = StandNumerical
        else:
            raise ValueError(f'E: The column type is not supported for standardization: {coltype}')
        
        op = Operator(op_type='empty_operator')
        while True:
            prompt = self._standardize_prompt(data, col, coltype, key)
            out = self.gpt.query(prompt)
            self.logger.log_message(line_limit=cut_log, level='debug', msg='Prompt: ' + prompt)
            self.logger.log_message(line_limit=cut_log, level='debug', msg=f'Output: {out}')

            try:
                op = OP(llm_model=self.gpt.model, log_root=self.logger.root, log_file=self.logger.log_file)
                op.complete_args_with_output(data, out)
                data = op.execute(data)
                self.logger.log_message(line_limit=cut_log, level='debug', msg=f'New Table is:\n{data.tbl}')
                break
            except Exception as e:
                self._record_error_raise(data.id + '(ID)' + str(e))
        
        if self.last_log is not None:
            self.last_log = None
            
            self.logger.log_message(msg=f'[DEBUG_CORRECT_FLAG]---- ID: {data.id}, SUCCESSFULLY DEBUG IN {self.err_raise_cnt} times! ----')
        else:
            self.logger.log_message(msg=f'[NO_BUG_FLAG]---- ID: {data.id}, NO BUGS! ----')

        return data, op