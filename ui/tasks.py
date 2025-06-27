import flet as ft
import psycopg2
from datetime import datetime

def get_username_by_id(conn, user_id):
    cursor = conn.cursor()
    cursor.execute("SELECT full_name FROM users WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()
    return result[0] if result else "Неизвестно"

def load_tasks(conn, user_id=None):
    cursor = conn.cursor()
    if user_id:
        cursor.execute("SELECT task_id, description, execution_date, status, fk_user_id FROM tasks WHERE fk_user_id = %s ORDER BY execution_date", (user_id,))
    else:
        cursor.execute("SELECT task_id, description, execution_date, status, fk_user_id FROM tasks ORDER BY execution_date")
    return cursor.fetchall()

def update_task_status(conn, task_id, new_status):
    cursor = conn.cursor()
    cursor.execute("UPDATE tasks SET status = %s WHERE task_id = %s", (new_status, task_id))
    conn.commit()

def create_task_row(task_id, description, execution_date, status, responsible_name, can_edit, on_status_change, on_delete_task):
    checkbox = ft.Checkbox(value=status == "выполнено", on_change=lambda e: on_status_change(task_id, "выполнено" if checkbox.value else "не выполнено"))
    
    controls = [
        checkbox,
        ft.Text(description, expand=True, color=ft.Colors.GREY_700),
        ft.Text(f"Дедлайн: {execution_date.strftime('%Y-%m-%d')}", color=ft.Colors.GREY_700),
        ft.Text(f"Ответственный: {responsible_name}", color=ft.Colors.GREY_700)
    ]
    
    if can_edit:
        controls.append(
            ft.IconButton(
                icon=ft.Icons.DELETE, 
                tooltip="Удалить", 
                on_click=lambda e: on_delete_task(task_id)
            )
        )
    
    return ft.Row(controls=controls)

def build_tasks_section(conn, page, user_id=None, is_director=False, on_status_change=None, on_delete_task=None):
    tasks_container = ft.Column()
    filter_tabs = ft.Tabs(
        selected_index=0,
        tabs=[
        ft.Tab(text="Все задачи"),
        ft.Tab(text="Активные"),
        ft.Tab(text="Завершенные")
    ],
    label_color=ft.Colors.GREY_700,
    unselected_label_color=ft.Colors.GREY_700,
    indicator_color=ft.Colors.PINK_50,
    divider_color=ft.Colors.GREY_300,
    label_padding=ft.padding.symmetric(horizontal=16, vertical=8),
		)
    
    def status_changed(task_id, new_status):
        if on_status_change:
            on_status_change(task_id, new_status)
    
    def task_deleted(task_id):
        if on_delete_task:
            on_delete_task(task_id)
    
    def update_filter(e=None):
        selected = filter_tabs.tabs[filter_tabs.selected_index].text
        tasks_container.controls.clear()
        
        for task in all_tasks:
            visible = (
                selected == "Все задачи" or
                (selected == "Активные" and not task["checkbox"].value) or
                (selected == "Завершенные" and task["checkbox"].value)
            )
            task["row"].visible = visible
            if visible:
                tasks_container.controls.append(task["row"])
        
        page.update()
    
    def refresh_tasks():
        nonlocal all_tasks
        tasks = load_tasks(conn, None if is_director else user_id)
        all_tasks = []
        
        for task in tasks:
            task_id, desc, date, status, fk_uid = task
            name = get_username_by_id(conn, fk_uid)
            
            row = ft.Row(
                controls=[
                    ft.Checkbox(
                        value=status == "выполнено",
                        on_change=lambda e, task_id=task_id: status_changed(
                            task_id, "выполнено" if e.control.value else "не выполнено"
                        )
                    ),
                    ft.Text(desc, expand=True, color=ft.Colors.GREY_700),
                    ft.Text(f"Дедлайн: {date.strftime('%Y-%m-%d')}", color = ft.Colors.GREY_700),
                    ft.Text(f"Ответственный: {name}", color = ft.Colors.GREY_700),
                    ft.IconButton(
                        icon=ft.Icons.DELETE,
                        tooltip="Удалить",
                        on_click=lambda e, task_id=task_id: task_deleted(task_id),
                        icon_color=ft.Colors.GREY_700
                    ) if is_director else ft.Container()
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            )
            
            all_tasks.append({
                "row": row,
                "checkbox": row.controls[0]
            })
        
        update_filter()
    
    all_tasks = []
    filter_tabs.on_change = update_filter
    refresh_tasks()
    
    return ft.Column(controls=[
        filter_tabs,
        ft.Divider(),
        tasks_container
    ], scroll=ft.ScrollMode.AUTO)