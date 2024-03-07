import numpy as np
import cv2
import pytesseract
import easyocr
from config.config import PYTESSERACT_PATH

pytesseract.pytesseract.tesseract_cmd = PYTESSERACT_PATH



class TesseractOCR():
    
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

    
    def ocr_process_image(self, image: np.ndarray, inpaint: bool = False) -> tuple[np.ndarray, np.ndarray, list]:
        
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
                mask[max(y-4, 0):y+h+4, max(x-4, 0):x+w+4] = 255        
            
            if (prev_line, prev_block, prev_par) == (line, block, par):
                full_text += text + ' '
                word_sizes.append((y, y+h, x, x+w))
            else:
                prev_line, prev_block, prev_par = line, block, par
                if len(word_sizes):
                    lines.append((full_text.rstrip(), *self.get_line_size(word_sizes)))
                full_text = text + ' '
                word_sizes = [(y, y+h, x, x+w)]
    
        lines.append((full_text.rstrip(), *self.get_line_size(word_sizes)))
        lines = list(filter(lambda line: all((line[0], line[2], line[4])), lines))
        
        if inpaint:
            inpainted_image = np.array(
                cv2.inpaint(image, mask, 5, cv2.INPAINT_TELEA), dtype=np.uint8
            )
            return (inpainted_image, mask, lines)
        
        return (np.empty(shape = (0,)), np.empty(shape = (0,)), lines)


