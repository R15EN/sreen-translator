from PyQt5.QtCore import Qt, QThread, QSemaphore, pyqtSignal 
from PyQt5.QtGui import QPixmap, QImage, QFont
from PyQt5.QtWidgets import QLabel, QWidget, QSizePolicy
import numpy as np
from typing import Tuple
from src.window_capture import ScreenCapture

class SubwindowThread(QThread):
    
    update_signal = pyqtSignal(list, np.ndarray, np.ndarray)
    
    def __init__(self, parent=None):
        super(SubwindowThread, self).__init__(parent=parent)
        self.sct = ScreenCapture()
        self.ocr_system = self.parent().ocr_system
        self.inpaint = self.parent().inpaint
        
        self.coordinates = None
        self.screen_rect = None
        self.is_running = True
        self.semaphore = QSemaphore(1)
        

    def run(self):
        while self.is_running:
            try:
                active_window_hwnd = self.sct.active_window_hwnd()
                if active_window_hwnd:
                    img = self.sct.grab(
                        active_window_hwnd, 
                        monitor_rect=self.screen_rect, 
                        area=self.coordinates
                    )
                    inpainted, mask, lines = self.ocr_system.ocr_process_image(
                        img, inpaint=self.inpaint
                    )
                    self.semaphore.acquire()  # Блокируем семафор перед отправкой сигнала
                    self.update_signal.emit(lines, inpainted, mask)
                    self.semaphore.release()  # Разблокируем семафор после отправки сигнала
            except Exception as e:
                print(e)
    
    
    def stop(self) -> None:
        self.is_running = False
        
        
    def start(self, **kwargs) -> None:
        self.is_running = True
        return super().start(**kwargs)
    
    
    def set_ocr_system(self, ocr_system):
        self.ocr_system = ocr_system
        
        
    def set_coordinates(self, coordinates: Tuple[int, int, int, int]):
        if len(coordinates) == 4:
            self.coordinates = coordinates
        else:
            raise ValueError('Coordinates must have 4 values (x, y, w, h)')
    
    
    def set_screen_rect(self, screen_rect: Tuple[int, int, int, int]):
        if len(screen_rect) == 4:
            self.screen_rect = screen_rect
        else:
            raise ValueError('Screen coordinates must have 4 values (x, y, w, h)')
        
    
