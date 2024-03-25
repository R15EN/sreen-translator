import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QRubberBand, 
    QMdiSubWindow, QVBoxLayout, QMdiArea, QHBoxLayout, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import (
    Qt, QRect, QSize, QPoint, QThread,
    QPropertyAnimation, QEasingCurve, QSettings
)
from PyQt5.QtCore import  pyqtSignal
from PyQt5.QtGui import QPixmap, QPainter, QColor, QPalette, QBrush, QImage

from src.ocr_systems import TesseractOCR, EasyOCR
from src.subtitle_window import BackgroundSubtitleWindow, InpaintingSubtitleWindow
from src.widgets import InterfaceSettingsWidget, MainSettingsWidget, FontStyleSettingsWidget
from src.translators.translators import GoogleTranslator, DeeplTranslator, YandexTranslator
from src.translators.driver import WebDriverManager
from config.config import *  # noqa: F403

import pytesseract
from pynput import keyboard
from typing import Union, Tuple


pytesseract.pytesseract.tesseract_cmd = PYTESSERACT_PATH  # noqa: F405
    
class MinMaxThread(QThread):
    
    update_signal = pyqtSignal()
    
    def __init__(self, window, parent=None):
        super(MinMaxThread, self).__init__(parent)
        self.window = window
        
        self.hotkey_combination = {
            keyboard.Key.ctrl_l, 
            keyboard.Key.alt_l, 
        }
        self.current_keys = set()

        
    def run(self):
        with keyboard.Listener(on_press=self.on_key_press, on_release=self.on_key_release) as listener:
            listener.join()
        
                
    def on_key_press(self, key):
        try:
            if key in self.hotkey_combination:
                self.current_keys.add(key)
                # If all combination keys are pressed, minimize/maximize the window
                if all(k in self.current_keys for k in self.hotkey_combination):
                    self.update_signal.emit()
        except Exception as e:
            print(e)


    def on_key_release(self, key):
        if key in self.current_keys:
            self.current_keys.remove(key)       


class MDISubWindow(QMdiSubWindow):
    
    closed = pyqtSignal()
        
    def __init__(self, title_name='', base_widget = None, parent=None):
        super(MDISubWindow, self).__init__(parent=parent)
        self.setWindowTitle(title_name)
        self.setWindowFlags(
            Qt.Window 
            | Qt.WindowTitleHint 
            | Qt.CustomizeWindowHint 
            | Qt.WindowCloseButtonHint
        )
        if base_widget:
            self.set_base_widget(base_widget)
        else:
            self.__base_widget = None
            
        self.settings = QSettings(SETTINGS_PATH, QSettings.IniFormat)  # noqa: F405
        self.setMaximumSize(QSize(400, 400))
                 
    
    def set_base_widget(self, base_widget):
        self.__base_widget = base_widget
        self.setWidget(self.__base_widget)
        
        
    def get_base_widget(self):
        if self.__base_widget:
            return self.__base_widget
        
        
    def moveEvent(self, event):
        pos = event.pos()
        left = pos.x()
        right = left + self.width()
        top = pos.y()
        bottom = top + self.height()
        area = self.mdiArea()
        
        if right > area.width():
            self.move(area.width() - self.width(), top)
            return
        if left < area.x():
            self.move(area.x(), top)
        if bottom > area.height():
            self.move(left, area.height() - self.height())

    
    def save_geometry(self):
        self.settings.beginGroup('MdiSubWindowSettings')
        self.settings.setValue(self.windowTitle(), self.geometry())
        self.settings.endGroup()
    
    
    def load_geometry(self):
        self.settings.beginGroup('MdiSubWindowSettings')
        geometry = self.settings.value(self.windowTitle(), QRect(100, 100, 400, 400))
        self.settings.endGroup()
        self.setGeometry(geometry)
    
    
    def closeEvent(self, event) -> None:
        self.save_geometry()
        self.closed.emit()
        self.deleteLater()
        return super().closeEvent(event)


