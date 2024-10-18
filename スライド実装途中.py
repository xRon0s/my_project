from tkinter import filedialog, messagebox, Canvas, Text, NW
from PIL import Image, ImageTk
import customtkinter as ctk
import json
import os
import threading

# 設定を保存する関数


def save_settings(settings):
    try:
        with open('settings.json', 'w') as f:
            json.dump(settings, f)
    except IOError as e:
        messagebox.showerror("Error", f"Error saving settings: {e}")

# 設定を読み込む関数


def load_settings():
    if os.path.exists('settings.json'):
        try:
            with open('settings.json', 'r') as f:
                return json.load(f)
        except IOError as e:
            messagebox.showerror("Error", f"Error loading settings: {e}")
    return {}


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # ウィンドウの設定
        self.title("新しいウィンドウの名前")

        # 前回の設定を読み込む
        self.settings = load_settings()
        self.geometry(self.settings.get('geometry', '800x600+100+100'))

        self.current_slide_index = 0

        # 画像とテキストボックスの参照を保持するリスト
        self.images = []
        self.image_ids = []  # キャンバス上の画像IDを保持するリスト
        self.text_ids = []  # キャンバス上のテキストボックスIDを保持するリスト
        self.selected_id = None

        self.image_paths = self.settings.get('image_path', [])
        self.image_data = self.settings.get('image_data', [])
        self.is_fullscreen = False

        # 利用可能なフォントのリスト
        self.available_fonts = ["Helvetica", "Arial",
                                "Times New Roman", "Courier New", "Comic Sans MS"]

        # ボタンのコマンド設定

        def select_image():
            file_paths = filedialog.askopenfilenames(
                filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.gif")])
            for file_path in file_paths:
                if file_path:
                    self.display_image(file_path)
                    self.settings['image_paths'] = self.settings.get(
                        'image_paths', []) + [file_path]

        # ボタンの詳細設定
        button = ctk.CTkButton(master=self, text="画像を選択",
                               command=select_image)
        button.grid(row=0, column=0, padx=20, pady=20,
                    sticky="ew", columnspan=2)
        self.grid_columnconfigure(0, weight=1)

        # テキストボックス生成ボタン
        text_button = ctk.CTkButton(
            master=self, text="テキストボックスを追加", command=self.create_text_box)
        text_button.grid(row=0, column=1, padx=20, pady=20,
                         sticky="ew", columnspan=2)

        fullscreen_button = ctk.CTkButton(
            master=self, text="スライドショー", command=self.toggle_fullscreen)
        fullscreen_button.grid(row=0, column=2, padx=20, pady=20,
                               sticky="ew", columnspan=2)

        # キャンバスを追加
        self.canvas = Canvas(
            self, bg='white', highlightthickness=1, highlightbackground='gray')
        self.canvas.grid(row=1, column=0, padx=20, pady=20,
                         sticky="nsew", columnspan=2)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.left_button = ctk.CTkButton(
            master=self, text="<", command=self.show_previous_slide)
        self.left_button.grid(row=2, column=0, padx=(
            20, 0), pady=20, sticky="ew")
        self.right_button = ctk.CTkButton(
            master=self, text=">", command=self.show_next_slide)
        self.right_button.grid(
            row=2, column=1, padx=(0, 20), pady=20, sticky="ew")

        for image_info in self.image_data:
          if 'path' in image_info and 'size' in image_info and 'position' in image_info:
            self.load_image(image_info)

        # 画像削除ボタンの詳細設定
        delete_button = ctk.CTkButton(
            master=self, text="選択したアイテムを削除", command=self.delete_selected_item)
        delete_button.grid(row=2, column=0, padx=20,
                           pady=20, sticky="ew", columnspan=2)

        # 入力用テキストエリアを追加
        self.text_entry = ctk.CTkEntry(master=self)
        self.text_entry.grid(row=3, column=0, padx=20,
                             pady=10, sticky="ew", columnspan=2)
        self.text_entry.bind("<Return>", self.save_text_edit)
        self.text_entry.bind("<FocusOut>", self.on_text_entry_focus_out)
        self.text_entry.grid_remove()

        # 前回表示していた画像を表示
        for file_path in self.settings.get('image_paths', []):
            if file_path:
                image_info = {
                    'path': file_path,
                    'position': (50, 50),
                    'size': (100, 100)
                }
                self.load_image(image_info)

        # 前回のテキストボックスを表示
        for text_box_info in self.settings.get('text_boxes', []):
            self.load_text_box(text_box_info)

        self.bind("<Escape>", self.exit_fullscreen)

        # ウィンドウが閉じられるときに設定を保存
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def display_image(self, file_path):
        try:
            image = Image.open(file_path)
            photo = ImageTk.PhotoImage(image)

            self.photo = photo

            if self.image_data:
                column = len(self.image_data) % 5
                row = len(self.image_data) // 5
                x = 50 + (column * 120)
                y = 50 + (row * 120)
            else:
                x, y = 50, 50

            image_id = self.canvas.create_image(x, y, anchor='nw', image=photo)

            self.images.append(photo)
            self.image_ids.append(image_id)
# 座標も保存

            self.image_data.append({
                'path': file_path,
                'position': (x, y),
                'size': image.size
            })

            self.canvas.tag_bind(
                image_id, "<ButtonPress-1>", self.on_item_press)
            self.canvas.tag_bind(image_id, "<B1-Motion>", self.on_item_move)

            self.canvas.config(scrollregion=self.canvas.bbox("all"))
        except IOError as e:
            messagebox.showerror("Error", f"Error loading image: {e}")

    def load_image(self, image_info):
        if not image_info or not image_info.get('path'):
          return

        try:
            image = Image.open(image_info['path'])
            resized_image = image.resize(image_info['size'], Image.LANCZOS)
            self.photo = ImageTk.PhotoImage(resized_image)

            x, y = image_info['position']
            image_id = self.canvas.create_image(
                x, y, anchor="nw", image=self.photo)

            self.images.append(self.photo)
            self.image_ids.append(image_id)

            self.canvas.config(scrollregion=self.canvas.bbox('all'))

            self.canvas.tag_bind(
                image_id, "<ButtonPress-1>", self.on_item_press)
            self.canvas.tag_bind(image_id, "<B1-Motion>", self.on_item_move)

        except IOError as e:
            messagebox.showerror("Error", f"Error loading image: {e}")

    def create_text_box(self):
        text_box = self.canvas.create_text(
            200, 200, anchor='nw', text="Edit me", font=("Helvetica", 32))
        self.text_ids.append(text_box)
        self.update_selection_rectangle()  # 修正：テキストボックスの選択領域を更新

        self.canvas.tag_bind(text_box, "<ButtonPress-1>", self.on_item_press)
        self.canvas.tag_bind(text_box, "<B1-Motion>", self.on_item_move)

    def load_text_box(self, text_box_info):
        text = text_box_info['text']
        font_name = text_box_info['font_name']
        font_size = text_box_info['font_size']
        x, y = text_box_info['position']

        text_box = self.canvas.create_text(
            x, y, anchor='nw', text=text, font=(font_name, font_size))
        self.text_ids.append(text_box)
        self.update_selection_rectangle()

        self.canvas.tag_bind(text_box, "<ButtonPress-1>", self.on_item_press)
        self.canvas.tag_bind(text_box, "<B1-Motion>", self.on_item_move)

    def toggle_fullscreen(self):
      self.is_fullscreen = not self.is_fullscreen
      self.attributes("-fullscreen", self.is_fullscreen)

      if self.is_fullscreen:
        self.hide_buttons_and_entries()
        self.text_entry.grid_remove()
      else:
        self.show_buttons_and_entries()

    def hide_buttons_and_entries(self):
      for widget in self.grid_slaves():
        if isinstance(widget, ctk.CTkButton) or isinstance(widget, ctk.CTkEntry):
          widget.grid_remove()

    def show_buttons_and_entries(self):
      for widget in self.grid_slaves():
        if isinstance(widget, ctk.CTkButton) or isinstance(widget, ctk.CTkEntry):
          widget.grid()

    def exit_fullscreen(self, event=None):
      self.attributes("-fullscreen", False)
      self.show_buttons_and_entries()

    def on_item_press(self, event):
        clicked_item_id = self.canvas.find_withtag("current")[0]
        self.selected_id = clicked_item_id

        self.item_start_x = event.x
        self.item_start_y = event.y

        self.update_selection_rectangle()

        if self.is_fullscreen:
          return

        # テキストボックスが選択された場合は入力エリアを表示
        if self.selected_id in self.text_ids:
            self.text_entry.grid()
            self.text_entry.delete(0, 'end')
            self.text_entry.insert(
                0, self.canvas.itemcget(self.selected_id, 'text'))
            self.text_entry.focus_set()
        else:
            self.text_entry.grid_remove()

    def on_text_entry_focus_out(self, event):
        self.save_text_edit(None)
        self.text_entry.grid_remove()

    def update_selection_rectangle(self):
        if hasattr(self, 'selection_rect'):
            self.canvas.delete(self.selection_rect)
        if hasattr(self, 'resize_handles'):
            for handle in self.resize_handles:
                self.canvas.delete(handle)

        if self.selected_id:
            x0, y0, x1, y1 = self.canvas.bbox(self.selected_id)
            self.selection_rect = self.canvas.create_rectangle(
                x0, y0, x1, y1, outline='gray', dash=(2, 2))
            self.resize_handles = [
                self.canvas.create_oval(
                    x0-5, y0-5, x0+5, y0+5, fill='gray'),  # Top-left
                self.canvas.create_oval(
                    x1-5, y0-5, x1+5, y0+5, fill='gray'),  # Top-right
                self.canvas.create_oval(
                    x0-5, y1-5, x0+5, y1+5, fill='gray'),  # Bottom-left
                self.canvas.create_oval(
                    x1-5, y1-5, x1+5, y1+5, fill='gray'),  # Bottom-right
                self.canvas.create_oval(
                    (x0+x1)/2-5, y0-5, (x0+x1)/2+5, y0+5, fill='gray'),  # Top-center
                self.canvas.create_oval(
                    (x0+x1)/2-5, y1-5, (x0+x1)/2+5, y1+5, fill='gray'),  # Bottom-center
                self.canvas.create_oval(
                    x0-5, (y0+y1)/2-5, x0+5, (y0+y1)/2+5, fill='gray'),  # Left-center
                self.canvas.create_oval(
                    x1-5, (y0+y1)/2-5, x1+5, (y0+y1)/2+5, fill='gray')   # Right-center
            ]

            for handle in self.resize_handles:
                self.canvas.tag_bind(
                    handle, "<ButtonPress-1>", self.on_resize_press)
                self.canvas.tag_bind(
                    handle, "<B1-Motion>", self.on_resize_item)

    def update_text_size(self, event):
        new_text = self.text_entry.get()
        self.canvas.itemconfig(self.selected_id, text=new_text)
        self.update_selection_rectangle()

    def on_item_move(self, event):
        if not self.selected_id or self.is_fullscreen:
            return

        dx = event.x - self.item_start_x
        dy = event.y - self.item_start_y
        self.canvas.move(self.selected_id, dx, dy)

        if self.selected_id in self.image_ids:
            current_index = self.image_ids.index(self.selected_id)

            if current_index < len(self.image_data):
              self.image_data[current_index]['position'] = self.canvas.coords(self.selected_id)[
                  :2]

        if hasattr(self, 'selection_rect'):
            self.canvas.move(self.selection_rect, dx, dy)
        if hasattr(self, 'resize_handles'):
            for handle in self.resize_handles:
                self.canvas.move(handle, dx, dy)
        self.item_start_x = event.x
        self.item_start_y = event.y

    def on_resize_press(self, event):
        self.resize_start_x = event.x
        self.resize_start_y = event.y

    def on_resize_item(self, event):
        if not self.selected_id or self.is_fullscreen:
            return

        dx = event.x - self.resize_start_x
        dy = event.y - self.resize_start_y

        x0, y0, x1, y1 = self.canvas.bbox(self.selected_id)

        new_x0 = x0 + dx
        new_y0 = y0 + dy
        new_x1 = x1 + dx
        new_y1 = y1 + dy

        if self.selected_id in self.image_ids:
            current_index = self.image_ids.index(self.selected_id)

            if 0 <= current_index < len(self.image_data):
              self.image_data[current_index]['size'] = (
                  new_x1 - new_x0, new_y1 - new_y0)

            else:
              print(
                  f"Index out of range for current_index: {current_index}, image_data length: {len(self.image_data)}")

        try:
            handle_index = self.resize_handles.index(
                self.canvas.find_withtag("current")[0])
        except ValueError:
            return  # If the handle is not found, do nothing

        if handle_index == 0:  # Top-left
            new_x0, new_y0 = x0 + dx, y0 + dy
            new_x1, new_y1 = x1, y1
        elif handle_index == 1:  # Top-right
            new_x0, new_y0 = x0, y0 + dy
            new_x1, new_y1 = x1 + dx, y1
        elif handle_index == 2:  # Bottom-left
            new_x0, new_y0 = x0 + dx, y0
            new_x1, new_y1 = x1, y1 + dy
        elif handle_index == 3:  # Bottom-right
            new_x0, new_y0 = x0, y0
            new_x1, new_y1 = x1 + dx, y1 + dy
        elif handle_index == 4:  # Top-center
            new_x0, new_y0 = x0, y0 + dy
            new_x1, new_y1 = x1, y1
        elif handle_index == 5:  # Bottom-center
            new_x0, new_y0 = x0, y0
            new_x1, new_y1 = x1, y1 + dy
        elif handle_index == 6:  # Left-center
            new_x0, new_y0 = x0 + dx, y0
            new_x1, new_y1 = x1, y1
        elif handle_index == 7:  # Right-center
            new_x0, new_y0 = x0, y0
            new_x1, new_y1 = x1 + dx, y1

        new_width = int(new_x1 - new_x0)
        new_height = int(new_y1 - new_y0)
        if new_width > 0 and new_height > 0:
            if self.selected_id in self.image_ids:
                current_index = self.image_ids.index(self.selected_id)
                image = Image.open(self.settings['image_paths'][current_index])
                resized_image = image.resize(
                    (new_width, new_height), Image.LANCZOS)

                self.photo = ImageTk.PhotoImage(resized_image)
                self.canvas.itemconfig(self.selected_id, image=self.photo)
                self.images[current_index] = self.photo

                self.canvas.coords(self.selected_id, new_x0, new_y0)

            elif self.selected_id in self.text_ids:
                text_content = self.canvas.itemcget(self.selected_id, "text")
                self.canvas.coords(self.selected_id, new_x0, new_y0)
                self.canvas.itemconfig(self.selected_id, width=new_width)

            if hasattr(self, 'selection_rect'):
                self.canvas.coords(self.selection_rect,
                                   new_x0, new_y0, new_x1, new_y1)

            handle_coords = [
                (new_x0, new_y0),  # Top-left
                (new_x1, new_y0),  # Top-right
                (new_x0, new_y1),  # Bottom-left
                (new_x1, new_y1),  # Bottom-right
                ((new_x0 + new_x1) / 2, new_y0),  # Top-center
                ((new_x0 + new_x1) / 2, new_y1),  # Bottom-center
                (new_x0, (new_y0 + new_y1) / 2),  # Left-center
                (new_x1, (new_y0 + new_y1) / 2)   # Right-center
            ]
            for index, handle in enumerate(self.resize_handles):
                x, y = handle_coords[index]
                self.canvas.coords(handle, x - 5, y - 5, x + 5, y + 5)

        self.resize_start_x = event.x
        self.resize_start_y = event.y

    def save_text_edit(self, event):
        if self.is_fullscreen:
          return

        new_text = self.text_entry.get()
        if self.selected_id and self.selected_id in self.text_ids:
            parts = new_text.split('*')
            text_content = parts[0].strip()
            font_name = "Helvetica"  # デフォルトのフォント
            font_size = 32  # デフォルトのフォントサイズ
            if len(parts) > 1:
                try:
                    font_size = int(parts[1].strip())
                except ValueError:
                    pass
            if len(parts) > 2 and parts[2].strip() in self.available_fonts:
                font_name = parts[2].strip()

            # テキスト内容に改行を追加
            text_content = text_content.replace('~~', '\n')

            self.canvas.itemconfig(
                self.selected_id, text=text_content, font=(font_name, font_size))
        self.text_entry.grid_remove()

    def delete_selected_item(self):
        if self.selected_id:
            if self.selected_id in self.image_ids:
                index = self.image_ids.index(self.selected_id)
                if index < len(self.image_data):
                    del self.settings['image_paths'][index]  # 画像のパスを削除
                    self.image_ids.remove(self.selected_id)
                    self.image_data.pop(index)
                    self.canvas.delete(self.selected_id)

            elif self.selected_id in self.text_ids:
                index = self.text_ids.index(self.selected_id)
                if index < len(self.text_ids):
                    self.text_ids.remove(self.selected_id)
                    self.canvas.delete(self.selected_id)

            self.selected_id = None
            if hasattr(self, 'selection_rect'):
                self.canvas.delete(self.selection_rect)
            if hasattr(self, 'resize_handles'):
                for handle in self.resize_handles:
                    self.canvas.delete(handle)
            save_settings(self.settings)  # 設定を保存

    def on_closing(self):
        self.settings['geometry'] = self.geometry()

        self.settings['image_data'] = self.image_data

        text_boxes = []
        for text_id in self.text_ids:
            x, y = self.canvas.coords(text_id)
            text = self.canvas.itemcget(text_id, 'text')
            font_info = self.canvas.itemcget(text_id, 'font')

            # フォント情報の解析
            font_parts = font_info.split()
            font_name = font_parts[0]
            font_size = None
            for part in font_parts:
                if part.isdigit():
                    font_size = int(part)
                    break
            if font_size is None:
                font_size = 32  # デフォルトのフォントサイズ

            text_boxes.append({
                'text': text,
                'font_name': font_name,
                'font_size': font_size,
                'position': (x, y)
            })
        self.settings['text_boxes'] = text_boxes

        save_settings(self.settings)
        self.destroy()

    def load_saved_content(self):
           for file_path in self.settings.get('image_paths', []):
              if file_path:
                image_info = {
                    'path': file_path,
                  'position': (50, 50),  # デフォルトの位置
                  'size': (100, 100)     # デフォルトのサイズ
                }
                self.load_image(image_info)

    # 前回のテキストボックスを表示
            if self.image_paths:
              self.display_slide(self.current_slide_index)

    def show_next_slide(self):
         if self.current_slide_index < len(self.image_paths) - 1:
            self.current_slides_index += 1
            self.display_slides(self.current_slide_index)

    def show_previous_slide(self):
           # 現在のスライドインデックスを更新
         if self.current_slide_index > 0:
            self.current_slide_index -= 1
            self.display_slide(self.current_slide_index)

    def display_slide(self, index):
         self.canvas.delete('all')

        # 指定されたインデックスの画像を表示
          if index < len(self.image_paths):
            # 画像を読み込んで表示
            image_path = self.image_paths[index]
            image_info = {
                'path': image_path,
                'position': (50, 50),  # デフォルトの位置
                'size': (400, 300)     # サイズを適宜調整
            }
            self.load_image(image_info)


if __name__ == "__main__":
    app = App()
    app.mainloop()
