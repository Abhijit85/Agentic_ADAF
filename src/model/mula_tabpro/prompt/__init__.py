from global_values import TASK_TYPE

if TASK_TYPE == 'tableqa' or TASK_TYPE == 'finqa' or TASK_TYPE == 'birdqa' or TASK_TYPE == 'tablebenchqa_nr' or TASK_TYPE == 'tablebenchqa_fc':
    from .tableqa.nl2sql_prompt_complete import *
    from .tableqa.nl2sql_prompt_prep import *
    from .tableqa.end2ender_prompt import *
    from .tableqa.cot_end2ender_prompt import *
    from .tableqa.manager_prompt import *
    from .tableqa.nl2code_prompt_prep import *
    from .tableqa.nl2code_prompt_complete import *
    from .tableqa.code_prep_prompt import *
    from .tableqa.planner_prompt import *

elif TASK_TYPE == 'tablefact':
    from .tablefact.nl2sql_prompt_prep import *
    from .tablefact.nl2sql_prompt_complete import *
    from .tablefact.binder_prompt import *
    from .tablefact.end2ender_prompt import *
    from .tablefact.cot_end2ender_prompt import *
    from .tablefact.manager_prompt import *
    from .tablefact.nl2code_prompt_prep import *
    from .tablefact.nl2code_prompt_complete import *
    from .tablefact.code_prep_prompt import *
    from .tableqa.planner_prompt import *

elif TASK_TYPE == 'fetaqa':
    from .fetaqa.nl2sql_prompt_prep import *
    from .fetaqa.nl2sql_prompt_complete import *
    from .fetaqa.binder_prompt import *
    from .fetaqa.end2ender_prompt import *
    from .fetaqa.cot_end2ender_prompt import *
    from .fetaqa.manager_prompt import *
    from .fetaqa.nl2code_prompt_prep import *
    from .fetaqa.nl2code_prompt_complete import *
    from .fetaqa.code_prep_prompt import *


from .coltype_deducer_prompt import *
from .imputater_prompt import *
from .cleaner_prompt import *
from .view_generator_prompt import *
from .op_agent_prompt import *
from .physical_op_prompt import *

from .coder_prompt import *
from .op2code_prompt import *
from .llm_code_evaluator_prompt import *
from .imputater_evaluator_prompt import *