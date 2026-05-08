
#TASK 3.1: Evaluation 
#Runs the Reflexion agent against all 5 benchmark problems
#gets pass/fail, iterations used, LLM calls made and time
#gives a summary table to stdout and saves results.csv 


import time     #for timing
import csv      #for saving results.csv
import sys      #for path manipulation

sys.path.insert(0, ".")            #to ensure local modules are available

from fixer import run_agent        #the Reflexion agent
from benchmark import PROBLEMS     #the 5 buggy problems



MAX_ITERATIONS = 5   #budget for each problem (matches assignment example)


# #TASK 3.2: Runs each problem and gets metrics

def evaluate_all(problems: list, max_iterations: int = MAX_ITERATIONS) -> list:
    """
    Iterates over each problem, run the agent, and collects metrics
    Returns a list of result dicts.
    """
    results = []   #accumulate one dict per problem

    for idx, problem in enumerate(problems):
        print(f"\n{'='*70}")
        print(f"PROBLEM {idx+1}/{len(problems)}: {problem['name']}")
        print(f"  Bug type:   {problem['bug_type']}")
        print(f"  Difficulty: {problem['expected_difficulty']}")
        print(f"  Notes:      {problem['notes'][:100]}...")
        print(f"{'='*70}")

        start_time = time.time()   #start timing before the agent is invoked

        try:
            #run the Reflexion agent on this problem
            agent_result = run_agent(
                buggy_code=problem["buggy_code"],
                test_code=problem["test_code"],
                max_iterations=max_iterations,
            )
            wall_time = time.time() - start_time   #measure seconds

            #LLM calls == iterations (one LLM call per generator node activation)
            llm_calls = agent_result["iterations"]

            result = {
                "problem":      problem["name"],
                "bug_type":     problem["bug_type"],
                "difficulty":   problem["expected_difficulty"],
                "passed":       agent_result["passed"],
                "iterations":   agent_result["iterations"],
                "llm_calls":    llm_calls,
                "wall_time_s":  round(wall_time, 2),
                "final_code":   agent_result["final_code"],
                "test_output":  agent_result["test_output"],
                "trace_length": len(agent_result["trace"]),
                "error":        None,
            }

        except Exception as e:
            #if the agent itself crashes, record the error and move on
            wall_time = time.time() - start_time
            print(f"[EVALUATE] Agent raised an exception: {e}")
            result = {
                "problem":      problem["name"],
                "bug_type":     problem["bug_type"],
                "difficulty":   problem["expected_difficulty"],
                "passed":       False,
                "iterations":   0,
                "llm_calls":    0,
                "wall_time_s":  round(wall_time, 2),
                "final_code":   "",
                "test_output":  str(e),
                "trace_length": 0,
                "error":        str(e),
            }

        results.append(result)

        #print a per problem summary immediately we can follow along
        status_icon = "PASS" if result["passed"] else "FAIL"
        print(f"\n[RESULT] {status_icon} | iterations={result['iterations']} | "
              f"llm_calls={result['llm_calls']} | time={result['wall_time_s']}s")

    return results


# TASK 3.4: the summary table


def print_table(results: list):
   
    col_w = [30, 12, 10, 8, 10, 9, 9]   #column widths for alignment

    header = (
        f"{'Problem':<{col_w[0]}} "
        f"{'Bug Type':<{col_w[1]}} "
        f"{'Difficulty':<{col_w[2]}} "
        f"{'Passed':<{col_w[3]}} "
        f"{'Iterations':<{col_w[4]}} "
        f"{'LLM Calls':<{col_w[5]}} "
        f"{'Time (s)':<{col_w[6]}}"
    )
    divider = "-" * len(header)

    print(f"\n{'='*len(header)}")
    print("EVALUATION SUMMARY")
    print(f"{'='*len(header)}")
    print(header)
    print(divider)

    passes = 0
    total_iters = 0
    total_calls = 0
    total_time  = 0.0

    for r in results:
        passed_str = "PASS" if r["passed"] else "FAIL"
        if r["passed"]:
            passes += 1
        total_iters += r["iterations"]
        total_calls += r["llm_calls"]
        total_time  += r["wall_time_s"]

        print(
            f"{r['problem']:<{col_w[0]}} "
            f"{r['bug_type']:<{col_w[1]}} "
            f"{r['difficulty']:<{col_w[2]}} "
            f"{passed_str:<{col_w[3]}} "
            f"{r['iterations']:<{col_w[4]}} "
            f"{r['llm_calls']:<{col_w[5]}} "
            f"{r['wall_time_s']:<{col_w[6]}}"
        )

    print(divider)
    print(f"\nSummary: {passes}/{len(results)} passed | "
          f"total iterations={total_iters} | total LLM calls={total_calls} | "
          f"total time={round(total_time, 2)}s")


#TASK 3.5: Save results.csv

def save_csv(results: list, path: str = "results.csv"):
    #define which fields go into the CSV (exclude full code and trace for readability)
    fieldnames = [
        "problem", "bug_type", "difficulty",
        "passed", "iterations", "llm_calls",
        "wall_time_s", "trace_length", "error"
    ]

    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()     #write the header row
        writer.writerows(results)  #write one row per problem

    print(f"\n[EVALUATE] Results saved to {path}")


# #TASK 3.6: final code and trace for each problem

def print_traces(results: list):
    """Print the final fixed code and message trace for each problem."""
    print(f"\n\n{'#'*70}")
    print("# DETAILED TRACES")
    print(f"{'#'*70}")

    for r in results:
        print(f"\n{'='*70}")
        print(f"PROBLEM: {r['problem']} — {'PASS' if r['passed'] else 'FAIL'}")
        print(f"Final code:\n{r['final_code']}")
        print(f"\nFinal test output:\n{r['test_output']}")


# #TASK 3.7: entry point

if __name__ == "__main__":

    print("****Reflexion Agent Evaluation, All 5 Problems****")
    print(f"Budget per problem: {MAX_ITERATIONS} iterations\n")

    #run all problems and collect metrics
    results = evaluate_all(PROBLEMS, max_iterations=MAX_ITERATIONS)

    #display the summary table
    print_table(results)

    #save to CSV
    save_csv(results, "results.csv")

    #print detailed traces
    print_traces(results)

    print("\n[EVALUATE] Done.")