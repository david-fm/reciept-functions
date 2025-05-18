from langgraph.constants import START, END
from langgraph.graph import StateGraph,START, END
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
    selected_categories_subcategories: Annotated[List[Tuple[str, str]], lambda old, new: new]
    available_categories: CategoriesData

class SelectedCategories(BaseModel):
    categories: List[str]

class SelectedSubCategory(BaseModel):
    subcategory: str

class SelectedCategory(BaseModel):
    category: str
llm = ChatVertexAI(model_name=settings.VERTEXAI_MODEL_NAME, temperature=0)    
structured_llm_categories = llm.with_structured_output(SelectedCategories)
structured_llm_subcategories = llm.with_structured_output(SelectedSubCategory)
structured_llm_category = llm.with_structured_output(SelectedCategory)

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
    selected_categories_subcategories = [(r,'') for r in response.categories]
    return {"selected_categories_subcategories": selected_categories_subcategories}

def select_subcategories(state: State):
    """
    Select the subcategories of the product
    """
    def get_subcategories(state: State, category: str):
        categories_data: CategoriesData = state["available_categories"]
        iterator = filter(lambda x: x.name == category,categories_data.categories)
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
            string += f"\n- Category: {cat}, Subcategory: {subcat}"
        
        return string
    
    def get_subcategory(state: State, category: str):
        iterator = filter(lambda x: x[0] == category, state["selected_categories_subcategories"])
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