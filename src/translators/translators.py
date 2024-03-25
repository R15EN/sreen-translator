# This is a temporary solution
import re
from abc import ABC, abstractmethod
from typing import List

import requests
from urllib.parse import quote, urlencode
from bs4 import BeautifulSoup
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from src.translators.driver import WebDriverManager
from src.translators.constants import *


class BaseTranslator(ABC):
    
    def __init__(self, source: str, target: str, codes: dict):
        if not source:
            raise ValueError('Invalud source language')
        if not target:
            raise ValueError('Invalid target language')
        
        self.languages = codes 
             
        self.source_lang = self._language_to_code(source)
        self.target_lang = self._language_to_code(target)
        
    def _is_same_language(self) -> bool:
        return self.target_lang == self.source_lang
    
    
    def _is_empty(self, text: str) -> bool:
        return text == ""
    
        
    def _language_to_code(self, language: str) -> str:
        if language in self.languages.keys():
            return self.languages[language]
        elif language in self.languages.values():
            return language
        else:
            raise ValueError(f'No support for the following language: {language}')
    
        
    @property
    def target(self):
        return self.target_lang
    
    
    @target.setter
    def target(self, language):
        self.target_lang = self._language_to_code(language)


    @property
    def source(self):
        return self.source
        
        
    @source.setter    
    def source(self, language):
        self.source_lang = self._language_to_code(language)


    @abstractmethod
    def translate(self, text: str, **kwargs) -> str:
        pass
    
    
    def translate_batch(self, batch: List[str], **kwargs) -> List[str]:
        if not batch:
            raise ValueError('Batch cannot be empty')
        result_batch = [''] * len(batch)
        for i, text in enumerate(batch):
            result_batch[i] = self.translate(text)
        return result_batch
    
        
    def translate_batch_concat(self, batch: List[str], **kwargs) -> List[str]:
        pattern = r'\s*#\s*\$\s*#\s*'
        unstrans_elem = '#$#' # #$# - untranslatable element
        
        all_text = unstrans_elem.join(batch)
        if all_text:
            translated_text = self.translate(all_text)
        translated_text = re.sub(pattern, unstrans_elem, str(translated_text)).split(unstrans_elem)
        return translated_text
    
    

class YandexTranslator(BaseTranslator):
    
    def __init__(self, source: str, target: str):
        super(YandexTranslator, self).__init__(
            source, target,
            codes = YANDEX_CODES
        )
        self._driver = WebDriverManager()
        self._wait_time = WebDriverWait(self._driver, 3)
        
        self._base_url = "https://translate.yandex.ru/?source_lang={}&target_lang={}&text={}"
        self._driver.get(self._generate_url(text = ''))
        
        
    def _generate_url(self, text: str, **kwargs) -> str:
        return self._base_url.format(self.source_lang, self.target_lang, quote(text))


    def translate(self, text: str, **kwargs) -> str:
        if not isinstance(text, str):
            raise ValueError('Unsupported type of text')
        if self._is_empty(text) or self._is_same_language():
            return text

        self._driver.get(self._generate_url(text))
        try:
            elements = self._wait_time.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'translation-word')))
        except Exception as e:
            print(f'Error while finding elements: {e}')
            return ''
        
        try:
            translated_text = ''.join([elem.text for elem in elements])
        except StaleElementReferenceException:
            elements = self._wait_time.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'translation-word')))
            translated_text = ''.join([elem.text for elem in elements])
            return translated_text
        except Exception as e:
            print(f'Error while getting text: {e}')
            return ''
        
        return translated_text
    
    def translate_batch_concat(self, batch: List[str], **kwargs) -> List[str]:
        pattern = r'\s*\[\s*1\s*\]\s*'
        unstrans_elem = '[1]' # #$# - untranslatable element

        all_text = unstrans_elem.join(batch)
        if all_text:
            translated_text = self.translate(all_text)
        translated_text = re.sub(pattern, unstrans_elem, str(translated_text)).split(unstrans_elem)
        return translated_text
        
        
class DeeplTranslator(BaseTranslator):
    def __init__(self, source, target):
        super(DeeplTranslator, self).__init__(
            source, target,
            codes = DEEPL_CODES
        )
        self._driver = WebDriverManager()
        self._wait_time = WebDriverWait(self._driver, 3)
        
        self._base_url = "https://www.deepl.com/translator#{}/{}/{}"
        self._driver.get(self._generate_url(text = ''))
        
        
    def _generate_url(self, text: str, **kwargs) -> str:
        return self._base_url.format(self.source_lang, self.target_lang, quote(text))
        
    
    def translate(self, text: str, **kwargs) -> str:
        if not isinstance(text, str):
            raise ValueError('Unsupported type of text')
        if self._is_empty(text) or self._is_same_language():
            return text
        
        self._driver.get(self._generate_url(text))
        xpath = "//*[@name='target']//*[contains(@class, 'sentence_highlight')]"
        try:
            elements = self._wait_time.until(EC.presence_of_all_elements_located((By.XPATH, xpath)))
        except Exception as e:
            print(f'Error while finding elements: {e}')
            return ''
            
        try:
            translated_text = ''.join([elem.text for elem in elements])
        except StaleElementReferenceException:
            elements = self._wait_time.until(EC.presence_of_all_elements_located((By.XPATH, xpath)))
            translated_text = ''.join([elem.text for elem in elements])
            return translated_text
        except Exception as e:
            print(f'Error while getting text: {e}')
            return ''
        
        return translated_text
    
    
class GoogleTranslator(BaseTranslator):
    def __init__(self, source, target):
        super(GoogleTranslator, self).__init__(
            source, target,
            codes = GOOGLE_CODES
        )
        
        self._base_url = "https://translate.google.com/m?"
        
        
    def translate(self, text: str, **kwargs) -> str:
        if not isinstance(text, str):
            raise ValueError('Unsupported type of text')
        if self._is_empty(text) or self._is_same_language():
            return text
        

        url = self._base_url + urlencode({'sl':self.source_lang, 'tl':self.target_lang, 'q':text})
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'lxml')
            element = soup.find('div', class_='result-container')
            response.close()
            
            if not element:
                print('Translation not found')
                return ''
            return element.text
        else:
            print('Request Error')
            return ''
