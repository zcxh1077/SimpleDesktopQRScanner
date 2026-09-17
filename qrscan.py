import ctypes
import ctypes.wintypes as wt
import sys
import tkinter as tk
import webbrowser

import zxingcpp
from PIL import Image

user32, gdi32 = ctypes.windll.user32, ctypes.windll.gdi32
user32.GetDC.restype = gdi32.CreateCompatibleDC.restype = gdi32.CreateCompatibleBitmap.restype = wt.HANDLE
user32.ReleaseDC.argtypes = [wt.HWND, wt.HANDLE]
gdi32.CreateCompatibleDC.argtypes = gdi32.DeleteDC.argtypes = gdi32.DeleteObject.argtypes = [wt.HANDLE]
gdi32.CreateCompatibleBitmap.argtypes = [wt.HANDLE, ctypes.c_int, ctypes.c_int]
gdi32.SelectObject.argtypes = [wt.HANDLE, wt.HANDLE]
gdi32.BitBlt.argtypes = [wt.HANDLE] + [ctypes.c_int] * 4 + [wt.HANDLE, ctypes.c_int, ctypes.c_int, wt.DWORD]
gdi32.GetBitmapBits.argtypes = [wt.HANDLE, ctypes.c_long, ctypes.c_void_p]
gdi32.CreateRectRgn.restype = wt.HANDLE
gdi32.CombineRgn.argtypes = [wt.HANDLE, wt.HANDLE, wt.HANDLE, ctypes.c_int]
user32.SetWindowRgn.argtypes = [wt.HWND, wt.HANDLE, wt.BOOL]
user32.GetWindowRect.argtypes = [wt.HWND, ctypes.POINTER(wt.RECT)]


def grab(x, y, width, height):
    # Copies only this rect (~8ms). PIL's ImageGrab copies the whole desktop (~80ms), which froze the UI.
    src = user32.GetDC(None)
    dc = gdi32.CreateCompatibleDC(src)
    bmp = gdi32.CreateCompatibleBitmap(src, width, height)
    gdi32.SelectObject(dc, bmp)
    gdi32.BitBlt(dc, 0, 0, width, height, src, x, y, 0x00CC0020)  # SRCCOPY
    buf = ctypes.create_string_buffer(width * height * 4)
    gdi32.GetBitmapBits(bmp, len(buf), buf)
    gdi32.DeleteObject(bmp)
    gdi32.DeleteDC(dc)
    user32.ReleaseDC(None, src)
    return Image.frombuffer("RGB", (width, height), buf, "raw", "BGRX")


def is_url(text):
    return text.startswith(("http://", "https://"))


def selftest():
    img = zxingcpp.create_barcode("https://example.com", zxingcpp.BarcodeFormat.QRCode).to_image(scale=4)
    [code] = zxingcpp.read_barcodes(img)
    assert code.text == "https://example.com" and is_url(code.text)
    assert not is_url("hello")
    print("ok")


class App:
    def __init__(self, root):
        self.root = root
        self.last = None
        root.title("SimpleDesktopQRScanner")
        root.geometry("360x420")
        root.attributes("-topmost", True)
        self.scan_area = tk.Frame(root, bg="#e33")  # the 3px left around the hole is the red frame
        self.scan_area.pack(fill="both", expand=True)
        self.scan_area.bind("<Configure>", self.cut_hole)
        self.results = tk.Frame(root, bg="#222")
        self.results.pack(fill="x")
        self.show([])
        self.scan()

    def cut_hole(self, _event):
        # Cut a real hole in the window instead of using -transparentcolor. With that, Windows passed
        # clicks through the whole window, so the buttons and links couldn't be clicked.
        hwnd = int(self.root.wm_frame(), 16)
        rect = wt.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        a = self.scan_area
        left, top = a.winfo_rootx() - rect.left + 3, a.winfo_rooty() - rect.top + 3
        region = gdi32.CreateRectRgn(0, 0, rect.right - rect.left, rect.bottom - rect.top)
        hole = gdi32.CreateRectRgn(left, top, left + a.winfo_width() - 6, top + a.winfo_height() - 6)
        gdi32.CombineRgn(region, region, hole, 4)  # RGN_DIFF
        gdi32.DeleteObject(hole)
        user32.SetWindowRgn(hwnd, region, True)  # Windows takes ownership of region

    def scan(self):
        a = self.scan_area
        x, y, w, h = a.winfo_rootx() + 3, a.winfo_rooty() + 3, a.winfo_width() - 6, a.winfo_height() - 6
        if w > 10 and h > 10:
            texts = [c.text for c in zxingcpp.read_barcodes(grab(x, y, w, h)) if c.text]
            # Leave the last result up when nothing is found, so its buttons don't vanish while you click
            if texts and texts != self.last:
                self.show(texts)
        self.root.after(300, self.scan)

    def show(self, texts):
        self.last = texts
        for child in self.results.winfo_children():
            child.destroy()
        if not texts:
            tk.Label(self.results, text="QRコードを枠内に入れてください", fg="#aaa", bg="#222").pack(pady=6)
        for text in texts:
            row = tk.Frame(self.results, bg="#222")
            row.pack(fill="x", padx=6, pady=3)
            if is_url(text):
                link = tk.Label(row, text=text, fg="#6af", bg="#222", cursor="hand2",
                                font=("Segoe UI", 10, "underline"), wraplength=320, justify="left")
                link.pack(side="left")
                link.bind("<Button-1>", lambda e, t=text: webbrowser.open(t))
            else:
                tk.Button(row, text="コピー", command=lambda t=text: self.copy(t)).pack(side="right")
                tk.Label(row, text=text, fg="#eee", bg="#222", wraplength=260, justify="left").pack(side="left")

    def copy(self, text):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # tk coords must match screenshot pixels
        root = tk.Tk()
        App(root)
        root.mainloop()
