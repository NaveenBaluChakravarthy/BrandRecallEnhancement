# Imports
import os
import json
import openai
import pandas as pd


# Setup

c_root = 'content/drive/MyDrive/CommentAnalyzer'

def load_config():
    config = json.load(open(f'{c_root}/config.json'))
    openai.api_key = config['conf_openai_api_key0']
    openai.api_type = config['conf_openai_api_type']
    openai.api_version = config['conf_openai_api_vers']
    openai.api_base = config['conf_openai_api_base']
    return config


# Helper Functions

def get_data():
    df = pd.read_excel(f'{c_root}/comments.xlsx', sheet_name = 'ad_001')
    return df[['comment']]


def get_function_template():
    info_struct = [
        {
            "name": "extract_info",
            "description": "understand the intent of the comment",
            "parameters":
            {
                "type": "object",
                "properties":
                {
                    "ad_product": {
                        "type": "string",
                        "description": "the good or bad experience discussed"
                        },
                    "ad_execute": {
                        "type": "string",
                        "description": "opinion on the advertisement execution in less than 3 words"
                        },
                    "ad_message": {
                        "type": "string",
                        "description": "message conveyed by the comment summarized in less than 3 words"
                        },
                    "ad_emotion": {
                        "type": "string",
                        "description": "general emotion conveyed by the comment in less than 2 words"
                        }
                }
            }
        }
    ]
    return info_struct


def get_message_template():

    message_struct = [
        {
            "role": "system",
            "content": "You are very skilled in extracting vital information from a comment on an advertisement."
            },
        {
            "role": "user",
            "content": f"Here is a comment on a product advertisement - {comment}"
            },
        ]
    return message_struct



# Driver

conf_params = load_config()
comments_analysis = pd.DataFrame()
data = get_data()

for idx, comment in data.itertuples():
    response = openai.ChatCompletion.create(
        temperature = 0.0,
        engine = conf_params['conf_openai_engine'],
        messages = get_message_template(),
        functions = get_function_template(),
        function_call = {"name": "extract_info"}
    )

    arguments = response["choices"][0]["message"]["function_call"]["arguments"]
    json_response = json.loads(arguments)
    json_response.update({"comment": comment})

    temp_df = pd.DataFrame(json_response, index = [0])
    comments_analysis = pd.concat([comments_analysis, temp_df], axis = 0, ignore_index = True)


comments_analysis.to_excel(f"{c_root}/comments_analysis.xlsx", sheet_name = "AnalyzedComments", index = False)