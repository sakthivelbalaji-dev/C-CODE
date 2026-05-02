from app.database import SessionLocal
from app.models import Question
from app.question_content import build_problem_content

# Structure aligned with "C Foundation -- Updated.pdf" — five phases plus topics/examples from the syllabus.
SYLLABUS_MODULES = [
    {
        "module": "Phase 1 — Foundation",
        "topics": [
            "Introduction to C",
            "Structure of a C Program",
            "Keywords and Identifiers",
            "Variables",
            "Data Types",
            "Constants",
            "Header Files",
            "Input and Output (printf, scanf)",
            "Compilation process",
        ],
        "examples": [
            "Print Hello World",
            "Print name and city",
            "Add two numbers",
            "Swap without third variable",
            "Read name and age greeting",
            "Read character ASCII",
            "Read float decimal places",
            "Print data type sizes lab",
            "Print simple box border",
            "Student record variables",
        ],
    },
    {
        "module": "Phase 2 — Logic Building & Flow Control",
        "topics": [
            "Arithmetic, Relational, Logical, Assignment",
            "Increment and Decrement operators",
            "Conditional Statements (if, else, switch)",
            "Loops (for, while, do-while)",
            "Jump statements (break, continue, goto)",
        ],
        "examples": [
            "Check even/odd",
            "Find largest of 3 numbers",
            "Grade calculator",
            "Day of week switch",
            "Calculator switch menu",
            "Print multiplication table",
            "Read until zero sum",
            "Prime check",
            "Leap year",
            "Simple interest",
        ],
    },
    {
        "module": "Phase 3 — Functions",
        "topics": [
            "Function declaration, definition, and call",
            "Call by value and call by reference",
            "Using functions for primes, powers, factorial, gcd, lcm",
        ],
        "examples": [
            "Print primes in range",
            "Armstrong number check",
            "Floyd triangle pattern",
            "Equilateral star pattern",
            "Break on negative sum",
            "isEven function loop",
            "gcd euclidean",
            "lcm using gcd",
            "Recursive factorial",
            "Fibonacci series",
        ],
    },
    {
        "module": "Phase 4 — Data Collections",
        "topics": [
            "One-dimensional arrays",
            "Two-dimensional arrays (matrices)",
            "Strings basics and manipulation",
        ],
        "examples": [
            "Array reverse print",
            "Max min average array",
            "Second largest array",
            "Linear search array",
            "Matrix print 3x3",
            "Matrix row column sums",
            "Matrix addition 3x3",
            "Matrix transpose",
            "Symmetric matrix check",
            "Count above average",
        ],
    },
    {
        "module": "Phase 5 — Problem Practice",
        "topics": [
            "Mixed array, matrix, string, and number-theory drills",
            "Patterns, sorts, palindromes, gcd/lcm bundles",
        ],
        "examples": [
            "Pascal triangle rows",
            "String length manual",
            "Reverse a string",
            "Check palindrome",
            "Count vowels consonants spaces",
            "Concatenate without strcat",
            "Bubble sort array",
            "Palindrome number",
            "Strong number check",
            "Right angle star pattern",
        ],
    },
]

MIN_QUESTIONS_PER_MODULE = 10


def build_question_payload(module_name: str, topics: list[str], examples: list[str], index: int) -> dict:
    topic = topics[index % len(topics)]
    example = examples[index % len(examples)]

    title = f"{module_name} Practice {index + 1}: {example}"
    content = build_problem_content(module_name, topic, example)

    return {
        "title": title,
        "description": content["description"],
        "module": module_name,
        "input_format": content["input_format"],
        "output_format": content["output_format"],
        "constraints": content["constraints"],
        "algorithm_hint": content.get("algorithm_hint"),
        "functions_hint": content.get("functions_hint"),
        "sample_input": content["sample_input"],
        "expected_output": content["expected_output"],
        "examples_json": content["examples_json"],
        "test_cases_json": content["test_cases_json"],
    }


def seed_questions() -> None:
    db = SessionLocal()
    try:
        for module_info in SYLLABUS_MODULES:
            module_name = module_info["module"]
            topics = module_info["topics"]
            examples = module_info["examples"]

            existing_questions = db.query(Question).filter(Question.module == module_name).all()
            existing_titles = {question.title for question in existing_questions}
            current_count = len(existing_questions)

            if current_count >= MIN_QUESTIONS_PER_MODULE:
                print(f"{module_name}: already has {current_count} questions")
                continue

            to_add = MIN_QUESTIONS_PER_MODULE - current_count
            generated = 0
            index = 0
            while generated < to_add:
                payload = build_question_payload(module_name, topics, examples, index)
                index += 1
                if payload["title"] in existing_titles:
                    continue

                db.add(Question(**payload))
                existing_titles.add(payload["title"])
                generated += 1

            db.commit()
            final_count = db.query(Question).filter(Question.module == module_name).count()
            print(f"{module_name}: added {generated}, total {final_count}")

        print("\nFinal module counts:")
        for module_info in SYLLABUS_MODULES:
            module_name = module_info["module"]
            count = db.query(Question).filter(Question.module == module_name).count()
            print(f"- {module_name}: {count}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_questions()
