from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSlider, QWidget, QRadioButton, QButtonGroup, QDoubleSpinBox, QSizePolicy, QSpacerItem, QStackedWidget, QListWidget, QFormLayout, QComboBox, QFrame, QFontComboBox, QCheckBox, QLineEdit
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtCore import Qt, QSettings, pyqtSignal
from config.config import *


class BackgroundColorWidget(QWidget):
    
    colorChanged = pyqtSignal(QColor)
    
    def __init__(self, parent = None):
        super(BackgroundColorWidget, self).__init__(parent=parent)

        self.color = QColor()
        self.main_layout = QVBoxLayout(self)
        self.setLayout(self.main_layout)
        
        self.radio_btn_black = QRadioButton('Black')
        self.radio_btn_black.setChecked(True)
        self.radio_btn_white = QRadioButton('White')
        self.radio_btn_gray = QRadioButton('Gray')
        
        self.button_group = QButtonGroup()
        self.button_group.addButton(self.radio_btn_black)
        self.button_group.addButton(self.radio_btn_white)
        self.button_group.addButton(self.radio_btn_gray)
        
        self.label = QLabel('Opacity')
        
        self.slider_layout = QHBoxLayout()
        self.alpha_channel_slider = QSlider(Qt.Horizontal)
        self.alpha_channel_slider.setMinimum(51) # 51 == 0.2*255
        self.alpha_channel_slider.setMaximum(204) # 204 == 0.8*255
        self.spin_box = QDoubleSpinBox()
        self.spin_box.setMinimum(0.2)
        self.spin_box.setMaximum(0.8)
        
        self.slider_layout.addWidget(self.alpha_channel_slider)
        self.slider_layout.addWidget(self.spin_box)
        
        self.bot_spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
            
        self.main_layout.addWidget(self.radio_btn_black)
        self.main_layout.addWidget(self.radio_btn_white)
        self.main_layout.addWidget(self.radio_btn_gray)
        self.main_layout.addWidget(self.label)
        self.main_layout.addLayout(self.slider_layout)
        self.main_layout.addItem(self.bot_spacer)
        
        self.button_group.buttonClicked.connect(self.on_radio_button_clicked)
        self.alpha_channel_slider.valueChanged.connect(self.update_color)
        self.alpha_channel_slider.valueChanged.connect(self.set_spin_box_value)
        self.spin_box.valueChanged.connect(self.update_color)
        self.spin_box.valueChanged.connect(self.set_slider_value)
        
        
    def set_base_color_value(self, color: QColor) -> None:
        self.alpha_channel_slider.setValue(color.alpha())
        self.spin_box.setValue(color.alpha() / 255)


    def set_slider_value(self) -> None:
        self.alpha_channel_slider.setValue(int(self.spin_box.value() * 255))
        
        
    def set_spin_box_value(self) -> None:
        self.spin_box.setValue(self.alpha_channel_slider.value() / 255)
        

    def on_radio_button_clicked(self, button):
        alpha = self.alpha_channel_slider.value()
        if button.text() == 'Black':
            self.color = QColor(0, 0, 0, alpha)
        elif button.text() == 'White':
            self.color = QColor(255, 255, 255, alpha)
        else:
            self.color = QColor(128, 128, 128, alpha)
        self.update_color()


    def update_color(self):
        color = QColor()
        color.setRgb(
            self.color.red(), 
            self.color.green(), 
            self.color.blue(),
            self.alpha_channel_slider.value()
        )
        self.colorChanged.emit(color)
        
        
