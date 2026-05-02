import json

from .student_hints import DEFAULT_ALGORITHM_FALLBACK, DEFAULT_FUNCTIONS_FALLBACK, STUDENT_METADATA


# Maps seed / PDF wording to an existing canonical template key.
_EXAMPLE_ALIASES: dict[str, str] = {
    "swap without third variable": "swap two numbers",
    "recursive factorial": "factorial of number",
    "matrix addition 3x3": "matrix addition",
    "reverse a string": "reverse a string",
    "check palindrome": "check palindrome",
    "fibonacci series": "fibonacci series",
    "right angle star pattern": "pattern printing",
}


def build_problem_content(module_name: str, topic: str, example: str) -> dict:
    key = example.strip().lower()
    key = _EXAMPLE_ALIASES.get(key, key)

    templates = {
        "print hello world": _make_template(
            sample_input="",
            expected_output="Hello World",
            constraints="No input.",
            input_format="No input.",
            output_format="Print exactly: Hello World",
            examples=[{"input": "", "output": "Hello World"}, {"input": "", "output": "Hello World"}],
            tests=[{"input": "", "output": "Hello World"}],
        ),
        "add two numbers": _make_template(
            sample_input="7 3",
            expected_output="10",
            constraints="-10^9 <= a, b <= 10^9",
            input_format="Two integers a and b.",
            output_format="Print a + b.",
            examples=[{"input": "7 3", "output": "10"}, {"input": "-2 5", "output": "3"}],
            tests=[{"input": "2 2", "output": "4"}, {"input": "10 5", "output": "15"}, {"input": "-3 -4", "output": "-7"}],
        ),
        "swap two numbers": _make_template(
            sample_input="7 3",
            expected_output="3 7",
            constraints="-10^9 <= a, b <= 10^9",
            input_format="Two integers a and b.",
            output_format="Print swapped values: b a.",
            examples=[{"input": "7 3", "output": "3 7"}, {"input": "10 -1", "output": "-1 10"}],
            tests=[{"input": "1 2", "output": "2 1"}, {"input": "9 9", "output": "9 9"}, {"input": "-5 8", "output": "8 -5"}],
        ),
        "check even/odd": _make_template(
            sample_input="8",
            expected_output="Even",
            constraints="-10^9 <= n <= 10^9",
            input_format="One integer n.",
            output_format="Print Even if n is even, else Odd.",
            examples=[{"input": "8", "output": "Even"}, {"input": "7", "output": "Odd"}],
            tests=[{"input": "0", "output": "Even"}, {"input": "-3", "output": "Odd"}, {"input": "14", "output": "Even"}],
        ),
        "find largest of 3 numbers": _make_template(
            sample_input="9 2 5",
            expected_output="9",
            constraints="-10^9 <= a, b, c <= 10^9",
            input_format="Three integers a, b, c.",
            output_format="Print the largest value.",
            examples=[{"input": "9 2 5", "output": "9"}, {"input": "-1 -3 -2", "output": "-1"}],
            tests=[{"input": "1 2 3", "output": "3"}, {"input": "5 5 1", "output": "5"}, {"input": "7 4 7", "output": "7"}],
        ),
        "grade calculator": _make_template(
            sample_input="82",
            expected_output="B",
            constraints="0 <= marks <= 100",
            input_format="One integer marks.",
            output_format="Print grade: A (>=90), B (>=80), C (>=70), D (>=60), F (<60).",
            examples=[{"input": "82", "output": "B"}, {"input": "95", "output": "A"}],
            tests=[{"input": "74", "output": "C"}, {"input": "60", "output": "D"}, {"input": "48", "output": "F"}],
        ),
        "print multiplication table": _make_template(
            sample_input="5",
            expected_output="5 10 15 20 25 30 35 40 45 50",
            constraints="1 <= n <= 10^4",
            input_format="One integer n.",
            output_format="Print first 10 multiples of n separated by spaces.",
            examples=[{"input": "5", "output": "5 10 15 20 25 30 35 40 45 50"}, {"input": "2", "output": "2 4 6 8 10 12 14 16 18 20"}],
            tests=[{"input": "1", "output": "1 2 3 4 5 6 7 8 9 10"}, {"input": "7", "output": "7 14 21 28 35 42 49 56 63 70"}, {"input": "3", "output": "3 6 9 12 15 18 21 24 27 30"}],
        ),
        "factorial of number": _make_template(
            sample_input="5",
            expected_output="120",
            constraints="0 <= n <= 12",
            input_format="One integer n.",
            output_format="Print n!.",
            examples=[{"input": "5", "output": "120"}, {"input": "0", "output": "1"}],
            tests=[{"input": "1", "output": "1"}, {"input": "6", "output": "720"}, {"input": "3", "output": "6"}],
        ),
        "pattern printing": _make_template(
            sample_input="3",
            expected_output="*\n**\n***",
            constraints="1 <= n <= 20",
            input_format="One integer n.",
            output_format="Print a right-angle star pattern with n lines.",
            examples=[{"input": "3", "output": "*\n**\n***"}, {"input": "1", "output": "*"}],
            tests=[{"input": "2", "output": "*\n**"}, {"input": "4", "output": "*\n**\n***\n****"}, {"input": "5", "output": "*\n**\n***\n****\n*****"}],
        ),
        "find sum of array": _make_template(
            sample_input="5\n1 2 3 4 5",
            expected_output="15",
            constraints="1 <= n <= 10^5; -10^4 <= arr[i] <= 10^4",
            input_format="First line n, second line n integers.",
            output_format="Print sum of elements.",
            examples=[{"input": "5\n1 2 3 4 5", "output": "15"}, {"input": "3\n-1 2 4", "output": "5"}],
            tests=[{"input": "1\n10", "output": "10"}, {"input": "4\n0 0 0 0", "output": "0"}, {"input": "3\n7 8 9", "output": "24"}],
        ),
        "largest element": _make_template(
            sample_input="5\n1 2 9 4 5",
            expected_output="9",
            constraints="1 <= n <= 10^5; -10^9 <= arr[i] <= 10^9",
            input_format="First line n, second line n integers.",
            output_format="Print largest array element.",
            examples=[{"input": "5\n1 2 9 4 5", "output": "9"}, {"input": "3\n-5 -1 -9", "output": "-1"}],
            tests=[{"input": "1\n7", "output": "7"}, {"input": "4\n2 2 2 2", "output": "2"}, {"input": "5\n8 1 3 6 4", "output": "8"}],
        ),
        "matrix addition": _make_template(
            sample_input="2 2\n1 2\n3 4\n5 6\n7 8",
            expected_output="6 8\n10 12",
            constraints="1 <= r, c <= 20",
            input_format="r c, then matrix A (r lines), then matrix B (r lines).",
            output_format="Print A+B matrix row-wise.",
            examples=[{"input": "1 2\n1 3\n4 5", "output": "5 8"}, {"input": "2 1\n2\n3\n1\n4", "output": "3\n7"}],
            tests=[{"input": "1 1\n2\n7", "output": "9"}, {"input": "2 2\n1 1\n1 1\n2 2\n2 2", "output": "3 3\n3 3"}, {"input": "1 3\n1 2 3\n3 2 1", "output": "4 4 4"}],
        ),
        "reverse a string": _make_template(
            sample_input="hello",
            expected_output="olleh",
            constraints="1 <= length <= 10^4",
            input_format="One string (no spaces).",
            output_format="Print reversed string.",
            examples=[{"input": "hello", "output": "olleh"}, {"input": "abc", "output": "cba"}],
            tests=[{"input": "a", "output": "a"}, {"input": "racecar", "output": "racecar"}, {"input": "coder", "output": "redoc"}],
        ),
        "check palindrome": _make_template(
            sample_input="madam",
            expected_output="Yes",
            constraints="1 <= length <= 10^4",
            input_format="One string (no spaces).",
            output_format="Print Yes if palindrome, else No.",
            examples=[{"input": "madam", "output": "Yes"}, {"input": "hello", "output": "No"}],
            tests=[{"input": "a", "output": "Yes"}, {"input": "abba", "output": "Yes"}, {"input": "abc", "output": "No"}],
        ),
        "count vowels": _make_template(
            sample_input="education",
            expected_output="5",
            constraints="1 <= length <= 10^5",
            input_format="One lowercase/uppercase string.",
            output_format="Print vowel count (a, e, i, o, u).",
            examples=[{"input": "education", "output": "5"}, {"input": "sky", "output": "0"}],
            tests=[{"input": "AEIOU", "output": "5"}, {"input": "programming", "output": "3"}, {"input": "bcd", "output": "0"}],
        ),
        "factorial using function": _make_template(
            sample_input="5",
            expected_output="120",
            constraints="0 <= n <= 12",
            input_format="One integer n.",
            output_format="Print factorial of n using a function.",
            examples=[{"input": "5", "output": "120"}, {"input": "4", "output": "24"}],
            tests=[{"input": "0", "output": "1"}, {"input": "1", "output": "1"}, {"input": "6", "output": "720"}],
        ),
        "fibonacci series": _make_template(
            sample_input="7",
            expected_output="0 1 1 2 3 5 8",
            constraints="1 <= n <= 40",
            input_format="One integer n (number of terms).",
            output_format="Print first n Fibonacci numbers separated by spaces.",
            examples=[{"input": "5", "output": "0 1 1 2 3"}, {"input": "1", "output": "0"}],
            tests=[{"input": "2", "output": "0 1"}, {"input": "3", "output": "0 1 1"}, {"input": "6", "output": "0 1 1 2 3 5"}],
        ),
        "sum using recursion": _make_template(
            sample_input="5",
            expected_output="15",
            constraints="1 <= n <= 10^4",
            input_format="One integer n.",
            output_format="Print sum of numbers from 1 to n using recursion.",
            examples=[{"input": "5", "output": "15"}, {"input": "1", "output": "1"}],
            tests=[{"input": "2", "output": "3"}, {"input": "10", "output": "55"}, {"input": "7", "output": "28"}],
        ),
        "swap using pointers": _make_template(
            sample_input="4 9",
            expected_output="9 4",
            constraints="-10^9 <= a, b <= 10^9",
            input_format="Two integers a and b.",
            output_format="Print swapped numbers using pointer logic.",
            examples=[{"input": "4 9", "output": "9 4"}, {"input": "1 1", "output": "1 1"}],
            tests=[{"input": "-2 5", "output": "5 -2"}, {"input": "8 3", "output": "3 8"}, {"input": "0 7", "output": "7 0"}],
        ),
        "access array using pointer": _make_template(
            sample_input="4\n2 4 6 8",
            expected_output="20",
            constraints="1 <= n <= 10^5; -10^4 <= arr[i] <= 10^4",
            input_format="First line n, second line n integers.",
            output_format="Print sum of array elements using pointer traversal.",
            examples=[{"input": "4\n2 4 6 8", "output": "20"}, {"input": "3\n1 1 1", "output": "3"}],
            tests=[{"input": "1\n9", "output": "9"}, {"input": "5\n1 2 3 4 5", "output": "15"}, {"input": "2\n-1 4", "output": "3"}],
        ),
        "pointer to pointer": _make_template(
            sample_input="7",
            expected_output="7",
            constraints="-10^9 <= n <= 10^9",
            input_format="One integer n.",
            output_format="Print value using pointer-to-pointer dereference.",
            examples=[{"input": "7", "output": "7"}, {"input": "-2", "output": "-2"}],
            tests=[{"input": "0", "output": "0"}, {"input": "15", "output": "15"}, {"input": "-8", "output": "-8"}],
        ),
        "student record system": _make_template(
            sample_input="2\nAlice 20\nBob 22",
            expected_output="Alice 20\nBob 22",
            constraints="1 <= n <= 100; name length <= 30",
            input_format="n followed by n lines: name age.",
            output_format="Print all student records line by line.",
            examples=[{"input": "1\nRiya 19", "output": "Riya 19"}, {"input": "2\nA 18\nB 21", "output": "A 18\nB 21"}],
            tests=[{"input": "2\nTom 20\nSam 19", "output": "Tom 20\nSam 19"}, {"input": "1\nEve 25", "output": "Eve 25"}, {"input": "3\nA 1\nB 2\nC 3", "output": "A 1\nB 2\nC 3"}],
        ),
        "employee details": _make_template(
            sample_input="2\n101 Alice\n102 Bob",
            expected_output="101 Alice\n102 Bob",
            constraints="1 <= n <= 100; employee id is integer",
            input_format="n followed by n lines: id name.",
            output_format="Print employee details as id name per line.",
            examples=[{"input": "1\n201 John", "output": "201 John"}, {"input": "2\n1 A\n2 B", "output": "1 A\n2 B"}],
            tests=[{"input": "1\n301 Mia", "output": "301 Mia"}, {"input": "2\n11 Raj\n12 Dee", "output": "11 Raj\n12 Dee"}, {"input": "3\n1 X\n2 Y\n3 Z", "output": "1 X\n2 Y\n3 Z"}],
        ),
        "product inventory record": _make_template(
            sample_input="2\nP1 10\nP2 5",
            expected_output="P1 10\nP2 5",
            constraints="1 <= n <= 100; quantity >= 0",
            input_format="n followed by n lines: product_code quantity.",
            output_format="Print each product and quantity on new line.",
            examples=[{"input": "1\nA1 7", "output": "A1 7"}, {"input": "2\nX9 0\nY8 3", "output": "X9 0\nY8 3"}],
            tests=[{"input": "1\nB2 10", "output": "B2 10"}, {"input": "2\nC1 1\nC2 2", "output": "C1 1\nC2 2"}, {"input": "3\nD1 9\nD2 8\nD3 7", "output": "D1 9\nD2 8\nD3 7"}],
        ),
        "write data to file": _make_template(
            sample_input="hello",
            expected_output="hello",
            constraints="1 <= length <= 1000",
            input_format="A single line of text.",
            output_format="Echo the same text (simulating file write/read).",
            examples=[{"input": "hello", "output": "hello"}, {"input": "c lab", "output": "c lab"}],
            tests=[{"input": "abc", "output": "abc"}, {"input": "123", "output": "123"}, {"input": "file data", "output": "file data"}],
        ),
        "read file content": _make_template(
            sample_input="sample content",
            expected_output="sample content",
            constraints="1 <= length <= 1000",
            input_format="A single line of text.",
            output_format="Print the given text (simulating file content read).",
            examples=[{"input": "sample content", "output": "sample content"}, {"input": "line", "output": "line"}],
            tests=[{"input": "x", "output": "x"}, {"input": "read me", "output": "read me"}, {"input": "42", "output": "42"}],
        ),
        "copy file": _make_template(
            sample_input="copy this",
            expected_output="copy this",
            constraints="1 <= length <= 1000",
            input_format="A single line of text.",
            output_format="Print the same text (simulating copy output).",
            examples=[{"input": "copy this", "output": "copy this"}, {"input": "abc xyz", "output": "abc xyz"}],
            tests=[{"input": "mno", "output": "mno"}, {"input": "data", "output": "data"}, {"input": "done", "output": "done"}],
        ),
        # --- "C Foundation -- Updated.pdf" phase-aligned templates ---
        "print name and city": _make_template(
            sample_input="Riya\nChennai",
            expected_output="Riya\nChennai",
            constraints="single-word name and city each on its own input line.",
            input_format="Line 1: name. Line 2: city.",
            output_format="Print name on line 1, city on line 2.",
            examples=[
                {"input": "Ada\nBoston", "output": "Ada\nBoston"},
                {"input": "Riya\nChennai", "output": "Riya\nChennai"},
            ],
            tests=[
                {"input": "Ada\nBoston", "output": "Ada\nBoston"},
                {"input": "Riya\nChennai", "output": "Riya\nChennai"},
                {"input": "Zoe\nParis", "output": "Zoe\nParis"},
            ],
        ),
        "read name and age greeting": _make_template(
            sample_input="Alex\n21",
            expected_output="Hello Alex, you are 21 years old.",
            constraints="0 <= age <= 120; single-word name (no spaces).",
            input_format="Line 1: name string. Line 2: integer age.",
            output_format="Print one greeting sentence exactly.",
            examples=[
                {"input": "Mia\n19", "output": "Hello Mia, you are 19 years old."},
                {"input": "Alex\n21", "output": "Hello Alex, you are 21 years old."},
            ],
            tests=[
                {"input": "Amy\n17", "output": "Hello Amy, you are 17 years old."},
                {"input": "Leo\n0", "output": "Hello Leo, you are 0 years old."},
                {"input": "Zoe\n100", "output": "Hello Zoe, you are 100 years old."},
            ],
        ),
        "read character ascii": _make_template(
            sample_input="A",
            expected_output="65",
            constraints="One printable ASCII character.",
            input_format="A single character on one line.",
            output_format="Print its decimal ASCII code.",
            examples=[{"input": "A", "output": "65"}, {"input": "z", "output": "122"}],
            tests=[{"input": "0", "output": "48"}, {"input": "9", "output": "57"}, {"input": "@", "output": "64"}],
        ),
        "read float decimal places": _make_template(
            sample_input="3.14159",
            expected_output="3.14 3.1416 3.141590",
            constraints="Input is a float with a fractional part.",
            input_format="One float on one line.",
            output_format="Print three values with 2, 4, then 6 decimal places, space-separated.",
            examples=[
                {"input": "12.345678", "output": "12.35 12.3457 12.345678"},
                {"input": "3.14159", "output": "3.14 3.1416 3.141590"},
            ],
            tests=[
                {"input": "9.87", "output": "9.87 9.8700 9.870000"},
                {"input": "0.1", "output": "0.10 0.1000 0.100000"},
                {"input": "2.5", "output": "2.50 2.5000 2.500000"},
            ],
        ),
        "print data type sizes lab": _make_template(
            sample_input="",
            expected_output="4 4 8 1",
            constraints=(
                "Assume (for autograder portability) int=4, float=4, double=8, unsigned char=1 bytes "
                "as in the lab handout."
            ),
            input_format="No input.",
            output_format=(
                "Print four integers separated by spaces: sizeof(int) sizeof(float) "
                "sizeof(double) sizeof(unsigned char)."
            ),
            examples=[{"input": "", "output": "4 4 8 1"}],
            tests=[{"input": "", "output": "4 4 8 1"}],
        ),
        "print simple box border": _make_template(
            sample_input="3",
            expected_output="***\n* *\n***",
            constraints="3 <= n <= 20.",
            input_format="One integer n (side length of hollow square drawn with '*'). Middle uses spaces.",
            output_format=(
                "Print exactly n rows: rows 1 and n are n stars; rows 2..n-1 are star, "
                "(n-2 spaces), star."
            ),
            examples=[
                {"input": "3", "output": "***\n* *\n***"},
                {"input": "4", "output": "****\n*  *\n*  *\n****"},
            ],
            tests=[
                {"input": "3", "output": "***\n* *\n***"},
                {"input": "4", "output": "****\n*  *\n*  *\n****"},
                {"input": "5", "output": "*****\n*   *\n*   *\n*   *\n*****"},
            ],
        ),
        "student record variables": _make_template(
            sample_input="Mia\n19\nB\n72000",
            expected_output="Mia 19 B 72000",
            constraints=(
                "Name is single word; age integer 0-120; grade one letter A-F; fees non-negative integer."
            ),
            input_format="Four lines: name, age, grade letter, tuition fees.",
            output_format='Print four fields separated by spaces: name age grade fees.',
            examples=[
                {"input": "Ada\n21\nA\n90000", "output": "Ada 21 A 90000"},
                {"input": "Mia\n19\nB\n72000", "output": "Mia 19 B 72000"},
            ],
            tests=[
                {"input": "Raj\n22\nC\n61000", "output": "Raj 22 C 61000"},
                {"input": "Zoe\n18\nF\n8000", "output": "Zoe 18 F 8000"},
                {"input": "Leo\n30\nD\n41234", "output": "Leo 30 D 41234"},
            ],
        ),
        "day of week switch": _make_template(
            sample_input="3",
            expected_output="Wed",
            constraints="Day number must be integer 1-7 inclusive (1 = Mon … 7 = Sun).",
            input_format="One integer.",
            output_format="Print abbreviated weekday exactly: Mon Tue Wed Thu Fri Sat Sun",
            examples=[{"input": "1", "output": "Mon"}, {"input": "7", "output": "Sun"}],
            tests=[{"input": "4", "output": "Thu"}, {"input": "6", "output": "Sat"}, {"input": "2", "output": "Tue"}],
        ),
        "calculator switch menu": _make_template(
            sample_input="+\n4\n11",
            expected_output="15",
            constraints="Operator is single char + - * / on line 1; two integers total on next lines.",
            input_format="Line 1: op. Line 2: a. Line 3: b. Integer division for '/'.",
            output_format="Print integer result.",
            examples=[{"input": "-\n50\n38", "output": "12"}, {"input": "*\n3\n11", "output": "33"}],
            tests=[
                {"input": "+\n10\n5", "output": "15"},
                {"input": "/\n49\n7", "output": "7"},
                {"input": "*\n6\n7", "output": "42"},
            ],
        ),
        "read until zero sum": _make_template(
            sample_input="2\n12\n18\n20\n0",
            expected_output="52",
            constraints="Positive integers terminated by sentinel 0 on its own line. Sum excludes 0.",
            input_format="One integer per line; last line is 0 to stop reading.",
            output_format="Print sum of all integers before the line containing 0.",
            examples=[
                {"input": "5\n30\n50\n55\n0", "output": "140"},
                {"input": "2\n12\n18\n20\n0", "output": "52"},
            ],
            tests=[
                {"input": "1\n7\n9\n17\n0", "output": "17"},
                {"input": "3\n0", "output": "3"},
                {"input": "10\n20\n5\n0", "output": "35"},
            ],
        ),
        "prime check": _make_template(
            sample_input="7",
            expected_output="Prime",
            constraints="2 <= n <= 10^6",
            input_format="One integer n.",
            output_format='Print Prime or Not',
            examples=[{"input": "8", "output": "Not"}, {"input": "7", "output": "Prime"}],
            tests=[{"input": "2", "output": "Prime"}, {"input": "9", "output": "Not"}, {"input": "17", "output": "Prime"}],
        ),
        "leap year": _make_template(
            sample_input="2024",
            expected_output="Leap",
            constraints="1 <= year <= 10^9",
            input_format="One integer year.",
            output_format="Print Leap or Not",
            examples=[{"input": "2023", "output": "Not"}, {"input": "2024", "output": "Leap"}],
            tests=[{"input": "2000", "output": "Leap"}, {"input": "1900", "output": "Not"}, {"input": "1996", "output": "Leap"}],
        ),
        "simple interest": _make_template(
            sample_input="1000\n5\n2",
            expected_output="100",
            constraints="0 <= P,R,T <= 10^9; SI = (P*R*T)/100 using integer division.",
            input_format="Three lines: principal P, rate R, time T (all integers).",
            output_format="Print simple interest as integer.",
            examples=[{"input": "2000\n4\n3", "output": "240"}, {"input": "1000\n5\n2", "output": "100"}],
            tests=[{"input": "500\n10\n1", "output": "50"}, {"input": "1500\n8\n2", "output": "240"}, {"input": "9000\n0\n5", "output": "0"}],
        ),
        "print primes in range": _make_template(
            sample_input="5\n15",
            expected_output="5 7 11 13",
            constraints="1 <= lo <= hi <= 200",
            input_format="Two integers lo hi on one line.",
            output_format="Print all primes in [lo, hi] inclusive, space-separated, ascending.",
            examples=[{"input": "1\n10", "output": "2 3 5 7"}, {"input": "5\n15", "output": "5 7 11 13"}],
            tests=[{"input": "2\n2", "output": "2"}, {"input": "14\n18", "output": "17"}, {"input": "20\n30", "output": "23 29"}],
        ),
        "armstrong number check": _make_template(
            sample_input="153",
            expected_output="Yes",
            constraints="1 <= n <= 10^6",
            input_format="One integer n.",
            output_format="Print Yes or No if n is an Armstrong number.",
            examples=[{"input": "9474", "output": "Yes"}, {"input": "123", "output": "No"}],
            tests=[{"input": "1", "output": "Yes"}, {"input": "370", "output": "Yes"}, {"input": "200", "output": "No"}],
        ),
        "floyd triangle pattern": _make_template(
            sample_input="3",
            expected_output="1\n2 3\n4 5 6",
            constraints="1 <= n <= 30",
            input_format="One integer n (number of rows).",
            output_format="Floyd triangle: row i has i numbers, space-separated; rows separated by newline.",
            examples=[{"input": "2", "output": "1\n2 3"}, {"input": "3", "output": "1\n2 3\n4 5 6"}],
            tests=[{"input": "1", "output": "1"}, {"input": "4", "output": "1\n2 3\n4 5 6\n7 8 9 10"}, {"input": "3", "output": "1\n2 3\n4 5 6"}],
        ),
        "equilateral star pattern": _make_template(
            sample_input="4",
            expected_output="   *\n  * *\n * * *\n* * * *",
            constraints="1 <= n <= 20",
            input_format="One integer n (rows of centered star triangle).",
            output_format="Each row has leading spaces then stars separated by single space; pattern as sample.",
            examples=[
                {"input": "2", "output": " *\n* *"},
                {"input": "4", "output": "   *\n  * *\n * * *\n* * * *"},
            ],
            tests=[
                {"input": "1", "output": "*"},
                {"input": "3", "output": "  *\n * *\n* * *"},
                {"input": "4", "output": "   *\n  * *\n * * *\n* * * *"},
            ],
        ),
        "break on negative sum": _make_template(
            sample_input="3\n5\n8\n-2",
            expected_output="13",
            constraints="Read until first negative; sum only non-negative integers before it.",
            input_format="First line count n, then n integers one per line (last may be negative).",
            output_format="Print sum of values before first negative integer.",
            examples=[{"input": "2\n10\n-1", "output": "10"}, {"input": "3\n5\n8\n-2", "output": "13"}],
            tests=[
                {"input": "4\n1\n2\n3\n-9", "output": "6"},
                {"input": "1\n-5", "output": "0"},
                {"input": "5\n2\n2\n2\n2\n-1", "output": "8"},
            ],
        ),
        "iseven function loop": _make_template(
            sample_input="10",
            expected_output="2 4 6 8 10",
            constraints="1 <= n <= 10^4",
            input_format="One integer n.",
            output_format="Print all even numbers from 2 to n inclusive, space-separated.",
            examples=[{"input": "6", "output": "2 4 6"}, {"input": "10", "output": "2 4 6 8 10"}],
            tests=[{"input": "1", "output": ""}, {"input": "4", "output": "2 4"}, {"input": "12", "output": "2 4 6 8 10 12"}],
        ),
        "gcd euclidean": _make_template(
            sample_input="48\n18",
            expected_output="6",
            constraints="1 <= a,b <= 10^9",
            input_format="Two integers a b on separate lines.",
            output_format="Print GCD(a,b).",
            examples=[{"input": "100\n35", "output": "5"}, {"input": "48\n18", "output": "6"}],
            tests=[{"input": "7\n13", "output": "1"}, {"input": "54\n24", "output": "6"}, {"input": "17\n17", "output": "17"}],
        ),
        "lcm using gcd": _make_template(
            sample_input="4\n6",
            expected_output="12",
            constraints="1 <= a,b <= 10^6",
            input_format="Two integers a b on separate lines.",
            output_format="Print LCM(a,b) using LCM = a*b/GCD(a,b) with integer arithmetic.",
            examples=[{"input": "5\n7", "output": "35"}, {"input": "4\n6", "output": "12"}],
            tests=[{"input": "3\n9", "output": "9"}, {"input": "8\n12", "output": "24"}, {"input": "11\n13", "output": "143"}],
        ),
        "array reverse print": _make_template(
            sample_input="4\n1 2 3 4",
            expected_output="4 3 2 1",
            constraints="1 <= n <= 10^5",
            input_format="First line n, second line n integers.",
            output_format="Print elements in reverse order, space-separated.",
            examples=[{"input": "3\n9 8 7", "output": "7 8 9"}, {"input": "4\n1 2 3 4", "output": "4 3 2 1"}],
            tests=[{"input": "1\n42", "output": "42"}, {"input": "2\n0 5", "output": "5 0"}, {"input": "5\n1 1 2 3 5", "output": "5 3 2 1 1"}],
        ),
        "max min average array": _make_template(
            sample_input="4\n2 8 4 6",
            expected_output="8 2 5",
            constraints="1 <= n <= 10^5",
            input_format="First line n, second line n integers.",
            output_format="Print max min average as integers: average = floor(sum/n).",
            examples=[{"input": "3\n10 20 30", "output": "30 10 20"}, {"input": "4\n2 8 4 6", "output": "8 2 5"}],
            tests=[{"input": "1\n7", "output": "7 7 7"}, {"input": "2\n1 2", "output": "2 1 1"}, {"input": "5\n1 1 1 1 1", "output": "1 1 1"}],
        ),
        "second largest array": _make_template(
            sample_input="5\n3 9 9 1 4",
            expected_output="4",
            constraints="n >= 2; values fit 32-bit int.",
            input_format="First line n, second line n integers.",
            output_format=(
                "Print the largest value that is strictly less than the global maximum "
                "(ignore duplicate copies of the maximum)."
            ),
            examples=[{"input": "3\n5 5 3", "output": "3"}, {"input": "5\n3 9 9 1 4", "output": "4"}],
            tests=[
                {"input": "2\n1 2", "output": "1"},
                {"input": "4\n4 4 4 4", "output": "4"},
                {"input": "6\n10 20 8 15 9 22", "output": "20"},
                {"input": "3\n100 75 90", "output": "90"},
                {"input": "4\n-2 -10 -10 -100", "output": "-10"},
            ],
        ),
        "linear search array": _make_template(
            sample_input="5\n1 4 7 9 2\n7",
            expected_output="2",
            constraints="1 <= n <= 10^5",
            input_format="Line 1: n. Line 2: n integers. Line 3: target.",
            output_format="Print 0-based index of first occurrence, or -1 if not found.",
            examples=[{"input": "3\n5 5 3\n5", "output": "0"}, {"input": "5\n1 4 7 9 2\n7", "output": "2"}],
            tests=[
                {"input": "4\n8 8 8 8\n8", "output": "0"},
                {"input": "2\n1 2\n3", "output": "-1"},
                {"input": "1\n42\n42", "output": "0"},
            ],
        ),
        "matrix print 3x3": _make_template(
            sample_input="1 2 3\n4 5 6\n7 8 9",
            expected_output="1 2 3\n4 5 6\n7 8 9",
            constraints="Fixed 3x3 matrix.",
            input_format="Three lines, each with three integers.",
            output_format="Print matrix row-wise with spaces between numbers per row.",
            examples=[{"input": "0 0 0\n1 1 1\n2 2 2", "output": "0 0 0\n1 1 1\n2 2 2"}],
            tests=[
                {"input": "9 8 7\n6 5 4\n3 2 1", "output": "9 8 7\n6 5 4\n3 2 1"},
                {"input": "1 0 0\n0 1 0\n0 0 1", "output": "1 0 0\n0 1 0\n0 0 1"},
            ],
        ),
        "matrix row column sums": _make_template(
            sample_input="1 2 3\n4 5 6\n7 8 9",
            expected_output="6 15 24\n12 15 18",
            constraints="Fixed 3x3 matrix.",
            input_format="Three lines, each three integers.",
            output_format="Line 1: row sums space-separated. Line 2: column sums space-separated.",
            examples=[{"input": "1 1 1\n1 1 1\n1 1 1", "output": "3 3 3\n3 3 3"}],
            tests=[
                {"input": "1 2 3\n4 5 6\n7 8 9", "output": "6 15 24\n12 15 18"},
                {"input": "0 0 1\n0 1 0\n1 0 0", "output": "1 1 1\n1 1 1"},
            ],
        ),
        "matrix transpose": _make_template(
            sample_input="1 2 3\n4 5 6\n7 8 9",
            expected_output="1 4 7\n2 5 8\n3 6 9",
            constraints="Fixed 3x3 matrix.",
            input_format="Three lines, each three integers.",
            output_format="Print transpose (3 lines).",
            examples=[{"input": "1 0 0\n0 1 0\n0 0 1", "output": "1 0 0\n0 1 0\n0 0 1"}],
            tests=[
                {"input": "1 2 3\n0 0 0\n7 8 9", "output": "1 0 7\n2 0 8\n3 0 9"},
                {"input": "1 2 3\n4 5 6\n7 8 9", "output": "1 4 7\n2 5 8\n3 6 9"},
                {"input": "2 0 1\n0 3 0\n1 0 2", "output": "2 0 1\n0 3 0\n1 0 2"},
            ],
        ),
        "symmetric matrix check": _make_template(
            sample_input="1 2 3\n2 4 5\n3 5 6",
            expected_output="Yes",
            constraints="3x3 integer matrix.",
            input_format="Three lines, each three integers.",
            output_format="Print Yes if symmetric (A[i][j]==A[j][i]), else No.",
            examples=[{"input": "1 0 0\n0 1 0\n0 0 1", "output": "Yes"}],
            tests=[
                {"input": "1 0 0\n0 1 0\n0 0 1", "output": "Yes"},
                {"input": "1 2 3\n0 1 4\n5 6 0", "output": "No"},
                {"input": "1 2 3\n2 4 5\n3 5 6", "output": "Yes"},
            ],
        ),
        "count above average": _make_template(
            sample_input="5\n2 2 2 2 8",
            expected_output="1",
            constraints="1 <= n <= 10^5",
            input_format="Line 1: n. Line 2: n integers.",
            output_format=(
                "Count elements strictly greater than floor(average); average = floor(sum/n)."
            ),
            examples=[{"input": "4\n1 2 3 4", "output": "2"}, {"input": "5\n2 2 2 2 8", "output": "1"}],
            tests=[
                {"input": "3\n10 10 10", "output": "0"},
                {"input": "4\n9 10 11 100", "output": "1"},
                {"input": "2\n5 15", "output": "1"},
            ],
        ),
        "pascal triangle rows": _make_template(
            sample_input="3",
            expected_output="1\n1 1\n1 2 1",
            constraints="1 <= n <= 12",
            input_format="One integer n = number of rows.",
            output_format="Print Pascal triangle: row i has i integers, space-separated.",
            examples=[{"input": "4", "output": "1\n1 1\n1 2 1\n1 3 3 1"}, {"input": "3", "output": "1\n1 1\n1 2 1"}],
            tests=[{"input": "1", "output": "1"}, {"input": "2", "output": "1\n1 1"}, {"input": "5", "output": "1\n1 1\n1 2 1\n1 3 3 1\n1 4 6 4 1"}],
        ),
        "string length manual": _make_template(
            sample_input="coding",
            expected_output="6",
            constraints="1 <= length <= 1000; no newline in string.",
            input_format="Single line string (ASCII).",
            output_format="Print length without using strlen.",
            examples=[{"input": "hi", "output": "2"}],
            tests=[
                {"input": "abcd", "output": "4"},
                {"input": "race", "output": "4"},
                {"input": "z", "output": "1"},
            ],
        ),
        "concatenate without strcat": _make_template(
            sample_input="code\nlab",
            expected_output="codelab",
            constraints="Each token has no spaces; length each <= 200.",
            input_format="Line 1 string A; line 2 string B.",
            output_format="Print A+B exactly.",
            examples=[{"input": "ab\ncd", "output": "abcd"}, {"input": "hello\n!", "output": "hello!"}],
            tests=[
                {"input": "x\nyz", "output": "xyz"},
                {"input": "tree\nHouse", "output": "treeHouse"},
                {"input": "a\nb", "output": "ab"},
            ],
        ),
        "bubble sort array": _make_template(
            sample_input="4\n4 1 3 2",
            expected_output="1 2 3 4",
            constraints="1 <= n <= 500",
            input_format="Line 1: n. Line 2: n integers.",
            output_format="Print sorted ascending, space-separated (bubble sort / any stable O(n^2) ok).",
            examples=[{"input": "3\n9 1 5", "output": "1 5 9"}, {"input": "4\n4 1 3 2", "output": "1 2 3 4"}],
            tests=[
                {"input": "2\n2 1", "output": "1 2"},
                {"input": "5\n5 4 3 2 1", "output": "1 2 3 4 5"},
                {"input": "1\n7", "output": "7"},
            ],
        ),
        "palindrome number": _make_template(
            sample_input="121",
            expected_output="Yes",
            constraints="0 <= n <= 10^9",
            input_format="One integer n (no leading zeros except single 0).",
            output_format="Print Yes if decimal digits read same forward/backward, else No.",
            examples=[{"input": "123", "output": "No"}, {"input": "121", "output": "Yes"}],
            tests=[{"input": "0", "output": "Yes"}, {"input": "1221", "output": "Yes"}, {"input": "10", "output": "No"}],
        ),
        "strong number check": _make_template(
            sample_input="145",
            expected_output="Yes",
            constraints="1 <= n <= 10^6",
            input_format="One integer n.",
            output_format="Print Yes if sum of factorials of digits equals n, else No.",
            examples=[{"input": "145", "output": "Yes"}, {"input": "123", "output": "No"}],
            tests=[
                {"input": "1", "output": "Yes"},
                {"input": "2", "output": "Yes"},
                {"input": "146", "output": "No"},
            ],
        ),
        "count vowels consonants spaces": _make_template(
            sample_input="Hi there",
            expected_output="3 4 1",
            constraints="Input is a single line; letters A-Z a-z and spaces only.",
            input_format="One line: sentence.",
            output_format=(
                "Print three integers: vowels (aeiou AEIOU), consonants (other letters), spaces."
            ),
            examples=[{"input": "aeiou", "output": "5 0 0"}, {"input": "Hi there", "output": "3 4 1"}],
            tests=[
                {"input": "ABC", "output": "1 2 0"},
                {"input": "a b c", "output": "1 2 2"},
                {"input": "rhythm", "output": "0 6 0"},
            ],
        ),
    }

    template = templates.get(key)
    if not template:
        template = _make_template(
            sample_input="5",
            expected_output="5",
            constraints="Inputs follow the descriptions in Input format below.",
            input_format="Read input from standard input.",
            output_format="Print required output.",
            examples=[{"input": "5", "output": "5"}, {"input": "10", "output": "10"}],
            tests=[{"input": "1", "output": "1"}, {"input": "2", "output": "2"}, {"input": "3", "output": "3"}],
        )

    _apply_student_layer(template, key)

    template["description"] = (
        f"Solve a {module_name.lower()} coding task focused on '{topic}'.\n"
        f"Problem style: {example}. Read input from stdin and print exact output."
    )
    return template


def _apply_student_layer(template: dict, canonical_key: str) -> None:
    meta = STUDENT_METADATA.get(canonical_key)
    if meta:
        template["constraints"] = meta["constraints"]
        template["algorithm_hint"] = meta["algorithm"]
        template["functions_hint"] = meta["functions"]
    else:
        template["algorithm_hint"] = DEFAULT_ALGORITHM_FALLBACK
        template["functions_hint"] = DEFAULT_FUNCTIONS_FALLBACK


def _make_template(
    sample_input: str,
    expected_output: str,
    constraints: str,
    input_format: str,
    output_format: str,
    examples: list[dict[str, str]],
    tests: list[dict[str, str]],
) -> dict:
    return {
        "sample_input": sample_input,
        "expected_output": expected_output,
        "constraints": constraints,
        "input_format": input_format,
        "output_format": output_format,
        "examples_json": json.dumps(examples),
        "test_cases_json": json.dumps(tests),
    }
