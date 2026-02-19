# Edge Cases and Considerations for Monthly Leave Limit

## 1. Leave Spanning Across Two Months
If the leave starts on the 29th of December and the requested duration is 5 days,  
it should not fail as long as only 3 days are counted within December.  
The remaining 2 days should be calculated as part of January.

## 2. Leap Year Handling
Leap years must be handled correctly, February (29 days).  
The calculation logic should dynamically adapt to the actual number of days in the month.

## 3. Cross-Month Calculation (Previous Month Impact)
From the perspective of any given month, leaves that started in the previous month and extend into the current month must be taken into account.  
Each month should consider overlapping leaves from adjacent months.

## 4. Avoid Hard Validation on Requested Duration
It is not valid to reject a leave request simply because the total requested days exceed the monthly limit (e.g., 8 days).  
The leave may span two months, such as 4 days in the current month and 4 days in the next month.

## 5. Next Month Validation After Approval
If a leave request starts near the end of a month (e.g., the 30th) and spans 10 days,  
the current month may not exceed its limit.  
However, the following month may exceed its allowed quota.  
The impact on the next month must also be evaluated to ensure it remains within the permitted range.

## 6. Working Days vs. Calendar Days
The calculation should be based on the employee’s working days according to their resource calendar,  
not simply on raw calendar day counting.

## 7. Leaves Requested in Hours
Leaves may be requested in hours rather than days.  
The logic must support and correctly calculate such cases.
