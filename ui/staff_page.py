import flet as ft
import psycopg2
from datetime import datetime
from db4 import get_all_animals
from ui.card import build_animal_card, cleanup_temp_images
from ui.tasks import build_tasks_section
from db4 import get_tasks_from_db, get_animals_from_db, add_animal_to_db, update_animal_in_db, delete_animal_from_db

conn = psycopg2.connect(
    dbname="shelter",
    user="postgres",
    password="root",
    host="localhost",
    port="5432"
)
cursor = conn.cursor()

def StaffPage(page: ft.Page, current_user_id):
    
    def on_page_close(e):
        cleanup_temp_images()

    page.on_close = on_page_close
    content_area = ft.Column(expand=True)
    
    def show_tasks(e):
        content_area.controls.clear()
        content_area.controls.append(ft.Text("Задачи", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700))
    
        tasks_section = build_tasks_section(
            conn=conn,
            page=page,
            user_id=current_user_id,
            is_director=False
        )
    
        content_area.controls.append(tasks_section)
        page.update()
            
    def show_animals(_):
      state = {
          "selected_image_bytes": None,
          "editing_animal": None,
          "current_photo": None
      }
  
      selected_file_path = ft.Text()
      animal_list = ft.Column(scroll=ft.ScrollMode.AUTO)
  
      file_picker = ft.FilePicker()
      def pick_file_result(e: ft.FilePickerResultEvent):
        if e.files:
            try:
                file_path = e.files[0].path
                with open(file_path, "rb") as f:
                    state["selected_image_bytes"] = f.read()
    
                if state["editing_animal"]:
                    edit_photo_text.value = e.files[0].name
                else:
                    selected_file_path.value = e.files[0].name
    
                page.open(ft.SnackBar(ft.Text("Фото успешно загружено")))
            except Exception as ex:
                page.open(ft.SnackBar(ft.Text(f"Ошибка загрузки файла: {str(ex)}")))
            page.update()

      file_picker.on_result = pick_file_result
      page.overlay.append(file_picker)
  
      name_field = ft.TextField(label="Имя", width=300)
      gender_field = ft.Dropdown(label="Пол", options=[ft.dropdown.Option("кот"), ft.dropdown.Option("кошка")], width=300)
      health_status_field = ft.Dropdown(label="Состояние здоровья", options=[
          ft.dropdown.Option("котики-инвалиды"),
          ft.dropdown.Option("требуется лечение"),
          ft.dropdown.Option("хорошее"),
          ft.dropdown.Option("отличное"),
      ], width=300)
      care_status_field = ft.Dropdown(label="Опека", options=[
          ft.dropdown.Option("доступна"),
          ft.dropdown.Option("под опекой"),
      ], width=300)
      admission_date_field = ft.TextField(label="Дата поступления (ГГГГ-ММ-ДД)", width=300)
      birth_date_field = ft.TextField(label="Дата рождения (ГГГГ-ММ-ДД)", width=300)
      character_description_field = ft.TextField(label="Описание", width=300, multiline=True)
      reason_field = ft.TextField(label="Почему в приюте", width=300, multiline=True)
  
      def reset_fields():
          for f in [name_field, gender_field, health_status_field, care_status_field,
                    admission_date_field, birth_date_field, character_description_field, reason_field]:
              f.value = ""
          selected_file_path.value = ""
          state["selected_image_bytes"] = None
          state["current_photo"] = None
          page.update()
  
      def submit_animal(_):
          if not name_field.value:
              page.open(ft.SnackBar(ft.Text("Введите имя животного"), open=True))
              page.update()
              return
  
          try:
              photo_bytes = state["selected_image_bytes"]
              add_animal_to_db(
                  name_field.value,
                  gender_field.value,
                  health_status_field.value,
                  care_status_field.value,
                  admission_date_field.value,
                  birth_date_field.value,
                  character_description_field.value,
                  reason_field.value,
                  photo_bytes
              )
              reset_fields()
              load_animals()
              page.open(ft.SnackBar(ft.Text("Животное успешно добавлено"), open=True))
          except Exception as ex:
              page.open(ft.SnackBar(ft.Text(f"Ошибка: {str(ex)}"), open=True))
          page.update()

      edit_name = ft.TextField(label="Имя", width=300)
      edit_gender = ft.Dropdown(label="Пол", options=[ft.dropdown.Option("кот"), ft.dropdown.Option("кошка")], width=300)
      edit_health = ft.Dropdown(label="Состояние здоровья", options=[
          ft.dropdown.Option("котики-инвалиды"),
          ft.dropdown.Option("требуется лечение"),
          ft.dropdown.Option("хорошее"),
          ft.dropdown.Option("отличное"),
      ], width=300)
      edit_care = ft.Dropdown(label="Опека", options=[
          ft.dropdown.Option("доступна"),
          ft.dropdown.Option("под опекой"),
      ], width=300)
      edit_admission = ft.TextField(label="Дата поступления", width=300)
      edit_birth = ft.TextField(label="Дата рождения", width=300)
      edit_description = ft.TextField(label="Описание", width=300, multiline=True)
      edit_reason = ft.TextField(label="Почему в приюте", width=300, multiline=True)
      edit_photo_text = ft.Text("Фото не выбрано")
  
      def close_dialog():
          dlg.open = False
          page.update()
  
      def pick_edit_photo(e):
          file_picker.pick_files(
              allow_multiple=False,
              allowed_extensions=["jpg", "jpeg", "png"],
              dialog_title="Выберите фото животного"
          )
  
      def save_edit_animal(e):
          try:
              animal_id = state["editing_animal"][0]
              photo_bytes = state["selected_image_bytes"] or state["current_photo"]
  
              update_animal_in_db(
                  animal_id,
                  edit_name.value,
                  edit_gender.value,
                  edit_health.value,
                  edit_care.value,
                  edit_admission.value,
                  edit_birth.value,
                  edit_description.value,
                  edit_reason.value,
                  photo_bytes
              )
              close_dialog()
              state["editing_animal"] = None
              state["selected_image_bytes"] = None
              state["current_photo"] = None
              load_animals()
              page.open(ft.SnackBar(ft.Text("Животное обновлено"), open=True))
              page.update()
          except Exception as ex:
              page.open(ft.SnackBar(ft.Text(f"Ошибка сохранения: {str(ex)}"), open=True))
              page.update()
  
      def edit_animal(animal):
          state["editing_animal"] = animal
          state["selected_image_bytes"] = None
  
          animal_id, name, gender, health, care, admission, birth, desc, reason, photo = animal
          state["current_photo"] = photo
  
          edit_name.value = name
          edit_gender.value = gender
          edit_health.value = health
          edit_care.value = care
          edit_admission.value = admission.strftime("%Y-%m-%d") if isinstance(admission, datetime) else admission
          edit_birth.value = birth.strftime("%Y-%m-%d") if isinstance(birth, datetime) else birth
          edit_description.value = desc
          edit_reason.value = reason
          edit_photo_text.value = "Фото выбрано" if photo else "Фото не загружено"
  
          dlg.open = True
          page.update()
  
      dlg = ft.AlertDialog(
          modal=True,
          title=ft.Text("Редактировать животное"),
          content=ft.Column([
              edit_name, edit_gender, edit_health, edit_care,
              edit_admission, edit_birth, edit_description, edit_reason,
              ft.ElevatedButton("Выбрать изображение", on_click=pick_edit_photo),
              edit_photo_text
          ]),
          actions=[
              ft.TextButton("Сохранить", on_click=save_edit_animal),
              ft.TextButton("Отмена", on_click=lambda e: close_dialog())
          ]
      )
      page.overlay.append(dlg)
  
      def load_animals():
          animal_list.controls.clear()
          animals = get_all_animals()
          for animal in animals:
              card = build_animal_card(
                  animal,
                  for_staff=True,
                  on_edit_click=edit_animal,
                  custom_button_text="Редактировать"
              )
              animal_list.controls.append(card)
          page.update()
  
      submit_button = ft.ElevatedButton("Добавить", on_click=submit_animal)
  
      content_area.controls.clear()
      content_area.controls.extend([
          ft.Text("Добавить животное", size=24, weight=ft.FontWeight.W_600),
          name_field, gender_field, health_status_field, care_status_field,
          admission_date_field, birth_date_field, character_description_field, reason_field,
          ft.ElevatedButton("Выбрать изображение", on_click=lambda _: file_picker.pick_files(
              allow_multiple=False,
              allowed_extensions=["jpg", "jpeg", "png"],
              dialog_title="Выберите фото животного"
          )),
          selected_file_path,
          submit_button,
          ft.Divider(),
          ft.Text("Список животных", size=24, weight=ft.FontWeight.W_600),
          animal_list
      ])
      load_animals()
    
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
        ],
        bgcolor=ft.Colors.GREY_300,
        selected_index=1,
        label_type=ft.NavigationRailLabelType.ALL,
        extended=True,
        on_change=lambda e: show_tasks(e) if e.control.selected_index == 0 else show_animals(e),
        unselected_label_text_style=ft.TextStyle(color=ft.Colors.GREY_700),
        selected_label_text_style=ft.TextStyle(color=ft.Colors.GREY_700, weight=ft.FontWeight.BOLD)
    )

    show_animals(None)

    return ft.Container(
        expand=True,
        content=ft.Column(
            controls=[
                ft.Container(
                    content=header,
                    padding=ft.padding.all(15),
                    bgcolor=ft.Colors.PINK_50
                ),
                ft.Container(
                    expand=True,
                    bgcolor=ft.Colors.PINK_50,
                    padding=ft.padding.all(20),
                    content=ft.Row(
                        expand=True,
                        spacing=20,
                        controls=[
                            ft.Container(
                                content=nav_bar,
                                width=250,
                                bgcolor=ft.Colors.GREY_300,
                                border_radius=20,
                                padding=ft.padding.all(10)
                            ),
                            ft.Container(
                                expand=True,
                                border_radius=20,
                                bgcolor=ft.Colors.WHITE,
                                padding=ft.padding.all(30),
                                content=ft.Column(
                                    expand=True,
                                    scroll="auto",
                                    controls=[content_area]
                                )
                            )
                        ]
                    )
                )
            ],
            expand=True,
            spacing=0
        )
    )