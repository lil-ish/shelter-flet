import flet as ft
import psycopg2
from datetime import datetime
import re

def DonationsPage(page: ft.Page):
    active_funds = []

    def go_home(e):
        from ui.home import HomePage
        page.clean()
        page.add(HomePage(page))

    header = ft.Container(
        content=ft.Row(
            controls=[
                ft.Container(
                    content=ft.Image(src="assets/logo_grey700.png", width=100, height=150, fit=ft.ImageFit.FIT_HEIGHT),
                    padding=ft.padding.only(left=70)
                ),
                ft.Container(
                    content=ft.Text("Котик&Ко", size=40, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_700)
                ),
                ft.Container(expand=True),
                ft.Container(
                    content=ft.ElevatedButton(
                        "Назад",
                        on_click=go_home,
                        bgcolor=ft.Colors.PINK_50,
                        color=ft.Colors.GREY_700,
                        style=ft.ButtonStyle(padding=15, text_style=ft.TextStyle(size=20))
                    ),
                    padding=ft.padding.only(right=100)
                )
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            height=50
        ),
        bgcolor=ft.Colors.PINK_50,
        padding=10
    )

    card_number = ft.TextField(label="Номер карты", hint_text="XXXX XXXX XXXX XXXX", max_length=19, keyboard_type=ft.KeyboardType.NUMBER, text_style=ft.TextStyle(color=ft.Colors.GREY_700))
    expiry_date = ft.TextField(label="Срок действия (ММ/ГГ)", hint_text="MM/YY", max_length=5, text_style=ft.TextStyle(color=ft.Colors.GREY_700))
    cvc_code = ft.TextField(label="CVC/CVV код", max_length=3, width=120, keyboard_type=ft.KeyboardType.NUMBER, password=True, text_style=ft.TextStyle(color=ft.Colors.GREY_700))
    donor_name = ft.TextField(label="Ваше имя (необязательно)", text_style=ft.TextStyle(color=ft.Colors.GREY_700))
    email = ft.TextField(label="Email для чека", keyboard_type=ft.KeyboardType.EMAIL, text_style=ft.TextStyle(color=ft.Colors.GREY_700))
    amount = ft.TextField(label="Сумма пожертвования", keyboard_type=ft.KeyboardType.NUMBER, suffix_text="руб.", text_style=ft.TextStyle(color=ft.Colors.GREY_700))
    fund_dropdown = ft.Dropdown(label="Выберите сбор (необязательно)", text_style=ft.TextStyle(color=ft.Colors.GREY_700))
    terms_checkbox = ft.Checkbox(label="Соглашаюсь с условиями оферты", value=False, label_style=ft.TextStyle(color=ft.Colors.GREY_700))
    privacy_checkbox = ft.Checkbox(label="Соглашаюсь с политикой обработки персональных данных", value=False, label_style=ft.TextStyle(color=ft.Colors.GREY_700))
    error_text = ft.Text(color=ft.Colors.RED)
    success_text = ft.Text(color=ft.Colors.GREEN)

    def format_card_number(e):
        value = e.control.value.replace(" ", "")
        if value:
            value = " ".join([value[i:i+4] for i in range(0, len(value), 4)])[:19]
        e.control.value = value
        page.update()

    card_number.on_change = format_card_number

    def validate_card_number(num):
        return len(num.replace(" ", "")) == 16 and num.replace(" ", "").isdigit()

    def validate_expiry_date(date):
        return re.match(r"^(0[1-9]|1[0-2])\/([0-9]{2})$", date)

    def validate_email(addr):
        return re.match(r"^[^@]+@[^@]+\.[^@]+$", addr)

    def load_fundraisings():
        try:
            conn = psycopg2.connect(dbname="shelter", user="postgres", password="root", host="localhost", port="5432")
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE fundraising
                SET status = 'завершён'
                WHERE status = 'активен' AND collected_amount >= target_amount
            """)
            cursor.execute("""
                SELECT fund_id, goal, target_amount, collected_amount, description
                FROM fundraising WHERE status = 'активен' ORDER BY end_date DESC
            """)
            funds = cursor.fetchall()
            active_funds.clear()
            active_funds.extend(funds)
            fund_dropdown.options = [
                ft.dropdown.Option(
                    text=f"{goal} (Собрано {collected}/{target} руб.)",
                    key=str(fund_id)
                ) for fund_id, goal, target, collected, _ in funds
            ]
            conn.commit()
        except Exception as e:
            print("Ошибка загрузки сборов:", e)
        finally:
            if 'conn' in locals():
                conn.close()
            page.update()

    donations_history = ft.ListView(expand=True)

    def load_donations_history():
        try:
            conn = psycopg2.connect(dbname="shelter", user="postgres", password="root", host="localhost", port="5432")
            cursor = conn.cursor()
            cursor.execute("""
                SELECT d.amount, d.payment_date,
                  COALESCE(u.full_name, d.comment, 'Аноним') AS donor_name,
                  COALESCE(f.goal, 'Общий сбор') AS fund_name
                FROM donations d
                LEFT JOIN users u ON d.fk_user_id = u.user_id
                LEFT JOIN fundraising f ON d.fk_fund_id = f.fund_id
                ORDER BY d.donat_id DESC
                LIMIT 14""")
            rows = cursor.fetchall()
            donations_history.controls.clear()
            for amount_, date, name, fund in rows:
                donations_history.controls.append(
                    ft.Container(
                        bgcolor=ft.Colors.WHITE,
                        border_radius=10,
                        padding=10,
                        margin=ft.margin.only(bottom=10),
                        content=ft.Row([
                            ft.Text(f"{amount_} руб.", width=100, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_700),
                            ft.Text(name, width=160, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_700),
                            ft.Text(fund, expand=True, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_700),
                            ft.Text(date.strftime("%d.%m.%Y"), weight=ft.FontWeight.W_600, color=ft.Colors.GREY_700)
                        ])
                    )
                )
        except Exception as e:
            print("Ошибка загрузки истории:", e)
        finally:
            if 'conn' in locals():
                conn.close()
            page.update()

    def submit_donation(e):
      errors = []
      try:
        if not validate_card_number(card_number.value):
            errors.append("Некорректный номер карты")
        if not validate_expiry_date(expiry_date.value):
            errors.append("Некорректный срок действия карты (ММ/ГГ)")
        if not cvc_code.value or not cvc_code.value.isdigit() or len(cvc_code.value) != 3:
            errors.append("CVC код должен содержать 3 цифры")
        try:
            amt = int(amount.value)
            if amt <= 0:
                raise ValueError
        except:
            errors.append("Укажите корректную сумму (> 0)")
        if not email.value or not validate_email(email.value):
            errors.append("Укажите корректный email")
        if not terms_checkbox.value:
            errors.append("Подтвердите согласие с условиями оферты")
        if not privacy_checkbox.value:
            errors.append("Подтвердите согласие с политикой обработки данных")

        if errors:
            error_text.value = "\n".join(errors)
            success_text.value = ""
            page.update()
            return

        conn = psycopg2.connect(dbname="shelter", user="postgres", password="root", host="localhost", port="5432")
        cursor = conn.cursor()
        current_user_id = getattr(page, "current_user_id", None)
        selected_fund_id = int(fund_dropdown.value) if fund_dropdown.value else None
        donation_amount = int(amount.value)
        now = datetime.now()

        donor_display_name = donor_name.value.strip() if donor_name.value else "Аноним"

        if selected_fund_id:
            cursor.execute("SELECT target_amount, collected_amount FROM fundraising WHERE fund_id = %s", (selected_fund_id,))
            target, collected = cursor.fetchone()
            available = target - collected

            if available <= 0:
                # в общий фонд
                cursor.execute("""
                    INSERT INTO donations (amount, payment_date, comment, fk_user_id, fk_fund_id)
                    VALUES (%s, %s, %s, %s, NULL)
                """, (donation_amount, now, donor_display_name, current_user_id))
            else:
                part_to_fund = min(available, donation_amount)
                part_to_common = donation_amount - part_to_fund

                # В сбор
                cursor.execute("""
                    INSERT INTO donations (amount, payment_date, comment, fk_user_id, fk_fund_id)
                    VALUES (%s, %s, %s, %s, %s)
                """, (part_to_fund, now, donor_display_name, current_user_id, selected_fund_id))

                cursor.execute("""
                    UPDATE fundraising
                    SET collected_amount = collected_amount + %s,
                        status = CASE WHEN collected_amount + %s >= target_amount THEN 'завершён' ELSE status END
                    WHERE fund_id = %s
                """, (part_to_fund, part_to_fund, selected_fund_id))

                # излишек в общий фонд
                if part_to_common > 0:
                    cursor.execute("""
                        INSERT INTO donations (amount, payment_date, comment, fk_user_id, fk_fund_id)
                        VALUES (%s, %s, %s, %s, NULL)
                    """, (part_to_common, now, donor_display_name + " (излишек)", current_user_id))
        else:
            # Без сбора
            cursor.execute("""
                INSERT INTO donations (amount, payment_date, comment, fk_user_id, fk_fund_id)
                VALUES (%s, %s, %s, %s, NULL)
            """, (donation_amount, now, donor_display_name, current_user_id))

        conn.commit()

        for field in [amount, donor_name, card_number, expiry_date, cvc_code, email]:
            field.value = ""
        terms_checkbox.value = False
        privacy_checkbox.value = False
        error_text.value = ""
        success_text.value = "Спасибо за ваше пожертвование!"

        on_page_load()

      except Exception as err:
        error_text.value = f"Ошибка при обработке: {err}"
      finally:
        if 'conn' in locals():
            conn.close()
        page.update()

    def set_fund(e, fund_id):
        fund_dropdown.value = str(fund_id)
        page.update()

    def create_fund_card(fund_id, goal, target, collected, description):
      progress = collected / target if target else 0
      return ft.Card(
        content=ft.Container(
            content=ft.Column(
                [
                    ft.Column(
                        [
                            ft.Text(goal, size=18, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_700),
                            ft.Text(description, size=13, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_700),
                            ft.Text(f"Собрано {collected} из {target} руб.", weight=ft.FontWeight.W_600, color=ft.Colors.GREY_700),
                            ft.ProgressBar(value=progress),
                        ],
                        expand=True,
                    ),
                    ft.Container(
                        content=ft.ElevatedButton(
                            "Помочь", 
                            on_click=lambda e, fid=fund_id: set_fund(e, fid), 
                            bgcolor=ft.Colors.PINK_50, 
                            color=ft.Colors.GREY_700
                        ),
                        alignment=ft.alignment.bottom_center
                    )
                ],
                spacing=6,
                height=200
            ),
            padding=10,
            bgcolor=ft.Colors.WHITE,
            border_radius=10,
            expand=True
        ),
        width=280
    )

    funds_container = ft.Row(scroll=ft.ScrollMode.AUTO, spacing=20)

    donation_form = ft.Container(
        content=ft.Column([
            ft.Text("Сделать пожертвование", size=24, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_700),
            ft.Row([
                ft.Text("Данные карты", size=18, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_700),
                ft.Icon(ft.Icons.ADD_CARD, color=ft.Colors.GREY_700)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            card_number,
            ft.Row([expiry_date, ft.Container(content=cvc_code, width=120)]),
            ft.Divider(),
            amount,
            donor_name,
            email,
            fund_dropdown,
            ft.Divider(),
            terms_checkbox,
            privacy_checkbox,
            ft.ElevatedButton("Пожертвовать", on_click=submit_donation, bgcolor=ft.Colors.PINK_50, color=ft.Colors.GREY_700),
            error_text,
            success_text
        ], spacing=15),
        width=500,
        bgcolor=ft.Colors.GREY_100,
        border_radius=10,
        padding=20
    )

    donation_block = ft.Container(
        content=ft.Column([
            ft.Text("История пожертвований", size=20, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_700),
            donations_history
        ]),
        expand=True,
        bgcolor=ft.Colors.GREY_100,
        border_radius=10,
        padding=20
    )

    def on_page_load():
        load_fundraisings()
        load_donations_history()
        funds_container.controls.clear()
        for fund_id, goal, target, collected, description in active_funds:
            funds_container.controls.append(create_fund_card(fund_id, goal, target, collected, description))
        page.update()

    content = ft.Column([
        ft.Text("Активные сборы", size=20, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_700),
        ft.Container(content=funds_container, height=250),
        ft.Divider(),
        ft.Row([donation_form, ft.VerticalDivider(), donation_block], expand=True)
    ], spacing=20, expand=True)

    scroll_view = ft.Column(
        controls=[
            header,
            ft.Container(content=content, padding=20, bgcolor=ft.Colors.PINK_50, expand=True)
        ],
        spacing=0,
        scroll=ft.ScrollMode.AUTO,
        expand=True
    )

    on_page_load()
    return scroll_view
