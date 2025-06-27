import flet as ft
from datetime import date
from db4 import get_all_animals
from ui.login import LoginPage
from ui.donations import DonationsPage
from ui.card import build_animal_card, cleanup_temp_images

def HomePage(page: ft.Page):
    selected_filters = {
        "gender": "Все",
        "age": "Все",
        "health": "Все",
        "care": "Все"
    }

    def filter_animals():
        age_filter = selected_filters["age"]
        age_range = None
        if age_filter == "до года":
            age_range = (0, 1)
        elif age_filter == "1 - 5 лет":
            age_range = (1, 5)
        elif age_filter == "6 - 10 лет":
            age_range = (6, 10)
        elif age_filter == "от 10 лет":
            age_range = (10, 100)

        animals = get_all_animals(
            gender=None if selected_filters["gender"] == "Все" else selected_filters["gender"],
            age_range=age_range,
            health=None if selected_filters["health"] == "Все" else selected_filters["health"],
            care=None if selected_filters["care"] == "Все" else selected_filters["care"]
        )

        animal_cards.controls.clear()
        for animal in animals:
          card = build_animal_card(
            animal,
            for_staff=False
            #on_name_click=lambda a, img, age: open_animal(
            #  page, a[0], img, age, a[2], a[3], a[4], a[5], a[6], a[7]
            #)
          )
          animal_cards.controls.append(card)
        page.update()

        

    def on_filter_change(e):
        selected_filters[e.control.data] = e.control.value
        filter_animals()

    def create_filter_group(title, options, filter_key):
       radio_style = ft.TextStyle(color=ft.Colors.GREY_800)
       return ft.Column([
        ft.Text(title, weight=ft.FontWeight.W_600, size=16, color=ft.Colors.GREY_700),
        ft.RadioGroup(
            value="Все",
            on_change=on_filter_change,
            data=filter_key,
            content=ft.Column(
                [ft.Radio(value="Все", label="Все", label_style=radio_style)] +
                [ft.Radio(value=o, label=o, label_style=radio_style) for o in options]
            )
        )
    ], spacing=10)


    filter_panel = ft.Row(
    controls=[
        ft.Container(
            padding=20,
            border=ft.border.all(1, ft.Colors.GREY_700),
            border_radius=12,
            bgcolor=ft.Colors.GREY_300,
            content=ft.Row([
                ft.Container(width=260, content=create_filter_group("Пол", ["Кот", "Кошка"], "gender")),
                ft.Container(width=300, content=create_filter_group("Возраст", ["до года", "1 - 5 лет", "6 - 10 лет", "от 10 лет"], "age")),
                ft.Container(width=320, content=create_filter_group("Здоровье", ["котики-инвалиды", "требуется лечение", "хорошее", "отличное"], "health")),
                ft.Container(width=260, content=create_filter_group("Опека", ["доступна", "под опекой"], "care")),
            ], spacing=50, wrap=False,alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.START )
        )
    ],
       #alignment=ft.MainAxisAlignment.SPACE_BETWEEN
    )


    animal_cards = ft.ResponsiveRow(spacing=-40, run_spacing=20, alignment=ft.MainAxisAlignment.CENTER)
    filter_animals()

    animal_section = ft.Column([
    ft.Container(
    padding=ft.padding.only(left=30),
    content=ft.Text("🐾 Наши котики", size=40, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_700)),
    ft.Row([filter_panel],
        alignment=ft.MainAxisAlignment.CENTER,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=30
    ),ft.Container(content=animal_cards, expand=True, alignment=ft.alignment.center)
], spacing=40)



    def open_login(e):
        cleanup_temp_images()
        page.clean()
        page.add(LoginPage(page))
        
    def open_donations(e):
        cleanup_temp_images()
        page.clean()
        page.add(DonationsPage(page))
    
    def go_home(e):
        page.clean()
        page.add(HomePage(page))

    def on_page_close(e):
        cleanup_temp_images()

    page.on_close = on_page_close

    header = ft.Row(
    [
        ft.GestureDetector(
            on_tap=go_home,
            content=ft.Container(
                content=ft.Image(src="/assets/logo_grey700.png", width=100, height=150, fit=ft.ImageFit.FIT_HEIGHT),
                padding=ft.padding.only(left=70)
            )
        ),
        ft.Container(
            content=ft.Text(
                "Котик&Ко",
                size=40,
                weight=ft.FontWeight.W_600,
                color=ft.Colors.GREY_700
            ),
            #padding=ft.padding.only(left=5)
        ),
        ft.Container(expand=True),
        ft.Container(
            content=ft.Row([
                ft.ElevatedButton(
                    "Пожертвовать",
                    on_click=open_donations,
                    bgcolor=ft.Colors.GREY_700,
                    color=ft.Colors.WHITE,
                    style=ft.ButtonStyle(
                        padding=15,
                        text_style=ft.TextStyle(size=20))
                ),
                ft.ElevatedButton(
                    "Вход",
                    on_click=open_login,
                    bgcolor=ft.Colors.PINK_50,
                    color=ft.Colors.GREY_700,
                    style=ft.ButtonStyle(
                        padding=15,
                        text_style=ft.TextStyle(size=20))
                )
            ], spacing=20),
            padding=ft.padding.only(right=70)
        )
    ],
    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    vertical_alignment=ft.CrossAxisAlignment.CENTER,
    height=50
)
    
    main_section = ft.Row([
        ft.Container(
            content=ft.Image(src="assets/cat_main.png", width=850, height=500, fit=ft.ImageFit.FIT_HEIGHT),
            alignment=ft.alignment.center
        ),
        ft.Container(
            content=ft.Column([
                ft.Text("ПРИЮТ\nДЛЯ КОШЕК", size=55, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_700),
                ft.Text("Здесь вы можете найти\nсвоего друга", size=25, color=ft.Colors.GREY_700),
            ], spacing=20, alignment=ft.MainAxisAlignment.CENTER)
        )
    ], alignment=ft.MainAxisAlignment.START, spacing=40, height=460)

    return ft.Container(
    content=ft.Column(
        [
            ft.Container(content=header, padding=ft.padding.all(15), bgcolor=ft.Colors.PINK_50),
            ft.Container(content=main_section, padding=0, bgcolor=ft.Colors.GREY_400),
            #ft.Container(content=filter_panel, padding=ft.padding.only(left=70, right=70, top=30)),
            ft.Container(content=animal_section, padding=ft.padding.only(left=70, top=30, right=70), bgcolor=ft.Colors.PINK_50, expand=True)
        ],
        spacing=0,
        scroll="auto",
        expand=True
    ),
    expand=True
)
