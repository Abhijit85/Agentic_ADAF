from .simple_agent import *

def execute_code_from_string(code_string, df, glo = globals(), loc = locals(), ret_variable='result'):
    try:
        loc['df'] = df
        exec(code_string, glo, loc)
        return loc[ret_variable]
    except Exception as e:
        raise ValueError(f"Error executing code: {e}")

class Op2Coder(Agent):
    def __init__(self, llm_name=LLM_NAME, chains: List = [InitOP()], PROMPT = None, agent_name='op2coder', logger_root='tmp/table_llm_log', logger_file=f'mula_tabpro_v{TABLELLM_VERSION}.log'):
        super().__init__(llm_name=llm_name, chains=chains, PROMPT=PROMPT, agent_name=agent_name, logger_root=logger_root, logger_file=logger_file)

    def implement_logical_operator(self, data:TQAData, logical_op:LogicalOperator):
        self.last_log = None
        self.self_corr_inses = []
        self.icl_inses = []
        self.err_raise_cnt = 0
        self.data, self.op = data, None

        cols, require = logical_op.cols, logical_op.req

        while True:
            prompt = self._ans_gen_prompt(self.data, cols, require)
            self.logger.log_message(line_limit=cut_log, level='debug', msg='Prompt: ' + prompt)
            out = self.gpt.query(prompt)
            self.logger.log_message(line_limit=cut_log, level='debug', msg=f'Output: {out}')
            try:
                self.op = LLMCodePhysicalOp(llm_model=self.gpt.model, log_root=self.logger.root, log_file=self.logger.log_file)
                self.op.complete_args(self.data, out)
                self.logger.log_message(line_limit=cut_log, level='debug', msg=f'Origin tbl: {df_to_cotable(self.data.tbl)}')
                self.op.execute(self.data)
                self.logger.log_message(line_limit=cut_log, level='debug', msg=f'New tbl: {df_to_cotable(self.data.tbl)}')
                break
            except Exception as e:
                self._record_error_raise(self.data.id + '(ID)' + str(e))
        
        if self.last_log is not None:
            self.last_log = None

        return self.data, self.op

    def _ans_gen_prompt(self, data:TQAData, cols:str, require:str):
        row_len = len(data.tbl)
        row_len = min(row_len, DEFAULT_ROW_CUT)
        prompt = ''
        for row_lim in range(row_len, 0, -2):
            demo = copy.deepcopy(DEMO_OP2CODE)
            
            table_ret = df_to_str_columns_add_quo(df=data.tbl, exclude_cols=[c for c in data.tbl.columns if c not in cols], cut_line=row_lim)
            col_str = ', '.join([f'`{col}`' for col in cols])

            query = QUERY_OP2CODE.format(table=table_ret, col=col_str, question=require)

            if self.self_correction and self.last_log is not None:
                query = query.replace('Code:', 'Last Error: ' + self.last_log + '\n' + 'Code:')
            
            prompt = demo + '\n\n' + query
            if cal_tokens(prompt) <= MAX_INPUT_LIMIT-MAX_OUTPUT_LIMIT:
                break
        if len(prompt) == 0:
            raise ValueError(f'E: The prompt is empty, the first row is too long!')
        return prompt

def get_key_for_icl(question:str, columns:List[str], context: str):
    return f'{context}\nQuestion: {question}\ncolumns: {", ".join(columns)}'

def get_instance(id='None', create_table='None', title='None', table='None', question='None', last_a='None', last_err='None', a='None', type='None', key='None'):
    if key == 'None':
        key = question
        
    return SelfCorrectionInstance(
        id = id,
        context=f"""{create_table}
/*
Title: {title}
example rows:
SELECT * FROM w LIMIT 3;
{table}
*/""",
        q=question,
        last_a=last_a,
        last_err=last_err,
        a=a,
        type=type,
        key=key
    )