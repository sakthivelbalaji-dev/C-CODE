# Student-facing guidance keyed like build_problem_content (after aliases).
# Constraints = plain-language input expectations (not judge-style bounds).
DEFAULT_ALGORITHM_FALLBACK = (
    "Follow the Input format like a checklist, compute the answer, "
    "then print using the Output format so every line matches the examples."
)
DEFAULT_FUNCTIONS_FALLBACK = (
    "#include <stdio.h> — use scanf / printf as needed; add loops (for, while) and if–else "
    "when the logic requires branching or repetition."
)

STUDENT_METADATA: dict[str, dict[str, str]] = {
    "print hello world": {
        "constraints": "This program runs without waiting for typed input.",
        "algorithm": "There is nothing to calculate; emit the exact required text once.",
        "functions": "`printf()` only may be enough. Optional: wrap in `int main()` and return 0.",
    },
    "add two numbers": {
        "constraints": "The user enters two ordinary integers.",
        "algorithm": "Read two values, compute their sum, print that integer.",
        "functions": "`scanf` with `%d` twice or once with two `%d`; `printf` to print sum.",
    },
    "swap two numbers": {
        "constraints": "Two integers arrive in order.",
        "algorithm": "Rewrite their positions so first printed value equals second input (use a temporary or arithmetic trick).",
        "functions": "Three variables or bitwise/arithmetic swap; use `scanf` / `printf`.",
    },
    "check even/odd": {
        "constraints": "One integer (can be negative or zero).",
        "algorithm": "If remainder modulo 2 is 0 → Even; else → Odd.",
        "functions": "Modulus `%`; `scanf` `%d`; `printf` literal words Even / Odd.",
    },
    "find largest of 3 numbers": {
        "constraints": "Three integers separated on one line (or consecutive reads).",
        "algorithm": "Compare pairwise (nested if–else or a small chain); keep the greatest.",
        "functions": "`if`/`else`; optional `scanf` three `%d`; one `printf` for winner.",
    },
    "grade calculator": {
        "constraints": "One mark from 0 to 100.",
        "algorithm": "Map ranges to letter grades A,B,C,D,F with clear cut-offs.",
        "functions": "`if`-`else if` ladder or concise comparisons; `%d`; print single letter.",
    },
    "print multiplication table": {
        "constraints": "One positive integer controlling the factor.",
        "algorithm": "Print first ten multiples separated by spaces (loop with counter).",
        "functions": "`for` loop; `printf` with space between numbers.",
    },
    "factorial of number": {
        "constraints": "Small non-negative integer n (factorial grows fast).",
        "algorithm": "Multiply 1 × 2 × … × n.",
        "functions": "`for` or `while`; start from 1; use `long long` if needed.",
    },
    "pattern printing": {
        "constraints": "One height n determines how many lines of stars.",
        "algorithm": "Outer loop = line; inner loop prints increasing star counts.",
        "functions": "Nested loops; nested `printf` or print `*` in inner loop.",
    },
    "find sum of array": {
        "constraints": "First n, then exactly n integers on the next input line.",
        "algorithm": "Read into array or accumulate while reading; add all elements.",
        "functions": "Array `[MAX]` plus loop; `%d`; running sum variable.",
    },
    "largest element": {
        "constraints": "n then n integers.",
        "algorithm": "Track current maximum while scanning the array.",
        "functions": "`for` scan; conditional updates; `%d`; print winner.",
    },
    "matrix addition": {
        "constraints": "Dimensions plus two matrices stacked in stdin order.",
        "algorithm": "For each row/column index, add matching cells.",
        "functions": "Nested loops; 2-D arrays `[r][c]`; store then print.",
    },
    "reverse a string": {
        "constraints": "One word/token without spaces (matching how the checker reads input).",
        "algorithm": "Walk from both ends swapping, or iterate backward building output.",
        "functions": "`char[]`; indexing; `%s` or `%c` loops; optionally `strlen` if allowed.",
    },
    "check palindrome": {
        "constraints": "One string with no gaps.",
        "algorithm": "Compare character at i with symmetric position n−1−i.",
        "functions": "`for`/`while`; `%s`; print Yes / No literals.",
    },
    "count vowels": {
        "constraints": "One line mix of uppercase/lowercase letters.",
        "algorithm": "Loop each letter; tally if vowel-set member.",
        "functions": "`switch`/`if`; `toupper`/`tolower` optional; single integer print.",
    },
    "factorial using function": {
        "constraints": "Same as factorial puzzle but enforce your own helper.",
        "algorithm": "Define `fact(n)` recursion or loop; print `fact(read_n)`.",
        "functions": "User-defined function; prototype + definition; `%d`.",
    },
    "fibonacci series": {
        "constraints": "Count of terms to emit.",
        "algorithm": "Start 0 and 1 (or variants per statement); derive next iteratively.",
        "functions": "`for`; two variables swapping previous terms; spaced `printf`.",
    },
    "sum using recursion": {
        "constraints": "One positive integer n.",
        "algorithm": "`sum(n)` = `n + sum(n−1)` with base small n.",
        "functions": "Recursive helper; beware stack for large n.",
    },
    "swap using pointers": {
        "constraints": "Two integers as usual swap problem.",
        "algorithm": "`swap(int *a, int *b)` dereference and interchange.",
        "functions": "`int *`; passing addresses `&x`, `&y`; `*` and temp.",
    },
    "access array using pointer": {
        "constraints": "Length plus list of ints.",
        "algorithm": "`p` traverses contiguous memory till n elements summed.",
        "functions": "`int *p = arr` then `*(p+i)` increments.",
    },
    "pointer to pointer": {
        "constraints": "One integer echoed conceptually.",
        "algorithm": "Chain pointers so final dereference retrieves original.",
        "functions": "`**` idioms minimal; pedagogical dereference ladder.",
    },
    "student record system": {
        "constraints": "Count then lines formatted name + integer age.",
        "algorithm": "Read each tuple; print echoed lines row wise.",
        "functions": "`%s %d`; loop over students.",
    },
    "employee details": {
        "constraints": "Count then lines with id integer and name.",
        "algorithm": "Read & print sequentially.",
        "functions": "`%d %s` pairing in loop.",
    },
    "product inventory record": {
        "constraints": "Count then product code strings with quantity.",
        "algorithm": "Loop each SKU line; replicate input as output ordering.",
        "functions": "`%s %d` scans; deterministic printing.",
    },
    "write data to file": {
        "constraints": "Single textual line echoed (simulates file write).",
        "algorithm": "Read line; identical print for judge simulation.",
        "functions": "`fgets`/`scanf` `%[^\n]`; `printf`; real `fopen` optional.",
    },
    "read file content": {
        "constraints": "One line echoed as-if read from disk.",
        "algorithm": "Input passthrough unchanged.",
        "functions": "`printf` entire buffer.",
    },
    "copy file": {
        "constraints": "One line echoed as duplicated output.",
        "algorithm": "No transform; verbatim copy semantics.",
        "functions": "Same as stdin echo drills.",
    },
    "print name and city": {
        "constraints": "You get two answers the user typed: first the name word, second the city word — each alone on its line.",
        "algorithm": "Read line 1, read line 2, print exactly the same order on two separate lines.",
        "functions": "Two `%s` reads with `scanf` or two narrow `fgets` strips newline; exactly two `printf` lines.",
    },
    "read name and age greeting": {
        "constraints": "Person gives one word nickname, then a normal human age.",
        "algorithm": 'Build one sentence literally like: Hello <name>, you are <age> years old.',
        "functions": "`char name[]`; `scanf(\"%s%d\", …)` plus `printf`; mind comma placement.",
    },
    "read character ascii": {
        "constraints": "One visible character keyed by user.",
        "algorithm": "Cast or print integer form of signed/unsigned char semantics.",
        "functions": "`getchar()` / `scanf(\" %c\", &ch)`; cast `(int)`; `%d`.",
    },
    "read float decimal places": {
        "constraints": "One fractional number shown with decimal digits.",
        "algorithm": "Format same numeric value thrice widths 2 then 4 then 6 after decimal.",
        "functions": "`printf` width/precision modifiers or `sprintf`/`snprintf`; read `double` `%lf`.",
    },
    "print data type sizes lab": {
        "constraints": "No input values (lab assumes fixed widths for grading).",
        "algorithm": "Emit four ints matching sizeof rules described in lectures.",
        "functions": "`sizeof(int)` typed printout; spaced integers.",
    },
    "print simple box border": {
        "constraints": "Border size decides rows/columns counts for hollow square artwork.",
        "algorithm": "First/last rows all stars; middle rows stars with interior spaces.",
        "functions": "Double loop; `%c` repeats or stitched `printf` each row newline.",
    },
    "student record variables": {
        "constraints": "Four separate answers: word name, numeric age, one letter grade, tuition digits.",
        "algorithm": "Read four lines in order — echo them spaced on one formatted output line.",
        "functions": "Mix `%s` `%d` `%c`; watch whitespace newline handling.",
    },
    "day of week switch": {
        "constraints": "Integer 1..7 referencing weekday numbering from handout.",
        "algorithm": "`switch`/cases map day index to abbreviated label.",
        "functions": "`switch`; `scanf` `%d`; `printf` abbreviated names.",
    },
    "calculator switch menu": {
        "constraints": "Operator letter then two operands lines.",
        "algorithm": "`switch(operator)` computes + − * /. Integer-divide semantics as stated.",
        "functions": "`%c`; optional space skip; `%d` pairs; beware newline before char read.",
    },
    "read until zero sum": {
        "constraints": "User enters positive steps line-by-line stopping at sentinel line reading zero.",
        "algorithm": "Accumulate totals until encountering exactly zero sentinel line exiting loop.",
        "functions": "`while` reading `%d`; break or condition with sum accumulator.",
    },
    "prime check": {
        "constraints": "One integer roughly ≥2 check primality semantics.",
        "algorithm": "Test divisibility by integers upto sqrt heuristic or trial division.",
        "functions": "`for` divides; modulus tests; literals Prime / Not output.",
    },
    "leap year": {
        "constraints": "One calendar year typed.",
        "algorithm": "Divisibility by 400 /100 /4 Gregorian rules condensed.",
        "functions": "`if` ladders; Booleans combos; Leap / Not strings.",
    },
    "simple interest": {
        "constraints": "Three integers Principal Rate Time whole numbers.",
        "algorithm": "`SI = Principal*Rate*Time/100` integer division semantics per spec.",
        "functions": "`long long` if wide multiplies avoiding overflow.",
    },
    "print primes in range": {
        "constraints": "Two bounds lo and hi on one line (space-separated), inclusive range.",
        "algorithm": "Double loop or sieve-like walk printing ascending primes spaced.",
        "functions": "`is_prime` helper function recommended; `%d spaced`.",
    },
    "armstrong number check": {
        "constraints": "One integer verifying digit-power property.",
        "algorithm": "Count digits duplicate value split digits powering sums compare original.",
        "functions": "`while digit extract`; `pow`/manual multiply loop; Yes/No print.",
    },
    "floyd triangle pattern": {
        "constraints": "Height rows grows consecutive integers pattern.",
        "algorithm": "`counter++` increments each printed cell nesting row column loops.",
        "functions": "Nested loops; spaces between ints same row newline between rows.",
    },
    "equilateral star pattern": {
        "constraints": "Same spacing rule for every row: row r uses (n-1-r) spaces then r+1 stars with single spaces between stars; no trailing spaces.",
        "algorithm": "Per row: pad with spaces, then join r+1 stars with ' * ' pattern ending with last star—no space after it.",
        "functions": "`for` rows; inner loop prints stars; `printf` careful spacing.",
    },
    "break on negative sum": {
        "constraints": "Count prefixed then sequence entries until negative sentinel occurs.",
        "algorithm": "Add positives strictly before first negative skipping negative itself.",
        "functions": "`for`/`while`; break semantics; tally.",
    },
    "is even function loop": {
        "constraints": "Upper bound counting evens inclusively downward.",
        "algorithm": "`if (!(i%2))` collect even sequence from 2..n spaced.",
        "functions": "Helper `unsigned isEven_like` conceptual or inline check.",
    },
    "gcd euclidean": {
        "constraints": "Two positive integers on one line (space-separated), same as typical scanf pair input.",
        "algorithm": "`while(b){ r=a%b;a=b;b=r;} ` classic swap.",
        "functions": "`%` loop; iterative not necessarily recursion.",
    },
    "lcm using gcd": {
        "constraints": "Two integers on one line (space-separated).",
        "algorithm": "`LCM=a*b/GCD(a,b)` after computing gcd reliably.",
        "functions": "`long long`; divide after multiply carefully ordering.",
    },
    "array reverse print": {
        "constraints": "`n` then list length n ints.",
        "algorithm": "Index from last-to-first printing sequentially.",
        "functions": "`for (i=n-1; i>=0; i--)` and array storage.",
    },
    "max min average array": {
        "constraints": "`n` then n ints manageable array sizes.",
        "algorithm": "One pass trackers min/max and sum aggregator floor average.",
        "functions": "`/` integer division nuances; spaced triple print.",
    },
    "second largest array": {
        "constraints": "At least length two ints; duplicates allowed.",
        "algorithm": "Find global max M; then scan for the largest value < M. If none exists (all equal), print M.",
        "functions": "Two-pass or sort; `%d`; condition `< max`.",
    },
    "linear search array": {
        "constraints": "Array listing plus target finder.",
        "algorithm": "Linear scan earliest index equality else −1 sentinel.",
        "functions": "`for i` compare `arr[i]`; integer index print `-1 absent`.",
    },
    "matrix print 3x3": {
        "constraints": "Exactly nine ints row major three lines typed.",
        "algorithm": "Mirror reading row ordering printing mirrored layout.",
        "functions": "`int m[3][3]` loops row col.",
    },
    "matrix row column sums": {
        "constraints": "`3 × 3` numeric grid unchanged.",
        "algorithm": "Row sums scanning columns; transpose-like column accumulators separately.",
        "functions": "`for` nesting plus secondary accumulators lines.",
    },
    "matrix transpose": {
        "constraints": "`3 × 3` square matrix.",
        "algorithm": "`out[j][i]=in[i][j]` mapping.",
        "functions": "`i j` swaps indexes printing three lines.",
    },
    "symmetric matrix check": {
        "constraints": "`3 × 3` ints.",
        "algorithm": "`A[i][j]==A[j][i]` all ordered pairs symmetrical property.",
        "functions": "`for` doubly nested comparators booleans degrade Yes/No quick.",
    },
    "count above average": {
        "constraints": "Array ints general distribution.",
        "algorithm": "`avg=floor(sum/n)` tally strictly exceeding threshold.",
        "functions": "`sum` accumulating two-pass or store array then second pass tally.",
    },
    "pascal triangle rows": {
        "constraints": "`n` rows modest combinator growth.",
        "algorithm": "`C(n,k)` recurrence triangular addition neighbor parents rule.",
        "functions": "`arr[i][j]=arr[i-1][j-1]+arr[i-1][j]` base ones edges.",
    },
    "string length manual": {
        "constraints": "Non-empty string without embedded newline simplifying scanner.",
        "algorithm": "`len=0; while(str[len]) ++len ;` iterative.",
        "functions": "`char[]`; forbid `strlen` verifying spec.",
    },
    "concatenate without strcat": {
        "constraints": "Two textual tokens sequentially lines.",
        "algorithm": "`dest[i++]=src` manual copy both segments.",
        "functions": "`char out[]`; cursor index append loop.",
    },
    "bubble sort array": {
        "constraints": "`n` moderate sortable ints.",
        "algorithm": "`n-1 passes` adjacent swap until stable sorted ascending.",
        "functions": "Nested loops flag optional micro optimization unstoppable ok.",
    },
    "palindrome number": {
        "constraints": "Integer decimal digit symmetry checking.",
        "algorithm": "`reverse_digits` accumulator compare originals.",
        "functions": "`while n>0 remainder build reversed`.",
    },
    "strong number check": {
        "constraints": "Integer moderate digit factorial property.",
        "algorithm": "`digit factorial sum` reused small helper facts precompute maybe.",
        "functions": "`switch` factorial micro function per digit aggregator.",
    },
    "count vowels consonants spaces": {
        "constraints": "One sentence letters spaces only simplifying classification.",
        "algorithm": "`if vowel tally else consonant tally else space increment`.",
        "functions": "`isalpha`/`isspace` optional manual classification triple integers output.",
    },
}