class ColorWidget(QWidget):
    
    colorChanged = pyqtSignal(QColor)
    
    def __init__(self, base_color: QColor = QColor(255, 255, 255), parent = None):
        super(ColorWidget, self).__init__(parent=parent)

        self.base_color = base_color

        self.color_label = QLabel('Selected Color:', self)
        self.color_label.setAlignment(Qt.AlignCenter)
        self.color_label.setStyleSheet(f'background-color: {base_color.name()};')

        self.red_slider = QSlider(Qt.Horizontal, self)
        self.green_slider = QSlider(Qt.Horizontal, self)
        self.blue_slider = QSlider(Qt.Horizontal, self)
        
        self.red_slider.setMinimum(0)
        self.red_slider.setMaximum(255)
        self.green_slider.setMinimum(0)
        self.green_slider.setMaximum(255)
        self.blue_slider.setMinimum(0)
        self.blue_slider.setMaximum(255)

        self.setup_layout()


    def setup_layout(self):
        layout = QVBoxLayout(self)
        layout.addWidget(self.color_label)
                
        sliders_layout = QVBoxLayout()
        sliders_layout.addWidget(self.red_slider)
        sliders_layout.addWidget(self.green_slider)
        sliders_layout.addWidget(self.blue_slider)

        layout.addLayout(sliders_layout)

        self.red_slider.valueChanged.connect(self.update_color)
        self.green_slider.valueChanged.connect(self.update_color)
        self.blue_slider.valueChanged.connect(self.update_color)
        
        
    def set_base_color_value(self, color: QColor) -> None:
        self.red_slider.setValue(color.red())
        self.green_slider.setValue(color.green())
        self.blue_slider.setValue(color.blue())

    
    def update_color(self):
        color = QColor()
        color.setRgb(
            self.red_slider.value(), 
            self.green_slider.value(), 
            self.blue_slider.value()
        )

        self.color_label.setStyleSheet(f'background-color: {color.name()};')
        self.colorChanged.emit(color)    
    
        
class InterfaceSettingsWidget(QWidget):
    def __init__(self, parent=None):
        super(InterfaceSettingsWidget, self).__init__(parent = parent)    
        self.section = [
            'Background color',
            'Selection color'
        ]
        self.background_color_widget = BackgroundColorWidget()
        self.selection_color_widget = ColorWidget()
        
        self.list_widget = QListWidget()
        self.stacked_widget = QStackedWidget()
        
        self.list_widget.setMinimumWidth(150)
        self.list_widget.setMaximumWidth(200)
        self.stacked_widget.setMinimumWidth(150)
        self.stacked_widget.setMinimumWidth(200)
        
        self.setup_layout()
        self.setup_list_widget()
        self.setup_stacked_widget()

        
    def setup_layout(self):
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)
        
        main_layout.addWidget(self.list_widget)
        main_layout.addWidget(self.stacked_widget)
        
    
    def setup_list_widget(self):
        self.list_widget.addItems(self.section)
        self.list_widget.currentRowChanged.connect(self.stacked_widget.setCurrentIndex)

    
    def setup_stacked_widget(self):
        self.stacked_widget.addWidget(self.background_color_widget)
        self.stacked_widget.addWidget(self.selection_color_widget)
        

