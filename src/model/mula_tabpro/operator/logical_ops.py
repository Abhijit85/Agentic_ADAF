

class LogicalOperator:
    def __init__(self, type, req, cols):
        self.type = type
        self.req = req
        self.cols = cols
    
    def __str__(self):
        return f'{self.type}(req="{self.req}", cols={self.cols})'

class AugmentOp(LogicalOperator):
    def __init__(self, req, cols):
        super().__init__('Augment', req, cols)

class NormalizeOp(LogicalOperator):
    def __init__(self, req, col):
        super().__init__('Normalize', req, [col])

class FilterOp(LogicalOperator):
    def __init__(self, req, cols):
        super().__init__('Filter', req, cols)