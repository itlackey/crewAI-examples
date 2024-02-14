from fileinput import filename
import sys
from crewai import Agent, Task, Crew, Process
import os
from dotenv import load_dotenv
from langchain.llms import Ollama
from tools import (
    aider_coder_tool,
    aider_search_tool,
    aider_code_finder_tool,
    aider_files_tool,
)

load_dotenv()


hermes_llm = Ollama(model="openhermes", temperature=0.9)
mistral = Ollama(model="starling-lm:7b-alpha-q8_0", temperature=0.6)
coder_llm = Ollama(model="codellama:7b", temperature=0.8)


def search_code(folder_path, query):
    """
    Use aider RepoMap to ask questions about the specified repo.

    Args:
        filename (str): The path to the repo to be queried.

    Returns:
        str: A response to your question about the code.

    """

    # Define the agents
    manager_agent = Agent(
        role="Manager",
        goal="""Provide details about the code that are useful to answer
        the question.""",
        backstory="""You are an expert code reviewer. You search through
        code repositories to find answers to questions.""",
        allow_delegation=True,
        verbose=True,
        tools=[],
        llm=mistral,
    )
    assistant_agent = Agent(
        role="Assistant",
        goal="""Provide details about the code that are useful to answer
        the question.""",
        backstory="""You are an expert code reviewer. You search through
        code repositories to find answers to questions.""",
        allow_delegation=False,
        verbose=True,
        tools=[ aider_files_tool, aider_code_finder_tool],
        llm=mistral,
    )
    code_agent = Agent(
        role="Coder",
        goal="""Use tools to examine code and answer questions for the manager.""",
        backstory="""You are an expert code reviewer. You search through
        code repositories to find answers to questions.""",
        allow_delegation=False,
        verbose=True,
        tools=[ aider_files_tool, aider_code_finder_tool],
        llm=mistral,
    )



    # define the tasks
    state_question = Task(description=f"""Give instructions to the team about
                          the goal of finding files in {folder_path} that may contain
                          content related to {query}""",
                          agent=manager_agent)
    
    get_file_list_task = Task(
        description=f"""Get a list of files from this folder: {folder_path}.

      Provide ONLY the list of files that are relavant in your response.
      DO NOT provide feedback or suggestions.
      It is VERY important that the final answer is ONLY the list of files.
      Like this:

      <FILE_LIST>
        [replace this with the list of files]
      </FILE_LIST>      
      """,
        agent=assistant_agent,
    )
    trim_file_list_task = Task(description=f"""Trim the list of files 
                               to files that may contain content related to 
                               {query}""",
                               agent=code_agent)
    
    # get_file_list_task2 = Task(
    #     description=f"""
		# 	Provide a list of files from this folder: {folder_path} that may 
    #   contain information about this question:
    #   {query}

    #   Provide ONLY the list of files that are relavant in your response.
    #   It is VERY important that the final answer is ONLY the list of files.

    #   Final Answer:
    #   <FILE_LIST>
    #   - path/to/file1
    #   - path/to/file2
    #   </FILE_LIST>      
    #   """,
    #     agent=general_agent,
    # )

    # summarize_files_task = Task(
    #     description=f"""
		# 	Review the content of each of the files list in previous tasks
    #   and provide notes about any code that may be related to the following question:
    #   {query}          
    #   """,
    #     agent=general_agent,
    # )

    # summary_task = Task(
    #     description="""Summaize the information that was found
    #                     by searching the code.""",
    #     agent=general_agent,
    # )

    file_edit_crew = Crew(
        tasks=[get_file_list_task,trim_file_list_task], #, summarize_files_task, summary_task],
        agents=[manager_agent,assistant_agent,code_agent],
        process=Process.sequential,
    )

    result = file_edit_crew.kickoff()

    return result


# If called directly from the command line take the first argument as the filename
if __name__ == "__main__":

    if len(sys.argv) > 1:
        query = sys.argv[1]
        filename = sys.argv[2] if len(sys.argv) >  2 else "."
        response = search_code(filename, query)
        print(response)
