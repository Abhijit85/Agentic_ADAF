from global_values import TASK_TYPE

if TASK_TYPE == 'tableqa' or TASK_TYPE == 'tablebenchqa_nr' or TASK_TYPE == 'tablebenchqa_fc':
    from .tableqa.critic_prompt import *
    from .tableqa.user_prompt import *
    from .tableqa.engineer_prompt import *
    from .tableqa.planner_prompt import *
elif TASK_TYPE == 'tablefact':
    from .tablefact.critic_prompt import *
    from .tablefact.user_prompt import *
    from .tablefact.engineer_prompt import *
    from .tablefact.planner_prompt import *