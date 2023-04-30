import os
import openai
openai.organization = "org-LsKW391027OdGGA07kr2YFsi"
openai.api_key = "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"
print(openai.Model.list())


curl https://api.openai.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer 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" \
  -d '{
     "model": "gpt-3.5-turbo",
     "messages": [{"role": "user", "content": "Say this is a test!"}],
     "temperature": 0.7
   }