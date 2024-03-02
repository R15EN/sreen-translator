import numpy as np
import cv2
import pytesseract
import easyocr
from config.config import PYTESSERACT_PATH

pytesseract.pytesseract.tesseract_cmd = PYTESSERACT_PATH


class BaseOCR():
    def __init__(self):
        pass
    
    def ocr_process_image(self, image, inpaint: bool):
        pass
    
    
class TesseractOCR(BaseOCR):
    
    languages = {
        'english': 'eng',
        'chinese (traditional)': 'chi_tra',
        'chinese (simplified)': 'chi_sim',
        'japanese': 'jpn',
        'korean': 'kor',
        'russian': 'rus',
    } 
    
    def __init__(self, language: str = 'english'):
        self.language = language.lower()
    

    def get_line_size(self, word_sizes):
        if not isinstance(word_sizes, np.ndarray):
            word_sizes = np.array(word_sizes)
        try:
            y1, y2 = np.median(word_sizes[:, :2], axis=0).astype(int)
            h = np.ceil(y2-y1).astype(int)
            x1 = np.floor(word_sizes[:, -2].min(axis=0)).astype(int)
            x2 = np.ceil(word_sizes[:, -1].max(axis=0)).astype(int)
        except Exception:
            return 0, 0, 0, 0
            
        return y1, h, x1, x2-x1
    
    
    def detect_and_recognize(self, image: np.ndarray):
        return pytesseract.image_to_data(
            image, lang=self.languages[self.language], 
            output_type=pytesseract.Output.DICT
        )


    def preprocessing_image(self, image: np.ndarray):
        kernel = np.ones((1,1), dtype=np.uint8)
        image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        image = cv2.threshold(image, 128, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,  cv2.THRESH_BINARY)[1]
        image = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)
        return np.array(image)

    
    def ocr_process_image(self, image, inpaint=False):
    
        if not isinstance(image, np.ndarray):
            image = np.array(image, dtype=np.uint8)
        if inpaint:
            mask = np.zeros_like(image, shape=image.shape[:-1], dtype=np.uint8)   
            
        ocr_data = self.detect_and_recognize(self.preprocessing_image(image))
        prev_line, prev_block, prev_par = -1, -1, -1
        lines = []
        word_sizes = []
        full_text = ''
        
        for x, y, w, h, text, line, block, level, par, conf in zip(
            ocr_data["left"],
            ocr_data["top"],
            ocr_data["width"],
            ocr_data["height"],
            ocr_data["text"],
            ocr_data["line_num"],
            ocr_data['block_num'],
            ocr_data['level'],
            ocr_data['par_num'],
            ocr_data['conf']
        ):
            text = text.strip()
            if level != 5 or not text or conf < 1:
                continue
            
            text = text.replace('|', 'I') # small correction
            
            if inpaint:
                mask[max(y-2, 0):y+h+2, max(x-2, 0):x+w+2] = 255        
            
            if (prev_line, prev_block, prev_par) == (line, block, par):
                full_text += text + ' '
                word_sizes.append((y, y+h, x, x+w))
            else:
                prev_line, prev_block, prev_par = line, block, par
                if len(word_sizes):
                    lines.append((full_text, *self.get_line_size(word_sizes)))
                full_text = text + ' '
                word_sizes = [(y, y+h, x, x+w)]

        lines.append((full_text, *self.get_line_size(word_sizes)))
        lines = list(filter(lambda line: all(line), lines))
        if inpaint:
            inpainted_image = np.array(
                cv2.inpaint(image, mask, 5, cv2.INPAINT_TELEA), dtype=np.uint8
            )
            return (inpainted_image, mask, lines)
        
        return (np.empty(shape = (0,)), np.empty(shape = (0,)), lines)


class EasyOCR(BaseOCR):
    
    languages = {
        'english': ['en'],
        'chinese (traditional)': ['ch_tra', 'en'],
        'chinese (simplified)': ['ch_sim', 'en'],
        'japanese': ['ja', 'en'],
        'korean': ['ko', 'en'],
        'russian': ['ru', 'en'],
    }
    
    
    def __init__(self, language: str = 'english'):
        self.language = language.lower()
        self.reader = easyocr.Reader(
            lang_list = self.languages[self.language], 
            detect_network = 'craft', 
            gpu = True
        ) 

    
    def preprocessing_image(self, image: np.ndarray) -> np.ndarray:
        # Because The text on the images can be anything at all,
        # no idea yet which transformations are best to use

        return np.array(image)

    
    def detect_and_recognize(self, image: np.ndarray) -> list:
        return self.reader.readtext(image, detail=1, width_ths=1, add_margin=0, min_size=5)
    
    
    def ocr_process_image(self, image: np.ndarray, inpaint=False):
        
        if not isinstance(image, np.ndarray):
            image = np.array(image, dtype=np.uint8)
        if inpaint:
            mask = np.zeros_like(image, shape=image.shape[:-1], dtype=np.uint8)   

        ocr_data = self.detect_and_recognize(self.preprocessing_image(image))
        corr_coef = 0.7
        tmp = []
        
        for bbox, text, prob in ocr_data:
            top = int((bbox[0][1] + bbox[1][1]) // 2)
            bottom = int((bbox[2][1] + bbox[3][1]) // 2)
            h = int(bottom - top)
            mean_line = int((top + bottom) // 2)
            left = int((bbox[0][0] + bbox[3][0]) // 2)
            right = int((bbox[1][0] + bbox[2][0]) // 2)
            w = int(right - left)
            tmp.append([top, bottom, h, mean_line, left, right, w, text, prob])
        tmp.sort(key=lambda x: x[0])
        
        lines = []
        j = 0
        for i, (t, b, m_l, h, left, right, w, text, prob) in enumerate(tmp[1:], start=1):
            if t > tmp[i-1][3]:
                lines.append(sorted(tmp[j: i], key = lambda x: x[4]))
                j = i
                if i == len(tmp)-1:
                    lines.append([tmp[i]])
                    continue
            if i == len(tmp)-1:
                lines.append(sorted(tmp[j: ], key = lambda x: x[4]))    
                
        new_lines = []

        for line in lines:
            line = np.array(line)
            
            coords = line[:, :7].astype(int)
            y = coords[:, 0].min().astype(int)
            h = np.ceil(coords[:, 2].mean()).astype(int)
            x = coords[:, 4].min().astype(int)
            r = coords[:, 5].max().astype(int) 
            w = r - x
            
            text = ' '.join(line[:, 7].tolist()).strip()
            text = text.replace('_', ' ')
            text = text.replace("$", "s")
            text = text.replace('|', 'I')
            text = text.replace('@', 'a')

            new_lines.append((text, y, int(h * corr_coef), x, w))
            
            if inpaint:
                mask[max(y-2, 0):y+h+2, max(x-2, 0):x+w+2] = 255 

        lines = list(filter(lambda line: all(line), new_lines))
        
        if inpaint:
            inpainted_image = np.array(
                cv2.inpaint(image, mask, 5, cv2.INPAINT_TELEA), dtype=np.uint8
            )
            return (inpainted_image, mask, lines)
        else:
            return (np.empty(shape = (0,)), np.empty(shape = (0,)), lines)


class TesseractEasyOCR(TesseractOCR):
    '''
    In the future, this class will use detection from EasyOCR and recognition from Tesseeract (or vice versa).
    '''
    def __init__(self):
        pass