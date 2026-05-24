from src.model.mula_tabpro.agent.simple_agent import List, Agent, InitOP, TQAData, TABLELLM_VERSION, execute_code_from_string, LLM_NAME
import pandas as pd
import sqlite3

class AutoTQAExecutor(Agent):
    def __init__(self, llm_name=LLM_NAME, chains: List = [InitOP()], PROMPT = None, agent_name='executor', logger_root='tmp/autotqa_log', logger_file=f'autotqa_v{TABLELLM_VERSION}.log', mode='base'):
        super().__init__(llm_name=llm_name, chains=chains, PROMPT=PROMPT, agent_name=agent_name, logger_root=logger_root, logger_file=logger_file)
        self.mode = mode
        self.conn = sqlite3.connect(':memory:')
    
    def exe_sql(self, sql: str, data:TQAData):
        tbl = data.tbl
        tbl.to_sql('w', self.conn, index=False, if_exists='replace')
        ans = pd.read_sql(sql, self.conn)
        return ans
    
    def exe_code(self, code: str, data:TQAData):
        df = data.tbl
        result = execute_code_from_string(code, df)
        
        # check if any duplicated columns in the `result`, if so, rename the column and modify the code
        for i in range(len(result.columns)):
            cur_col = result.columns[i]
            idx = 1
            for j in range(i+1, len(result.columns)):
                comp_col = result.columns[j]
                if cur_col.lower() == comp_col.lower():
                    # rename comp_col to {cur_col}_{idx}
                    new_col = f'{cur_col}_{idx}'
                    result.rename(columns={comp_col: new_col}, inplace=True)
                    idx += 1

        return result