LLM_CODE_EVALUATOR_DEMO = """# Task Description

Given original table and processed table and a logical operator, you should deduce whether the logical operator is executed successfully on the processed table.

# Demonstration

## Demonstration 1

Original Table:
/*
row_id | result | site | tv | date | attendance | opponent_number | rank_number | tide_points
---|---|---|---|---|---|---|---|---
1 | w 42-13 | legion field birmingham, al | [n.a.] | september 3 | 82109 | tennessee-chattanooga* | #11 | 42
2 | w 17-7 | bryant-denny stadium tuscaloosa, al | jps | september 10 | 70123 | vanderbilt | #11 | 17
3 | w 13-6 | razorback stadium fayetteville, ar | abc | september 17 | 52089 | at arkansas | #12 | 13
4 | w 20-10 | legion field birmingham, al | [n.a.] | september 24 | 81421 | tulane* | #11 | 20
5 | w 29-28 | bryant-denny stadium tuscaloosa, al | espn | october 1 | 70123 | georgia | #11 | 29
*/

Processed Table:
/*
row_id | result | site | tv | date | attendance | opponent_number | rank_number | tide_points | sortable_date
---|---|---|---|---|---|---|---|---|---
1 | w 42-13 | legion field birmingham, al | [n.a.] | september 3 | 82109 | tennessee-chattanooga* | #11 | 42 | 19940903
2 | w 17-7 | bryant-denny stadium tuscaloosa, al | jps | september 10 | 70123 | vanderbilt | #11 | 17 | 19940910
3 | w 13-6 | razorback stadium fayetteville, ar | abc | september 17 | 52089 | at arkansas | #12 | 13 | 19940917
4 | w 20-10 | legion field birmingham, al | [n.a.] | september 24 | 81421 | tulane* | #11 | 20 | 19940924
*/

Logical Operator: Augment(req="Convert the date to a sortable format (e.g., YYYYMMDD) to ensure proper ordering. For incomplete dates, assume the year is 1994 unless specified otherwise.", cols=['date'])

Output: ```No``` The date is converted to a float format, not to a YYYYMMDD format as required.

## Demonstration 2

Original Table:
/*
row_id | tour | report | venue | prize_money_usd | date_finish | official_title | city | date_start
---|---|---|---|---|---|---|---|---
1 | 1 | report | stadium badminton kuala lumpur | 200000 | january 21 | malaysia super series | kuala lumpur | january 16
2 | 2 | report | seoul national university gymnasium | 300000 | january 28 | korea open super series | seoul | january 23
3 | 3 | report | national indoor arena | 200000 | march 11 | all england super series | birmingham | march 6
4 | 4 | report | st. jakobshalle | 200000 | march 18 | swiss open super series | basel | march 12
5 | 5 | report | singapore indoor stadium | 200000 | may 6 | singapore super series | singapore | may 1
*/

Processed Table:
/*
row_id | tour | report | venue | prize_money_usd | date_finish | official_title | city | date_start | duration_days
---|---|---|---|---|---|---|---|---|---
1 | 1 | report | stadium badminton kuala lumpur | 200000 | january 21 | malaysia super series | kuala lumpur | january 16 | 5
2 | 2 | report | seoul national university gymnasium | 300000 | january 28 | korea open super series | seoul | january 23 | 5
3 | 3 | report | national indoor arena | 200000 | march 11 | all england super series | birmingham | march 6 | 5
4 | 4 | report | st. jakobshalle | 200000 | march 18 | swiss open super series | basel | march 12 | 6
5 | 5 | report | singapore indoor stadium | 200000 | may 6 | singapore super series | singapore | may 1 | 5
*/

Logical Operator: Augment(req="Calculate the duration in days between date_start and date_finish. If the event is marked as "cancelled", the duration should be 0.", cols=['date_start', 'date_finish'])

Output: ```Yes``` The duration is correctly calculated.

## Demonstration 3

Original Table:
/*
row_id | column_from | honours | to | nationality | comments | name
---|---|---|---|---|---|---
1 | 2012-07-01 | [n.a.] | present | denmark | [n.a.] | henrik jensen
2 | 2012-06-18 | [n.a.] | 23 june 2012 | denmark | caretaker for one league match | john 'tune' kristiansen
3 | 2012-01-01 | won promotion to the third tier | 18 june 2012 | denmark | [n.a.] | peer f. hansen
4 | 2010-07-27 | won promotion to the fourth tier | 30 december 2011 | denmark | originally had contract until summer 2012 | john 'tune' kristiansen
5 | 2010-07-17 | [n.a.] | 27 july 2010 | denmark | never coached the team in a match | rene heitmann
*/

Processed Table:
/*
row_id | column_from | honours | to | nationality | comments | name | standardized_to
---|---|---|---|---|---|---|---
1 | 2012-07-01 | [n.a.] | present | denmark | [n.a.] | henrik jensen | 9999-12-31
2 | 2012-06-18 | [n.a.] | 23 june 2012 | denmark | caretaker for one league match | john 'tune' kristiansen | 2012-06-23
3 | 2012-01-01 | won promotion to the third tier | 18 june 2012 | denmark | [n.a.] | peer f. hansen | 2012-06-18
4 | 2010-07-27 | won promotion to the fourth tier | 30 december 2011 | denmark | originally had contract until summer 2012 | john 'tune' kristiansen | 2011-12-30
5 | 2010-07-17 | [n.a.] | 27 july 2010 | denmark | never coached the team in a match | rene heitmann | 2010-07-27
*/

Logical Operator: Normalize(req="Standard the column `to` to sortable string like 'YYYY-MM-DD'. Handle special cases like 'present' by replacing them with a future date like '9999-12-31'.", cols=['to'])

Output: ```Yes``` The column `to` is correctly standardized."""

LLM_CODE_EVALUATOR_QUERY = """# Evaluation

Original Table:
/*
{in_tbl}
*/

Processed Table:
/*
{out_tbl}
*/

Logical Operator: {op}

Output ```yes_or_not``` with NO EXTRA Texts.
Output: """