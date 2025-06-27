import flet as ft
from auth import authenticate_user
import flet as ft
from db4 import authenticate_user
from ui.director import DirectorPage
from ui.staff_page import StaffPage
from ui.guardian_page import GuardianPage
from ui.vet_page import VetPage

def LoginPage(page: ft.Page):
    email = ft.TextField(label="Логин", width=300, text_style=ft.TextStyle(color=ft.Colors.GREY_700))
    password = ft.TextField(label="Пароль", password=True, can_reveal_password=True, width=300, text_style=ft.TextStyle(color=ft.Colors.GREY_700))
    error_text = ft.Text("", color=ft.Colors.RED)
    
    def on_home_click(e):
        from ui.home import HomePage
        page.clean()
        page.add(HomePage(page))
        
    def on_login_click(e):
      role_info = authenticate_user(email.value, password.value)
      if role_info:
          role, user_id, is_deleted = role_info 
          if is_deleted:
              error_text.value = "Ваш аккаунт деактивирован. Обратитесь к администратору."
              page.update()
              return
              
          page.session.set("user_id", user_id)
          page.clean()
          if role == "Директор":
              page.add(DirectorPage(page, current_user_id=user_id))
          elif role == "Сотрудник":
              page.add(StaffPage(page, current_user_id=user_id))
          elif role == "Попечитель":
              page.add(GuardianPage(page, current_user_id=user_id))
          elif role == "Ветеринар":
              page.add(VetPage(page, current_user_id=user_id))
      else:
          error_text.value = "Неверный логин или пароль"
          page.update()

    return ft.Container(
        expand=True,
        alignment=ft.alignment.center,
        bgcolor=ft.Colors.PINK_50,
        content=ft.Column(
            [
                ft.Text("Котик&Ко", size=36, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_700),
                ft.Text("Вход", size=44, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
                email,
                password,
                error_text,
                ft.ElevatedButton(
                    text="Войти",
                    bgcolor=ft.Colors.GREY_700,
                    color=ft.Colors.WHITE,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=30), padding=ft.padding.all(20)),
                    on_click=on_login_click
                ),
                ft.TextButton(
                    text="Назад",
                    style=ft.ButtonStyle(color=ft.Colors.GREY_800),
                    on_click=on_home_click,
                    #color=ft.Colors.GREY_700
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20
        )
    )