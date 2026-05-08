#I DIVIDED THE ASSIGNMENT SECTIONS INTO TASKS MYSELF TO FOLLOW THE SAME PATTERN OF 
#THE PREVIOUS ASSIGNMENTS FSOR ORGANIZATION PURPOSES.

#TASK 1.1: Reflexion-Based Self-Healing Code Fixer Agent


import os                         
import operator                    #for Annotated reducer in state
import subprocess                  #to run code in isolated subprocess
import tempfile                    #to create temp files for code execution
import re                          #regex for extracting code blocks from LLM output
from typing import Annotated, TypedDict  #type hints for LangGraph state

from dotenv import load_dotenv    
from langchain_groq import ChatGroq  #Groq LLM 
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage  #message types
from langgraph.graph import StateGraph, END  #LangGraph graph builder and terminal node

load_dotenv()  


# TASK 1.2: State Definition
# All fields are explicit so nodes don't have to parse message history and look for specific info hence keeps node logic simple and focused on its own task

class AgentState(TypedDict):
    buggy_code: str          #the original broken function 
    current_code: str        #latest fix produced by the generator
    test_code: str           #the test suite to run against the fix
    test_output: str         #most recent test execution result
    iteration: int           #how many fix attempts have been made so far
    max_iterations: int      #to prevent infinite loops
    passed: bool             #True when all tests pass (extra field i added)
    messages: Annotated[list, operator.add]  #LLM conversation history (append only insted of replacing)


# #TASK 1.3: run_tests Tool (programmatic, no LLM because its  cheaper and faster and just as effective when the feedback is based on the direct observation so theres nothing the LLM can reason about))
# Executes candidate code + test suite in an isolated subprocess just incase something fails and with timeout to prevent looping forever
# Returns a dict with passed (True or False for the test passing), stdout (everything the program printed nornally), stderr (everything program printed as an error),
# returncode (to indicate whether or not the program exited normally)


def run_tests(code: str, tests: str) -> dict:
    """Runs candidate code against test suite in a isolated subprocess"""
    #combine the candidate code and tests into one runnable script
    script = code + "\n\n" + tests + '\nprint("ALL TESTS PASSED")\n'

    #write to temp file 
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(script)
        path = f.name
    #file is now closed (required before another process can read it)

    try:
        import sys
        result = subprocess.run(
            [sys.executable, path],
            capture_output=True,
            text=True,
            encoding="utf-8",      #explicit encoding prevents Windows related issues
            timeout=10
        )
        passed = "ALL TESTS PASSED" in result.stdout
        return {
            "passed": passed,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"passed": False, "stdout": "", "stderr": "TIMEOUT", "returncode": -1}
    except Exception as e:
        return {"passed": False, "stdout": "", "stderr": str(e), "returncode": -1}
    finally:
        os.unlink(path)



# #TASK 1.4: LLM Setup

def get_llm():
    """Instantiates the Groq LLM"""
    return ChatGroq(
        model="llama-3.3-70b-versatile",   
        temperature=0,                       #deterministic output for code fixing since e dont want any randomness
        groq_api_key=os.environ.get("GROQ_API_KEY"),
    )


