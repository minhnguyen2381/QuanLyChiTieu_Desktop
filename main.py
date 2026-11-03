from app.container import build_services
from app.presentation.loading_window import LoadingWindow
from app.presentation.main_window import MainWindow


def main():
    loading = LoadingWindow(connect=build_services)
    loading.mainloop()
    if loading.result is not None:
        MainWindow(loading.result).mainloop()


if __name__ == "__main__":
    main()