class MainSettingsWidget(QWidget):
    
    update_ocr_signal = pyqtSignal(str, str)
    update_subtitle_signal = pyqtSignal(str)
    update_translator_signal = pyqtSignal(str, str)
    
    def __init__(self, main_window, parent=None):
        super(MainSettingsWidget, self).__init__(parent=parent)
        self.settings = QSettings(SETTINGS_PATH, QSettings.IniFormat)
        self.main_window = main_window 
        self.ocr_systems = {
            name: [i.capitalize() for i in system.languages] 
            for name, system in main_window.ocr_systems_dict.items()
        }
        self.subtitle_modes = list(main_window.subtitle_modes_dict.keys())
        self.translators = list(main_window.translators_dict.keys())
        self.target_languages = list(map(str.capitalize, main_window.translator.languages.keys()))
        self.initUI()
        
        
    def initUI(self):
        self.label_ocr = QLabel('OCR system')
        self.label_ocr.setMinimumWidth(100)
        self.combo_box_ocr = QComboBox()
        self.combo_box_ocr.addItems(self.ocr_systems.keys())
        self.combo_box_ocr.setCurrentIndex(
            self.combo_box_ocr.findText(self.main_window.ocr_system_name)
        )
        
        self.label_source_lang = QLabel('Recognized language')
        self.label_source_lang.setMinimumWidth(100)
        self.combo_box_source_lang = QComboBox()
        self.combo_box_source_lang.addItems(self.ocr_systems[self.combo_box_ocr.currentText()])
        self.combo_box_source_lang.setCurrentIndex(
            self.combo_box_source_lang.findText(self.main_window.ocr_system_language.capitalize())
        )
        
        self.label_subtitle_mode = QLabel('Mode')
        self.label_subtitle_mode.setMinimumWidth(100)
        self.combo_box_subtitle_mode = QComboBox()
        self.combo_box_subtitle_mode.addItems(self.subtitle_modes)
        self.combo_box_subtitle_mode.setCurrentIndex(
            self.combo_box_subtitle_mode.findText(self.main_window.subtitle_mode_name)
        )
        
        self.label_translator = QLabel('Translator')
        self.label_translator.setMaximumWidth(100)
        self.combo_box_translator = QComboBox()
        self.combo_box_translator.addItems(self.translators)
        self.combo_box_translator.setCurrentIndex(
            self.combo_box_translator.findText(self.main_window.translator_name)
        )
        
        self.label_target_lang = QLabel('Target Language')
        self.label_target_lang.setMaximumWidth(100)
        self.combo_box_target_lang = QComboBox()
        self.combo_box_target_lang.addItems(self.target_languages)
        self.combo_box_target_lang.setCurrentIndex(
            self.combo_box_target_lang.findText(self.main_window.translator_target_language.capitalize())
        )
        self.push_button = QPushButton('Apply')
        
        self.setup_layout()
        self.update_supported_languages()
        self.update_target_languages()
        # self.update_source_languges()
        
    def setup_layout(self):
        self.main_layout = QVBoxLayout(self)
        self.setLayout(self.main_layout)
        
        self.form_layout = QFormLayout()
        self.form_layout.setWidget(0, QFormLayout.LabelRole, self.label_ocr)
        self.form_layout.setWidget(0, QFormLayout.FieldRole, self.combo_box_ocr)
        self.form_layout.setWidget(1, QFormLayout.LabelRole, self.label_source_lang)
        self.form_layout.setWidget(1, QFormLayout.FieldRole, self.combo_box_source_lang)
        self.form_layout.setWidget(2, QFormLayout.LabelRole, self.label_subtitle_mode)
        self.form_layout.setWidget(2, QFormLayout.FieldRole, self.combo_box_subtitle_mode)
        self.form_layout.setWidget(3, QFormLayout.LabelRole, self.label_translator)
        self.form_layout.setWidget(3, QFormLayout.FieldRole, self.combo_box_translator)
        self.form_layout.setWidget(4, QFormLayout.LabelRole, self.label_target_lang)
        self.form_layout.setWidget(4, QFormLayout.FieldRole, self.combo_box_target_lang)

        self.main_layout.addLayout(self.form_layout)
        self.main_layout.addWidget(self.push_button)
        
        self.combo_box_ocr.currentIndexChanged.connect(self.update_supported_languages)
        self.combo_box_source_lang.currentIndexChanged.connect(self.update_target_languages)
        self.combo_box_target_lang.currentIndexChanged.connect(self.update_source_languges)
        self.push_button.clicked.connect(self.apply_configuration)
        self.push_button.clicked.connect(self.save_configuration)
    
    
    def update_supported_languages(self):
        """
        Updates the list of supported languages based on the selected OCR system.
        """
        selected_ocr = self.combo_box_ocr.currentText()
        supported_languages = self.ocr_systems[selected_ocr]
        source_language = self.combo_box_source_lang.currentText()
        self.combo_box_source_lang.clear()
        self.combo_box_source_lang.addItems(supported_languages)
        if source_language in supported_languages:
            self.combo_box_source_lang.setCurrentIndex(self.combo_box_source_lang.findText(source_language))
    
    
    def update_target_languages(self):
        source_language = self.combo_box_source_lang.currentText() # current detect language
        target_language = self.combo_box_target_lang.currentText() # current target language
        
        if source_language in self.target_languages:
            target_languages = list(filter(lambda x: x!=source_language, self.target_languages))
            self.combo_box_target_lang.currentIndexChanged.disconnect(self.update_source_languges)
            self.combo_box_target_lang.clear()
            self.combo_box_target_lang.addItems(target_languages)
            self.combo_box_target_lang.setCurrentIndex(self.combo_box_target_lang.findText(target_language))
            self.combo_box_target_lang.currentIndexChanged.connect(self.update_source_languges) 
        
        
    def update_source_languges(self):
        target_language = self.combo_box_target_lang.currentText() # current target language
        source_language = self.combo_box_source_lang.currentText() # current detect language
        supported_languages = self.ocr_systems[self.combo_box_ocr.currentText()] # Available languages for current ocr system
        
        if target_language in supported_languages:
            supported_languages = list(filter(lambda x: x!=target_language, supported_languages))
            self.combo_box_source_lang.currentIndexChanged.disconnect(self.update_target_languages)
            self.combo_box_source_lang.clear()
            self.combo_box_source_lang.addItems(supported_languages)
            self.combo_box_source_lang.setCurrentIndex(self.combo_box_source_lang.findText(source_language))
            self.combo_box_source_lang.currentIndexChanged.connect(self.update_target_languages) 
            
    
    def update_ocr_configuration(self):
        selected_ocr = self.combo_box_ocr.currentText()
        selected_language = self.combo_box_source_lang.currentText().lower()
        self.update_ocr_signal.emit(selected_ocr, selected_language)
        
    
    def update_subtitle_mode_configuration(self):
        selected_mode = self.combo_box_subtitle_mode.currentText()
        self.update_subtitle_signal.emit(selected_mode)
        
        
    def update_translator_configuration(self):
        selected_translator = self.combo_box_translator.currentText()
        selected_language = self.combo_box_target_lang.currentText()
        self.update_translator_signal.emit(selected_translator, selected_language)
    
        
    def apply_configuration(self):
        self.update_ocr_configuration()
        self.update_subtitle_mode_configuration()
        self.update_translator_configuration()
    
        
    def save_configuration(self):
        self.settings.beginGroup(APP_SETTINGS_GROUP)
        self.settings.setValue(
            OCR_SYSTEM_NAME_KEY, 
            self.combo_box_ocr.currentText()
        )
        self.settings.setValue(
            OCR_SYSTEM_LANGUAGE_KEY, 
            self.combo_box_source_lang.currentText().lower()
        )
        self.settings.setValue(
            SUBTITLE_MODE_NAME_KEY, 
            self.combo_box_subtitle_mode.currentText()
        )
        self.settings.setValue(
            TRANSLATOR_NAME_KEY, 
            self.combo_box_translator.currentText()
        )
        self.settings.setValue(
            TRANSLATOR_TARGET_LANGUAGE_KEY, 
            self.combo_box_target_lang.currentText().lower()
        )
        self.settings.endGroup()
        