class EasyOCR():
    
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
        return self.reader.readtext(image, detail=1, width_ths=1, add_margin=0, min_size=2)
    

    def ocr_process_image(self, image: np.ndarray, inpaint: bool = False) -> tuple[np.ndarray, np.ndarray, list]:
        
        def split_by_space(data_list: list, splitted_data: list, flag: bool = False):
            for i, value in enumerate(data_list[1:], start=1):
                if flag: return flag  # noqa: E701
                        
                previous_value = data_list[i-1]
                space = value['left'] - previous_value['right']
                
                max_space = min(value['mean_char_width'], previous_value['mean_char_width']) * 3
                if space > max_space and space > x_thresh:
                    splitted_data.append(data_list[:i])            
                    flag = split_by_space(data_list[i:], splitted_data, flag=False)
                    
            if flag: return flag   # noqa: E701
            splitted_data.append(data_list)
            return True

        def correct_text(text):
            replacement_pairs = (('_', ' '), ("$", "s"), ('|', 'I'), ('@', 'a'), ('[', 'I'))
            for pair in replacement_pairs:
                text = text.replace(*pair)
            return text
    
        
        if not isinstance(image, np.ndarray):
            image = np.array(image, dtype=np.uint8)
        if inpaint:
            mask = np.zeros_like(image, shape=image.shape[:-1], dtype=np.uint8)   
        
        height_corr_coef = 0.7 # A coefficient that is multiplied by the height of the returned text.
        y_thresh = 4 # threshold at which detected elements are combined along the y-axis
        x_thresh = 25 # threshold at which detected elements are separated along the x-axis
        ocr_data = []
        
        # forming a general structure of the data that was detected 
        tmp = self.detect_and_recognize(self.preprocessing_image(image))
        for i, (bbox, text, prob) in enumerate(tmp):    
            data_dict = {
                'top': int((bbox[0][1] + bbox[1][1]) // 2),
                'bottom': int((bbox[2][1] + bbox[3][1]) // 2),
                'left': int((bbox[0][0] + bbox[3][0]) // 2),
                'right': int((bbox[1][0] + bbox[2][0]) // 2),
                'text': text.strip(),
                'prob': prob
            } 
            data_dict['height'] = data_dict['bottom'] - data_dict['top']
            data_dict['width'] = data_dict['right'] - data_dict['left']
            data_dict['mean_line'] = (data_dict['top'] + data_dict['bottom']) // 2
            if len(data_dict['text']):
                data_dict['mean_char_width'] = data_dict['width'] / len(data_dict['text'])
            else:
                data_dict['mean_char_width'] = 0
            ocr_data.append(data_dict)
            
            if inpaint:
                mask[
                    max(data_dict['top']-2, 0):data_dict['bottom']+2, 
                    max(data_dict['left']-2, 0):data_dict['right']+2
                ] = 255             
        
        # combining and dividing data into groups, depending on their position
        splitted_data = [] 
        data_group_by_mean_lines = {}
        for data in ocr_data:
            data_group_by_mean_lines.setdefault(data['mean_line'], []).append(data)
        data_group_by_mean_lines = sorted(list(map(list, data_group_by_mean_lines.items())))

        for i, (key, value) in enumerate(data_group_by_mean_lines):
            if i == len(data_group_by_mean_lines) - 1:
                value.sort(key=lambda x: x['left'])
                split_by_space(value, splitted_data)
                continue
            next_key = data_group_by_mean_lines[i+1][0]
            if next_key - key > y_thresh:
                value.sort(key=lambda x: x['left'])
                split_by_space(value, splitted_data)    
            else:
                data_group_by_mean_lines[i+1] = [key, value + data_group_by_mean_lines[i+1][1]]
                data_group_by_mean_lines[i] = None

        
        # creating a list with unique values of the left coordinates for future lines
        unique_left_coords = sorted(set([d[0]['left'] for d in splitted_data]))
        for i, coord in enumerate(unique_left_coords):   
            if i == len(unique_left_coords) - 1:
                break
            next_coord = unique_left_coords[i + 1]
            # 4 - threshold at which we consider that the coordinates are actually the same
            if next_coord - coord <= 4: # 
                unique_left_coords[i+1] = coord
                unique_left_coords[i] = None
        unique_left_coords = [c for c in unique_left_coords if c]
        
        
        # grouping elements into blocks by left coordinates
        blocks = [[] for _ in range(len(unique_left_coords))]
        for data in splitted_data:
            data_left_coord = data[0]['left']
            for i, left_coord in enumerate(unique_left_coords):
                if i == len(unique_left_coords) - 1 or left_coord <= data_left_coord < unique_left_coords[i+1]:    
                    groupped_row =  {
                        'top': np.mean([elem['top'] for elem in data]).astype(int),
                        'bottom': np.mean([elem['bottom'] for elem in data]).astype(int),
                        'height': np.mean([elem['height'] for elem in data]).astype(int),
                        'mean_line': np.mean([elem['mean_line'] for elem in data]).astype(int),
                        'left': data[0]['left'],
                        'right': data[-1]['right'],
                        'text': ' '.join([elem['text'] for elem in data])
                    }
                    groupped_row['width'] =  groupped_row['right'] - groupped_row['left']
                    groupped_row['mean_char_width'] = groupped_row['width'] / len(groupped_row['text'])
                    blocks[i].append(groupped_row)
                    break
        
        
        # Additional division of existing blocks taking into account the distance between lines
        for i in range(len(blocks)):
            block = blocks[i]
            k = 0
            for j, line in enumerate(block):
                if j == len(block) - 1:
                    break
                next_line = block[j+1]
                line_height = line['height']
                line_bottom = line['bottom']
                next_line_height = next_line['height']
                next_line_top = next_line['top']
                if next_line_top - line_bottom > min(line_height, next_line_height) * 1.25:
                    blocks.append(block[: j+1])
                    block[k: j+1] = [None] * len(block[k: j+1])
                    k = j + 1
        blocks = [[line for line in block if line] for block in blocks]
        
        # Setting the same height and left coordinate for all line elements in blocks
        for block in blocks:
            block = [line for line in block if line]
            mean_height = np.mean([line['height'] for line in block]).astype(int) 
            min_left = min([line['left'] for line in block])
            for line in block:
                line['height'] = mean_height
                line['left'] = min_left
                
                    
        blocks.sort(key=lambda block: block[0]['top'])            
        lines = [line for block in blocks for line in block]
        lines = [
            (
                correct_text(line['text']),
                line['top'],
                np.ceil(line['height'] * height_corr_coef).astype(int),
                line['left'],
                line['right'] - line['left']
            )
        for line in lines]  
        
        if inpaint:
            inpainted_image = np.array(
                cv2.inpaint(image, mask, 5, cv2.INPAINT_TELEA), dtype=np.uint8
            )
            return (inpainted_image, mask, lines)
        else:
            return (np.empty(shape = (0,)), np.empty(shape = (0,)), lines)
        