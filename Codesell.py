import tkinter as tk
from tkinter import simpledialog, messagebox

class PresentationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Presentation App")

        self.canvas = tk.Canvas(self.root, width=800, height=600)
        self.canvas.pack()

        self.slides = []
        self.current_slide = 0

        self.create_widgets()

    def create_widgets(self):
        self.add_slide_button = tk.Button(self.root, text="Add Slide", command=self.add_slide)
        self.add_slide_button.pack(side=tk.LEFT)

        self.add_code_cell_button = tk.Button(self.root, text="Add Code Cell", command=self.add_code_cell)
        self.add_code_cell_button.pack(side=tk.LEFT)

        self.execute_code_button = tk.Button(self.root, text="Execute Code", command=self.execute_current_slide_code)
        self.execute_code_button.pack(side=tk.LEFT)

        self.next_slide_button = tk.Button(self.root, text="Next Slide", command=self.next_slide)
        self.next_slide_button.pack(side=tk.RIGHT)

        self.prev_slide_button = tk.Button(self.root, text="Previous Slide", command=self.prev_slide)
        self.prev_slide_button.pack(side=tk.RIGHT)

    def add_slide(self):
        slide = Slide(self.canvas)
        self.slides.append(slide)
        self.show_slide(len(self.slides) - 1)

    def add_code_cell(self):
        if self.slides:
            code_cell = self.slides[self.current_slide].add_code_cell()
            code_cell.pack()

    def next_slide(self):
        if self.current_slide < len(self.slides) - 1:
            self.show_slide(self.current_slide + 1)

    def prev_slide(self):
        if self.current_slide > 0:
            self.show_slide(self.current_slide - 1)

    def show_slide(self, index):
        for slide in self.slides:
            slide.hide()
        self.slides[index].show()
        self.current_slide = index

    def execute_current_slide_code(self):
        self.execute_slide_code(self.current_slide)

    def execute_slide_code(self, index):
        slide = self.slides[index]
        for code_cell in slide.code_cells:
            code = code_cell.get("1.0", tk.END)
            try:
                exec(code)
            except Exception as e:
                messagebox.showerror("Error", f"Error executing code: {e}")

class Slide:
    def __init__(self, canvas):
        self.canvas = canvas
        self.frame = tk.Frame(canvas)
        self.code_cells = []

    def add_code_cell(self):
        code_cell = tk.Text(self.frame, height=5, width=60)
        self.code_cells.append(code_cell)
        return code_cell

    def show(self):
        self.frame.pack()

    def hide(self):
        self.frame.pack_forget()

if __name__ == "__main__":
    root = tk.Tk()
    app = PresentationApp(root)
    root.mainloop()