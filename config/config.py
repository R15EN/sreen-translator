PYTESSERACT_PATH = 'C:/Users/USER_NAME/AppData/Local/Programs/Tesseract-OCR/tesseract.exe'

SETTINGS_PATH = './config/settings.ini'

APP_SETTINGS_GROUP = 'AppSettings'
OCR_SYSTEM_NAME_KEY = 'ocr_system_name'
OCR_SYSTEM_LANGUAGE_KEY = 'ocr_system_language'
SUBTITLE_MODE_NAME_KEY = 'subtitle_mode_name'
TRANSLATOR_NAME_KEY = 'translator_name'
TRANSLATOR_TARGET_LANGUAGE_KEY = 'translator_target_language'

SUBTITLE_SETTINGS_GROUP = 'SubtitleSettings'
TEXT_STYLE_KEYS = ['font-family', 'font-style', 'font-weight', 'text-decoration', 'color', 'background-color']

DEFAULT_SETTINGS = {
    f'{APP_SETTINGS_GROUP}/{OCR_SYSTEM_NAME_KEY}': 'TesseractOCR',
    f'{APP_SETTINGS_GROUP}/{OCR_SYSTEM_LANGUAGE_KEY}': 'english',
    f'{APP_SETTINGS_GROUP}/{SUBTITLE_MODE_NAME_KEY}': 'Background Mode',
    f'{APP_SETTINGS_GROUP}/{TRANSLATOR_NAME_KEY}': 'Google Translator',
    f'{APP_SETTINGS_GROUP}/{TRANSLATOR_TARGET_LANGUAGE_KEY}': 'russian',
    **{f'{SUBTITLE_SETTINGS_GROUP}/{key}': default for key, default in {
        'font-family': 'Arial',
        'font-style': 'normal',
        'font-weight': 'normal',
        'text-decoration': 'none',
        'color': 'rgb(0, 0, 0)',
        'background-color': 'rgb(255, 255, 255)',
    }.items()}
}
