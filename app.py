import argparse
import csv
import tkinter as tk
from collections import defaultdict
from random import choices
from tkinter import ttk


class WindowedApplication(tk.Tk):
    '''TKinter App supporting multiple hidden windows.
    
    Args:
        *args, **kwargs: Parameters to pass to tk.Tk
        title (str): Window title
    '''

    def __init__(self, *args, title:str = 'Too Lazy to Set a Title', **kwargs):
        super().__init__(*args, **kwargs)
        super().title(title)
        self._frame = None


    def show_page(self, page_class):
        '''Show a page.
        
        Args:
            page_class: tk.Frame-like callable to instantiate and show
        '''
        if self._frame:
            self._frame.destroy()
        self._frame = page_class(self)
        self._frame.pack(side='top', fill='y', expand=1)


class Page(tk.Frame):
    '''TKinter frame for use with WindowedApplication.
    
    Args:
        master: tkinter container object with a show_page method.
        *args, **kwargs: Parameters to pass to tk.Frame. 
    '''

    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.master = master


    def show_page(self, page_class):
        '''Call the master method to show `page_class`'''
        self.master.show_page(page_name)


def load_questions(file='questions.csv'):
    questions = defaultdict(list)
    with open('questions.csv', encoding='utf-8') as infile:
        reader = csv.reader(infile)
        for row in reader:
            category_key = tuple(row[0:4])
            category_val = [int(row[4])]+row[5:]
            questions[category_key].append(category_val)
    return questions


def choose_random_category(questions):
    return choices(list(questions.keys()))[0]


class App(tk.Tk):

    def __init__(self, title='J-Practice', *args, **kwargs):
        super().__init__(*args, **kwargs)
        ttk.Style().theme_use('clam')
        self.geometry('600x100')
        self.log_file = log_file
        
        self.questions = load_questions(question_file)
        self.question_queue = []
        self.category = None
        self.active_question = None
        
        self._create_widgets()
        self._next_question()


    def _create_widgets(self):
        question_frame = ttk.Frame(self)
        question_frame.grid(row=0, column=0, sticky='nesw')
        
        self.category_l = ttk.Label(question_frame, text='', 
                                    anchor=tk.CENTER)
        self.category_l.grid(row=0, column=0, sticky='nesw')
        
        self.question_l = ttk.Label(question_frame, text='',
                                    wraplength=400,
                                    anchor=tk.CENTER)
        self.question_l.grid(row=1, column=0, sticky='nesw')
        
        question_frame.grid_columnconfigure(0, weight=1)
        for row in range(2):
            question_frame.grid_rowconfigure(row, weight=1)
        
        b_frame = ttk.Frame(self)
        b_frame.grid(row=1, column=0, sticky='nesw')
        
        self.left_b = ttk.Button(b_frame)
        self.left_b.grid(row=0, column=0, sticky='nesw')
        
        self.right_b = ttk.Button(b_frame)
        self.right_b.grid(row=0, column=1, sticky='nesw')
        
        b_frame.grid_rowconfigure(0, weight=1)
        for col in range(2):
            b_frame.grid_columnconfigure(col, weight=1)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)


    def _answer(self):
        self.left_b.configure(text='Correct', 
                              command=self._correct_answer)
        self.right_b.configure(text='Incorrect',
                               command=self._incorrect_answer)
        self._show_answer()


    def _show_answer(self):
        self.question_l.configure(text=self.active_question[2])


    def _next_question(self):
        if not self.question_queue:
            self.category = choose_random_category(self.questions)
            self.category_l.configure(text=self.category[3])
            self.question_queue = self.questions[self.category]
        self.active_question = self.question_queue.pop(0)
        self.question_l.configure(text=self.active_question[1])
        self.left_b.configure(text='Buzz In',
                              command=self._answer,
                              state=tk.ACTIVE)
        self.right_b.configure(text='Skip/No Answer',
                               command=self._skip_question)


    def _skip_question(self):
        self._write('Skip')
        self._show_answer()
        self.left_b.configure(state=tk.DISABLED)
        self.right_b.configure(text='Continue', command=self._next_question)

                    
    def _correct_answer(self):
        self._write(True)
        self._next_question()


    def _incorrect_answer(self):
        self._write(False)
        self._next_question()


    def _write(self, correct):
        correct_values = {True: 'Correct', False: 'Incorrect', 'Skip': 'Not Answered'}
        with open(self.log_file, 'a', encoding='utf-8', newline='') as outfile:
            writer = csv.writer(outfile)
            row = list(self.category)+self.active_question+[correct_values[correct]]
            writer.writerow(row)


if __name__ == '__main__':
    app = App()
    app.mainloop()
