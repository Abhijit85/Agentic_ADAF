from global_values import NAMES

AUGMENTATION = {
    #! HEAD
    "_head": f"You are an agent to generate new columns. You can use operators from one of the following: {NAMES['EXT_COL']}, {NAMES['CAL_COL']}, {NAMES['BOOL_COL']}, {NAMES['COMB_COL']}.",

    #! QUERY
    "_query": """Please complete the following prompt.
/*
{table}
*/
Requirement: please process the column {col} to satisfy: {question}
Operator:""",

    #! OP CATALOG
    "_catalog": [NAMES['EXT_COL'], NAMES['CAL_COL'], NAMES['BOOL_COL'], NAMES['COMB_COL'], NAMES['GEN_NEW_COL']],

    # EXT_COL
    f"desc_{NAMES['EXT_COL']}": f"The operator {NAMES['EXT_COL']} aims to extract sub-string from given column. We use the operator by specifying the arguments `new_column` and the extraction function `func`.",

    f"demo_{NAMES['EXT_COL']}": f"""Here are examples of using the operator,
/*
"career_win_loss": "22-88" | "nan" | "17-20" | "11-14"
*/
Requirement: please process the column `career_win_loss` to satisfy: Extract the win number from the column 'career\nwin-loss'. If missing some records, fill in the missing records with `MIN_VALUE` since the question is asking for a larger win number.
Operator: ```{NAMES['EXT_COL']}(df, new_column="win_number_team_a", func=lambda x: int(str(x['career_win_loss']).split('-')[0]) if '-' in str(x['career_win_loss']) else MIN_VALUE)```""",

    # CAL_COL
    f"desc_{NAMES['CAL_COL']}": f"The operator {NAMES['CAL_COL']} aims to calculate new column based on the existing columns. We use the operator by specifying the arguments `new_column` and the calculation function `func`.",

    f"demo_{NAMES['CAL_COL']}": f"""Here are examples of using the operator,
/*
"enter_office": "1996-99" | "1998-2002" | "2000-04" | "2002-06" | "2004-08"
*/
Requirement: please process the column `enter_office` to satisfy: Calculate the duration of the term. First split the term into two parts, then calculate the abs difference between the two parts.
Operator: ```{NAMES['CAL_COL']}(df, new_column="year_duration_in_office", func=lambda x: (int(str(x['enter_office']).split('-')[1][-2:]) - int(str(x['enter_office']).split('-')[0][-2:]))%100)```

/*
"term": "1859-1864" | "?-1880" | "1864-1869" | "1869-1880"
*/
Requirement: please process the column `term` to satisfy: Extract the duration of the term. If the term is missing, return `MAX_VALUE` since the question is asking for a smaller term.
Operator: ```{NAMES['CAL_COL']}(df, new_column="serve_duration", func=lambda x: int(x['term'].split('-')[1]) - int(x['term'].split('-')[0]) if '?' not in x else MAX_VALUE)```""",

    # COMB_COL
    f"desc_{NAMES['COMB_COL']}": f"The operator {NAMES['COMB_COL']} aims to combine multiple columns into a new column. We use the operator by specifying the arguments `new_column` and the combination function `func`.",

    f"demo_{NAMES['COMB_COL']}": f"""Here are examples of using the operator,
/*
"year": 2005 | 2010 | 2007 | 2009
"month": 5 | 5 | [n.a.] | 12
"day": 4 | 22 | 1 | 31
*/
Requirement: please process the column `year`, `month`, `day` to satisfy: what is the date? if '[n.a.]' then return assume the value to be 00.
Operator: ```{NAMES['COMB_COL']}(df, new_column="date_yyyy_mm_dd", func=lambda x: f"{{x['year']}}-{{str(x['month']).replace('[n.a.]', '00').zfill(2)}}-{{str(x['day']).zfill(2)}})""",

    # BOOL_COL
    f"desc_{NAMES['BOOL_COL']}": f"The operator {NAMES['BOOL_COL']} aims to generate boolean column based on the existing column. We use the operator by specifying the arguments `new_column` and the boolean function `func`.",

    f"demo_{NAMES['BOOL_COL']}": f"""Here are examples of using the operator,
/*
"place": "søfteland , norway" | "nan" | "york , united kingdom" | "burrator , united kingdom"
*/
Requirement: please process the column `place` to satisfy: Return whether the competition is held in the UK.
Operator: ```{NAMES['BOOL_COL']}(df, new_column="is_competition_held_in_uk", func=lambda x: 'united kingdom' in str(x['place']))```""",

    # GEN_NEW_COL
    f"desc_{NAMES['GEN_NEW_COL']}": f"If all operators above can not satisfy the requirement, use the operator {NAMES['GEN_NEW_COL']}. We use the operator by specifying the arguments `new_column` and the generation function `func`.",

    f"demo_{NAMES['GEN_NEW_COL']}": f"""Here are examples of using the operator,

/*
"career_win_loss": "22-88" | "nan" | "17-20" | "11-14"
*/
Requirement: please process the column `career_win_loss` to satisfy: extract the win number from the column.
Operator: ```{NAMES['GEN_NEW_COL']}(df, new_column="win_number", func=lambda x: int(str(x['career_win_loss']).split('-')[0]) if '-' in str(x['career_win_loss']) else '[n.a.]')```""",


}


