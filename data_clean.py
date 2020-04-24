# -*- coding: utf-8 -*-
"""
Created on Thu Apr 23 21:28:13 2020

@author: Tang
"""
import re
import json

content = []
with open ('data/bigger_sample.json', "r", encoding="utf8") as f:
    Lines = f.readlines() 
    
    for l in Lines:
        a = json.loads(l)
        body = a['body']
        body = re.sub(r'http\S+', '', body)
        body = " ".join(filter(lambda x:x[0]!='$', body.split()))
        body = body.encode('ascii', 'ignore').decode('ascii')
        a['body'] = body
        content.append(a)
        
        
        
with open ('data/big_cleaned.json', 'w') as jf:
     json.dump(content, jf, indent=2)
        
        
# Reading from file 
#data = json.loads(f.read()) 
  
# Iterating through the json 
# list 
#for i in data['emp_details']: 
#    print(i) 
  
# Closing file 





