import numpy as np
from typing import Tuple

import win32gui
import win32ui
import ctypes
from ctypes import windll, wintypes


class WINDOWPLACEMENT(ctypes.Structure):
    _fields_ = [
        ("length", wintypes.UINT),
        ("flags", wintypes.UINT),
        ("showCmd", wintypes.INT),
        ("ptMinPosition", wintypes.POINT),
        ("ptMaxPosition", wintypes.POINT),
        ("rcNormalPosition", wintypes.RECT),
    ]
    
class ScreenCapture():
    def __init__(self):
        self.user32 = ctypes.WinDLL('user32')
        self.rect = ctypes.wintypes.RECT()
        

    def window_state(self, hWnd: int) -> int:
        placement = WINDOWPLACEMENT()
        placement.length = ctypes.sizeof(WINDOWPLACEMENT)

        if self.user32.GetWindowPlacement(hWnd, ctypes.byref(placement)):
            if placement.showCmd == 3: # 3 == SW_SHOWMAXIMIZED (Fullscreen)
                return placement.showCmd
            elif placement.showCmd == 1: # 1 == SW_SHOWNORMAL (Window)
                return placement.showCmd
            elif placement.showCmd == 2: # 2 == SW_SHOWMINIMIZED (Minimize)
                raise Exception("Window is Minimized")
            else:
                raise Exception("Unknown window state")
        else:
            raise Exception("Error while retrieving window location information")


    def active_window_hwnd(self) -> int:
        hwnd = self.user32.GetForegroundWindow()
        if not hwnd:
            raise Exception("No Active Window")
        return hwnd


    def window_rect(self, hWnd: int) -> Tuple[int, int, int, int]:
        self.user32.GetWindowRect(hWnd, ctypes.pointer(self.rect))
        return self.rect.left, self.rect.top, self.rect.right, self.rect.bottom
    

    def grab(
        self, 
        hWnd: int = None, 
        monitor_rect: Tuple[int, int, int, int] = None, 
        area: Tuple[int, int, int, int] = None
    ) -> np.ndarray:
        if not hWnd:
            hWnd = self.active_window_hwnd()
            
        left, top, right, bottom = self.window_rect(hWnd)
        width = right - left
        height = bottom - top
    
        area_left, area_top, area_width, area_height = area if area else monitor_rect

        
        hwndDC = win32gui.GetWindowDC(hWnd)
        mfcDC  = win32ui.CreateDCFromHandle(hwndDC)
        saveDC = mfcDC.CreateCompatibleDC()

        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
        saveDC.SelectObject(saveBitMap)

        result = windll.user32.PrintWindow(hWnd, saveDC.GetSafeHdc(), 2)

        bmpinfo = saveBitMap.GetInfo()
        bmpstr = saveBitMap.GetBitmapBits(True)

        img = np.frombuffer(bmpstr, np.uint8) \
            .reshape(bmpinfo["bmHeight"], bmpinfo["bmWidth"], -1)[..., 2::-1][:,:,:3]

        win32gui.DeleteObject(saveBitMap.GetHandle())
        saveDC.DeleteDC()
        mfcDC.DeleteDC()
        win32gui.ReleaseDC(hWnd, hwndDC)
        
        if not result:
            raise Exception('Failed to capture a window')
        
        full_img = np.zeros(
            shape=(area_height,  area_width, 3), dtype=np.uint8
        )
        
        # If the region does not contain an application window
        if (area_top + area_height < top) or \
           (area_left + area_width < left) or \
           (area_left > right) or \
           (area_top > bottom):
            return full_img  
         
        img = img[
            max(area_top - top, 0): min(area_top+area_height-top, height), 
            max(area_left - left, 0): min(area_left+area_width-left, width), 
            :
        ]

        full_img[
            max((top - area_top), 0): max((top - area_top), 0)+img.shape[0],
            max((left - area_left), 0): max((left - area_left), 0)+img.shape[1],
            :      
        ] = img

        return full_img