class FontStyleSettingsWidget(QWidget):
    
    update_style_signal = pyqtSignal(dict)
    
    def __init__(self, main_window, parent=None):
        super(FontStyleSettingsWidget, self).__init__(parent=parent)
        self.settings = QSettings(SETTINGS_PATH, QSettings.IniFormat)
        self.main_window = main_window
        self.colors = {
            'white': QColor(255, 255, 255),
            'red': QColor(255, 0, 0),
            'blue': QColor(0, 0, 255),
            'green': QColor(0, 255, 0),
            'black': QColor(0, 0, 0),
        }
        self.text_params = self.main_window.text_style
        self.initUI()
        self.update_interface()
        
    
    def initUI(self):
        self.label_font = QLabel('Font')
        self.label_font.setMinimumWidth(100)
        self.combo_box_font = QFontComboBox()
        
        self.label_bold = QLabel('Bold')
        self.label_bold.setMinimumWidth(100)
        self.check_box_bold = QCheckBox()
        
        self.label_italic = QLabel('Italic')
        self.label_italic.setMinimumWidth(100)
        self.check_box_italic = QCheckBox()

        self.label_underline = QLabel('Underline')
        self.label_underline.setMinimumWidth(100)
        self.check_box_underline = QCheckBox()
        
        self.line_1 = QFrame()
        self.line_1.setFrameShape(QFrame.HLine)
        self.line_1.setFrameShadow(QFrame.Sunken)
        
        self.label_text_clr = QLabel('Text color')
        self.label_text_clr.setMinimumWidth(100)
        self.combo_box_text_clr = QComboBox()

        self.label_background_clr = QLabel('Background color')
        self.label_background_clr.setMinimumWidth(100)
        self.combo_box_background_clr = QComboBox()

        self.text_edit = QLineEdit('Example')
        self.text_edit.setFont(QFont(self.combo_box_font.currentText(), 20))
        self.push_button = QPushButton('Apply')
        
        self.combo_box_text_clr.addItems(self.colors.keys())
        self.combo_box_background_clr.addItems(self.colors.keys())
        
        self.setup_layout()


    def setup_layout(self):
        self.main_layout = QVBoxLayout(self)
        self.setLayout(self.main_layout)
        
        self.form_layout = QFormLayout()
        self.form_layout.setWidget(1, QFormLayout.LabelRole, self.label_font)
        self.form_layout.setWidget(1, QFormLayout.FieldRole, self.combo_box_font)
        self.form_layout.setWidget(2, QFormLayout.LabelRole, self.label_bold)
        self.form_layout.setWidget(2, QFormLayout.FieldRole, self.check_box_bold)
        self.form_layout.setWidget(3, QFormLayout.LabelRole, self.label_italic)
        self.form_layout.setWidget(3, QFormLayout.FieldRole, self.check_box_italic)
        self.form_layout.setWidget(4, QFormLayout.LabelRole, self.label_underline)
        self.form_layout.setWidget(4, QFormLayout.FieldRole, self.check_box_underline)
        self.form_layout.setWidget(5, QFormLayout.SpanningRole, self.line_1)
        self.form_layout.setWidget(6, QFormLayout.LabelRole, self.label_text_clr)
        self.form_layout.setWidget(6, QFormLayout.FieldRole, self.combo_box_text_clr)
        self.form_layout.setWidget(7, QFormLayout.LabelRole, self.label_background_clr)
        self.form_layout.setWidget(7, QFormLayout.FieldRole, self.combo_box_background_clr)
        
        self.main_layout.addLayout(self.form_layout)
        self.main_layout.addWidget(self.text_edit)
        self.main_layout.addWidget(self.push_button)
        
        self.combo_box_font.currentIndexChanged.connect(self.update_combo_box_font)
        self.combo_box_text_clr.currentIndexChanged.connect(self.update_text_color)
        self.combo_box_background_clr.currentIndexChanged.connect(self.update_background_color)
        self.check_box_bold.stateChanged.connect(self.set_bold)
        self.check_box_italic.stateChanged.connect(self.set_italic)
        self.check_box_underline.stateChanged.connect(self.set_underline)
        self.push_button.clicked.connect(self.apply)
        self.push_button.clicked.connect(self.save_params)

    
    def apply(self):
        self.update_style_signal.emit(self.text_params)
    
    
    def update_interface(self):
        self.combo_box_font.setCurrentIndex(self.combo_box_font.findText(self.text_params['font-family']))
        background_color = QColor(self.text_params['background-color'])
        text_color = QColor(self.text_params['color'])
        for color_name, color in self.colors.items():
            if color == text_color:
                self.combo_box_text_clr.setCurrentIndex(self.combo_box_text_clr.findText(color_name))
            if color == background_color:
                self.combo_box_background_clr.setCurrentIndex(self.combo_box_background_clr.findText(color_name))
        if self.text_params['font-weight'] == 'bold':
            self.check_box_bold.setChecked(True)
        if self.text_params['font-style'] == 'italic':
            self.check_box_italic.setChecked(True)
        if self.text_params['text-decoration'] == 'underline':
            self.check_box_underline.setChecked(True)
        
        
    def update_combo_box_font(self):
        self.text_params['font-family'] = self.combo_box_font.currentText()
        self.set_style()
        
        
    def update_text_color(self) -> None:
        selected_color = self.colors[self.combo_box_text_clr.currentText()]
        self.text_params['color'] = selected_color.name()
        self.set_style()
        
        
    def update_background_color(self) -> None:
        selected_color = self.colors[self.combo_box_background_clr.currentText()]
        self.text_params['background-color'] = selected_color.name()
        self.set_style()
        

    def set_style(self) -> None:
        self.text_edit.setStyleSheet(
            '; '.join([f'{k}: {v}' for k, v in self.text_params.items()])
        )
        

    def set_bold(self, checked: bool) -> None:
        self.text_params['font-weight'] = 'bold' if checked else 'normal'
        self.set_style()
        
        
    def set_italic(self, checked: bool) -> None:
        self.text_params['font-style'] = 'italic' if checked else 'normal'
        self.set_style()

        
    def set_underline(self, checked: bool) -> None:
        self.text_params['text-decoration'] = 'underline' if checked else 'none'
        self.set_style()
        
    
    def save_params(self):
        self.settings.beginGroup('SubtitleSettings')
        for key, value in self.text_params.items():
            self.settings.setValue(key, value)
        self.settings.endGroup()
        
