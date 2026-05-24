from global_values import NAMES

PROMPT_VIEW_GENERATOR = {
    f"head": f"You are a agent to generate a new column. You Can use Operators from one of the following: {NAMES['EXT_COL']}, {NAMES['CAL_COL']}, {NAMES['BOOL_COL']}, {NAMES['COMB_COL']}.",
    
    # description for {NAMES['GEN_NEW_COL']}
    f"{NAMES['GEN_NEW_COL']}": f"""The operators aim to generate a new column based on the existing column(s). We use the operator by specifying the arguments `new_column` and the `func` function.""",

    # demo for {NAMES['GEN_NEW_COL']}
    f"demo_{NAMES['GEN_NEW_COL']}_from_column": f"""Here are example of using the operators,

/*
"career_win_loss": "22-88" | "nan" | "17-20" | "11-14"
*/
Given the column `career_win_loss` please generate a new column to answer: Extract the win number from the column 'career\nwin-loss'. If missing some records, fill in the missing records with `MIN_VALUE` since the question is asking for a larger win number.
Operator: ```{NAMES['EXT_COL']}(df, new_column="win_number_team_a", func=lambda x: int(str(x['career_win_loss']).split('-')[0]) if '-' in str(x['career_win_loss']) else MIN_VALUE)```

/*
"enter_office": "1996-99" | "1998-2002" | "2000-04" | "2002-06" | "2004-08"
*/
Given the column `enter_office` please generate a new column to answer: Calculate the duration of the term. First split the term into two parts, then calculate the abs difference between the two parts.
Operator: ```{NAMES['CAL_COL']}(df, new_column="year_duration_in_office", func=lambda x: (int(str(x['enter_office']).split('-')[1][-2:]) - int(str(x['enter_office']).split('-')[0][-2:]))%100)```

/*
"year": 2005 | 2010 | 2007 | 2009
"month": 5 | 5 | [n.a.] | 12
"day": 4 | 22 | 1 | 31
*/
Given the column `year`, `month`, `day` please generate a new column to answer: what is the date? if '[n.a.]' then return assume the value to be 00.
Operator: ```{NAMES['COMB_COL']}(df, new_column="date_yyyy_mm_dd", func=lambda x: f"{{x['year']}}-{{str(x['month']).replace('[n.a.]', '00').zfill(2)}}-{{str(x['day']).zfill(2)}})```

/*
"term": "1859-1864" | "?-1880" | "1864-1869" | "1869-1880"
*/
Given the column `term` please generate a new column to answer: Extract the duration of the term. If the term is missing, return `MAX_VALUE` since the question is asking for a smaller term.
Operator: ```{NAMES['CAL_COL']}(df, new_column="serve_duration", func=lambda x: int(x['term'].split('-')[1]) - int(x['term'].split('-')[0]) if '?' not in x else MAX_VALUE)```

/*
"prominence": "10080 ft; 3072 m" | "1677 ft; 511 m" | "7196 ft; 2193 m" | 10000 | 10000 | 10000
*/
Given the column `prominence` please generate a new column to answer: Extract the prominence in feet. If the value is missing, return `MIN_VALUE` since the question is asking for a larger prominence.
Operator: ```{NAMES['EXT_COL']}(df, new_column="prominence_ft", func=lambda x: int(str(x['prominence']).split(';')[0].split(' ')[0]) if ';' in str(x['prominence']) else MIN_VALUE)```

/*
"place": "søfteland , norway" | "nan" | "york , united kingdom" | "burrator , united kingdom"
*/
Given the column `place` please generate a new column to answer: Return whether the competition is held in the UK.
Operator: ```{NAMES['BOOL_COL']}(df, new_column="is_competition_held_in_uk", func=lambda x: 'united kingdom' in str(x['place']))```""",

    # query for {NAMES['GEN_NEW_COL']}_from_column
    f"query_{NAMES['GEN_NEW_COL']}_from_column": """Please complete the following prompt.

/*
{table}
*/
Given the column {col} please generate a new column to answer: {question}
Operator:""",

    "self_correc_ins": """/*
{context}
*/
Requirement: {question}
Last Error: {last_error}
Operator: {a}"""
}
