# This is a temporary solution

import deep_translator


class BaseTranslator():
    languages = {
        'english': 'en', 
        'japanese': 'ja', 
        'korean': 'ko', 
        'russian': 'ru',
        'chinese (simplified)': 'zh-CN', 
        'chinese (traditional)': 'zh-TW',
    }

class GoogleTranslator(BaseTranslator, deep_translator.GoogleTranslator):
    
    def __init__(self, source, target):
        super(GoogleTranslator, self).__init__(
            source = self.languages[source.lower()],
            target = self.languages[target.lower()]
        )
        
        
class MicrosoftTranslator(BaseTranslator, deep_translator.MicrosoftTranslator):
    
    def __init__(self, source, target):
        super(MicrosoftTranslator, self).__init__(
            source = self.languages[source.lower()],
            target = self.languages[target.lower()]
        )
    
        
class DeeplTranslator(BaseTranslator, deep_translator.DeeplTranslator):
    
    def __init__(self, source, target):
        super(DeeplTranslator, self).__init__(
            source = self.languages[source.lower()],
            target = self.languages[target.lower()]
        )
        
        
class BaiduTranslator(BaseTranslator, deep_translator.BaiduTranslator):
    
    def __init__(self, source, target):
        super(BaiduTranslator, self).__init__(
            source = self.languages[source.lower()],
            target = self.languages[target.lower()]
        )
        
        
class YandexTranslator(BaseTranslator, deep_translator.YandexTranslator):
    
    def __init__(self, source, target):
        super(YandexTranslator, self).__init__(
            source = self.languages[source.lower()],
            target = self.languages[target.lower()]
        )