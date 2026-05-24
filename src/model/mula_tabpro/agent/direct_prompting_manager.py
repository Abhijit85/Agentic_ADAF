from .simple_agent import *

class DirectPromptingManager(Agent):
    def __init__(self, llm_name=LLM_NAME, chains: List = [InitOP()], PROMPT = None, agent_name='direct_prompting_manager', logger_root='tmp/table_llm_log', logger_file=f'mula_tabpro_v{TABLELLM_VERSION}.log'):
        super().__init__(llm_name=llm_name, chains=chains, PROMPT=PROMPT, agent_name=agent_name, logger_root=logger_root, logger_file=logger_file)

    def process(self, data:TQAData):
        self.last_log = None
        self.self_corr_inses = []
        self.icl_inses = []
        self.err_raise_cnt = 0
        
        while True:
            prompt = self._ans_gen_prompt(data)
            out = self.gpt.query(prompt)
            self.logger.log_message(line_limit=cut_log, level='debug', msg='Prompt: ' + prompt)
            self.logger.log_message(line_limit=cut_log, level='debug', msg=f'Output: {out}')
            parsed_out = parse_any_string(out).lower()
            try:
                self.check_output(parsed_out)
                rel_cols, aug_reqs, nor_reqs = self._generate_dataprep_requirements(data, parsed_out)
                break
            except ValueError as e:
                self._record_error_raise(data.id + '(ID)' + str(e))
                continue
        
        if self.last_log is not None:
            self.last_log = None
            
            self.logger.log_message(msg=f'[DEBUG_CORRECT_FLAG]---- ID: {data.id}, SUCCESSFULLY DEBUG IN {self.err_raise_cnt} times! ----')
        else:
            self.logger.log_message(msg=f'[NO_BUG_FLAG]---- ID: {data.id}, NO BUGS! ----')

        return rel_cols, aug_reqs, nor_reqs
    
    def check_output(self, out: str):
        if not('(1)' in out and '(2)' in out and '(3)' in out):
            raise ValueError(f'E: The output does not contain three aspects, please generate follow the above format: {out}')
    
    def _generate_dataprep_requirements(self, out: str):
        # 1. split the out into three parts
        one_part = out[out.find('(1)')+4: out.find('(2)')].strip()
        two_part = out[out.find('(2)')+4: out.find('(3)')].strip()
        three_part = out[out.find('(3)')+4:].strip()

        # 2. get the related columns
        col_str = one_part.replace('(1)', '').replace('related columns:').strip()
        rel_cols = [x.strip() for x in col_str.split(',')]
        if len(rel_cols) == 0:
            raise ValueError(f'E: No related columns found: {one_part}')
        
        # 3. get augmenter requirements
        aug_reqs = []
        sent_str = two_part.replace('(2)', '').strip()
        if 'none.' not in sent_str:
            for sent in sent_str.split(';'):
                sent = sent.strip()
                if len(sent) != 0:
                    aug_reqs.append(sent)

        # 4. get normalizer requirements
        nor_reqs = []
        sent_str = three_part.replace('(3)', '').strip()
        if 'none.' not in sent_str:
            for sent in sent_str.split(';'):
                sent = sent.strip()
                if len(sent) != 0:
                    nor_reqs.append(sent)

        return rel_cols, aug_reqs, nor_reqs


    def _ans_gen_prompt(self, data:TQAData):
        tbl, question = data.tbl, data.question

        row_len = len(tbl)
        row_len = min(row_len, DEFAULT_ROW_CUT)
        prompt = ''
        for row_lim in range(row_len, 0, -2):
            demo = copy.deepcopy(DEMO_MANAGER)
            _, table_ret = binder_nl2sql_prompt(data, cut_line=row_lim)
            query = QUERY_MANAGER.format(table=table_ret, question=question, title=data.title)

            if self.self_correction and self.last_log is not None:
                query = query.replace('Requirements:', 'Last Error: ' + self.last_log + '\nRequirements:')

            prompt = demo + '\n\n' + query

            if cal_tokens(prompt) <= MAX_INPUT_LIMIT-MAX_OUTPUT_LIMIT:
                break
            
        if cal_tokens(prompt) > MAX_INPUT_LIMIT-MAX_OUTPUT_LIMIT:
            raise ValueError(f'E: The prompt is empty, the first row is too long!')
        return prompt
