from .simple_agent import *

class Programmer(SimpleAgent):
    def __init__(self, llm_name=LLM_NAME, chains: List = [InitOP()], PROMPT = None, agent_name='programmer', logger_root='tmp/table_llm_log', logger_file=f'mula_tabpro_v{TABLELLM_VERSION}.log'):
        if PROMPT is None:
            raise ValueError(f'E: PROMPT is None!')
        super().__init__(llm_name=llm_name, chains=chains, agent_name=agent_name, PROMPT=PROMPT, logger_root=logger_root, logger_file=logger_file)

        self.MAX_ERR_RAISE_CNT = 4
    
    def _get_physical_op_prompt(self, op_type):
        return self.PROMPT[f"desc_{op_type}"] + '\n' + self.PROMPT[f"demo_{op_type}"]
    
    def _generate_prompt(self, data:TQAData, cols:str, require:str):
        catalog = self.PROMPT['_catalog']
        head = self.PROMPT['_head']
        query_temp = self.PROMPT[f"_query"]

        prompt = ''
        row_len = min(len(data.tbl), DEFAULT_ROW_CUT)
        for row_lim in range(row_len, 0, -2):
            fewshot_demos = '\n\n'.join([self._get_physical_op_prompt(op_type) for op_type in catalog])
            
            table = df_to_str_columns_add_quo(df=data.tbl, exclude_cols=[c for c in data.tbl.columns if c not in cols], cut_line=row_lim)
            col_str = ', '.join([f'`{col}`' for col in cols])
            query = query_temp.format(table=table, col=col_str, question=require)

            if self.self_correction and self.last_log != None:
                query = query.replace('Operator:', 'Last Error: ' + self.last_log + '\n' + 'Operator:')                
            
            prompt = head + '\n\n' + fewshot_demos + '\n\n' + query
            if cal_tokens(prompt) <= MAX_INPUT_LIMIT-MAX_OUTPUT_LIMIT:
                break

        if cal_tokens(prompt) > MAX_INPUT_LIMIT-MAX_OUTPUT_LIMIT:
            raise ValueError(f'E: The prompt is too long, the first row is too long!')

        return prompt
    
    def implement_logical_operator(self, data:TQAData, logical_op:LogicalOperator):
        self.last_log = None
        self.err_raise_cnt = 0

        cols, require = logical_op.cols, logical_op.req
        
        for col in cols:
            if col not in data.tbl.columns:
                raise ValueError(f'E: The column {col} does not exist in the table!')
        while True:
            prompt = self._generate_prompt(data, cols, require)
            out = self.gpt.query(prompt)

            self.logger.log_message(msg='Prompt: ' + prompt)
            self.logger.log_message(msg=f'Output: {out}')
            out = parse_any_string(out).strip('`')

            try:
                OpClass = AutoOP.deduce_op(out, type=logical_op.type)
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


class Augmenter(Programmer):
    def __init__(self, llm_name=LLM_NAME, chains: List = [InitOP()], PROMPT = AUGMENTATION, agent_name='augmenter', logger_root='tmp/table_llm_log', logger_file=f'mula_tabpro_v{TABLELLM_VERSION}.log'):
        super().__init__(llm_name=llm_name, chains=chains, PROMPT=PROMPT, agent_name=agent_name, logger_root=logger_root, logger_file=logger_file)

    def implement_augment(self, data:TQAData, augmentop:AugmentOp):
        return self.implement_logical_operator(data, augmentop)

class Normalizer(Programmer):
    def __init__(self, llm_name=LLM_NAME, chains: List = [InitOP()], PROMPT = NORMALIZATION, agent_name='normalizer', logger_root='tmp/table_llm_log', logger_file=f'mula_tabpro_v{TABLELLM_VERSION}.log'):
        super().__init__(llm_name=llm_name, chains=chains, PROMPT=PROMPT, agent_name=agent_name, logger_root=logger_root, logger_file=logger_file)

    def implement_normalize(self, data:TQAData, normalizeop:NormalizeOp):
        return self.implement_logical_operator(data, normalizeop)
