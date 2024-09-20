from importlib.resources import files
import threading
import tkinter as tk
from tkinter import ttk
from timeit import timeit

SPINNER = files('animations').joinpath('spinner_earth_50x50.gif')


class ProgressPopup(tk.Toplevel):
    progress_text = ""
    elapsed = 0  # Time elapsed in seconds

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Scanning")
        self.geometry("350x100")
        self.resizable(False, False)

        # Create a frame to hold the canvas and text widget
        self.frame = ttk.Frame(self)
        self.frame.grid(pady=10)

        self.canvas = tk.Canvas(self.frame, width=50, height=50)
        self.canvas.grid(row=0, column=0, padx=10)

        self.text = tk.Text(self.frame, width=30, height=2, wrap=tk.CHAR,
                            state=tk.DISABLED, bg=self.cget('bg'), relief='flat', borderwidth=0)
        self.text.grid(row=0, column=1, sticky=tk.W)

        self.text.config(state=tk.NORMAL)
        self.text.config(state=tk.DISABLED)

        self.frames = [tk.PhotoImage(file=SPINNER,
                                     format='gif -index %i' % i) for i in range(62)]
        self.current_frame = 0
        self.animation_running = False

    def start_animation(self):
        self.elapsed = 0
        self.animation_running = True
        self.update_animation()
        self.update_progress()

    def stop_animation(self):
        self.animation_running = False
        self.update_text("Done!")
        self.text.config(state=tk.DISABLED)

        self.after(1000, self.destroy)

    def update_animation(self):
        if self.animation_running:
            self.canvas.create_image(25, 25, image=self.frames[self.current_frame])
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.after(25, self.update_animation)

    def update_text(self, new_text):
        self.text.config(state=tk.NORMAL)
        self.text.delete(1.0, tk.END)
        self.text.insert(tk.END, new_text)
        self.text.config(state=tk.DISABLED)

    def update_progress(self):
        if self.animation_running:
            # Update the text or any other progress indicator here
            self.update_text(f"Scanning...\nTime elapsed: {self.elapsed} seconds")
            self.after(1000, self.update_progress)
            self.elapsed += 1


def fib(n):
    if n <= 1:
        return n
    else:
        return fib(n-1) + fib(n-2)


def do_work(n: int, progress: ProgressPopup = None):
    print(f'do work start, n={n}')
    f = fib(n)
    print('do work end')
    print(f'fib({n}) = {f}')
    # if progress:
    #     progress.update_progress()


class mainwin:
    def __init__(self):
        self.root = tk.Tk()
        self.root.geometry("300x200")
        self.info_label = ttk.Label(text="Main window")
        self.info_label.pack()
        self.button1 = tk.Button(self.root, text='Do Task', command=self.do_task)
        self.button1.pack(padx=10, pady=10)
        self.root.mainloop()

    def do_task(self):
        def openprog(self):
            global progress
            self.button1["state"] = "disabled"
            progress = ProgressPopup(self.root)

        def check_done(t: threading.Thread):
            if not t.is_alive():
                progress.stop_animation()
                self.button1["state"] = "normal"
            else:
                self.root.after(1000, check_done, t)

        def task():
            openprog(self)
            progress.start_animation()
            t = threading.Thread(target=do_work, args=(40,))
            t.start()
            self.root.after(1000, check_done, t)

        task()


def main():
    mainwin()


def timer_test():
    for n in range(35, 40):
        st = timeit(lambda: do_work(n), number=1)
        print(f'fib({n}) takes {st:.5f} seconds')


if __name__ == "__main__":
    # timer_test()
    main()
