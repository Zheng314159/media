import os
os.environ["HTTP_PROXY"] = "http://127.0.0.1:1081"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:1081"
from deep_translator import GoogleTranslator
print(GoogleTranslator(source='zh-CN', target='en').translate('世界这么美好我想去看看'))