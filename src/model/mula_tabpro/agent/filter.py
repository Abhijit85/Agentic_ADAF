from .simple_agent import *

class Filter(SimpleAgent):
    def __init__(self, llm_name=LLM_NAME, chains: List = [InitOP()], PROMPT = AUGMENTATION, agent_name='filter', logger_root='tmp/table_llm_log', logger_file=f'mula_tabpro_v{TABLELLM_VERSION}.log'):
        super().__init__(llm_name=llm_name, chains=chains, agent_name=agent_name, PROMPT=PROMPT, logger_root=logger_root, logger_file=logger_file)

        self.MAX_ERR_RAISE_CNT = 4
    
    def implement_filter(self, data:TQAData, filterop:FilterOp):
        self.last_log = None
        self.err_raise_cnt = 0

        cols = filterop.cols
        
        for col in cols:
            if col not in data.tbl.columns:
                raise ValueError(f'E: The column {col} does not exist in the table!')
        
        op = FilterColumn()
        op.give_arg_val(columns=cols)
        data = op.execute(data)
        
        self.logger.log_message(msg=f'New Table is:\n{data.tbl}')

        return data, op