class BaseSubtitleWindow(QWidget):
    
    stop_signal = pyqtSignal()
    
    def __init__(
        self, 
        ocr_system,
        geometry: Tuple[int, int, int, int], 
        screen_rect: Tuple[int, int, int, int],
        inpaint: bool = False,
        text_style: dict = None,
        translator = None,
        translate : bool = False,
        parent = None
    ) -> None:
        super(BaseSubtitleWindow, self).__init__(parent=parent)
        
        self.ocr_system = ocr_system
        self.inpaint = inpaint
        self.screen_rect = screen_rect
        self.setGeometry(*geometry)
        
        self.labels = []        
        self.base_font = QFont(text_style['font-family'])        
        self.translate = translate
        self.translator = translator

        self.text_style = '; '.join([f'{k}: {v}' for k, v in text_style.items()])
    
        self.initUI()
 
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint
            | Qt.FramelessWindowHint
            | Qt.WindowTransparentForInput
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        
        self.work_thread = SubwindowThread(parent = self)
        self.work_thread.set_coordinates(geometry)
        self.work_thread.set_screen_rect(self.screen_rect)
        self.work_thread.update_signal.connect(self.update)
        self.start_thread()
        self.semaphore = self.work_thread.semaphore
    
        
    def initUI(self) -> None:        
        pass
            
        
    def stop_thread(self) -> None:
        self.work_thread.is_running = False
        self.work_thread.stop()
        self.work_thread.quit()
        self.work_thread.wait()
        
    
    def start_thread(self) -> None:
        self.work_thread.start()
        
        
    def close(self) -> bool:
        self.stop_thread()
        return super().close()
    
    
    def closeEvent(self, event) -> None:
        self.stop_signal.emit()
        event.accept()
        
    
    def remove_labels(self) -> None:
        for label in self.labels:
            label.deleteLater()
        self.labels = []
        
        
    def create_label(self, text: str, parent = None) -> QLabel:
        label = QLabel(text, parent)
        label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        return label
    
    
    def update_label(self, label: QLabel, text_info: tuple) -> None:
        text, y, h, x, w = text_info
        font = self.base_font
        font.setPixelSize(h)

        label.move(x, y)
        label.setText(text)
        label.setFont(font)
        label.setMinimumWidth(w)     
        label.setMinimumHeight(h)
        label.setStyleSheet(self.text_style)
        # label.setWordWrap(True)

    
    def update_image(self, *args):
        pass
    
    
    def translate_text(self, text_list: list) -> None:
        tmp_text = '[0]'.join(text_list)
        tmp_text = self.translator.translate(tmp_text)
        tmp_text = tmp_text.split('[0]')
        return tmp_text
    
    
    def update_text(self, text_data: list) -> None:
        if self.labels:
            self.remove_labels()
        if self.translate:
            try:
                text_data = [
                    (t, y, h, x, w) for t, (_, y, h, x, w) in 
                    zip(self.translate_text([k[0] for k in text_data]), text_data)
                ]  
            except AttributeError as e:
                print(e)
                return
        for text_info in text_data:
            label = self.create_label('', self)
            self.update_label(label, text_info)
            self.labels.append(label)
            label.show()
            
    
    def update(self, text_data: list, image: np.ndarray = None, mask: np.ndarray = None) -> None:
        self.semaphore.release()  
        if image is not None and mask is not None: 
            self.update_image(image, mask)
        self.update_text(text_data)
        self.semaphore.acquire()  

    
                
class BackgroundSubtitleWindow(BaseSubtitleWindow):
    def __init__(
        self, 
        ocr_system,
        geometry: Tuple[int, int, int, int], 
        screen_rect: Tuple[int, int, int, int],
        text_style: dict = None,
        translator = None,
        translate: bool = False,
        parent = None
    ):
        if text_style:
            text_style['background-color'] = text_style.get('background-color', 'rgb(255, 255, 255)')
        text_style = {'background-color': 'rgb(255, 255, 255)'} if not text_style else text_style
        super(BackgroundSubtitleWindow, self).__init__(
            ocr_system = ocr_system,
            geometry = geometry,
            screen_rect = screen_rect,
            text_style = text_style,
            translator = translator,
            translate = translate, 
            inpaint = False,
            parent = parent
        )


class InpaintingSubtitleWindow(BaseSubtitleWindow):
    def __init__(
        self, 
        ocr_system,
        geometry: Tuple[int, int, int, int], 
        screen_rect: Tuple[int, int, int, int],
        text_style: dict = None,
        translator = None,
        translate: bool = False,
        parent = None
    ):  
        text_style['background-color'] = '' if text_style else {'background-color': ''}
        super(InpaintingSubtitleWindow, self).__init__(
            ocr_system = ocr_system,
            geometry = geometry,
            screen_rect = screen_rect,
            text_style = text_style,
            translator = translator,
            translate = translate,
            inpaint = True,
            parent = parent
        )
        self.image_label = QLabel(self)


    def update_image(self, image: np.ndarray, mask: np.ndarray) -> None:
        if not isinstance(image, np.ndarray):
            image = np.array(image)
            
        height, width, _ = image.shape
        image_with_alpha = np.concatenate((image, mask[:, :, np.newaxis]), axis=2)
        image_with_alpha = QImage(
            image_with_alpha.tobytes(), 
            width, height, 
            4 * width,
            QImage.Format_RGBA8888
        )
        self.image_label.setPixmap(QPixmap.fromImage(image_with_alpha))
        self.image_label.resize(width, height)
        self.image_label.setFixedSize(width, height)
    