from typing import List, Tuple
from src.tools.utils import *
from global_values import *
from src.model.autotqa.agent import *
from src.model.autotqa.prompt import *
from src.tools.logger import Logger
from typing import Any

class AutoTQA:
    def __init__(self, llm_name:str, logger_root='tmp/autotqa_log', logger_file=f'autotqa_v{TABLELLM_VERSION}.log'):
        self.llm_name = llm_name

        self.engineer = AutoTQAEngineer(llm_name=llm_name, logger_root=logger_root, logger_file=logger_file)
        self.critic = AutoTQACritic(llm_name=llm_name, logger_root=logger_root, logger_file=logger_file)
        self.user = AutoTQAUser(llm_name=llm_name, logger_root=logger_root, logger_file=logger_file)
        self.planner = AutoTQAPlanner(llm_name=llm_name, logger_root=logger_root, logger_file=logger_file)
        self.logger = Logger(name='AutoTQA', root=logger_root, log_file=logger_file)

    def process(self, data: Any):
        data.tbl, _ = base_clean_dataframe(data.tbl)
        
        start_time = time.time()

        self.process_log = {
            'id': data.id,
            'title': data.title,
            'table': df_to_cotable_old(data.tbl, DEFAULT_ROW_CUT), 
            'question': data.question, 
            'label': data.label
        }

        original_data = copy.deepcopy(data)
        reasoning_plan, final_report = None, None
        cur_round = 0

        while cur_round < AUTOTQA_ROUND:
            self.logger.log_message(msg=f'【Round {cur_round}】')
            try:
                data = copy.deepcopy(original_data)
                cur_round_record = {}

                if cur_round == 0 or reasoning_plan is None or final_report is None:
                    reasoning_plan = self.planner.process(data)
                    cur_round += 1
                else:
                    reasoning_plan = self.planner.modify_plan_from_critic(data, reasoning_plan, final_report)
                    cur_round += 1
                react_records = self.engineer.process(data, reasoning_plan)
                cur_round += self.engineer.cur_round
                preliminary_evaluation, summarize_the_result, final_report = self.critic.process(data, react_records)
                cur_round += 1

                cur_round_record['reasoning_plan'] = reasoning_plan
                cur_round_record['react_records'] = react_records
                cur_round_record['preliminary_evaluation'] = preliminary_evaluation
                cur_round_record['summarize_the_result'] = summarize_the_result
                cur_round_record['final_report'] = final_report

                self.process_log[f'round_{cur_round}'] = cur_round_record

                if '[TERMINATE]' in final_report:
                    self.critic.logger.log_message(line_limit=cut_log, msg=f'【Finished in round {cur_round} with final report】: {final_report}')

                    answer = self.user.process(data, react_records)
                    cur_round += 1
                    self.process_log['final_answer'] = answer

                    self.user.logger.log_message(line_limit=cut_log, msg=f'【Final answer】: {answer}, 【Label】: {data.label}')

                    return self.process_log
                
            except Exception as e:
                self.logger.log_message(msg=f'!!!!!!!!!!!!!!!!!!!!!!!!!!!!【Error in AutoTQA】: {e}!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
                continue

        self.logger.log_message(msg=f'!!!!!!!!!!!!!!!!!!!!!!!!!!!!【Error in AutoTQA】: Exceed the round limit Direct answer the question!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
        answer = self.user.process(data, [])
        self.process_log['final_answer'] = answer
        self.process_log['MAX_ROUND'] = 'Exceed the round limit'
        
        return self.process_log