import flet as ft
import psycopg2
from datetime import datetime, timedelta, date
from ui.card import build_animal_card
from db4 import get_all_animals as get_animals_filtered

conn = psycopg2.connect(
    dbname="shelter",
    user="postgres",
    password="root",
    host="localhost",
    port="5432"
)
cursor = conn.cursor()

def GuardianPage(page: ft.Page, current_user_id):
    content_area = ft.Column(expand=True)

    selected_filters = {
        "gender": "Все",
        "age": "Все",
        "health": "Все",
        "care": "Все"
    }

    def get_filtered_animals():
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

        return get_animals_filtered(
            gender=None if selected_filters["gender"] == "Все" else selected_filters["gender"],
            age_range=age_range,
            health=None if selected_filters["health"] == "Все" else selected_filters["health"],
            care=None if selected_filters["care"] == "Все" else selected_filters["care"]
        )

    def show_guardian_dialog(animal_id):
        card_field = ft.TextField(label="Номер карты", hint_text="XXXX XXXX XXXX XXXX", max_length=16, keyboard_type=ft.KeyboardType.NUMBER, width=400)
        amount_dropdown = ft.Dropdown(
            label="Выберите сумму пожертвования",
            width=400,
            options=[
                ft.dropdown.Option("1500"),
                ft.dropdown.Option("3000"),
                ft.dropdown.Option("5000")
            ]
        )
        def close_dialog(e, dlg, page):
               dlg.open = False
               page.update()

        def submit(e):
          amount = int(amount_dropdown.value)
          card = card_field.value
          today = date.today()
          next_day = today + timedelta(days=1)
          #Транзакция
          try:
              cursor.execute("BEGIN")

              cursor.execute("""
                  INSERT INTO subscriptions (fk_user_id, fk_animal_id, start_date, cancel_date, next_payment_date, card_info, amount)
                  VALUES (%s, %s, %s, NULL, %s, %s, %s)
                  RETURNING sub_id
              """, (current_user_id, animal_id, today, next_day, card, amount))
              sub_id = cursor.fetchone()[0]

              cursor.execute("""
                  INSERT INTO animal_guardian (fk_animal_id, fk_user_id)
                  VALUES (%s, %s) ON CONFLICT DO NOTHING
              """, (animal_id, current_user_id))

              cursor.execute("""
                  UPDATE animal SET care_status = 'под опекой' WHERE animal_id = %s
              """, (animal_id,))

              cursor.execute("""
                  INSERT INTO payments (fk_sub_id, payment_date, amount)
                  VALUES (%s, %s, %s)
              """, (sub_id, datetime.now(), amount))

              conn.commit()
              dlg.open = False
              page.open(ft.SnackBar(ft.Text("Спасибо, вы спасаете котика!!")))
              show_section("my_animals")
              
          except Exception as ex:
              conn.rollback()
              page.open(ft.SnackBar(ft.Text(f"Ошибка при оформлении опеки: {ex}")))
          page.update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Оформление опеки", color = ft.Colors.GREY_700),
            content=ft.Column([
                card_field,
                amount_dropdown,
                ft.ElevatedButton("Оформить", bgcolor=ft.Colors.GREY_700,
                    color=ft.Colors.WHITE, on_click=submit)
            ], tight=True),
            actions=[ft.ElevatedButton("Отмена", bgcolor=ft.Colors.GREY_700,
                    color=ft.Colors.WHITE, on_click=lambda e: close_dialog(e, dlg, page))],
            actions_alignment=ft.MainAxisAlignment.END
        )
        page.overlay.append(dlg)
        page.dialog = dlg
        dlg.open = True
        page.update()

    gender_radio = ft.RadioGroup(value=selected_filters["gender"], data="gender", content=[])
    age_radio = ft.RadioGroup(value=selected_filters["age"], data="age", content=[])
    health_radio = ft.RadioGroup(value=selected_filters["health"], data="health", content=[])
    care_radio = ft.RadioGroup(value=selected_filters["care"], data="care", content=[])

    def on_filter_change(e):
      selected_filters[e.control.data] = e.control.value
      show_section("all_animals")

    def create_filter_group(title, options, key, group):
      radio_style = ft.TextStyle(color=ft.Colors.GREY_800)
      group.on_change = on_filter_change
      group.content = ft.Column([
        ft.Radio(value="Все", label="Все", label_style=radio_style)
      ] + [ft.Radio(value=o, label=o, label_style=radio_style) for o in options])
      group.data = key
      return ft.Column([ft.Text(title, weight=ft.FontWeight.W_600, color = ft.Colors.GREY_700), group])

    def filter_panel():
      return ft.Row([
        create_filter_group("Пол", ["Кот", "Кошка"], "gender", gender_radio),
        create_filter_group("Возраст", ["до года", "1 - 5 лет", "6 - 10 лет", "от 10 лет"], "age", age_radio),
        create_filter_group("Здоровье", ["котики-инвалиды", "требуется лечение", "хорошее", "отличное"], "health", health_radio),
        create_filter_group("Опека", ["доступна", "под опекой"], "care", care_radio),
      ], spacing=50, wrap=False)


    def show_section(section):
        content_area.controls.clear()

        if section == "my_animals":
            cursor.execute("""
                SELECT a.animal_id, a.name, a.gender, a.health_status, a.care_status,
                       a.admission_date, a.birth_date, a.character_description, a.reason, a.photo
                FROM animal_guardian ag
                JOIN animal a ON ag.fk_animal_id = a.animal_id
                WHERE ag.fk_user_id = %s
            """, (current_user_id,))
            animals = cursor.fetchall()
            content_area.controls.append(ft.Text("\ud83d\udc3e Мои животные", size=24, weight=ft.FontWeight.BOLD, color = ft.Colors.GREY_700))

            grid = ft.ResponsiveRow(spacing=-40, run_spacing=20, alignment=ft.MainAxisAlignment.CENTER)
            for animal in animals:
                #content_area.controls.append(build_animal_card(animal, for_staff=False))
                grid.controls.append(build_animal_card(animal, for_staff=False))
            content_area.controls.append(grid)

        elif section == "all_animals":
            animals = get_filtered_animals()
            content_area.controls.append(ft.Text("Все животные приюта", size=24, weight=ft.FontWeight.BOLD, color = ft.Colors.GREY_700))
            content_area.controls.append(filter_panel())
            grid = ft.ResponsiveRow(spacing=-40, run_spacing=20, alignment=ft.MainAxisAlignment.CENTER)
            for animal in animals:
                grid.controls.append(build_animal_card(animal, for_staff=False, on_edit_click=lambda a=animal: show_guardian_dialog(a[0]), custom_button_text="Взять под опеку"))
            content_area.controls.append(grid)

        elif section == "subscription":
            content_area.controls.append(ft.Text("📃 Подписки", size=24, weight=ft.FontWeight.BOLD, color = ft.Colors.GREY_700))

            cursor.execute("""
                SELECT sub_id, start_date, cancel_date, next_payment_date, amount, card_info
                FROM subscriptions
                WHERE fk_user_id = %s
                ORDER BY start_date DESC
            """, (current_user_id,))
            subscriptions = cursor.fetchall()

            if subscriptions:
                for sub in subscriptions:
                    sub_id, start, cancel, next_pay, amount, card = sub
                    card_controls = [
                        ft.Text(f"💳 {start.strftime('%Y-%m-%d')} — {amount} руб.", color = ft.Colors.GREY_700),
                    ]
                    if cancel:
                        card_controls.append(ft.Text(f"❌ Отменена: {cancel.strftime('%Y-%m-%d')}", color=ft.Colors.RED))
                    else:
                        card_controls.append(ft.Text(f"📅 Следующее списание: {next_pay.strftime('%Y-%m-%d')}", color = ft.Colors.GREY_700))
                        card_controls.append(
                            ft.ElevatedButton("Отменить подписку", bgcolor=ft.Colors.GREY_700,
                                             color=ft.Colors.WHITE, on_click=lambda e, sid=sub_id: cancel_subscription(sid))
                        )

                    content_area.controls.append(
                        ft.Container(
                            content=ft.Column(card_controls),
                            padding=10,
                            border=ft.border.all(1, ft.Colors.GREY_300),
                            border_radius=10,
                            margin=ft.margin.only(bottom=10)
                        )
                    )
            else:
                content_area.controls.append(ft.Text("Нет подписок."))

    # история платежей
            content_area.controls.append(ft.Divider())
            content_area.controls.append(ft.Text("📅 История списаний", size=22, weight=ft.FontWeight.W_600, color = ft.Colors.GREY_700))
            cursor.execute("""
              SELECT p.payment_date, p.amount 
              FROM payments p
              JOIN subscriptions s ON p.fk_sub_id = s.sub_id
              WHERE s.fk_user_id = %s
              ORDER BY p.payment_date DESC
          """, (current_user_id,))

            payments = cursor.fetchall()
            if payments:
                for pay in payments:
                    content_area.controls.append(ft.Text(f"{pay[0].strftime('%Y-%m-%d')} — {pay[1]} руб.", color = ft.Colors.GREY_700))
            else:
                content_area.controls.append(ft.Text("Нет записей.", color = ft.Colors.GREY_700))
        page.update()

    def cancel_subscription(sub_id):
        cursor.execute("SELECT fk_animal_id FROM subscriptions WHERE sub_id = %s", (sub_id,))
        animal_id = cursor.fetchone()[0]
        cursor.execute("UPDATE subscriptions SET cancel_date = CURRENT_DATE WHERE sub_id = %s", (sub_id,))

        cursor.execute("DELETE FROM animal_guardian WHERE fk_user_id = %s AND fk_animal_id = %s", (current_user_id, animal_id))
        cursor.execute("UPDATE animal SET care_status = 'доступна' WHERE animal_id = %s", (animal_id,))

        conn.commit()
        page.open(ft.SnackBar(ft.Text("Подписка отменена")))
        page.update()
        show_section("subscription")


    def go_home(e):
        from ui.home import HomePage
        page.clean()
        page.add(HomePage(page))

    nav_bar = ft.NavigationRail(
        destinations=[
            ft.NavigationRailDestination(icon=ft.Icon(ft.Icons.PETS, color=ft.Colors.GREY_700), label="Мои животные"),
            ft.NavigationRailDestination(icon=ft.Icon(ft.Icons.CREDIT_CARD, color=ft.Colors.GREY_700), label="Подписка"),
            ft.NavigationRailDestination(icon=ft.Icon(ft.Icons.PETS, color=ft.Colors.GREY_700), label="Все животные"),
        ],
        bgcolor=ft.Colors.GREY_300,
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        extended=True,
        unselected_label_text_style=ft.TextStyle(color=ft.Colors.GREY_700),
        selected_label_text_style=ft.TextStyle(color=ft.Colors.GREY_700, weight=ft.FontWeight.BOLD),
        on_change=lambda e: (
            show_section("my_animals") if e.control.selected_index == 0 else
            show_section("subscription") if e.control.selected_index == 1 else
            show_section("all_animals")
        ),
    )

    header = ft.Row([
        ft.Container(content=ft.Image(src="img/logo_grey700.png", width=100, height=150, fit=ft.ImageFit.FIT_HEIGHT), padding=ft.padding.only(left=70)),
        ft.Container(content=ft.Text("Котик&Ко", size=40, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_700)),
        ft.Container(expand=True),
        ft.Container(
            content=ft.ElevatedButton("Назад", on_click=go_home, bgcolor=ft.Colors.PINK_50, color=ft.Colors.GREY_700,
                style=ft.ButtonStyle(padding=15, text_style=ft.TextStyle(size=20))),
            padding=ft.padding.only(right=100)
        )
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER, height=50)

    show_section("my_animals")

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
                        bgcolor=ft.Colors.PINK_50,
                        padding=ft.padding.all(30),
                        content=ft.Column(expand=True, scroll="auto", controls=[content_area])
                    )
                ], expand=True, spacing=20)
            )
        ], expand=True, spacing=0)
    )
