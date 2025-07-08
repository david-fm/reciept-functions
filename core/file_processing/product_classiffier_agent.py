from langgraph.constants import START, END
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict
from pydantic import BaseModel
from typing import List, Tuple, Annotated
from langchain_google_vertexai import ChatVertexAI
from langchain_core.messages import HumanMessage, SystemMessage

import os

from .categories import CategoryLoader, CategoriesData, Category
from core.config import settings


class State(TypedDict):
    """
    A state in the state graph.
    """
    product: str
    category: str
    subcategory: str
    selected_categories_subcategories: Annotated[List[Tuple[str,
                                                            str]], lambda old, new: new]
    available_categories: CategoriesData


class SelectedCategories(BaseModel):
    """Selected categories for the product classification.

    Args:
        categories (List[str]): List of selected categories.
    """
    categories: List[str]


class SelectedSubCategory(BaseModel):
    subcategory: str


class SelectedCategory(BaseModel):
    category: str


llm = ChatVertexAI(
    model_name=settings.VERTEXAI_MODEL_NAME,
    temperature=0)
structured_llm_categories = llm.with_structured_output(SelectedCategories)
structured_llm_subcategories = llm.with_structured_output(SelectedSubCategory)
structured_llm_category = llm.with_structured_output(SelectedCategory)


def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Calculates the Levenshtein distance between two strings.
    The Levenshtein distance is the minimum number of single-character edits
    (insertions, deletions or substitutions) required to change one word into the other.

    Args:
        s1 (str): The first string.
        s2 (str): The second string.

    Returns:
        int: The Levenshtein distance between s1 and s2.
    """
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)

    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def tree_edit_similarity_search(input_list: list[str], search_string: str) -> str | None:
    """
    Performs a similarity search within a list of strings using Levenshtein distance
    (a form of edit distance) and returns the most similar element.

    Args:
        input_list (list[str]): A list of strings to search within.
        search_string (str): The string to find the most similar element for.

    Returns:
        str | None: The element from the input_list that is most similar to the
                    search_string, or None if the input_list is empty.
    """
    if not input_list:
        return None

    # Initialize with a very large distance and no best match
    min_distance = float('inf')
    most_similar_element = None

    # Iterate through each element in the list
    for element in input_list:
        # Calculate the Levenshtein distance between the current element and the search string
        distance = levenshtein_distance(element, search_string)

        # If this distance is less than the current minimum, update the minimum
        # and store the current element as the most similar
        if distance < min_distance:
            min_distance = distance
            most_similar_element = element
        elif distance == min_distance:
            # If distances are equal, you might want to add a tie-breaking rule.
            # For now, we'll just stick with the first one found that matches the min.
            pass

    return most_similar_element

def initial_classiffication(state: State):
    """
    Make the initial classification of the product.
    """

    response = structured_llm_categories.invoke(
        [
            SystemMessage(
                content=f"You are part of a team which task is to classify the product into its category. Your task in this team is to select the top 3 categories related to the product given by the user.\nThe categories are: {str(state['available_categories'])}"
            ),
            HumanMessage(
                content=state["product"]
            )
        ]
    )
    # print(f"Response categories: {response}")
    real_categories = []
    for category in response.categories:
        # Check if the category is in the available categories
        if category in state["available_categories"].categories:
            real_categories.append(category)
        else:
            # If not, find the most similar category using Levenshtein distance
            similar_category = tree_edit_similarity_search(
                [c.name for c in state["available_categories"].categories], category)
            if similar_category:
                real_categories.append(similar_category)
    # If we have more than 3 categories, take only the first 3
    if len(real_categories) > 3:
        real_categories = real_categories[:3]

    selected_categories_subcategories = [(r, '') for r in real_categories]
    return {"selected_categories_subcategories": selected_categories_subcategories}


def select_subcategories(state: State):
    """
    Select the subcategories of the product
    """
    def get_subcategories(state: State, category: str):
        categories_data: CategoriesData = state["available_categories"]
        iterator = filter(lambda x: x.name == category,
                          categories_data.categories)
        category: Category = next(iterator)

        return category.subcategories

    response = structured_llm_subcategories.batch([
        [SystemMessage(
            content=f"You are part of a team which task is to classify the product into its category. Your task in this team is to select the subcategory of the product given the user's.\nThe subcategories are: {get_subcategories(state, category)}"
        ),
            HumanMessage(
            content=state["product"]
        )
        ]
        for category, _ in state["selected_categories_subcategories"]
    ])

    selected_categories_subcategories = []
    for i, res in enumerate(response):
        selected_categories_subcategories.append(
            (state["selected_categories_subcategories"][i][0],
             res.subcategory))
    return {"selected_categories_subcategories": selected_categories_subcategories}


def final_classification(state: State):

    def to_string_selected_cat_subcat(state: State):
        string = ""
        for cat, subcat in state["selected_categories_subcategories"]:
            string += f"\n- Category: {cat}"

        return string

    def get_subcategory(state: State, category: str):
        iterator = filter(lambda x: x[0] == category,
                          state["selected_categories_subcategories"])
        category, subcategory = next(iterator)

        return subcategory

    response = structured_llm_category.invoke(
        [
            SystemMessage(
                content=f"You are part of a team which task is to classify the product into its category. Your task in this team is to select the best category related to the product given by the user.\nThe categories and their subcategories selected by your partners are: {to_string_selected_cat_subcat(state)}"
            ),
            HumanMessage(
                content=state["product"]
            )
        ]
    )

    category = response.category
    subcategory = get_subcategory(state, category)

    return {"category": category, "subcategory": subcategory}


def build_graph():
    """
    Build the state graph for the product classifier agent.
    """

    graph = StateGraph(State)

    graph.add_node("initial_classification", initial_classiffication)
    graph.add_node("select_subcategories", select_subcategories)
    graph.add_node("final_classification", final_classification)

    graph.add_edge(START, "initial_classification")
    graph.add_edge("initial_classification", "select_subcategories")
    graph.add_edge("select_subcategories", "final_classification")
    graph.add_edge("final_classification", END)

    return graph.compile()
