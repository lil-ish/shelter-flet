import flet as ft
from ui.home import HomePage

def main(page: ft.Page):
    page.title = "Приют для котиков"
    page.window.maximized = True
    page.padding = 0
    page.add(HomePage(page))

ft.app(target=main)