class ScreenTranslatorApp(QMainWindow):
        
    def __init__(self):
        super(ScreenTranslatorApp, self).__init__()
        self.origin = QPoint()  
        self.subwindow = None
        
        self.ocr_systems_dict = {
            "TesseractOCR": TesseractOCR, 
            "EasyOCR": EasyOCR
        }
        self.subtitle_modes_dict = {
            "Background Mode": BackgroundSubtitleWindow,
            "Inpainting Mode": InpaintingSubtitleWindow
        }
        self.translators_dict = {
            "Google Translator": GoogleTranslator,
            "Deepl Translator": DeeplTranslator,
            "Yandex Translator": YandexTranslator
        }
    
        WebDriverManager()
        self.init_configuration()
        self.setWindowFlags(
            Qt.Window 
            | Qt.CustomizeWindowHint 
            | Qt.WindowStaysOnTopHint
            | Qt.FramelessWindowHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        
        # Threads
        self.maxMinThread_instance = MinMaxThread(window=self)
        self.maxMinThread_instance.update_signal.connect(self.show_hide)
        self.maxMinThread_instance.start()
        
        self.initUI()
        
    
    def init_configuration(self) -> None:
        '''
        The `init_configuration` method is used to initialize application settings from a configuration file. 
        It reads settings values from a file and sets them to the corresponding object attributes. 
        If the setting value is not found in the file, the default value is used.
        '''
        self.settings = QSettings(SETTINGS_PATH, QSettings.IniFormat)  # noqa: F405
        self.ocr_system_name = self.settings.value(
            f'{APP_SETTINGS_GROUP}/{OCR_SYSTEM_NAME_KEY}',   # noqa: F405
            DEFAULT_SETTINGS[f'{APP_SETTINGS_GROUP}/{OCR_SYSTEM_NAME_KEY}']  # noqa: F405
        )
        self.ocr_system_language = self.settings.value(
            f'{APP_SETTINGS_GROUP}/{OCR_SYSTEM_LANGUAGE_KEY}',   # noqa: F405
            DEFAULT_SETTINGS[f'{APP_SETTINGS_GROUP}/{OCR_SYSTEM_LANGUAGE_KEY}']  # noqa: F405
        )
        self.subtitle_mode_name = self.settings.value(
            f'{APP_SETTINGS_GROUP}/{SUBTITLE_MODE_NAME_KEY}',   # noqa: F405
            DEFAULT_SETTINGS[f'{APP_SETTINGS_GROUP}/{SUBTITLE_MODE_NAME_KEY}']  # noqa: F405
        )
        self.translator_name = self.settings.value(
            f'{APP_SETTINGS_GROUP}/{TRANSLATOR_NAME_KEY}',   # noqa: F405
            DEFAULT_SETTINGS[f'{APP_SETTINGS_GROUP}/{TRANSLATOR_NAME_KEY}']  # noqa: F405
        )
        self.translator_target_language = self.settings.value(
            f'{APP_SETTINGS_GROUP}/{TRANSLATOR_TARGET_LANGUAGE_KEY}',   # noqa: F405
            DEFAULT_SETTINGS[f'{APP_SETTINGS_GROUP}/{TRANSLATOR_TARGET_LANGUAGE_KEY}']  # noqa: F405
        )
        self.text_style = {
            key: self.settings.value(
                f'{SUBTITLE_SETTINGS_GROUP}/{key}',   # noqa: F405
                DEFAULT_SETTINGS[f'{SUBTITLE_SETTINGS_GROUP}/{key}']  # noqa: F405
        ) for key in TEXT_STYLE_KEYS}      # noqa: F405

        self.subtitle_mode = self.subtitle_modes_dict[self.subtitle_mode_name]
        self.ocr_system = self.ocr_systems_dict[self.ocr_system_name](self.ocr_system_language)
        self.translator = self.translators_dict[self.translator_name](
            source=self.ocr_system_language,
            target=self.translator_target_language 
        )
        
        
    def initUI(self) -> None:
        '''
        Initializing the main window interface and some important parameters
        '''
        self.primary_screen = QApplication.primaryScreen()
        self.screen_list = sorted(QApplication.screens(), key=lambda x: x.geometry().left())
        self.screen_index = self.screen_list.index(self.primary_screen)
        self.screen_geometry =  self.primary_screen.geometry()
        self.setGeometry(self.screen_geometry)
        
        # coordinates of the selection area
        self.X, self.Y, self.W, self.H = self.screen_geometry.getRect()
        
        self.background = QLabel(self)
        self.background.setScaledContents(True)
        self.background_color = QColor(255, 255, 255, 51)
        self.background_image = QImage(QSize(self.width(), self.height()), QImage.Format_RGBA8888)
        self.background_painter = QPainter()
        self.set_background_color(self.background_color)
        
        # after that you will need to change the selection logic,
        # many unsolvable problems with QRubberBand
        self.rb_color = QColor(0, 0, 255)
        rb_palette = QPalette()
        rb_palette.setBrush(QPalette.Highlight, self.rb_color)
        self.rubber_band = QRubberBand(QRubberBand.Rectangle, self)
        self.rubber_band.setPalette(rb_palette)
        self.rubber_band_selected = False
        
        self.interface_window = None
        self.settings_window = None
        self.style_window = None

        self.set_ui()


    def set_ui(self) -> None:
        '''
        Initializing the main window interface
        '''
        self.main_left_spacer = QSpacerItem(20, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.central_layout = QVBoxLayout()
        self.main_right_spacer = QSpacerItem(20, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)
        
        self.top_spacer = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.top_horizontal_layout = QHBoxLayout()
        self.central_top_spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.central_horizontal_layout = QHBoxLayout()
        self.central_bot_spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.bot_horizontal_layout = QHBoxLayout()
        self.bot_spacer = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed) 
        
        self.central_layout.addItem(self.top_spacer)
        self.central_layout.addLayout(self.top_horizontal_layout)
        self.central_layout.addItem(self.central_top_spacer)
        self.central_layout.addLayout(self.central_horizontal_layout)
        self.central_layout.addItem(self.central_bot_spacer)
        self.central_layout.addLayout(self.bot_horizontal_layout)
        self.central_layout.addItem(self.bot_spacer)
        
        # top_horizontal_layout 
        self.spacer_11 = QSpacerItem(20, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.button_1 = QPushButton('_')
        self.spacer_12 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.button_2 = QPushButton()
        self.button_3 = QPushButton()
        self.button_4 = QPushButton()
        self.spacer_13 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.button_5 = QPushButton('X')
        self.spacer_14 = QSpacerItem(20, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)

        self.button_1.setFixedSize(50, 50)
        self.button_2.setFixedSize(50, 50)
        self.button_3.setFixedSize(50, 50)
        self.button_4.setFixedSize(50, 50)
        self.button_5.setFixedSize(50, 50)
        
        self.central_buttons_layout = QHBoxLayout()
        self.central_buttons_layout.addWidget(self.button_2)
        self.central_buttons_layout.addWidget(self.button_3)
        self.central_buttons_layout.addWidget(self.button_4)
        
        self.top_horizontal_layout.addItem(self.spacer_11)
        self.top_horizontal_layout.addWidget(self.button_1)
        self.top_horizontal_layout.addItem(self.spacer_12)
        self.top_horizontal_layout.addLayout(self.central_buttons_layout)
        self.top_horizontal_layout.addItem(self.spacer_13)
        self.top_horizontal_layout.addWidget(self.button_5)
        self.top_horizontal_layout.addItem(self.spacer_14)
        
        # central_horizontal_layout
        self.spacer_21 = QSpacerItem(20, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.button_left = QPushButton('<')
        self.spacer_22 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.button_right = QPushButton('>')
        self.spacer_23 = QSpacerItem(20, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)
        
        self.button_left.setFixedSize(50, 100)
        self.button_right.setFixedSize(50, 100)
        
        self.central_horizontal_layout.addItem(self.spacer_21)
        self.central_horizontal_layout.addWidget(self.button_left)
        self.central_horizontal_layout.addItem(self.spacer_22)
        self.central_horizontal_layout.addWidget(self.button_right)
        self.central_horizontal_layout.addItem(self.spacer_23)
        
        # bot_horizontal_layout
        self.spacer_31 = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.bot_horizontal_layout.addItem(self.spacer_31)
        
        
        # other
        self.main_layout = QHBoxLayout()
        self.main_layout.addItem(self.main_left_spacer)
        self.main_layout.addLayout(self.central_layout)
        self.main_layout.addItem(self.main_right_spacer)
        
        self.mdi_area = QMdiArea(self)
        self.mdi_area.setBackground(QBrush(Qt.transparent))
        self.setCentralWidget(self.mdi_area)
        self.mdi_area.setLayout(self.main_layout)
        
        self.button_1.setToolTip('Minimize the window')
        self.button_2.setToolTip('Interface Settings')
        self.button_3.setToolTip('App Settings')
        self.button_4.setToolTip('Subtitle Settings')
        self.button_5.setToolTip('Close Application')
        self.button_left.setToolTip('Monitor to the left')
        self.button_right.setToolTip('Monitor to the right')
        
        self.button_1.clicked.connect(self.show_hide)
        self.button_2.clicked.connect(self.toggle_interface_settings_window)
        self.button_3.clicked.connect(self.toggle_settings_window)
        self.button_4.clicked.connect(self.toggle_style_settings_window)
        self.button_5.clicked.connect(self.close)
        self.button_left.clicked.connect(self.screen_before)
        self.button_right.clicked.connect(self.next_screen)
        
        
        if len(self.screen_list) == 1:
            self.button_left.hide()
            self.button_right.hide()
            
        
        
    def set_ocr_system(self, system_name: str, language: str) -> None:
        self.ocr_system = self.ocr_systems_dict[system_name](language=language)
        self.ocr_system_name = system_name
        self.ocr_system_language = language
    
    
    def set_subtitle_mode(self, mode_name: str) -> None:
        self.subtitle_mode = self.subtitle_modes_dict[mode_name]
        self.subtitle_mode_name = mode_name
    

    def set_translator(self, translator_name: str, target_language: str) -> None:
        self.translator_target_language = target_language.lower()
        self.translator_name = translator_name
        self.translator = self.translators_dict[translator_name](
            self.ocr_system_language, self.translator_target_language 
        )
        

    def toggle_interface_settings_window(self):
        if self.interface_window:
            self.remove_interface_settings_window()
        else:
            self.create_interface_settings_window()
            

    def create_interface_settings_window(self) -> None:     
        base_widget = InterfaceSettingsWidget()
        base_widget.background_color_widget.set_base_color_value(self.background_color)
        base_widget.selection_color_widget.set_base_color_value(self.rb_color)
        base_widget.background_color_widget.colorChanged.connect(self.set_background_color)
        base_widget.selection_color_widget.colorChanged.connect(self.set_rb_color)
        
        self.interface_window = MDISubWindow('Interface Settings', base_widget)
        self.interface_window.closed.connect(self.mdi_subwindow_closed)
        self.mdi_area.addSubWindow(self.interface_window)
        self.interface_window.show()
        self.interface_window.load_geometry()

    
    def remove_interface_settings_window(self) -> None:
        if self.interface_window:
            self.interface_window.close()
        self.interface_window = None

    
    def toggle_settings_window(self) -> None:
        if self.settings_window:
            self.remove_settings_window()
        else:
            self.create_settings_window()
            
        
    def create_settings_window(self) -> None:
        base_widget = MainSettingsWidget(main_window=self)
        base_widget.update_ocr_signal.connect(self.set_ocr_system)
        base_widget.update_subtitle_signal.connect(self.set_subtitle_mode)
        base_widget.update_translator_signal.connect(self.set_translator)

        self.settings_window = MDISubWindow('Base Settings', base_widget)
        self.settings_window.closed.connect(self.mdi_subwindow_closed)
        self.mdi_area.addSubWindow(self.settings_window)
        self.settings_window.show()
        self.settings_window.load_geometry()
        
        
    def remove_settings_window(self) -> None:
        if self.settings_window:
            self.settings_window.close()
            self.settings_window = None


    def toggle_style_settings_window(self) -> None:
        if self.style_window:
            self.remove_style_settings_window()
        else:
            self.create_style_settings_window()
            

    def create_style_settings_window(self) -> None:
        base_widget = FontStyleSettingsWidget(main_window=self)
        base_widget.update_style_signal.connect(self.set_text_style)
        
        self.style_window = MDISubWindow('Text Style Settings', base_widget)
        self.style_window.closed.connect(self.mdi_subwindow_closed)
        self.mdi_area.addSubWindow(self.style_window)
        self.style_window.show()
        self.style_window.load_geometry()
    

    def remove_style_settings_window(self) -> None:
        if self.style_window is not None:
            self.style_window.close()
        self.style_window = None


    def mdi_subwindow_closed(self) -> None:
        sender = self.sender()
        if sender == self.settings_window:
            self.settings_window = None
        elif sender == self.interface_window:
            self.interface_window = None
        elif sender == self.style_window:
            self.style_window = None

    
    def set_text_style(self, text_style: dict) -> None:
        self.text_style = text_style

    
    def set_background_color(self, color: Union[Tuple[int, int, int], Tuple[int, int, int, int], QColor]) -> None:
        if isinstance(color, (tuple, list)):
            if len(color) not in (3, 4):
                raise ValueError("Color must be have have 3 (RGB) or 4 (RGBA) values")
            for element in color:
                if not (0 <= element <= 255):
                    raise ValueError("All values must be in the range [0, 255]") 
            color = QColor(*color)
        
        self.background_image.fill(0)
        
        self.background_painter.begin(self.background_image)
        self.background_painter.setBrush(QBrush(color))
        self.background_painter.fillRect(QRect(0, 0, self.width(), self.height()), color)
        self.background_painter.end()
        
        self.background.setPixmap(QPixmap.fromImage(self.background_image))
        self.background.resize(self.width(), self.height())
        self.background_color = color  
        
    
    def set_rb_color(self, color: Union[Tuple[int, int, int], Tuple[int, int, int, int], QColor]) -> None:
        if isinstance(color, tuple):
            if len(color) not in (3, 4):
                raise ValueError("Color must be have have 3 (RGB) or 4 (RGBA) values")
            for element in color:
                if not (0 <= element <= 255):
                    raise ValueError("All values must be in the range [0, 255]") 
            color = QColor(*color)
            
        rb_palette = QPalette()
        rb_palette.setBrush(QPalette.Highlight, color)
        self.rubber_band.setPalette(rb_palette)
        self.rb_color = color


    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.origin = QPoint(event.pos())
            self.rubber_band.setGeometry(QRect(self.origin, QSize()))
            self.rubber_band.show()


    def mouseMoveEvent(self, event) -> None:
        if self.rubber_band.isVisible():
            self.rubber_band.setGeometry(
                QRect(
                    QPoint(
                        min(self.origin.x(), max(event.pos().x(), self.screen_geometry.x())),
                        min(self.origin.y(), max(event.pos().y(), self.screen_geometry.y())),
                    ),
                    QPoint(
                        min(self.screen_geometry.width(), max(self.origin.x(), event.pos().x())),
                        min(self.screen_geometry.height(), max(self.origin.y(), event.pos().y()))
                    )
                )
            )
    

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            x, y, w, h = self.rubber_band.geometry().getRect()
            if w > 0 and h > 0:
                self.X = self.x() + x 
                self.Y = self.y() + y
                self.W = w
                self.H = h
                self.rubber_band_selected = True
            else:
                self.rubber_band_selected = False
        
                
    def execute_continuous_function(self) -> None:
        if self.rubber_band_selected:
            self.close_subwindow()
            self.subwindow = self.subtitle_mode(
                ocr_system = self.ocr_system,
                geometry = (self.X, self.Y, self.W, self.H),
                screen_rect = self.screen_geometry.getRect(),
                text_style = self.text_style.copy(),
                translator = self.translator,
                translate = True
            )
            
            self.subwindow.show()

            
    def close_subwindow(self) -> None:
        if self.subwindow:
            self.subwindow.close()
        self.subwindow = None
        
        
    def hide_subwindow(self) -> None:
        if self.subwindow:
            self.subwindow.hide()
    
    
    def hide_main_window(self) -> None:
        self.setWindowOpacity(0)
        self.execute_continuous_function()
    
    
    def show_main_window(self) -> None:
        self.hide_subwindow()
        self.setWindowOpacity(1)
        self.close_subwindow()
        
            
    def show_hide(self) -> None:
        if self.windowOpacity():
            self.hide_main_window()
        else:
            self.show_main_window()
    
    
    def switch_screen(self) -> None:
        self.close_subwindow()
        # Создаем анимацию для изменения геометрии окна
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(300)  # Установка длительности анимации в миллисекундах
        self.animation.setStartValue(self.screen_geometry)
        self.screen_geometry = self.screen_list[self.screen_index].geometry()
        self.animation.setEndValue(self.screen_geometry)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)  # Использование квадратичного эффекта для плавности
        self.background.resize(self.screen_geometry.width(), self.screen_geometry.height())
        self.animation.start()
        

    def screen_before(self) -> None:
        self.screen_index = max(0, self.screen_index-1)
        self.switch_screen()


    def next_screen(self) -> None:
        self.screen_index = min(len(self.screen_list)-1, self.screen_index+1)
        self.switch_screen()
        
    
    def close(self, **kwargs) -> None:
        for mdi_subwindow in self.mdi_area.subWindowList():
            mdi_subwindow.save_geometry()
        super().close(**kwargs)
        
            
    def closeEvent(self, event) -> None:
        self.close_subwindow()
        event.accept()

        
def main():
    app = QApplication(sys.argv)
    window = ScreenTranslatorApp()
    window.showFullScreen()
    
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
