from .simple_agent import *
from src.model.mula_tabpro.agent import ColTypeDeducer

import sqlite3

def list_equal(l1:List, l2:List) -> bool:
    if len(l1) != len(l2):
        return False
    for i in range(len(l1)):
        if l1[i] not in l2:
            return False
    return True

class Planner(Agent):
    def __init__(self, llm_name=LLM_NAME, chains: List = [InitOP()], PROMPT = None, agent_name='planner', logger_root='tmp/table_llm_log', logger_file=f'mula_tabpro_v{TABLELLM_VERSION}.log'):
        super().__init__(llm_name=llm_name, chains=chains, PROMPT=PROMPT, agent_name=agent_name, logger_root=logger_root, logger_file=logger_file)

        self.coltype_deducer = ColTypeDeducer(llm_name=LLM_NAME, logger_root=logger_root, logger_file=logger_file)
        self.conn = sqlite3.connect(':memory:')

    def process(self, data:TQAData):
        self.logger.log_message(msg='\n'.join([f'/*************** describe data ***************/'
                                               f'【title】{data.title}',
                                               f'【Question】{data.question}',
                                               f'【Answer】{data.label}']))
        # VOTE
        post_sql, rel_cols, map_requires = 'NaN', [], []
        for _ in range(QASKETCH_VOTE):
            try:
                data.tbl = shuffle_columns(data.tbl)
                post_sql_i, rel_cols_i, map_requires_i = self.qa_sketch_generate(data)
            except Exception as e:
                post_sql_i = 'NaN'
                rel_cols_i = []
                map_requires_i = []

            # update rel_cols: just get the Union of all rel_cols
            rel_cols = list(set(rel_cols + rel_cols_i))
            # update post_sql and map_requires: just get the longest post_sql
            if len(post_sql_i) > len(post_sql):
                post_sql = post_sql_i

            for mr_i in map_requires_i:
                find = False
                for mr in map_requires:
                    if list_equal(mr[0], mr_i[0]):
                        find = True
                        break
                if find:
                    # compare the tar_col, get the longer one
                    if len(mr_i[1]) > len(mr[1]):
                        map_requires.remove(mr)
                        map_requires.append(mr_i)
                else:
                    map_requires.append(mr_i)
        if len(rel_cols) == 0:
            rel_cols = list(data.tbl.columns)

        
        self.logger.log_message(msg='\n'.join([f'/*************** when generating QA Sketch ***************/'
                                               f'【QA Sketch】{post_sql}',
                                               f'【Related Columns:】{rel_cols}',
                                               f'【Logical Operators:】{map_requires}',]))

        try:
            chains = self.generate_logical_op(data, post_sql, rel_cols, map_requires)
        except Exception as e:
            chains = []
        
        self.logger.log_message(msg='\n'.join([f'/*************** when generating QA Sketch ***************/'
                                               f'【Logical Operators:】{[str(op) for op in chains]}',]))
        return post_sql, rel_cols, chains

    def generate_logical_op(self, data:TQAData, post_sql:str, rel_cols:List[str], map_requires:List) -> List[LogicalOperator]:
        
        chains = []
        for src_cols, tar_col in map_requires:
            try:
                aug_op = self._generate_one_augment_op(data, post_sql, src_cols, tar_col)
            except Exception as e:
                self.logger.log_message(msg=f'[ERROR in Generating Augment for {",".join(src_cols)} --> {tar_col}]---- ID: {data.id}, ERROR: {e} ----')
                aug_op = None
            if aug_op is not None:
                chains.append(aug_op)

        tmp_sql = copy.deepcopy(post_sql)
        # mask the MAP() grammer, update tmp_sql
        qa_pattern = 'MAP\(\[.*?\],.*?\)'
        qas = re.findall(qa_pattern, tmp_sql)
        for idx, qa in enumerate(qas):
            tmp_sql = tmp_sql.replace(qa, f"placeholder{idx}")

        try:
            colty_dic = self.coltype_deducer.process(data, [x for x in rel_cols if x in tmp_sql], post_sql)
        except Exception as e:
            colty_dic = {}
        
        for col in rel_cols:
            if col not in tmp_sql:
                continue
            if col in colty_dic and colty_dic[col] not in ['datetime', 'numerical']:
                continue

            # if the column is all numerical, skip it
            all_num = True
            for val in data.tbl[col]:
                if not is_float(val):
                    all_num = False
                    break
            if all_num:
                # convert the column to numerical
                for i, val in enumerate(data.tbl[col]):
                    data.tbl[col][i] = my_float(val)

                continue
            try:
                nor_op = self._generate_one_normalize_op(data, tmp_sql, col)
            except Exception as e:
                self.logger.log_message(msg=f'[ERROR in Generating Normalize for {col}]---- ID: {data.id}, ERROR: {e} ----')
                nor_op = None
            if nor_op is not None:
                chains.append(nor_op)

        return chains

    def qa_sketch_generate(self, data:TQAData):
        self.last_log = None
        self.self_corr_inses = []
        self.icl_inses = []
        self.err_raise_cnt = 0

        data.tbl = add_row_number_to_df(data.tbl, col_name='row_id')
        data = update_TData_col_type(data, col_type={'row_id': 'numerical'})
        
        while True:
            prompt = self._qa_sketch_prompt(data)
            out = self.gpt.query(prompt)
            self.logger.log_message(line_limit=cut_log, level='debug', msg='Prompt: ' + prompt)
            self.logger.log_message(line_limit=cut_log, level='debug', msg=f'Output: {out}')
            planner_sql = parse_any_string(out)
            try:
                self._check_planner_sql(planner_sql)
                post_sql, rel_cols = post_process_sql(planner_sql, data.tbl, data.title)
                if len(rel_cols) == 0:
                    raise ValueError(f'E: No related columns found in the generated planner_sql: {post_sql}, please use specific column names instead of "*"!')
                map_requires = self._extract_map_requires(post_sql, rel_cols)
                break
            except ValueError as e:
                data.tbl = shuffle_columns(data.tbl)
                self._record_error_raise(data.id + '(ID)' + str(e))
                continue
        
        if self.last_log is not None:
            self.last_log = None
            
            self.logger.log_message(msg=f'[DEBUG_CORRECT_FLAG]---- ID: {data.id}, SUCCESSFULLY DEBUG IN {self.err_raise_cnt} times! ----')
        else:
            self.logger.log_message(msg=f'[NO_BUG_FLAG]---- ID: {data.id}, NO BUGS! ----')

        return post_sql, rel_cols, map_requires
    
    def _generate_one_normalize_op(self, data:TQAData, post_sql:str, src_col:str):
        self.last_log = None
        self.err_raise_cnt = 0

        while True:
            try:
                prompt = self._generate_normalize_prompt(data, post_sql, src_col)
                out = self.gpt.query(prompt)
                self.logger.log_message(line_limit=cut_log, level='debug', msg='Prompt: ' + prompt)
                self.logger.log_message(line_limit=cut_log, level='debug', msg=f'Output: {out}')
                requirement = parse_any_string(out)
                if 'skip' in requirement.lower() and 'flag' in requirement.lower():
                    return None
                else:
                    nor_op = NormalizeOp(req=requirement, col=src_col)
                    return nor_op
            except ValueError as e:
                data.tbl = shuffle_columns(data.tbl)
                self._record_error_raise(data.id + '(ID)' + str(e))
                continue

    def _generate_one_augment_op(self, data:TQAData, post_sql:str, src_cols:List[str], tar_col:str):
        self.last_log = None
        self.err_raise_cnt = 0

        while True:
            try:
                prompt = self._generate_augment_prompt(data, post_sql, src_cols, tar_col)
                out = self.gpt.query(prompt)
                self.logger.log_message(line_limit=cut_log, level='debug', msg='Prompt: ' + prompt)
                self.logger.log_message(line_limit=cut_log, level='debug', msg=f'Output: {out}')
                requirement = parse_any_string(out)
                if 'skip' in requirement.lower() and 'flag' in requirement.lower():
                    return None
                else:
                    aug_op = AugmentOp(req=requirement, cols=src_cols)
                    return aug_op
            except ValueError as e:
                data.tbl = shuffle_columns(data.tbl)
                self._record_error_raise(data.id + '(ID)' + str(e))
                continue
    
    def _generate_normalize_prompt(self, data:TQAData, post_sql:str, src_col:str):
        tbl, question = data.tbl, data.question
        row_len = min(len(tbl), DEFAULT_ROW_CUT)
        prompt = ''
        for row_lim in range(row_len, 0, -2):
            demo = copy.deepcopy(DEMO_NOR_OP_GEN_PLANNER)
            table = df_to_str_columns_add_quo(data.tbl, cut_line=row_lim, exclude_cols=[col for col in data.tbl.columns if col != src_col])
            query = QUERY_NOR_OP_GEN_PLANNER.format(table=table, question=question, title=data.title, neural_sql=post_sql, column=src_col)

            if self.self_correction and self.last_log is not None:
                query = query.replace('Requirement:', 'Last Error: ' + self.last_log + '\Requirement:')

            prompt = demo + '\n\n' + query
            if cal_tokens(prompt) <= MAX_INPUT_LIMIT-MAX_OUTPUT_LIMIT:
                break

        if cal_tokens(prompt) > MAX_INPUT_LIMIT-MAX_OUTPUT_LIMIT:
            raise ValueError(f'E: The prompt is empty, the first row is too long!')
        return prompt

    def _generate_augment_prompt(self, data:TQAData, post_sql:str, src_cols:List[str], tar_col:str):
        tbl, question = data.tbl, data.question
        row_len = min(len(tbl), DEFAULT_ROW_CUT)
        prompt = ''
        for row_lim in range(row_len, 0, -2):
            demo = copy.deepcopy(DEMO_AUG_OP_GEN_PLANNER)
            table = df_to_str_columns_add_quo(data.tbl, cut_line=row_lim, exclude_cols=[col for col in data.tbl.columns if col not in src_cols])

            query = QUERY_AUG_OP_GEN_PLANNER.format(table=table, question=question, title=data.title, neural_sql=post_sql, new_column=tar_col)

            if self.self_correction and self.last_log is not None:
                query = query.replace('Requirement:', 'Last Error: ' + self.last_log + '\Requirement:')

            prompt = demo + '\n\n' + query
            if cal_tokens(prompt) <= MAX_INPUT_LIMIT-MAX_OUTPUT_LIMIT:
                break
            
        if cal_tokens(prompt) > MAX_INPUT_LIMIT-MAX_OUTPUT_LIMIT:
            raise ValueError(f'E: The prompt is empty, the first row is too long!')
        return prompt

    def _qa_sketch_prompt(self, data:TQAData):
        tbl, question = data.tbl, data.question
        row_len = len(tbl)
        row_len = min(row_len, DEFAULT_ROW_CUT)
        prompt = ''
        for row_lim in range(row_len, 0, -2):
            demo = copy.deepcopy(DEMO_QA_SKETCH_PLANNER)
            table = df_to_str_columns_add_quo(data.tbl, cut_line=row_lim)
            query = QUERY_QA_SKETCH_PLANNER.format(table=table, question=question, title=data.title, columns=', '.join([f'"{col}"' for col in tbl.columns]))

            if self.self_correction and self.last_log is not None:
                query = query.replace('QA-Sketch:', 'Last Error: ' + self.last_log + '\nQA-Sketch:')

            prompt = demo + '\n\n' + query
            if cal_tokens(prompt) <= MAX_INPUT_LIMIT-MAX_OUTPUT_LIMIT:
                break
            
        if cal_tokens(prompt) > MAX_INPUT_LIMIT-MAX_OUTPUT_LIMIT:
            raise ValueError(f'E: The prompt is empty, the first row is too long!')
        return prompt

    def _check_planner_sql(self, sql: str):
        unacceptable_keywords = ['STRFTIME(', 'SUBSTRING(', 'SUBSTR(', 'SUBSTRING_INDEX(', 'SPLIT_PART(', 'SPLIT(', 'EXTRACT(', 'REPLACE(']
        include_dict = {}
        tmp_sql = copy.deepcopy(sql).upper()
        for keyword in unacceptable_keywords:
            if keyword in tmp_sql:
                include_dict[keyword] = True

        if len(include_dict) > 0:
            key_str = ','.join([x[:-1] for x in include_dict.keys()])
            raise ValueError(f'E: The SQL contains unacceptable keywords: {key_str}. DO NOT USE KEYWORD {", ".join([x.replace("(","") for x in unacceptable_keywords])}. USE MAP() grammer to generate new columns INSTEAD.')

    def _exe_sql(self, sql: str, data:TQAData):
        tbl = data.tbl
        tbl.to_sql('w', self.conn, index=False, if_exists='replace')
        ans = pd.read_sql(sql, self.conn)
        return ans
    
    def _extract_map_requires(self, planner_sql:str, related_cols: List[str]):
        temp_sql = copy.deepcopy(planner_sql)
        for col in related_cols:
            temp_sql = temp_sql.replace(col, '#'*len(col))

        idx = 0
        ret = []
        while idx < len(planner_sql):
            # planner_sql: SELECT MAP("extract country from cyclist"; `Cyclist`) AS Country, COUNT(*) AS C
            # temp_sql: SELECT MAP("extract country from cyclist"; `#######`) AS Country, COUNT(*) AS C
            if planner_sql[idx: idx+4] == 'MAP(': # find the begin of the mapping statement
                # example: MAP(["team_a", "team_b"], "score_difference")

                # find the idx of '['
                left_start_idx = planner_sql.find('[', idx)
                right_start_idx = planner_sql.find(']', left_start_idx)
                if left_start_idx == -1 or right_start_idx == -1:
                    raise ValueError(f'E: mapping grammer error, source column list is not complete: {planner_sql}')
                
                source_cols = eval(planner_sql[left_start_idx: right_start_idx+1])
                if len(source_cols) == 0:
                    raise ValueError(f'E: mapping grammer error, source column list is empty: {planner_sql}')
                
                # find the first ","
                comma_idx = planner_sql.find(',', right_start_idx)
                # find the first ")"
                bracket_end_idx = planner_sql.find(')', comma_idx)
                if comma_idx == -1 or bracket_end_idx == -1:
                    raise ValueError(f'E: mapping grammer error, target column is not complete: {planner_sql}')
                tar_col = planner_sql[comma_idx+1: bracket_end_idx].strip()
                if tar_col[0] == '`' and tar_col[-1] == '`':
                    tar_col = tar_col[1:-1]
                if tar_col[0] == '"' and tar_col[-1] == '"' or tar_col[0] == "'" and tar_col[-1] == "'":
                    tar_col = eval(tar_col)

                if (source_cols, tar_col) not in ret:
                    ret.append((source_cols, tar_col))

                idx = bracket_end_idx + 1

            idx += 1

        return ret