import json

from collections import OrderedDict


def read_config(file):

    with open(file, 'r') as input_file:
                
             input_data = input_file.readlines()
                
    ############# ignore the comments in single line #############  

    for i in range(len(input_data)):
                
             input_data[i] = input_data[i].split('#')[0]
                    
    ############# ignore the comments in multiple lines ############# 

    input_data=''.join(input_data)
                                
    input_datas = input_data.split('**')                
                
    for i in range((len(input_datas)-1)/2):
                
             input_datas[1+2*i] = ''
                
    input_data=''.join(input_datas) 
                
    ############# reverse the feature to hide modules ############# 
                
    data_info = json.loads(input_data, object_pairs_hook=OrderedDict)
    
    
    return data_info
                
