import os
from datetime import date, datetime
import flet as ft
import tempfile
import uuid

temp_image_files = []

def save_temp_image(image_bytes, ext="jpg"):
    temp_dir = tempfile.gettempdir()
    filename = f"{uuid.uuid4()}.{ext}"
    file_path = os.path.join(temp_dir, filename)

    with open(file_path, "wb") as f:
        f.write(image_bytes)

    temp_image_files.append(file_path)
    return file_path

def cleanup_temp_images():
    for path in temp_image_files:
        try:
            os.remove(path)
        except Exception as e:
            print(f"Не удалось удалить временный файл {path}: {e}")
    temp_image_files.clear()

def format_age(birth_date):
    today = date.today()
    years = today.year - birth_date.year
    months = today.month - birth_date.month
    if today.day < birth_date.day:
        months -= 1
    if months < 0:
        years -= 1
        months += 12
    if years == 0:
        return f"{months} мес."
    elif 1 <= years <= 4:
        return f"{years} года {months} мес." if months > 0 else f"{years} года"
    else:
        return f"{years} лет"

def build_animal_card(animal, for_staff=False, on_edit_click=None, on_name_click=None, custom_button_text=None):
    animal_id, name, gender, health_status, care_status, admission_date, birth_date, character_description, reason, photo = animal
    image_src = save_temp_image(photo) if photo else "assets/cat_default.jpg"

    if isinstance(birth_date, str):
        try:
            birth_date = datetime.strptime(birth_date, "%Y-%m-%d").date()
        except ValueError:
            birth_date = date.today()

    age = format_age(birth_date)

    if for_staff:
        # staff-style card
        button_label = custom_button_text or "Редактировать"

        image_control = ft.Image(
            src=image_src,
            width=300,
            height=200,
            fit=ft.ImageFit.COVER,
            border_radius=10
        )

        info_column = ft.Column([
            ft.Text(f"Имя: {name}", weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
            ft.Text(f"Пол: {gender}", color=ft.Colors.GREY_700),
            ft.Text(f"Возраст: {age}", color=ft.Colors.GREY_700),
            ft.Text(f"Здоровье: {health_status}", color=ft.Colors.GREY_700),
            ft.Text(f"Опека: {care_status}", color=ft.Colors.GREY_700),
            ft.Text(f"Поступление: {admission_date.strftime('%d.%m.%Y')}", color=ft.Colors.GREY_700),
            ft.Text(f"Характер: {character_description}", color=ft.Colors.GREY_700),
            ft.Text(f"Причина: {reason}", color=ft.Colors.GREY_700),
        ], spacing=3, expand=True)

        button = ft.ElevatedButton(
            button_label,
            bgcolor=ft.Colors.PINK_50,
            color=ft.Colors.GREY_700,
            on_click=lambda e: on_edit_click(animal) if on_edit_click else None
        )

        return ft.Container(
            content=ft.Row([
                image_control,
                ft.Container(info_column, expand=True, padding=10),
                ft.Container(button, alignment=ft.alignment.bottom_right)
            ], alignment=ft.MainAxisAlignment.START),
            border_radius=15,
            padding=10,
            bgcolor=ft.Colors.GREY_100,
            margin=5,
        )

    else:
        # home-style tile card
        adopt_button = None
        if on_edit_click:
            adopt_button = ft.ElevatedButton(
                custom_button_text or "Взять под опеку",
                bgcolor=ft.Colors.PINK_50,
                color=ft.Colors.GREY_700,
                on_click=lambda e: on_edit_click(animal)
            )

        return ft.Container(
            content=ft.Column([
                ft.Container(
                    height=250,
                    width=320,
                    clip_behavior=ft.ClipBehavior.HARD_EDGE,
                    border_radius=20,
                    content=ft.Image(src=image_src, fit=ft.ImageFit.COVER, width=400, height=220)
                ),
                ft.Container(
                    height=340,
                    width=320,
                    bgcolor=ft.Colors.PINK_50,
                    border_radius=ft.border_radius.only(bottom_left=20, bottom_right=20),
                    padding=10,
                    content=ft.Column([
                        ft.Text(name, size=20, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_800),
                        ft.Text(f"{'Кот' if gender == 'кот' else 'Кошка'}", size=17, color=ft.Colors.GREY_800),
                        ft.Text(f"Возраст: {age}", size=17, color=ft.Colors.GREY_800),
                        ft.Text(f"Состояние здоровья: {health_status}", size=17, color=ft.Colors.GREY_800),
                        ft.Text(f"Опека: {care_status}", size=17, color=ft.Colors.GREY_800),
                        ft.Text(f"Поступление: {admission_date.strftime('%d.%m.%Y')}", size=17, color=ft.Colors.GREY_800),
                        ft.Text(f"{character_description} {reason}", size=17, max_lines=4, overflow="ellipsis", color=ft.Colors.GREY_800),
                        ft.Container(
                            content=adopt_button,
                            alignment=ft.alignment.bottom_right,
                            padding=ft.padding.only(top=10),
                            expand=True
                        ) if adopt_button else ft.Container()
                    ], spacing=3)
                )
            ], spacing=0),
            padding=ft.padding.only(left=33, top=30, right=33),
            col={"xs": 12, "sm": 6, "md": 4, "lg": 3}
        )

