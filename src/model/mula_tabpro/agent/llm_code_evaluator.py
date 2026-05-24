from .simple_agent import *

def cat_substring_between(s, start, end):
    # not included
    start_idx = s.find(start)
    if start_idx == -1:
        raise ValueError(f"Substring not found: {start}")
    start_idx += len(start)

    if end != 'END_OF_SENTENCE':
        end_idx = s.find(end, start_idx)
        if end_idx == -1:
            raise ValueError(f"Substring not found: {end}")
        return s[start_idx:end_idx]
    else:
        return s[start_idx:]

class LLMCodeEvaluator(Agent):
    def __init__(self, llm_name=LLM_NAME, chains: List = [InitOP()], PROMPT = None, agent_name='llm_code_evaluator', logger_root='tmp/table_llm_log', logger_file=f'mula_tabpro_v{TABLELLM_VERSION}.log'):
        super().__init__(llm_name=llm_name, chains=chains, PROMPT=PROMPT, agent_name=agent_name, logger_root=logger_root, logger_file=logger_file)

    def process_all_records(self, records: dict):
        true_cnt, false_cnt = 0, 0
        for id in records:
            rec = records[id]
            phy_ops = rec['physical_ops']
            log_ops = rec['logical_ops']
            for i, op in enumerate(phy_ops):
                if 'llm_code_op(' in op:
                    logop = log_ops[i]
                    in_tbl_str = cat_substring_between(op, start=', in_columns=', end=', out_columns=')
                    out_tbl_str = cat_substring_between(op, start=', out_columns=', end='END_OF_SENTENCE')
                    ans = self.process(logop, in_tbl_str, out_tbl_str)
                    if ans:
                        true_cnt += 1
                    else:
                        false_cnt += 1
                    self.logger.log_message(line_limit=cut_log, level='debug', msg=f'# num: {true_cnt + false_cnt}, true: {true_cnt}, false: {false_cnt}, acc: {true_cnt / (true_cnt + false_cnt)}')

        return true_cnt, false_cnt

    def process(self, op: str, in_tbl_str: str, out_tbl_str: str):
        self.err_raise_cnt = 0
        try:
            prompt = self._ans_gen_prompt(op, in_tbl_str, out_tbl_str)
            out = self.gpt.query(prompt)
            self.logger.log_message(line_limit=cut_log, level='debug', msg='Prompt: ' + prompt)
            self.logger.log_message(line_limit=cut_log, level='debug', msg=f'Output: {out}')
            self.ans = self.parse_answer(out)
        except Exception as e:
            self.ans = False
            self._record_error_raise(str(e))
        return self.ans
    
    def parse_answer(self, ans: str):
        ans = ans.lower()
        ans = parse_any_string(ans, hard_replace='output:').strip()
        if 'yes' in ans:
            return True
        else:
            return False

    def _ans_gen_prompt(self, op: str, in_tbl_str: str, out_tbl_str: str):

        demo = LLM_CODE_EVALUATOR_DEMO
        query = LLM_CODE_EVALUATOR_QUERY.format(in_tbl=in_tbl_str, out_tbl=out_tbl_str, op=op)
        if self.last_log is not None:
            query = query.replace('Output:', 'Last Error: ' + self.last_log + '\n' + 'Output:')
        prompt = demo + '\n\n' + query
        return prompt
