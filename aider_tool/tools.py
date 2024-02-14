from fileinput import filename
import os
from langchain.tools import tool
import sys
import openai
from aider.coders import Coder
from aider import models
from aider.repo import GitRepo
from aider.repomap import RepoMap, find_src_files
from aider.io import InputOutput


@tool("aider_files_tool")
def aider_files_tool(folder_path: str) -> str:
    """
    A tool to get a list of tracked files from the specified folder.

    Args:
        folder_path(str): The directory containing the files to list.

    Returns:
        str: A list of the files in the folder
    """
    #print(f"Searching {folder_path}")
    try:
        folder_path = os.path.abspath(os.path.join(os.curdir, 
                        folder_path.replace("'", "")))
        if not os.path.exists(folder_path):
            return f"Invalid folder path provided: {folder_path}"

        all_fnames = find_src_files(folder_path)
        repo = GitRepo(io=InputOutput(), git_dname=folder_path, 
                       aider_ignore_file=".aiderignore",
                       fnames=all_fnames)
        
        all_fnames = repo.get_tracked_files()
        
        return f"Available files:\n\n{all_fnames}"

    except Exception as error:
        return "There was an error searching the code.\n\n" + str(error)

@tool("aider_code_finder_tool")
def aider_code_finder_tool(filepath: str) -> str:
    """
    A tool get a summary of a file at the specified path. The summary
    will include details about functions and other code found in the file.

    Args:
        filepath (str): The path to a file to get the summary of.

    Returns:
        str: A summary of the code in the specified file including 
        function definitions and other details about the content.
    """
    #folder_path, query = filepath.split("|")
    folder_path = os.path.dirname(filepath)
    #print("\n\nSearching " + folder_path + "\n\nQuery: " + query)
    try:
        filepath = os.path.abspath(filepath)
        if not os.path.exists(filepath):
            return f"Invalid file path provided: {filepath}"

        client = openai.OpenAI(
            api_key=os.environ.get(
                "AIDER_OPENAI_API_KEY", os.environ["OPENAI_API_KEY"]
            ),
            base_url="http://localhost:8080/v1",
        )

        model_name = os.environ.get("AIDER_MODEL", "gpt-3.5-turbo")
        all_fnames = find_src_files(filepath)
        model = models.Model.create(model_name, client)
        repo = GitRepo(io=InputOutput(), git_dname=folder_path, 
                       aider_ignore_file=".aiderignore",
                       fnames=all_fnames)
        rm = RepoMap(root=folder_path, io=InputOutput(), verbose=True, main_model=model)
        
        all_fnames = repo.get_tracked_files()
        chat_fnames = [
           filename
        ]
       
        print(f"Found these files:\n{str(all_fnames)}")

        # # repo_map = rm.get_ranked_tags_map(chat_fnames, other_fnames=other_files)
        # # if repo_map is not None:
        # #     print(len(repo_map))

        # repo_map = rm.get_repo_map(chat_files=chat_fnames, other_files=all_fnames)
        # if repo_map is not None:
        #     print("MAP:\n\n")
        #     print(repo_map)

        # #print(rm.get_tags("../instagram_post/main.py", "../instagram_post/main.pyy"))

        ranked_tags = rm.get_ranked_tags_map(chat_fnames, other_fnames=all_fnames)
        #print("ranked\n\n" + ranked_tags)
        return "Matching Conent:\n\n" + str(ranked_tags)

    except Exception as error:
        return "There was an error searching the code.\n\n" + str(error)


