from .simple_operator import *
from src.model.mula_tabpro.prompt import AUGMENTATION

class GenNewCol(SimpleOperator):
    def __init__(self, llm_model='gpt-3.5-turbo', op_type=NAMES['GEN_NEW_COL'], log_root='tmp/table_llm_log', log_file=f'mula_tabpro_v{TABLELLM_VERSION}.log', PROMPT=AUGMENTATION):
        super().__init__(llm_model, op_type, log_root, log_file, PROMPT)

    def _get_related_cols(self, func:str):
        var = re.findall(r'lambda (.*?):', func)[0]
        finds = re.findall(rf'{var}\[\'(.*?)\'\]', func) + re.findall(rf'{var}\[\"(.*?)\"\]', func)
        return finds
    
    def execute(self, data:TQAData):
        df = copy.deepcopy(data.tbl)
        table = eval(self.complete_func_str)

        if table is None or len(table) == 0:
            raise ValueError(f'E({self.type}): Empty table returned')
        if type(table) != type(pd.DataFrame()):
            raise ValueError(f'E({self.type}): Not pd.Dataframe')
        data.tbl = table

        new_col = self.args['new_column']
        # if the col value if boolean, convert it to string
        data.tbl[new_col] = data.tbl[new_col].apply(lambda x: x if type(x)==int or type(x)==float else str(x))
        # replace nan into '[n.a.]'
        data.tbl[new_col] = data.tbl[new_col].apply(lambda x: '[n.a.]' if pd.isna(x) else x)

        return data
 
    def _check_func_name(self, op_str:str):
        if not op_str.startswith(self.type):
            raise ValueError(f'E({self.type}): Please output follow the required format: Function name not found in the output. The function name should be {self.type}')

    def _parse_args(self, data: TQAData, output: str):
        op_str = parse_any_string(output).strip()
        op_str = op_str.replace('MAX_VALUE', '9999999').replace('MIN_VALUE', '-9999999')
        self._check_func_name(op_str)
        
        try:
            new_column, func = parse_two_args(op_str, 'new_column', 'func', data.tbl)
        except:
            raise ValueError(f'E(GEN_NEW_COL): Error in parsing function: {op_str}') if PRE_CHECK_GRAMMAR else None
        
        source_cols = self._get_related_cols(func)
        source_cols = list(set(source_cols))
        for col in source_cols:
            if col not in data.tbl.columns:
                raise ValueError(f'E(GEN_NEW_COL): The column {col} is not in the table')
        
        try:
            eval(func)
        except:
            raise ValueError(f'E({self.type}): Error in parsing the lambda function: {func}. The lambda function is not valid') if PRE_CHECK_GRAMMAR else None
        
        if PRE_CHECK_GRAMMAR and new_column in data.tbl.columns:
            raise ValueError(f'E({self.type}): The target column {new_column} already exists in the table')
        
        return {'new_column': new_column, 'func': func, 'source_cols': source_cols}, op_str

class ExtractColumn(GenNewCol):
    def __init__(self, llm_model='gpt-3.5-turbo', op_type=NAMES['EXT_COL'], log_root='tmp/table_llm_log', log_file=f'mula_tabpro_v{TABLELLM_VERSION}.log', PROMPT={'demo': '', 'query': '', 'head': ''}):
        super().__init__(llm_model, op_type, log_root, log_file, PROMPT)

class CalculateColumn(GenNewCol):
    def __init__(self, llm_model='gpt-3.5-turbo', op_type=NAMES['CAL_COL'], log_root='tmp/table_llm_log', log_file=f'mula_tabpro_v{TABLELLM_VERSION}.log', PROMPT={'demo': '', 'query': '', 'head': ''}):
        super().__init__(llm_model, op_type, log_root, log_file, PROMPT)

class BooleanColumn(GenNewCol):
    def __init__(self, llm_model='gpt-3.5-turbo', op_type=NAMES['BOOL_COL'], log_root='tmp/table_llm_log', log_file=f'mula_tabpro_v{TABLELLM_VERSION}.log', PROMPT={'demo': '', 'query': '', 'head': ''}):
        super().__init__(llm_model, op_type, log_root, log_file, PROMPT)

class CombineColumn(GenNewCol):
    def __init__(self, llm_model='gpt-3.5-turbo', op_type=NAMES['COMB_COL'], log_root='tmp/table_llm_log', log_file=f'mula_tabpro_v{TABLELLM_VERSION}.log', PROMPT={'demo': '', 'query': '', 'head': ''}):
        super().__init__(llm_model, op_type, log_root, log_file, PROMPT)



class FilterColumn(SimpleOperator):
    def __init__(self, llm_model='gpt-3.5-turbo', op_type=NAMES['FILTER_COL'], log_root='tmp/table_llm_log', log_file=f'mula_tabpro_v{TABLELLM_VERSION}.log', PROMPT=AUGMENTATION):
        super().__init__(llm_model, op_type, log_root, log_file, PROMPT)

    def give_arg_val(self, columns):
        self.complete_func_str = f'{self.type}(df, columns={columns})'
        self.update_arg('columns', columns)
        self.update_arg('complete_func_str', self.complete_func_str)


class LLMCodePhysicalOp(SimpleOperator):
    def __init__(self, llm_model='gpt-3.5-turbo', op_type=NAMES['LLM_CODE_OP'], log_root='tmp/table_llm_log', log_file=f'mula_tabpro_v{TABLELLM_VERSION}.log', PROMPT=None):
        super().__init__(llm_model, op_type, log_root, log_file, PROMPT)

    def _execute_code_from_string(self, code_string, df, glo = globals(), loc = locals(), ret_variable='result'):
        try:
            loc['df'] = df
            exec(code_string, glo, loc)
            return loc[ret_variable]
        except Exception as e:
            raise ValueError(f"Error executing code: {e}")
    
    def execute(self, data:TQAData):
        code = self.args['code']
        df = copy.deepcopy(data.tbl)
        ret_df = self._execute_code_from_string(code, df, ret_variable='df')
        # get generated cols
        new_cols = [col for col in ret_df.columns if col not in data.tbl.columns]
        if len(new_cols) > 0:
            self.args['new_column_lis'] = new_cols
        data.tbl = ret_df

        return data

    def complete_args(self, data: TQAData, out: str):
        code_op_src_cols = []
        code = parse_any_string(out, hard_replace='Code:')
        for col in data.tbl.columns:
            if f'{col}' in code or f"{col}" in code:
                code_op_src_cols.append(col)
        
        self.args = {'code_op_src_cols': code_op_src_cols, 'code': code}
