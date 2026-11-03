"""Tiện ích dùng chung cho các cửa sổ Tkinter."""
from contextlib import contextmanager
from tkinter import messagebox

from tkcalendar import DateEntry

from app.application.report_service import NoDataError
from app.domain.entities import InvalidTransaction
from app.presentation.i18n import t


@contextmanager
def reported_errors(parent):
    """Bắt lỗi trong khối `with` và báo bằng messagebox đã dịch.

    Khi có lỗi, các dòng còn lại trong khối không chạy; chương trình tiếp tục sau khối.
    """
    try:
        yield
    except InvalidTransaction:
        messagebox.showerror(t("dialog.error"), t("error.invalid_transaction"), parent=parent)
    except NoDataError:
        messagebox.showerror(t("dialog.error"), t("error.no_data"), parent=parent)
    except (FileNotFoundError, PermissionError) as error:
        messagebox.showerror(t("dialog.error"), t("error.file", detail=error), parent=parent)
    except Exception as error:  # Firestore/mạng: báo cho người dùng thay vì chỉ in traceback
        messagebox.showerror(t("dialog.error"), t("error.generic", detail=error), parent=parent)


def make_date_entry(parent, value=None) -> DateEntry:
    entry = DateEntry(parent, width=12, background="darkblue", foreground="white", borderwidth=2,
                      date_pattern="dd/mm/yyyy")  # khớp formatters.DATE_FORMAT
    if value is not None:
        entry.set_date(value)
    return entry
