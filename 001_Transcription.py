# Imports

import re
import json
import openai
import pandas as pd
import soundfile as sf
import whisper


# Configuration
model = whisper.load_model("large")
with open('config.json', 'r') as json_file:
    config = json.load(json_file)
	

# Helper Functions	

def get_transcription(audiofile):
    if audiofile[0:2] in ['na', 'uk']:
        whisper_result = model.transcribe(audiofile, fp16 = False)
        original = whisper_result["text"]
        english = whisper_result["text"]
    else:
        whisper_result = model.transcribe(audiofile, fp16 = False)
        original = whisper_result["text"]
        whisper_result = model.transcribe(audiofile, fp16 = False, task = 'translate')
        english = whisper_result["text"]
    return {'original': original, 'english': english}


def get_audio_duration(audiofile):
    f = sf.SoundFile(audiofile)
    audio_duration = int((f.frames / f.samplerate) // 1)
    return audio_duration


def get_llm_response(transcript):

    conversation = [
        {"role": "system", "content": "You are a market expert who can identify the pros and cons of a product from a text."},
        {"role": "user", "content": f"""Understand the following transcript and extract the following items 
                                        [brand, sub-brand, benefits, problems, product category].
                                        When looking for benefits and problems, consider only those arising out of use of the product.  
                                        Here is the text : {transcript}
                                        Present only the results in a neat JSON format. Always use lists when representing the values.
                                        Bargain detergents are competing products. So ignore the problems and benefits of competing products.
                                        Take a deep breath. Let us solve this rationally.
                                        """}
    ]

    openai.api_key = config['api_key']
    results = openai.Completion.create(
        engine = config['model_name'],
        max_tokens = 200
    )

    response = results['choices'][0]['text'].strip()

    return response


def type_correction(resp):
    for value in ['brand', 'sub_brand', 'product_category', 'benefits', 'problems']:
        x = resp[value]
        if x:
            if type(x) == str:
                resp[value] = [x]
        else:
            resp[value] = ''

    for value in ['benefits', 'problems']:
        resp[f'{value}_count'] = len(resp[value])
        resp[value] = ', '.join(resp[value])

    return resp


def wordcounter(text, word):
    text = re.sub('[^A-Za-z0-9]', ' ', text)
    text = re.sub('\s+', ' ', text)
    words_list = [x.strip() for x in text.split()]
    return words_list.count(word)


def brand_subbrand_correction():
    for brand in corrected_llm_resp['brand']:
        list_of_counts = []
        count = wordcounter(whisper_response['english'], brand)
        list_of_counts.append(count)
        corrected_llm_resp[f'brand_count'] = list_of_counts

    for sub_brand in corrected_llm_resp['sub_brand']:
        list_of_counts = []
        count = wordcounter(whisper_response['english'], sub_brand)
        list_of_counts.append(count)
        corrected_llm_resp[f'sub_brand_count'] = list_of_counts
		

# Driver
files_list = ['de_001.mp3', 'ph_001.mp3', 'ph_002.mp3', 'ph_003.mp3', 'de_002.mp3', 'de_003.mp3', 'ksa_002.mp3', 'ja_001.mp3']

all_responses = []

for filename in files_list:
    whisper_response = get_transcription(filename)

    llm_response = get_llm_response(whisper_response['english'])
    corrected_llm_resp = type_correction(llm_response)
    brand_subbrand_correction()

    corrected_llm_resp['original'] = whisper_response['original'].strip()
    corrected_llm_resp['english'] = whisper_response['english'].strip()
    corrected_llm_resp['duration'] = get_audio_duration(filename)
    corrected_llm_resp['filename'] = filename
    all_responses.append(corrected_llm_resp)
    print(filename)		
		

# Export


df = pd.DataFrame()
for resp in all_responses:
    tdf = pd.DataFrame.from_records(resp, index = [0])
    df = pd.concat([df, tdf], axis = 0, ignore_index = True)
df.to_csv('transcript_extract.csv', index = False)