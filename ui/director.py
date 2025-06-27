import flet as ft
import psycopg2
from datetime import datetime
from db4 import get_all_animals
from ui.card import build_animal_card, cleanup_temp_images
from ui.tasks import build_tasks_section
from ui.staff_page import add_animal_to_db, update_animal_in_db, delete_animal_from_db
from db4 import add_user, get_tasks_from_db, get_user_id_by_name, add_task_to_db, delete_task_from_db, update_task_in_db, get_all_users, get_reports_from_db, add_report_to_db, delete_report_from_db

conn = psycopg2.connect(
    dbname="shelter",
    user="postgres",
    password="root",
    host="localhost",
    port="5432"
)
cursor = conn.cursor()

def DirectorPage(page: ft.Page, current_user_id):
    def on_page_close(e):
        cleanup_temp_images()

    page.on_close = on_page_close
    content_area = ft.Column(expand=True)

    def show_tasks(e):
      content_area.controls.clear()
      content_area.controls.append(ft.Text("Управление задачами", size=24, weight=ft.FontWeight.BOLD, color = ft.Colors.GREY_700))
      task_description = ft.TextField(label="Описание задачи", multiline=True, min_lines=2, max_lines=5, width=400, text_style=ft.TextStyle(color=ft.Colors.GREY_700))
      task_date = ft.TextField(label="Срок выполнения (ГГГГ-ММ-ДД)", width=400, text_style=ft.TextStyle(color=ft.Colors.GREY_700))
      task_status = ft.Dropdown(
          label="Статус",
          options=[
              ft.dropdown.Option("не выполнено"),
              ft.dropdown.Option("выполнено")
          ],
          value="не выполнено",
          width=400,
          text_style=ft.TextStyle(color=ft.Colors.GREY_700)
      )
      task_responsible = ft.Dropdown(
          label="Ответственный",
          options=[ft.dropdown.Option(user[1]) for user in get_all_users()],
          width=400,
          text_style=ft.TextStyle(color=ft.Colors.GREY_700)
      )

      def submit_task(e):
          user_id = get_user_id_by_name(task_responsible.value)
          if not user_id:
              page.open(ft.SnackBar(ft.Text("Пользователь не найден!")))
              page.update()
              return
  
          add_task_to_db(
              task_description.value,
              task_date.value,
              task_status.value,
              user_id
          )
          refresh_tasks()
          task_description.value = ""
          task_date.value = ""
          task_responsible.value = ""
          page.open(ft.SnackBar(ft.Text("Задача добавлена!")))
          page.update()

      add_task_form = ft.Container(
          content=ft.Column([
              ft.Text("Добавить новую задачу", size=18, color=ft.Colors.GREY_700),
              task_description,
              task_date,
              task_status,
              task_responsible,
              ft.ElevatedButton("Добавить задачу", on_click=submit_task, bgcolor=ft.Colors.PINK_50, color=ft.Colors.GREY_700,)
          ]),
          padding=20,
          border=ft.border.all(1, ft.Colors.GREY_300),
          border_radius=10,
          margin=ft.margin.only(bottom=20)
      )
      
      def update_task_status(task_id, new_status):
          cursor.execute("UPDATE tasks SET status = %s WHERE task_id = %s", (new_status, task_id))
          conn.commit()
          refresh_tasks()

      def delete_task(task_id):
          delete_task_from_db(task_id)
          refresh_tasks()
          page.open(ft.SnackBar(ft.Text("Задача удалена!")))
          page.update()

      def refresh_tasks():
          if len(content_area.controls) > 2:
              content_area.controls.pop()

          tasks_section = build_tasks_section(
              conn=conn,
              page=page,
              user_id=None,
              is_director=True,
              on_status_change=update_task_status,
              on_delete_task=delete_task
          )
          
          content_area.controls.append(tasks_section)
          page.update()

      content_area.controls.extend([
          add_task_form,
          ft.Divider()
      ])
      refresh_tasks()
        
    def build_users_section(conn, page):
      users_container = ft.Column()
      role_tabs = ft.Tabs(
        selected_index=0,
        tabs=[
            ft.Tab(text="Все"),
            ft.Tab(text="Сотрудник"),
            ft.Tab(text="Ветеринар"),
            ft.Tab(text="Попечитель")
        ],
      label_color=ft.Colors.GREY_700,
      unselected_label_color=ft.Colors.GREY_700,
      indicator_color=ft.Colors.PINK_50,
      divider_color=ft.Colors.GREY_300
    )

      def load_users():
        nonlocal all_users
        cursor.execute("SELECT user_id, full_name, contact_info, email, role, start_date FROM users WHERE deleted_at IS NULL ORDER BY start_date DESC")
        all_users = []
        for user in cursor.fetchall():
            user_id, full_name, contact_info, email, role, start_date = user

            def delete_user(e, uid=user_id):
              if uid == current_user_id:
                page.open(ft.SnackBar(ft.Text("Нельзя удалить самого себя")))
                page.update()
                return

              cursor.execute("SELECT full_name FROM users WHERE user_id = %s", (uid,))
              old_user_name = cursor.fetchone()[0]

              users = [(u[0], u[1]) for u in get_all_users() if u[0] != uid]
              user_dropdown = ft.Dropdown(
                  label="Кому передать задачи?",
                  options=[ft.dropdown.Option(u[1]) for u in users]
              )

              def confirm_delete(ev):
                  new_user_id = get_user_id_by_name(user_dropdown.value)
                  cursor.execute("UPDATE tasks SET fk_user_id = %s WHERE fk_user_id = %s", (new_user_id, uid))
                  cursor.execute("UPDATE users SET deleted_at = NOW() WHERE user_id = %s", (uid,))
                  conn.commit()
                  dlg.open = False
                  load_users()
                  page.open(ft.SnackBar(ft.Text("Пользователь удалён и задачи переданы")))
                  page.update()

              dlg = ft.AlertDialog(
                  title=ft.Text(f"Удаление: {old_user_name}"),
                  content=user_dropdown,
                  actions=[
                      ft.TextButton("Подтвердить", on_click=confirm_delete),
                      ft.TextButton("Отмена", on_click=lambda e: close_dialog(e, dlg))
                  ]
              )
              page.overlay.append(dlg)
              page.dialog = dlg
              dlg.open = True
              page.update()

            def edit_user(e, uid=user_id, name=full_name, contact=contact_info, mail=email, r=role, start=start_date):
                name_field = ft.TextField(label="ФИО", value=name, text_style=ft.TextStyle(color=ft.Colors.GREY_700))
                contact_field = ft.TextField(label="Контакты", value=contact, text_style=ft.TextStyle(color=ft.Colors.GREY_700))
                email_field = ft.TextField(label="Email", value=mail, text_style=ft.TextStyle(color=ft.Colors.GREY_700))
                roles = ["Сотрудник", "Ветеринар", "Попечитель"]
                role_field = ft.Dropdown(
                  label="Роль",
                  text_style=ft.TextStyle(color=ft.Colors.GREY_700),
                  options=[ft.dropdown.Option(role_name) for role_name in roles],
                  value=r
                  )
                start_field = ft.TextField(label="Дата начала", value=str(start), text_style=ft.TextStyle(color=ft.Colors.GREY_700))
                
                def save_edit(ev):
                    cursor.execute(
                        "UPDATE users SET full_name=%s, contact_info=%s, email=%s, role=%s, start_date=%s WHERE user_id=%s",
                        (name_field.value, contact_field.value, email_field.value, role_field.value, start_field.value, uid)
                    )
                    conn.commit()
                    dlg.open = False
                    load_users()
                    page.open(ft.SnackBar(ft.Text("Пользователь обновлён")))
                    page.update()

                dlg = ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Редактировать пользователя"),
                    content=ft.Column([
                        name_field,
                        contact_field,
                        email_field,
                        role_field,
                        start_field,
                    ]),
                    actions=[
                        ft.TextButton("Сохранить", on_click=save_edit),
                        ft.TextButton("Отмена", on_click=lambda e: close_dialog(e, dlg))
                    ]
                )
                page.overlay.append(dlg)
                page.dialog = dlg
                dlg.open = True
                page.update()

            def close_dialog(e, dlg):
                dlg.open = False
                page.update()

            row = ft.Row([
                ft.Text(f"{full_name} — {email} ({role})", color=ft.Colors.GREY_700),
                ft.Row([
                    ft.IconButton(icon=ft.Icons.EDIT, icon_color=ft.Colors.GREY_700, on_click=lambda e, uid=user_id, name=full_name, contact=contact_info, mail=email, r=role, start=start_date: edit_user(e, uid, name, contact, mail, r, start)),
                    ft.IconButton(icon=ft.Icons.DELETE, icon_color=ft.Colors.GREY_700, on_click=lambda e, uid=user_id: delete_user(e, uid))
                ])
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            all_users.append({"row": row, "role": role})

        update_filter()

      def update_filter(e=None):
        selected = role_tabs.tabs[role_tabs.selected_index].text
        users_container.controls.clear()
        for u in all_users:
            if selected == "Все" or u["role"] == selected:
                users_container.controls.append(u["row"])
        page.update()

      role_tabs.on_change = update_filter
      all_users = []
      load_users()

      return ft.Column(controls=[role_tabs, users_container])

    def show_add_user(e):
      content_area.controls.clear()
      content_area.controls.append(ft.Text("Добавление пользователя", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700))

      full_name = ft.TextField(label="ФИО", width=400, text_style=ft.TextStyle(color=ft.Colors.GREY_700))
      contact_info = ft.TextField(label="Контактная информация", width=400, text_style=ft.TextStyle(color=ft.Colors.GREY_700))
      email = ft.TextField(label="Email", width=400, text_style=ft.TextStyle(color=ft.Colors.GREY_700))
      password = ft.TextField(label="Пароль", password=True, can_reveal_password=True, width=400, text_style=ft.TextStyle(color=ft.Colors.GREY_700))
      role = ft.Dropdown(
        label="Роль",
        options=[
            ft.dropdown.Option("Сотрудник"),
            ft.dropdown.Option("Ветеринар"),
            ft.dropdown.Option("Попечитель"),
        ],
        width=400, text_style=ft.TextStyle(color=ft.Colors.GREY_700)
      )
      start_date = ft.TextField(label="Дата начала работы (ГГГГ-ММ-ДД)", hint_text="например, 2024-06-01", width=400, text_style=ft.TextStyle(color=ft.Colors.GREY_700))

      status_text = ft.Text("")

      def on_submit(e):
        try:
            add_user(
                full_name.value,
                contact_info.value,
                email.value,
                password.value,
                role.value,
                start_date.value
            )
            status_text.value = "✅ Пользователь успешно добавлен"
            for field in [full_name, contact_info, email, password, role, start_date]:
                field.value = ""
            content_area.controls[-1] = build_users_section(conn, page)
        except Exception as ex:
            status_text.value = f"❌ Ошибка: {ex}"
        page.update()

      submit_btn = ft.ElevatedButton("Добавить", on_click=on_submit, bgcolor=ft.Colors.PINK_50, color=ft.Colors.GREY_700,)

      content_area.controls.extend([
        full_name,
        contact_info,
        email,
        password,
        role,
        start_date,
        submit_btn,
        status_text,
        ft.Divider(),
        ft.Text("Список пользователей", size=18, weight=ft.FontWeight.W_500, color=ft.Colors.GREY_700),
        build_users_section(conn, page)
      ])
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
      admission_date_field = ft.TextField(label="Дата поступления", width=300)
      birth_date_field = ft.TextField(label="Дата рождения", width=300)
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
              page.oopen(ft.SnackBar(ft.Text(f"Ошибка: {str(ex)}"), open=True))
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
    
    def show_reports(e):
      content_area.controls.clear()
      content_area.controls.append(ft.Text("Управление отчетностью", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700))

      report_date = ft.TextField(label="Дата публикации (ГГГГ-ММ-ДД)", width=400, text_style=ft.TextStyle(color=ft.Colors.GREY_700))
      report_period = ft.Dropdown(
        label="Период",
        options=[
            ft.dropdown.Option("годовой"),
            ft.dropdown.Option("ежемесячный")
        ],
        width=400, text_style=ft.TextStyle(color=ft.Colors.GREY_700)
      )
      report_link = ft.TextField(label="Ссылка на документ", width=400, text_style=ft.TextStyle(color=ft.Colors.GREY_700))
    
      selected_file_path = ft.Text()
      file_picker = ft.FilePicker()
      page.overlay.append(file_picker)

      def submit_report(e):
        if not all([report_date.value, report_period.value, report_link.value]):
            page.snack_bar = ft.SnackBar(ft.Text("Заполните все поля!"))
            page.snack_bar.open = True
            page.update()
            return

        add_report_to_db(
            report_date.value,
            report_period.value,
            report_link.value,
            current_user_id
        )
        refresh_reports()
        report_date.value = ""
        report_period.value = ""
        report_link.value = ""
        selected_file_path.value = ""
        page.open(ft.SnackBar(ft.Text("Отчет добавлен!")))
        page.update()

      add_report_form = ft.Container(
        content=ft.Column([
            ft.Text("Добавить новый отчет", size=18, color=ft.Colors.GREY_700),
            report_date,
            report_period,
            ft.Row([
                report_link]),
            selected_file_path,
            ft.ElevatedButton("Добавить отчет", bgcolor=ft.Colors.PINK_50,
            color=ft.Colors.GREY_700, on_click=submit_report)
        ]),
        padding=20,
        border=ft.border.all(1, ft.Colors.GREY_300),
        border_radius=10,
        margin=ft.margin.only(bottom=20)
    )

      def delete_report(report_id):
        delete_report_from_db(report_id)
        refresh_reports()
        page.open(ft.SnackBar(ft.Text("Отчет удален!")))
        page.update()

      def refresh_reports():
        reports_container.controls.clear()
        reports = get_reports_from_db()
        
        for report in reports:
            report_id, pub_date, period, doc_link, author = report
            author = author if author else "Неизвестно"
            
            row = ft.Row(
                controls=[
                    ft.Text(f"{pub_date.strftime('%Y-%m-%d')}", width=100, color=ft.Colors.GREY_700),
                    ft.Text(period, width=100, color=ft.Colors.GREY_700),
                    ft.Text(author, width=150, color=ft.Colors.GREY_700),
                    ft.ElevatedButton(
                      "Открыть",
                      bgcolor=ft.Colors.PINK_50,
                      color=ft.Colors.GREY_700,
                      on_click=lambda e, link=doc_link: page.launch_url(link) if link else None,
                      disabled=not doc_link,
                      tooltip="Открыть документ" if doc_link else "Документ не доступен"
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DELETE,
                        tooltip="Удалить",
                        icon_color=ft.Colors.GREY_700,
                        on_click=lambda e, report_id=report_id: delete_report(report_id)
                    )
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            )
            reports_container.controls.append(row)
        
        page.update()

      reports_container = ft.Column(scroll=ft.ScrollMode.AUTO)
      refresh_reports()

      content_area.controls.extend([
        add_report_form,
        ft.Divider(),
        ft.Text("Список отчетов", size=18, color = ft.Colors.GREY_700),
        reports_container
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
            ft.NavigationRailDestination(icon=ft.Icon(ft.Icons.TASK, color=ft.Colors.GREY_700),label="Задачи"),
            ft.NavigationRailDestination(icon=ft.Icon(ft.Icons.PETS, color=ft.Colors.GREY_700), label="База животных"),
            ft.NavigationRailDestination(icon=ft.Icon(ft.Icons.PERSON_ADD, color=ft.Colors.GREY_700), label="Пользователи"),
            ft.NavigationRailDestination(icon=ft.Icon(ft.Icons.INSERT_CHART, color=ft.Colors.GREY_700), label="Отчетность"),
        ],
        unselected_label_text_style=ft.TextStyle(color=ft.Colors.GREY_700),
        selected_label_text_style=ft.TextStyle(color=ft.Colors.GREY_700, weight=ft.FontWeight.BOLD),
        bgcolor=ft.Colors.GREY_300,
        selected_index=0,
        #label_type=ft.NavigationRailLabelType.ALL,
        extended=True,
        on_change=lambda e: (
        show_tasks(e) if e.control.selected_index == 0 else
        show_animals(e) if e.control.selected_index == 1 else
        show_add_user(e) if e.control.selected_index == 2 else
        show_reports(e)
        
        ),
    )
    show_tasks(None)

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
                                    controls=[
                                        content_area
                                    ]
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