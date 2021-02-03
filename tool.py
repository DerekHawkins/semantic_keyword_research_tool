
### Import Libraries ###

import urllib
import requests
import pandas as pd
from tqdm.notebook import tqdm
from urllib.parse import urlparse

### Load API Key
api_key = ''
service_url = 'https://api.semrush.com'


### Function used to monitor credit use for SEMrush API
def credits_remaining():
    url = "http://www.semrush.com/users/countapiunits.html?key="
    url += api_key
    call = requests.get(url)
    response = call.json()
    api_credits = response
    return print("Program Complete. You have", api_credits, "API credits remaining")

def build_seo_urls(phrase):
    params = {
        "?type": "phrase_organic",
        'key': api_key,
        'phrase': term,
        'database': 'us', # change for different market
        'display_limit': '10',
        }
    data = urllib.parse.urlencode(params, doseq=True)
    main_call = urllib.parse.urljoin(service_url, data)
    main_call = main_call.replace(r'%3F', r'?')

    return main_call
  
def parse_response(call_data):
        results = []
        data = call_data.decode('unicode_escape')
        lines = data.split('\r\n')
        lines = list(filter(bool, lines))
        columns = lines[0].split(';')

        for line in lines[1:]:
            result = {}
            for i, datum in enumerate(line.split(';')):
                result[columns[i]] = datum.strip('"\n\r\t')
            results.append(result)

        return results

def url_org(i_urls):
    params = {
        "?type": "url_organic",
        'key': api_key,
        'url': i_urls,
        'database': 'us', # change for different market
        'display_filter': '+|Po|Lt|11'
    }
    data = urllib.parse.urlencode(params, doseq=True)
    main_call = urllib.parse.urljoin(service_url, data)
    main_call = main_call.replace(r'%3F', r'?')
    return main_call    

def secondary_layer(crawl_urls):
    keyword_frame = []
    for urls in crawl_urls:
        url_call = url_org(i_urls=urls)
        url_response = requests.get(url_call)
        url_final = parse_response(call_data=url_response.content)
        df2 = pd.DataFrame(url_final)
        df2 = df2.drop(columns=['Number of Results', 'Timestamp', 'Traffic (%)', 'Traffic Cost (%)', 'Trends'])
        df2 = df2[['Keyword', 'Search Volume', 'Position', 'CPC', 'SERP Features', 'Competition']]
        df2['Top'] = df2['Position'].astype(int).between(0,10, inclusive=True)
        df_top = df2[df2.Top.astype(str).str.contains("True")]
        keyword_frame.append(df_top)
    second_layer = pd.concat(keyword_frame)
    second_layer['Search Volume'] = second_layer['Search Volume'].astype(int)
    second_layer = second_layer.sort_values(by='Search Volume', ascending=False)
    second_layer = second_layer.drop(columns=['Top'])
    return second_layer

def third_layer_setup(second_layer_kw):
    third_layer_result = keyword_list['Keyword'].value_counts()
    third_layer_data = pd.DataFrame(third_layer_result)
    third_layer_data['Occurance'] = third_layer_data['Keyword']
    third_layer_data['Keyword'] = third_layer_data.index
    third_layer_data = third_layer_data.reset_index(drop=True)
    third_layer_data['Top'] = third_layer_data['Occurance'].astype(int).between(0,10, inclusive=True)
    final_data = third_layer_data[third_layer_data.Top.astype(str).str.contains("True")]
    final_data = final_data.drop(columns=['Top'])
    return final_data

term = input('What keyword would you like to explore?')
df1 = pd.DataFrame(parse_response(requests.get(build_seo_urls(phrase=term)).content))

try:
    keyword_list = secondary_layer(crawl_urls=df1['Url'])
except KeyError as e:
    raise Exception("The keyword you have inputted is either not in SEMrush's database or your input was incorrectly submitted. Please rerun and try again.")
    
third_layer = third_layer_setup(second_layer_kw=keyword_list)
third_layer = third_layer.merge(keyword_list[['Keyword','Search Volume', 'CPC', 'Competition']], on="Keyword", how='left')
third_layer = third_layer.sort_values(by='Occurance', ascending=False)
third_layer.drop_duplicates(inplace=True)
third_layer = third_layer.reset_index(drop=True)
third_layer = third_layer[['Keyword', 'Search Volume', 'CPC', 'Competition', 'Occurance']]
third_layer['Competition'] = third_layer['Competition'].astype(float)

# Document how many keywords were found
print(f'There were {third_layer.shape[0]} relevant keywords collected.')
credits_remaining()
third_layer.to_csv(f'{term}.csv', index=False)
