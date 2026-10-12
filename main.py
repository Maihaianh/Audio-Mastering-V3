import asyncio
import sys
import os
import flet as ft
from mastering_engine import process_audio_file

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

def main(page: ft.Page):
    page.title = "Mastering Audio"
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 460
    page.window_height = 920
    page.padding = 15

    # Quản lý trạng thái ứng dụng
    state = {
        "mode": "auto",
        "file_path": None,
        "mastered_path": None
    }

    # Các thành phần hiển thị
    selected_file_text = ft.Text(value="Chưa chọn tệp âm thanh", italic=True, color=ft.colors.WHITE70, size=13)
    file_sub_text = ft.Text(value="Chạm 'Chọn file' để bắt đầu", size=11, color=ft.colors.WHITE54)
    status_text = ft.Text(value="", color=ft.colors.GREEN_ACCENT, size=12, weight=ft.FontWeight.BOLD)
    progress_ring = ft.ProgressRing(visible=False, width=18, height=18, stroke_width=2)

    eq_switch = ft.Switch(value=True, scale=0.7)
    boost_switch = ft.Switch(value=True, scale=0.7)

    # Khởi tạo AudioPlayers cho việc nghe thử
    audio_original = ft.Audio(autoplay=False)
    audio_mastered = ft.Audio(autoplay=False)
    page.overlay.extend([audio_original, audio_mastered])

    # 1. Xử lý FilePicker chọn file
    def on_file_picked(e: ft.FilePickerResultEvent):
        if e.files:
            file_info = e.files[0]
            state["file_path"] = file_info.path
            selected_file_text.value = file_info.name
            selected_file_text.italic = False
            selected_file_text.color = ft.colors.WHITE
            file_sub_text.value = f"Đã chọn • {round(file_info.size / 1024 / 1024, 2)} MB"
            status_text.value = "Sẵn sàng Mastering."
            status_text.color = ft.colors.BLUE_ACCENT
            
            # Gắn nguồn cho audio phát thử
            audio_original.src = file_info.path
            page.update()

    file_picker = ft.FilePicker(on_result=on_file_picked)
    page.overlay.append(file_picker)

    # 2. Xử lý chọn chế độ Mastering
    mode_containers = {}

    def select_mode(mode_key):
        state["mode"] = mode_key
        for key, container in mode_containers.items():
            if key == mode_key:
                container.bgcolor = ft.colors.INDIGO_900
            else:
                container.bgcolor = ft.colors.SURFACE_VARIANT
        page.update()

    # 3. Xử lý nút Mastering ngay và lưu tệp vào bộ nhớ
    def start_mastering(e):
        input_path = state["file_path"]
        
        if not input_path or not os.path.exists(input_path):
            status_text.value = "⚠️ Vui lòng bấm 'Chọn file' trước khi Mastering!"
            status_text.color = ft.colors.ORANGE_ACCENT
            page.update()
            return

        progress_ring.visible = True
        status_text.value = f"Đang xử lý ({state['mode'].upper()})..."
        status_text.color = ft.colors.YELLOW_ACCENT
        page.update()

        try:
            # Xác định thư mục lưu file (ưu tiên thư mục chứa file nguồn hoặc thư mục tạm của app)
            dir_name = os.path.dirname(input_path)
            base_name = os.path.splitext(os.path.basename(input_path))[0]
            output_path = os.path.join(dir_name, f"{base_name}_Mastered.wav")

            boost_val = 4.5 if boost_switch.value else 2.0
            normalize_val = eq_switch.value

            # Gọi thuật toán xử lý âm thanh
            process_audio_file(
                input_path=input_path,
                output_path=output_path,
                boost_db=boost_val,
                normalize=normalize_val,
                mode=state["mode"]
            )

            state["mastered_path"] = output_path
            audio_mastered.src = output_path

            status_text.value = f"Đã lưu file: {base_name}_Mastered.wav"
            status_text.color = ft.colors.GREEN_ACCENT
        except Exception as ex:
            status_text.value = f"Lỗi: {str(ex)}"
            status_text.color = ft.colors.RED_ACCENT
        finally:
            progress_ring.visible = False
            page.update()

    # 4. Sự kiện các nút chức năng phụ (Cài đặt, Điều hướng)
    def open_settings(e):
        page.show_snack_bar(ft.SnackBar(content=ft.Text("Cài đặt thông số nâng cao đang phát triển!")))

    def nav_clicked(e, tab_name):
        page.show_snack_bar(ft.SnackBar(content=ft.Text(f"Đang chuyển đến mục: {tab_name}")))

    # 5. Giao diện trực quan
    header = ft.Row([
        ft.Column([
            ft.Text("Mastering Audio", size=22, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_200),
            ft.Text("Nâng tầm âm nhạc của bạn", size=12, color=ft.colors.WHITE54)
        ], spacing=2),
        ft.IconButton(icon=ft.icons.SETTINGS, icon_color=ft.colors.WHITE70, on_click=open_settings)
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    banner = ft.Container(
        content=ft.Column([
            ft.Text("Biến bản thu thành âm thanh chuyên nghiệp", weight=ft.FontWeight.BOLD, size=13, color=ft.colors.WHITE),
            ft.Text("Khử DC Offset, nén động mềm và tối ưu hóa dải tần.", size=11, color=ft.colors.WHITE70)
        ], spacing=4),
        bgcolor=ft.colors.SURFACE_VARIANT,
        padding=12,
        border_radius=8
    )

    file_card = ft.Container(
        content=ft.Row([
            ft.Icon(ft.icons.AUDIO_FILE, color=ft.colors.BLUE, size=28),
            ft.Column([selected_file_text, file_sub_text], spacing=2, expand=True),
            ft.ElevatedButton(
                text="Chọn file",
                icon=ft.icons.FOLDER_OPEN,
                on_click=lambda _: file_picker.pick_files(allowed_extensions=["wav", "mp3"]),
                style=ft.ButtonStyle(bgcolor=ft.colors.INDIGO_900, color=ft.colors.WHITE, padding=10)
            )
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        bgcolor=ft.colors.SURFACE_VARIANT,
        padding=12,
        border_radius=8
    )

    # Khung nghe thử Original vs Mastered
    waveform_section = ft.Row([
        ft.Container(
            content=ft.Column([
                ft.Text("Audio (Original)", size=11, color=ft.colors.WHITE70),
                ft.Container(height=30, bgcolor=ft.colors.BLACK45, border_radius=4, alignment=ft.alignment.center, content=ft.Text("Phát bản gốc", size=10, color=ft.colors.WHITE54)),
                ft.Row([
                    ft.IconButton(icon=ft.icons.PLAY_ARROW, icon_size=16, padding=0, on_click=lambda _: audio_original.play()),
                    ft.IconButton(icon=ft.icons.PAUSE, icon_size=16, padding=0, on_click=lambda _: audio_original.pause()),
                ], alignment=ft.MainAxisAlignment.CENTER)
            ], spacing=5),
            bgcolor=ft.colors.SURFACE_VARIANT, padding=10, border_radius=8, expand=True
        ),
        ft.Container(
            content=ft.Column([
                ft.Text("Audio (Mastered)", size=11, color=ft.colors.BLUE_200),
                ft.Container(height=30, bgcolor=ft.colors.BLACK45, border_radius=4, alignment=ft.alignment.center, content=ft.Text("Phát bản đã xử lý", size=10, color=ft.colors.BLUE_200)),
                ft.Row([
                    ft.IconButton(icon=ft.icons.PLAY_ARROW, icon_size=16, padding=0, icon_color=ft.colors.BLUE, on_click=lambda _: audio_mastered.play()),
                    ft.IconButton(icon=ft.icons.PAUSE, icon_size=16, padding=0, icon_color=ft.colors.BLUE, on_click=lambda _: audio_mastered.pause()),
                ], alignment=ft.MainAxisAlignment.CENTER)
            ], spacing=5),
            bgcolor=ft.colors.SURFACE_VARIANT, padding=10, border_radius=8, expand=True
        )
    ], spacing=10)

    master_btn = ft.ElevatedButton(
        content=ft.Row([
            ft.Icon(ft.icons.AUTO_AWESOME, color=ft.colors.WHITE),
            ft.Text("Mastering ngay", size=15, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE)
        ], alignment=ft.MainAxisAlignment.CENTER),
        on_click=start_mastering,
        style=ft.ButtonStyle(bgcolor=ft.colors.INDIGO_700, padding=18),
        width=float("inf")
    )

    # Các nút chế độ
    mode_configs = [
        ("auto", "Tự động", ft.icons.MUSIC_NOTE),
        ("voice", "Giọng nói", ft.icons.MIC),
        ("instrument", "Nhạc cụ", ft.icons.LIBRARY_MUSIC),
        ("music", "Âm nhạc", ft.icons.AUDIOTRACK)
    ]

    mode_row_controls = []
    for key, label, icon in mode_configs:
        is_active = (key == "auto")
        container = ft.Container(
            content=ft.Column([ft.Icon(icon, size=18), ft.Text(label, size=10)], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=ft.colors.INDIGO_900 if is_active else ft.colors.SURFACE_VARIANT,
            padding=8,
            border_radius=8,
            expand=True,
            alignment=ft.alignment.center,
            ink=True,
            on_click=lambda e, k=key: select_mode(k)
        )
        mode_containers[key] = container
        mode_row_controls.append(container)

    modes_row = ft.Row(mode_row_controls, spacing=6)

    settings_section = ft.Row([
        ft.Container(
            content=ft.Row([
                ft.Icon(ft.icons.EQUALIZER, size=18, color=ft.colors.BLUE),
                ft.Text("Cân bằng âm sắc", size=11),
                eq_switch
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            bgcolor=ft.colors.SURFACE_VARIANT, padding=8, border_radius=8, expand=True
        ),
        ft.Container(
            content=ft.Row([
                ft.Icon(ft.icons.VOLUME_UP, size=18, color=ft.colors.BLUE),
                ft.Text("Tăng độ lớn", size=11),
                boost_switch
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            bgcolor=ft.colors.SURFACE_VARIANT, padding=8, border_radius=8, expand=True
        ),
    ], spacing=10)

    # Thanh điều hướng dưới đáy tương tác được
    bottom_nav = ft.Row([
        ft.Container(content=ft.Column([ft.Icon(ft.icons.HOME, size=18, color=ft.colors.BLUE), ft.Text("Trang chủ", size=10, color=ft.colors.BLUE)], horizontal_alignment=ft.CrossAxisAlignment.CENTER), on_click=lambda e: nav_clicked(e, "Trang chủ"), ink=True),
        ft.Container(content=ft.Column([ft.Icon(ft.icons.FOLDER, size=18, color=ft.colors.WHITE54), ft.Text("Dự án", size=10, color=ft.colors.WHITE54)], horizontal_alignment=ft.CrossAxisAlignment.CENTER), on_click=lambda e: nav_clicked(e, "Dự án"), ink=True),
        ft.Container(content=ft.Column([ft.Icon(ft.icons.HEADPHONES, size=18, color=ft.colors.WHITE54), ft.Text("Nghe thử", size=10, color=ft.colors.WHITE54)], horizontal_alignment=ft.CrossAxisAlignment.CENTER), on_click=lambda e: nav_clicked(e, "Nghe thử"), ink=True),
        ft.Container(content=ft.Column([ft.Icon(ft.icons.PERSON, size=18, color=ft.colors.WHITE54), ft.Text("Cá nhân", size=10, color=ft.colors.WHITE54)], horizontal_alignment=ft.CrossAxisAlignment.CENTER), on_click=lambda e: nav_clicked(e, "Cá nhân"), ink=True),
    ], alignment=ft.MainAxisAlignment.SPACE_AROUND)

    page.add(
        header,
        banner,
        file_card,
        waveform_section,
        master_btn,
        ft.Row([progress_ring, status_text], alignment=ft.MainAxisAlignment.CENTER, spacing=8),
        modes_row,
        settings_section,
        ft.Divider(height=5, color=ft.colors.TRANSPARENT),
        bottom_nav
    )

if __name__ == "__main__":
    ft.app(target=main)
