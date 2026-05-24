from src.tools.utils import parse_any_string
from global_values import NAMES
from .physical_ops import GenNewCol, ExtractColumn, CalculateColumn, BooleanColumn, CombineColumn
from .standardize_datetime import StandDatetime
from .standardize_numerical import StandNumerical

class AutoOP:
    class_dic = {
        NAMES['GEN_NEW_COL']: GenNewCol,
        NAMES['EXT_COL']: ExtractColumn,
        NAMES['CAL_COL']: CalculateColumn,
        NAMES['BOOL_COL']: BooleanColumn,
        NAMES['COMB_COL']: CombineColumn,

        
        NAMES['STAND_DATETIME']: StandDatetime,
        NAMES['STAND_NUMERICAL']: StandNumerical,
    }
    Aug_dic = {
        NAMES['GEN_NEW_COL']: GenNewCol,
        NAMES['EXT_COL']: ExtractColumn,
        NAMES['CAL_COL']: CalculateColumn,
        NAMES['BOOL_COL']: BooleanColumn,
        NAMES['COMB_COL']: CombineColumn,
    }
    Nor_dic = {
        NAMES['STAND_DATETIME']: StandDatetime,
        NAMES['STAND_NUMERICAL']: StandNumerical,
    }

    def deduce_op(op_str:str, type:str='Augment'):
        tar_dic = AutoOP.Aug_dic if type == 'Augment' else AutoOP.Nor_dic
        for key in tar_dic:
            if op_str.startswith(key):
                return tar_dic[key]
        raise ValueError(f'E: Function name not found in the output. The function name should be one of the {tar_dic.keys()}')
