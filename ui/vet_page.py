import flet as ft
import psycopg2
from datetime import datetime
from db4 import get_all_animals
from ui.card import build_animal_card, cleanup_temp_images
from ui.tasks import build_tasks_section
from db4 import get_tasks_from_db, get_animals_from_db, update_animal_health_in_db, get_animal_health_logs, add_animal_health_log

conn = psycopg2.connect(
    dbname="shelter",
    user="postgres",
    password="root",
    host="localhost",
    port="5432"
)
cursor = conn.cursor()

def VetPage(page: ft.Page, current_user_id):
    def on_page_close(e):
        cleanup_temp_images()

    page.on_close = on_page_close
    content_area = ft.Column(expand=True)

    def show_tasks(e):
        content_area.controls.clear()
        content_area.controls.append(ft.Text("Задачи", size=24, weight=ft.FontWeight.BOLD, color = ft.Colors.GREY_700))
        tasks_section = build_tasks_section(
            conn=conn,
            page=page,
            user_id=current_user_id,
            is_director=False
        )
        content_area.controls.append(tasks_section)
        page.update()

    def show_animals(_):
        def load_animals(filter_health=None):
            animal_list.controls.clear()
            animals = get_all_animals()
            for animal in animals:
                if filter_health and animal[3] != filter_health:
                    continue
                card = build_animal_card(
                    animal,
                    for_staff=True,
                    on_edit_click=open_edit_dialog
                )
                animal_list.controls.append(card)
            page.update()

        animal_list = ft.Column()

        health_filter = ft.Dropdown(
            label="Фильтр по состоянию здоровья",
            options=[
                ft.dropdown.Option("все"),
                ft.dropdown.Option("котики-инвалиды"),
                ft.dropdown.Option("требуется лечение"),
                ft.dropdown.Option("хорошее"),
                ft.dropdown.Option("отличное"),
            ],
            width=300,
            text_style=ft.TextStyle(color=ft.Colors.GREY_700),
            on_change=lambda e: load_animals(e.control.value if e.control.value != "все" else None)
        )

        def open_edit_dialog(animal):
            animal_id, name, gender, health_status, care_status, admission_date, birth_date, character_description, reason, photo = animal

            health_input = ft.Dropdown(
                label="Состояние здоровья", 
                value=health_status,
                options=[
                    ft.dropdown.Option("котики-инвалиды"),
                    ft.dropdown.Option("требуется лечение"),
                    ft.dropdown.Option("хорошее"),
                    ft.dropdown.Option("отличное"),
                ],
                width=300,
                text_style=ft.TextStyle(color=ft.Colors.GREY_700),
            )

            def close_dialog(e, dlg):
                dlg.open = False
                page.update()

            def save_edit(e):
                update_animal_health_in_db(animal_id, health_input.value)
                dlg.open = False
                load_animals(health_filter.value if health_filter.value != "все" else None)
                page.open(ft.SnackBar(ft.Text("Информация о здоровье обновлена")))
                page.update()

            dlg = ft.AlertDialog(
                content=ft.Container(
                    width=300,
                    height=150,
                    content=ft.Column([
                        ft.Text(f"Редактирование здоровья: {name}", size=20, weight=ft.FontWeight.BOLD),
                        health_input,
                    ])
                ),
                actions=[
                    ft.TextButton("Сохранить", on_click=save_edit),
                    ft.TextButton("Отмена", on_click=lambda e: close_dialog(e, dlg))
                ]
            )
            page.overlay.append(dlg)
            page.dialog = dlg
            dlg.open = True
            page.update()

        content_area.controls.clear()
        content_area.controls.extend([
            ft.Text("Список животных", weight=ft.FontWeight.W_600, color=ft.Colors.GREY_700, size=24),
            health_filter,
            ft.Divider(),
            animal_list
        ])
        load_animals()

    def show_history(_):
        content_area.controls.clear()
        content_area.controls.append(ft.Text("История осмотров", size=24, weight=ft.FontWeight.BOLD, color = ft.Colors.GREY_700))

        cursor.execute("SELECT animal_id, name FROM animal ORDER BY name")
        animal_options = cursor.fetchall()

        selected_animal = ft.Ref[ft.Dropdown]()
        note_field = ft.Ref[ft.TextField]()
        history_list = ft.Column()

        def load_history(animal_id):
            history_list.controls.clear()
            logs = get_animal_health_logs(animal_id)
            for date, note in logs:
                history_list.controls.append(ft.Text(f"📅 {date.strftime('%Y-%m-%d')} — {note}", color = ft.Colors.GREY_700))
            page.update()

        def on_animal_change(e):
            aid = int(e.control.value)
            load_history(aid)

        def on_add_log(e):
            aid = int(selected_animal.current.value)
            note = note_field.current.value.strip()
            if note:
                add_animal_health_log(aid, current_user_id, note)
                note_field.current.value = ""
                load_history(aid)

        content_area.controls.extend([
            ft.Row([
                ft.Dropdown(
                    ref=selected_animal,
                    label="Выберите животное",
                    width=300,
                    text_style=ft.TextStyle(color=ft.Colors.GREY_700),
                    options=[ft.dropdown.Option(str(aid), name) for aid, name in animal_options],
                    on_change=on_animal_change
                ),
                ft.TextField(ref=note_field, label="Комментарий", width=300, text_style=ft.TextStyle(color=ft.Colors.GREY_700)),
                ft.ElevatedButton("Добавить запись", on_click=on_add_log, bgcolor=ft.Colors.PINK_50, color=ft.Colors.GREY_700)
            ], spacing=20),
            ft.Divider(),
            history_list
        ])
        page.update()

    def go_home(e):
        from ui.home import HomePage
        cleanup_temp_images()
        page.clean()
        page.add(HomePage(page))

    header = ft.Row(
        [ft.Container(
                    content=ft.Image(src="img/logo_grey700.png", width=100, height=150, fit=ft.ImageFit.FIT_HEIGHT),
                    padding=ft.padding.only(left=70)),
            ft.Container(content=ft.Text("Котик&Ко", size=40, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_700)),
            ft.Container(expand=True),
            ft.Container(
                content=ft.ElevatedButton(
                    "Назад",
                    on_click=go_home,
                    bgcolor=ft.Colors.PINK_50,
                    color=ft.Colors.GREY_700,
                    style=ft.ButtonStyle(
                        padding=15,
                        text_style=ft.TextStyle(size=20)
                    )
                ),
                padding=ft.padding.only(right=100)
            )
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        height=50,
    )


    nav_bar = ft.NavigationRail(
        destinations=[
            ft.NavigationRailDestination(icon=ft.Icon(ft.Icons.TASK, color=ft.Colors.GREY_700), label="Задачи"),
            ft.NavigationRailDestination(icon=ft.Icon(ft.Icons.PETS, color=ft.Colors.GREY_700), label="База животных"),
            ft.NavigationRailDestination(icon=ft.Icon(ft.Icons.HEALING, color=ft.Colors.GREY_700), label="История осмотров"),
        ],
        bgcolor=ft.Colors.GREY_300,
        selected_index=1,
        label_type=ft.NavigationRailLabelType.ALL,
        extended=True,
        on_change=lambda e: show_tasks(e) if e.control.selected_index == 0 else show_animals(e) if e.control.selected_index == 1 else show_history(e),
        unselected_label_text_style=ft.TextStyle(color=ft.Colors.GREY_700),
        selected_label_text_style=ft.TextStyle(color=ft.Colors.GREY_700, weight=ft.FontWeight.BOLD)
    )

    show_animals(None)

    return ft.Container(
        expand=True,
        content=ft.Column([
            ft.Container(content=header, padding=ft.padding.all(15), bgcolor=ft.Colors.PINK_50),
            ft.Container(
                expand=True,
                bgcolor=ft.Colors.PINK_50,
                padding=ft.padding.all(20),
                content=ft.Row([
                    ft.Container(content=nav_bar, width=250, bgcolor=ft.Colors.GREY_300, border_radius=20, padding=ft.padding.all(10)),
                    ft.Container(
                        expand=True,
                        border_radius=20,
                        bgcolor=ft.Colors.WHITE,
                        padding=ft.padding.all(30),
                        content=ft.Column(expand=True, scroll="auto", controls=[content_area])
                    )
                ], expand=True, spacing=20)
            )
        ], expand=True, spacing=0)
    )
