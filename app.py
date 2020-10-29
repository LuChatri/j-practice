import configparser
import csv
import os.path
import random
import re
import tkinter as tk
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


class App(WindowedApplication):

    DEFAULTS = {
        'Settings': {
            'Title': 'J-Practice'
        },
        
        'Questions': {
            'File': 'questions.csv',
            'Delimiter': ',',
            'RoundIndex': '2',
            'CategoryIndex': '3',
            'ValueIndex': '4',
            'ClueIndex': '5',
            'AnswerIndex': '6'
        },
        
        'Performance': {
            'File': 'performance.csv',
            'Delimiter': ',',
            'RoundIndex': '0',
            'CategoryIndex': '1',
            'ValueIndex': '2',
            'ClueIndex': '3',
            'AnswerIndex': '4',
            'OutcomeIndex': '5'
        }
    }
    

    def __init__(self, *args, config_file:str = 'config.cnf', **kwargs):
        super().__init__(*args, **kwargs)
        self.config_file = config_file
        self.config = self._load_config()
        self.title(self.config.get('Settings', 'Title'))
        self.questions = self._load_questions()
        
        path = self.config.get('Performance', 'File')
        self.results = open(path, 'a+', encoding='utf-8', newline='')
        self.writer = csv.writer(self.results, delimiter=self.config.get('Performance', 'Delimiter'))
        
        self.active_question = None
        
        self._create_widgets()
        self._next_question()


    def _load_config(self):
        config = configparser.ConfigParser()
        config.read_dict(self.DEFAULTS)
        config.read(self.config_file)
        return config
        
        
    def _load_questions(self):
        questions = []
        file = self.config.get('Questions', 'File')
        
        if not os.path.isfile(file):
            self._error('Could not find {}.'.format(file))
            self.destroy()
        
        try:
            indices = (self.config.getint('Questions', 'RoundIndex'),
                       self.config.getint('Questions', 'CategoryIndex'),
                       self.config.getint('Questions', 'ValueIndex'),
                       self.config.getint('Questions', 'ClueIndex'),
                       self.config.getint('Questions', 'AnswerIndex'))
        except ValueError:
            self._error('Invalid Index Setting in Question File.')
            self.destroy()
        
        with open(file, encoding='utf-8') as infile:
            reader = csv.reader(infile)
            for row in reader:
                try:
                    q = [row[i] for i in indices]
                    q[2] = int(q[2])
                    questions.append(q)
                except (IndexError, ValueError):
                    continue
        return questions
    
    
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


    def _next_question(self):
        self.active_question = random.choice(self.questions)
        self.category_l.configure(text=self.active_question[1])
        self.question_l.configure(text=self.active_question[3])
        self.left_b.configure(text='Buzz In',
                              command=self._answer,
                              state=tk.ACTIVE)
        self.right_b.configure(text='Skip/No Answer',
                               command=self._skip_question)


    def _answer(self):
        self.left_b.configure(text='Correct', 
                              command=self._correct_answer)
        self.right_b.configure(text='Incorrect',
                               command=self._incorrect_answer)
        self._show_answer()


    def _show_answer(self):
        self.question_l.configure(text=self.active_question[4])


    def _skip_question(self):
        self._write(self.active_question, 'Skip')
        self._show_answer()
        self.left_b.configure(state=tk.DISABLED)
        self.right_b.configure(text='Continue', command=self._next_question)

                    
    def _correct_answer(self):
        self._write(self.active_question, 'Correct')
        self._next_question()


    def _incorrect_answer(self):
        self._write(self.active_question, 'Incorrect')
        self._next_question()


    def _write(self, question, correct):
        self.writer.writerow(question+[correct])


    def _error(self, error_text):
        print(error_text)
    
    
    def destroy(self):
        with open(self.config_file, 'w') as configfile:
            self.config.write(configfile)
        self.results.close()
        super().destroy()


if __name__ == '__main__':
    app = App()
    app.mainloop()
