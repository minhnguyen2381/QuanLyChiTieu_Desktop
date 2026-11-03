"""Màn hình 'Đang kết nối...' chạy connect() ở thread nền, có Thử lại / Thoát khi lỗi."""
import threading
import tkinter as tk
from tkinter import ttk

from app.presentation.i18n import t

POLL_MS = 100


class LoadingWindow(tk.Tk):
    def __init__(self, connect):
        super().__init__()
        self._connect = connect
        self._outcome = None  # ("ok", value) | ("error", exception), ghi từ thread nền
        self.result = None

        self.title(t("loading.title"))
        self.geometry("400x150")
        self.eval("tk::PlaceWindow . center")
        self.resizable(False, False)

        self._label = ttk.Label(self, text=t("loading.connecting"), font=("Arial", 11))
        self._label.pack(expand=True, pady=(20, 5))
        self._progress = ttk.Progressbar(self, mode="indeterminate")
        self._progress.pack(fill=tk.X, padx=30, pady=(0, 20))
        self._buttons = None
        self._start()

    def _start(self):
        self._outcome = None
        self._progress.start()
        threading.Thread(target=self._run_connect, daemon=True).start()
        self.after(POLL_MS, self._poll)

    def _run_connect(self):
        try:
            self._outcome = ("ok", self._connect())
        except Exception as error:
            self._outcome = ("error", error)

    def _poll(self):
        # Tkinter không an toàn khi gọi từ thread khác, nên thread chính tự kiểm tra kết quả.
        if self._outcome is None:
            self.after(POLL_MS, self._poll)
            return
        status, value = self._outcome
        if status == "ok":
            self.result = value
            self.destroy()
        else:
            self._show_error()

    def _show_error(self):
        self._progress.stop()
        self._label.config(text=t("loading.error"), foreground="red")
        self._buttons = ttk.Frame(self)
        self._buttons.pack(pady=10)
        ttk.Button(self._buttons, text=t("loading.retry"), command=self._retry).pack(side=tk.LEFT, padx=5)
        ttk.Button(self._buttons, text=t("loading.exit"), command=self.destroy).pack(side=tk.LEFT, padx=5)

    def _retry(self):
        self._buttons.destroy()
        self._label.config(text=t("loading.reconnecting"), foreground="black")
        self._start()