@tool("aider_search_tool")
def aider_search_tool(folder_path_and_query: str) -> str:
    """
    A tool to ask questions about the code in a give folder path.

    Args:
        folder_path_and_query (str): The directory containing the code to query.

        This string should be in the format "<folder_path>|<query>".

    Returns:
        str: A list of relavant source files and code examples
    """
    folder_path, query = folder_path_and_query.split("|")
    print("\n\nSearching " + folder_path + "\n\nQuery: " + query)
    try:
        if not os.path.exists(folder_path):
            return "Invalid folder path provided"

        client = openai.OpenAI(
            api_key=os.environ.get(
                "AIDER_OPENAI_API_KEY", os.environ["OPENAI_API_KEY"]
            ),
            base_url="http://localhost:8080/v1",
        )

        model_name = os.environ.get("AIDER_MODEL", "gpt-3.5-turbo")
        all_fnames = find_src_files(folder_path)
        model = models.Model.create(model_name, client)
        repo = GitRepo(io=InputOutput(), git_dname=folder_path, 
                       aider_ignore_file=".aiderignore",
                       fnames=all_fnames)
        rm = RepoMap(root=folder_path, io=InputOutput(), verbose=True, main_model=model)
        
        all_fnames = repo.get_tracked_files()
        chat_fnames = [
            "../landing_page_generator/main.py",
            "../markdown_validator/MarkdownTools.py"
        ]
        other_files = [
            "../screenplay_writer/screenplay_writer.py",
            "../aider_tool/bad.py",
            "../aider_tool/tools.py",
            "../instagram_post/main.py",
            "../instagram_post/tasks.py",
        ]
        print(f"Found these files:\n{all_fnames}")

        # # repo_map = rm.get_ranked_tags_map(chat_fnames, other_fnames=other_files)
        # # if repo_map is not None:
        # #     print(len(repo_map))

        # repo_map = rm.get_repo_map(chat_files=chat_fnames, other_files=all_fnames)
        # if repo_map is not None:
        #     print("MAP:\n\n")
        #     print(repo_map)

        # #print(rm.get_tags("../instagram_post/main.py", "../instagram_post/main.pyy"))

        ranked_tags = rm.get_ranked_tags_map(chat_fnames, other_fnames=other_files)
        #print("ranked\n\n" + ranked_tags)
        return "Matching Conent:\n\n" + ranked_tags

    except Exception as error:
        return "There was an error searching the code.\n\n" + str(error)


@tool("aider_coder_tool")
def aider_coder_tool(file_path_and_instructions: str) -> str:
    """
    A tool to edit files based on the provided instructions.

    Parameters:
    - file_path_and_instructions:  The changes to make to the
    file and the path to the file to be edited.

    This string should be in the format "<file_path>|<instructions>".

    Returns:
    - result: The status of the edit.
    """

    file_path, instructions = file_path_and_instructions.split("|")

    print("\n\nEditing file...\n\n" + file_path)

    result = None
    try:
        client = openai.OpenAI(
            api_key=os.environ.get(
                "AIDER_OPENAI_API_KEY", os.environ["OPENAI_API_KEY"]
            ),
            base_url=os.environ.get(
                "AIDER_OPENAI_API_BASE_URL",
                os.environ.get("OPENAI_API_BASE_URL", "https://api.openai.com/v1"),
            ),
        )

        model_name = os.environ.get("AIDER_MODEL", "gpt-3.5-turbo")

        model = models.Model.create(model_name, client)
        # Create a Coder object with the file to be updated
        coder = Coder.create(
            client=client,
            main_model=model,
            fnames=[file_path],
            auto_commits=False,
            pretty=False,
            stream=False,
        )

        ## To make repo map work you most use a model that supports it
        ## may be possible to force it by setting model.use_repo_map = True
        map = coder.get_repo_map()
        files = coder.get_all_relative_files()
        msgs = coder.get_files_messages()
        print("######")
        print(map)
        print("######")
        print(files)
        print("######")
        print(msgs)
        print("######")

        # Execute the instructions on the file
        result = coder.run(instructions)
        # print(result)

        return result
    except Exception as this_exception:
        print(f"File Edit Exception: {this_exception}", file=sys.stderr)
        return f"""Final Answer: There was an error when 
            editing the file:\n\n {str(this_exception)}"""