NORMALIZATION = {
    #! HEAD
    "_head": "You are an agent to normalize the table.",

    #! QUERY
    "_query": """Please complete the following prompt.
/*
{table}
*/
Requirement: please process the column {col} to satisfy: {question}
Output ```operator_with_args``` with NO other texts.
Operator:""",

    #! OP CATALOG
    "_catalog": [NAMES['STAND_DATETIME'], NAMES['STAND_NUMERICAL']],

    # STAND_DATETIME
    f"desc_{NAMES['STAND_DATETIME']}": f"The operator `{NAMES['STAND_DATETIME']}` aims to standardize the datetime format. We use the operator by specifying the arguments `column` and the format string `format`. Remember, only use the operators to standardize datetime-value column.",

    f"demo_{NAMES['STAND_DATETIME']}": f"""Here are some examples of using the operator `{NAMES['STAND_DATETIME']}`,

/*
"date": "october 19 2001" | "july 13 2009" | "september 23 governor's cup"
*/
Requirement: please standardize the column `date` to datetime format.
Operator: ```{NAMES['STAND_DATETIME']}(df, column='date', format='%B %d %Y')```

/*
"kickoff": "7:05pm" | "3:05pm" | "7:35pm" | "7:05pm" | "7:05pm"
*/
Requirement: please standardize the column `kickoff` to datetime format.
Operator: ```{NAMES['STAND_DATETIME']}(df, column='kickoff', format='%I:%M%p')```

/*
"when": "01/05/1999" | "05/12/2003" | "11/08/2007"
*/
Requirement: please standardize the column `when` to datetime format.
Operator: ```{NAMES['STAND_DATETIME']}(df, column='when', format='%m/%d/%Y')```

/*
"date": "may 23, 1958" | "july 20, 1953" | "february 14, 1953" | "january 1, 1953" | "may 1, 1953"
*/
Requirement: please standardize the column `date` to datetime format.
Operator: ```{NAMES['STAND_DATETIME']}(df, column='date', format='%B %d, %Y')```
""",

    # STAND_NUMERICAL
    f"desc_{NAMES['STAND_NUMERICAL']}": f"The operator `{NAMES['STAND_NUMERICAL']}` aims to standardize the numerical column. We use the operator by specifying the arguments `column` and the lambda function `func`.""",

    f"demo_{NAMES['STAND_NUMERICAL']}": f"""Here are some examples of using the operator `{NAMES['STAND_NUMERICAL']}`,

/*
"notes": "5000" | "5000" | "10,000" | "10,000" | "10000" | "10,000"
*/
Requirement: lease standardize the column `notes` to numerical format.
Operator: ```{NAMES['STAND_NUMERICAL']}(df, column='notes', func=lambda x: int(x.replace(',', '')))```

/*
"score": "25 pt" | "30 pt" | "20 pt" | "15 pt" | "10 pt"
*/
Requirement: please standardize the column `score` to numerical format.
Operator: ```{NAMES['STAND_NUMERICAL']}(df, score='date', func=lambda x: int(x.replace('pt', '').strip()))```

/*
"notes": 1 episode | 1 episode | 119 episodes | 13 episodes | voice<br>3 episodes | episode: \drugs are bad | [n.a.] | season 3 episode 24 'to tell the truth'
*/
Requirement: please standardize the column `notes` to numerical format.
Operator: ```{NAMES['STAND_NUMERICAL']}(df, column='notes', func=lambda x: int(re.search(r'\d+ ', x).group() if 'episodes' in x else 1 if 'episode' in x else '[n.a.]'))```""",

}