def extract_code(text: str) -> str:
    """
    Extracts Python code out of the LLM response.
    If theres ```python``` fences theyre removed else
    the raw text if no fences are found
    """
    #look for a ```python ... ``` block
    match = re.search(r"```python\s*(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()  #return only the code inside the fences
    #try a plain ``` block
    match = re.search(r"```\s*(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()  #no fences found, treat whole response as code



# #TASK 1.5: Generator Node (the LLM itself)
# gives a fix for the current code 

def generator_node(state: AgentState) -> dict:
    """
    Generator: asks the LLM to produce a corrected version of current_code
    On iteration 0 it uses the original buggy_code as the starting point
    On following iterations it passes the previous candidate + test failures.
    """
    llm = get_llm()

    #system prompt that frames the task for the LLM
    system_prompt = SystemMessage(content=(
        "You are an expert Python programmer. "
        "Your ONLY job is to fix the buggy Python function provided. "
        "Return ONLY the corrected function inside a ```python ... ``` block. "
        "Do NOT include test code, explanations, or anything else outside the block."
    ))

    iteration = state["iteration"]  #current attempt number

    if iteration == 0:
        #first attempt: start from the original buggy code
        user_msg = HumanMessage(content=(
            f"Fix this buggy Python function so it passes all the tests.\n\n"
            f"Buggy code:\n```python\n{state['buggy_code']}\n```\n\n"
            f"Tests that must pass:\n```python\n{state['test_code']}\n```\n\n"
            f"Return only the fixed function in a ```python``` block."
        ))
    else:
        #following attempts: pass the last candidate and its failure output
        user_msg = HumanMessage(content=(
            f"Your previous fix did NOT pass all tests.\n\n"
            f"Current (broken) code:\n```python\n{state['current_code']}\n```\n\n"
            f"Test output (errors/failures):\n{state['test_output']}\n\n"
            f"Tests that must pass:\n```python\n{state['test_code']}\n```\n\n"
            f"Please fix the code. Return only the corrected function in a ```python``` block."
        ))

    print(f"\n{'='*60}")
    print(f"[GENERATOR] Iteration {iteration + 1} — requesting fix from LLM...")

    #call the LLM with the accumulated message history + new user message
    response = llm.invoke([system_prompt] + state["messages"] + [user_msg])

    #extract only the Python code from the response
    fixed_code = extract_code(response.content)

    print(f"[GENERATOR] Received candidate code ({len(fixed_code)} chars)")

    #update state: add the new messages and store extracted code
    return {
        "messages": [user_msg, AIMessage(content=response.content)],
        "current_code": fixed_code,
        "iteration": iteration + 1,   #increment the attempt counter
    }


# #TASK 1.6: run_tests Node (programmatic, no LLM same reason as its tool)
# puts the run_tests tool as a LangGraph node to be in the actual graph


def run_tests_node(state: AgentState) -> dict:
    """
    Executes the current candidate code against the test suite
    Stores the result so the critic node can look at it 
    """
    print(f"[RUN_TESTS] Executing candidate code against test suite...")

    #call the isolated runner
    result = run_tests(state["current_code"], state["test_code"])

    #readable summary of the run
    if result["passed"]:
        output_summary = "ALL TESTS PASSED"
        print(f"[RUN_TESTS] All tests passed!")
    else:
        #combine stderr and stdout so the critic and generator see the full picture
        output_summary = ""
        if result["stderr"]:
            output_summary += f"STDERR:\n{result['stderr']}\n"
        if result["stdout"] and result["stdout"] != "\n":
            output_summary += f"STDOUT:\n{result['stdout']}\n"
        if not output_summary:
            output_summary = f"Return code: {result['returncode']}"
        print(f"[RUN_TESTS] Tests failed. Output:\n{output_summary}")

    return {
        "test_output": output_summary,  #store for critic and next generator call
        "passed": result["passed"],     #boolean flag for routing
    }



# TASK 1.7: Critic Node (programmatic)
# test execution is already direct and not subjective
# An LLM critic just adds tokens and latency with no need
# the generator node already receives the full failure output so the critic's job is not reasoning

def critic_node(state: AgentState) -> dict:
    """
    Critic: decides whether to loop back to the generator or end
    logic:
      If tests passed creates a trace message and set passed=True and go to END.
      If budget finished creates a trace message and go to END
      else go back to generator
    """
    iteration = state["iteration"]        #attempts used so far
    max_iter = state["max_iterations"]    #budget cap
    passed = state["passed"]             #if the last run passed

    print(f"\n[CRITIC] Iteration {iteration}/{max_iter} — passed={passed}")

    if passed:
        print("[CRITIC] All tests pass — routing to END.")
        #append a trace message so the conversation history shows the decision
        return {
            "messages": [HumanMessage(content=f"[CRITIC] Tests passed on iteration {iteration}. Terminating.")]
        }

    if iteration >= max_iter:
        print(f"[CRITIC] Budget exhausted ({iteration}/{max_iter}) — routing to END.")
        return {
            "messages": [HumanMessage(content=f"[CRITIC] Budget exhausted after {iteration} iterations. Terminating.")]
        }

    print(f"[CRITIC] Tests failed, budget remains — routing back to generator.")
    return {
        "messages": [HumanMessage(content=f"[CRITIC] Iteration {iteration} failed. Retrying (budget: {iteration}/{max_iter}).")]
    }


# #TASK 1.8: Conditional Edge: critic decides whats the next node

def should_continue(state: AgentState) -> str:
    """
    Edge function called after critic_node.
    Returns 'generator' to loop or 'end' to terminate.
    This is what LangGraph uses to route the graph.
    """
    if state["passed"]:
        return "end"                           #tests passed, we're done
    if state["iteration"] >= state["max_iterations"]:
        return "end"                           #budget exhausted, we're done
    return "generator"                         #keep trying


# #TASK 1.9: Build the LangGraph Graph
# flow: generator then run_tests then critic then (END or generator)

def build_graph():
    """Assemble and compile the Reflexion agent graph."""
    graph = StateGraph(AgentState)  #create a graph with our custom state

    #add the three nodes
    graph.add_node("generator", generator_node)
    graph.add_node("run_tests", run_tests_node)
    graph.add_node("critic", critic_node)

    #linear edges: generator always goes to run_tests, run_tests always goes to critic
    graph.add_edge("generator", "run_tests")
    graph.add_edge("run_tests", "critic")

    #conditional edge from critic: loop or end
    graph.add_conditional_edges(
        "critic",
        should_continue,         #the routing function
        {
            "generator": "generator",  #map return value "generator" to the generator node
            "end": END,                #map return value "end" to the terminal node
        }
    )

    graph.set_entry_point("generator")  #start at the generator node

    return graph.compile()  #compile into a runnable graph


#TASK 1.10: run_agent() (public API that will be called by evaluate.py to run the agent on each problem)

def run_agent(buggy_code: str, test_code: str, max_iterations: int = 5) -> dict:
    """
    Runs the Reflexion agent on a single buggy function
    Has:
        buggy_code:      The broken Python function as a string
        test_code:       The test suite as a string
        max_iterations:  Maximum number of fix attempts 

    Returns a dict with:
        final_code      - the last candidate produced (fixed or best attempt)
        passed          - True if all tests pass
        iterations      - number of LLM calls made
        trace           - the message history showing every attempt
        test_output     - the final test run output
    """
    app = build_graph()  #compile the graph

    #initial state: set all fields explicitly
    initial_state: AgentState = {
        "buggy_code": buggy_code,
        "current_code": buggy_code,    #start with the broken code
        "test_code": test_code,
        "test_output": "",             #no test results yet
        "iteration": 0,                #no attempts yet
        "max_iterations": max_iterations,
        "passed": False,               #assume failing until proven otherwise
        "messages": [],                #empty conversation history
    }

    print(f"\n{'#'*60}")
    print(f"# Starting Reflexion Agent (budget: {max_iterations} iterations)")
    print(f"{'#'*60}")

    #invoke the graph, LangGraph runs nodes until END is reached
    final_state = app.invoke(initial_state)

    return {
        "final_code": final_state["current_code"],
        "passed": final_state["passed"],
        "iterations": final_state["iteration"],
        "trace": final_state["messages"],
        "test_output": final_state["test_output"],
    }


# TASK 1.11: self-test when run directly (extra)

if __name__ == "__main__":
    #verify run_tests works before involving the LLM 
    print("=== Verifying run_tests tool (no LLM) ===")
    sanity = run_tests("def add(a, b): return a + b", "assert add(2, 3) == 5")
    assert sanity["passed"], "run_tests sanity check failed!"
    print(" run_tests sanity check passed.\n")

    #run the agent on the example given in the asg
    buggy = "def add(a, b):\n    return a - b"
    tests = (
        "assert add(2, 3) == 5\n"
        "assert add(0, 0) == 0\n"
        "assert add(-1, 1) == 0"
    )

    result = run_agent(buggy, tests, max_iterations=5)

    print(f"\n{'='*60}")
    print("RESULT SUMMARY")
    print(f"{'='*60}")
    print(f"Passed:     {result['passed']}")
    print(f"Iterations: {result['iterations']}")
    print(f"Final code:\n{result['final_code']}")
    print(f"\nFull trace ({len(result['trace'])} messages):")
    for i, msg in enumerate(result["trace"]):
        print(f"  [{i}] {type(msg).__name__}: {str(msg.content)[:120]}")


# TASK 1.12: Budget Cap Test (max_iterations=1)
# Confirms the iteration cap actually fires 

print("\n=== Testing budget cap (max_iterations=1) ===")
cap_result = run_agent(
    buggy_code="def add(a, b): return a - b",  #broken code
    test_code="assert add(2, 3) == 5",          #test to run
    max_iterations=1                             #hard cap of 1 iteration
)
assert cap_result["iterations"] <= 1, "Budget cap did not fire!"  #confirm it stopped at 1
print(f"Budget cap test passed — agent stopped after {cap_result['iterations']} iteration(s)")