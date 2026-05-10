/**
 * Aligned with "C Foundation -- Updated.pdf" — five phases (Foundation through Problem Practice).
 * Marks total 56 to match the previous syllabus weighting used in the UI.
 */
export const syllabusModules = [
  {
    id: 1,
    title: 'Phase 1 — Foundation',
    marks: 12,
    topics: [
      'Introduction to C / Hello World / Program structure',
      'Keywords, identifiers, variables',
      'Data types and constants',
      'Header files',
      'Input and output (printf, scanf)',
      'Compilation process',
    ],
    examples: [
      'Print your name and city on two separate lines',
      'Print a simple box border using * characters',
      'Hello World with single-line and multi-line comments explaining each line',
      'Five valid vs five invalid variable names (with explanations)',
      "Student record: name, age, grade, fees — appropriate types",
      'Swap two integers without a third variable',
      'Print an uninitialized variable and explain the observation',
    ],
  },
  {
    id: 2,
    title: 'Phase 2 — Logic Building & Flow Control',
    marks: 12,
    topics: [
      'Operators: arithmetic, relational, logical, assignment, increment/decrement',
      'Conditional statements: if, if-else, nested if, switch',
      'Loops: for, while, do-while',
      'Jump statements: break, continue, goto',
    ],
    examples: [
      'Variables of basic types int, float, double, char; sizeof() demo',
      'PI constant circle area; #define constants vs magic numbers',
      'Read name & age greeting; arithmetic on two integers',
      'Float formatting (2 / 4 / 6 decimals); ASCII of a character',
      'Marks table formatting; digit extract with / and % ; simple interest; automorphic number',
      'Ranges, vowels, leap year; positive / negative / zero; grades if-else if',
      'Largest of three nested if; weekday switch (1–7); calculator menu (switch)',
      'Loops: 1 to 100, multiplication table; sum integers until sentinel 0; prime check',
    ],
  },
  {
    id: 3,
    title: 'Phase 3 — Functions',
    marks: 11,
    topics: [
      'Function declaration, definition, and call',
      'Call by value and call by reference',
      'Using functions with loops and number-theory drills from the handbook',
    ],
    examples: [
      'Prime numbers between 1 and 50',
      'Perfect numbers; Armstrong checks and Armstrong numbers up to 1000',
      "Floyd's triangle",
      'Equilateral spaced-star pattern',
      'Right-angle star pattern nested loops',
      'Continue / break drills (skip multiples of 3, negative stop, divisible by 6 and 8)',
      'isEven(); power(base,exp) without pow(); isPrime(); factorial recursive vs iterative',
      'calculator(float a, float b, char op)',
      'gcd (Euclidean) and lcm via gcd — test multiple pairs',
    ],
  },
  {
    id: 4,
    title: 'Phase 4 — Data Collections',
    marks: 11,
    topics: ['One-dimensional arrays', 'Two-dimensional arrays (matrices)', 'Strings'],
    examples: [
      'Reverse 10 integers in an array',
      'Maximum, minimum, and average',
      'Elements greater than average; second-largest',
      'Linear search (index or not found)',
      '3×3 matrix print',
      'Row sums and column sums',
      'Add two matrices',
      'Matrix transpose and symmetric check',
      "Pascal's triangle to N rows",
      'String length without strlen; reverse; palindrome',
      'Vowels, consonants, spaces in a sentence',
      'Concatenate without strcat()',
    ],
  },
  {
    id: 5,
    title: 'Phase 5 — Problem Practice (Hard problems & doubt clearing)',
    marks: 10,
    topics: [
      'Mixed review: arrays, matrices, strings, and number theory',
      'Reusing factorial, isPrime, gcd/lcm in larger problems',
    ],
    examples: [
      'isStrong(n) reusing factorial (e.g. 145)',
      'Sum and product of all matrix elements',
      'Fibonacci iterative and recursive',
      'All Armstrong up to 1000; strong up to 10000; perfect up to 1000',
      'GCD and LCM of a list of numbers',
      "Pascal's triangle with proper formatting",
      'Primes in a range using isPrime()',
      'Palindrome for numbers and strings',
      'Bubble sort an array',
    ],
  },
]

export const totalMarks = syllabusModules.reduce((sum, item) => sum + item.marks, 0)
