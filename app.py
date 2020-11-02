import csv
import os.path
import random
import tkinter as tk

from configparser import ConfigParser
from typing import Callable, Iterable
from dataclasses import dataclass
from tkinter import ttk, messagebox

########## TKinter Wrapper


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


########## End TKinter Wrapper
########## Settings Parser


DEFAULTS = {
    'Settings': {
        'title': 'J-Practice'
    },
        
    'Questions': {
        'files': 'questions.csv',
        'ignorebadlines': 'yes'
    }
}


def load_jeopardy_settings(file:str = 'settings.cnf') -> ConfigParser:
    '''Load a ConfigParser with J-Practice settings.

    Args:
        file (str): Path to file to load settings from.

    Return (configparser.ConfigParser): Loaded settings.
    '''
    settings = configparser.ConfigParser()
    settings.read_dict(DEFAULTS)
    settings.read(file)    
    return settings


def save_jeopardy_settings(settings:ConfigParser, file:str = 'settings.cnf'):
    '''Save J-Practice settings.

    Args:
        settings (configparser.ConfigParser): Settings to save.
        file (str): Path to file to load settings from.
    '''
    with open(file, 'w') as settings_file:
        settings.write(settings_file)


########## End Settings Parser
########## Question Manager


@dataclass
class Question:
    identifer: str
    question: str
    answer: str
    correct_value: float
    incorrect_value: float
    skip_value: float
    tags: Iterable[str] = list


class QuestionManager:
    '''Loads and generates next J-Practice questions.

    Args:
        questions (Iterable[Question]): Initial question bank.
        queue (Iterable[Question]): Mext questions to get when next_question() is called.
    '''

    def __init__(self, questions: Iterable[Question] = [], queue: Iterable[Question] = []):
        self._questions = questions
        self._queue = []


    def load(self, file: str, *args, on_bad_line:Callable = None, **kwargs):
        '''Add questions from a file to the question bank.

        Args:
            file (str): Path to file to load questions from.
            ignore_bad_lines (Callable): Function to call when a malformed line is encountered.
            *args, **kwargs: Parameters to pass to file's CSV reader.

        Note:
            Each line is expected to contain a Question's fields in series. First, an
            identifier, then the question, answer, value when correct, value when incorrect,
            value when skipped, and tags, which can span any number of columns.
            If on_bad_line is not specified, an error will be raised. If it is specified,
            the bad row will be passed to the callable.
        '''
        with open(file, 'r', encoding='utf-8') as q_file:
            reader = csv.reader(file, *args, **kwargs)
            for row in reader:
                if len(row) < 6:
                    if on_bad_line is None:
                        raise IndexError('Row {} is too short'.format(row))
                    else:
                        on_bad_line(row)
                    

                try:
                    q_values = list(map(float, row[3:6]))
                except ValueError:
                    if on_bad_line is None:
                        raise ValueError('Bad float value in row {}'.format(row))
                    else:
                        on_bad_line(row)

                tags = row[6:]
                question = Question(*row[:3], *q_values, tags)
                self._questions.append(question)


    def random_question(self) -> Question:
        '''Choose a random question from the loaded questions.

        Return (Question): Chosen question.
        '''
        return random.choice(self._questions)


    def random_tag(self, ignore_frequency=True) -> str:
        '''Choose a random tag from the loaded questions.

        Args:
            ignore_frequency (bool): Whether to weight category choice by category frequency.

        Note:
            Raises IndexError if no questions are loaded.

        Return (str): Chosen tag.
        '''
        # I think generating a set outright rather than generating a list, then a set if
        # needed might prevent full evaluation of the list, conserving memory.
        if ignore_frequency:
            cats = set(t for t in q.tags for q in self.questions)
        else:
            cats = [t for t in q.tags for q in self.questions]
        return random.choice(cats)


########## End Question Manager
########## GUI


class App(WindowedApplication):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._settings = load_jeopardy_settings()

        title = self.settings.get('Settings', 'Title')
        self.title(title)

        # Load questions
        self._q_manager = QuestionManager()
        self._load_questions()


    def _load_questions(self):
        # In case ignorebadlines is incorrectly set.
        try:
            ibl = self.settings.getboolean('Questions', 'ignorebadlines')
        except (KeyError, ValueError):
            messagebox.showwarning('Warning', '{Invalid ignorebadlines setting.')
            ibl = DEFAULTS['Questions']['ignorebadlines']
        
        # Set function to be called on_bad_line.
        if ibl:
            obl = lambda x: None
        else:
            obl = lambda x: messagebox.showwarning('Warning', 'Bad line: {}'.format(x))
        
        paths = self.settings.get('Questions', 'files').split(',')
        for path in paths:
            if not os.path.isfile(path):
                messagebox.showerror('Error', '{} does not exist. Could not load questions.')
                continue
            self._q_manager.load(path, on_bad_line=obl)


    def destroy(self):
        save_jeopardy_settings(self._settings)
        super().destroy()


##class App(WindowedApplication):
##
##
##    def __init__(self, *args, config_file:str = 'config.cnf', **kwargs):
##        super().__init__(*args, **kwargs)
##        self.config_file = config_file
##        self.config = self._load_config()
##        self.title(self.config.get('Settings', 'Title'))
##        self.questions = self._load_questions()
##        
##        path = self.config.get('Performance', 'File')
##        self.results = open(path, 'a+', encoding='utf-8', newline='')
##        self.writer = csv.writer(self.results, delimiter=self.config.get('Performance', 'Delimiter'))
##        
##        self.active_question = None
##        
##        self._create_widgets()
##        self._next_question()
##
##
##    def _load_config(self):
##        config = configparser.ConfigParser()
##        config.read_dict(self.DEFAULTS)
##        config.read(self.config_file)
##        return config
##        
##        
##    def _load_questions(self):
##        questions = []
##        file = self.config.get('Questions', 'File')
##        
##        if not os.path.isfile(file):
##            self._error('Could not find {}.'.format(file))
##            self.destroy()
##        
##        try:
##            indices = (self.config.getint('Questions', 'RoundIndex'),
##                       self.config.getint('Questions', 'CategoryIndex'),
##                       self.config.getint('Questions', 'ValueIndex'),
##                       self.config.getint('Questions', 'ClueIndex'),
##                       self.config.getint('Questions', 'AnswerIndex'))
##        except ValueError:
##            self._error('Invalid Index Setting in Question File.')
##            self.destroy()
##        
##        with open(file, encoding='utf-8') as infile:
##            reader = csv.reader(infile)
##            for row in reader:
##                try:
##                    q = [row[i] for i in indices]
##                    q[2] = int(q[2])
##                    questions.append(q)
##                except (IndexError, ValueError):
##                    continue
##        return questions
##    
##    
##    def _create_widgets(self):
##        question_frame = ttk.Frame(self)
##        question_frame.grid(row=0, column=0, sticky='nesw')
##        
##        self.category_l = ttk.Label(question_frame, text='', 
##                                    anchor=tk.CENTER)
##        self.category_l.grid(row=0, column=0, sticky='nesw')
##        
##        self.value_l = ttk.Label(question_frame, text='', anchor=tk.CENTER)
##        self.value_l.grid(row=1, column=0, sticky='nesw')
##        
##        self.question_l = ttk.Label(question_frame, text='',
##                                    wraplength=400,
##                                    anchor=tk.CENTER)
##        self.question_l.grid(row=2, column=0, sticky='nesw')
##        
##        question_frame.grid_columnconfigure(0, weight=1)
##        question_frame.grid_rowconfigure(0, weight=1)
##        question_frame.grid_rowconfigure(1, weight=1)
##        question_frame.grid_rowconfigure(2, weight=1)
##        
##        b_frame = ttk.Frame(self)
##        b_frame.grid(row=1, column=0, sticky='nesw')
##        
##        self.left_b = ttk.Button(b_frame)
##        self.left_b.grid(row=0, column=0, sticky='nesw')
##        
##        self.right_b = ttk.Button(b_frame)
##        self.right_b.grid(row=0, column=1, sticky='nesw')
##        
##        self.analytics_b = ttk.Button(b_frame, text='Analytics', command=self._show_analytics)
##        self.analytics_b.grid(row=1, column=0, columnspan=2, sticky='nesw')
##        
##        b_frame.grid_rowconfigure(0, weight=1)
##        b_frame.grid_rowconfigure(1, weight=1)
##        b_frame.grid_columnconfigure(0, weight=1)
##        b_frame.grid_columnconfigure(1, weight=1)
##        
##        self.grid_columnconfigure(0, weight=1)
##        self.grid_rowconfigure(0, weight=1)
##        
##        
##    def _show_analytics(self):
##        pass
##
##
##    def _next_question(self):
##        self.active_question = random.choice(self.questions)
##        self.category_l.configure(text=self.active_question[1])
##        self.value_l.configure(text='$'+str(self.active_question[2]))
##        self.question_l.configure(text=self.active_question[3])
##        self.left_b.configure(text='Buzz In',
##                              command=self._answer,
##                              state=tk.ACTIVE)
##        self.right_b.configure(text='Skip/No Answer',
##                               command=self._skip_question)
##
##
##    def _answer(self):
##        self.left_b.configure(text='Correct', 
##                              command=self._correct_answer)
##        self.right_b.configure(text='Incorrect',
##                               command=self._incorrect_answer)
##        self._show_answer()
##
##
##    def _show_answer(self):
##        self.question_l.configure(text=self.active_question[4])
##
##
##    def _skip_question(self):
##        self._write(self.active_question, 'Skip')
##        self._show_answer()
##        self.left_b.configure(state=tk.DISABLED)
##        self.right_b.configure(text='Continue', command=self._next_question)
##
##                    
##    def _correct_answer(self):
##        self._write(self.active_question, 'Correct')
##        self._next_question()
##
##
##    def _incorrect_answer(self):
##        self._write(self.active_question, 'Incorrect')
##        self._next_question()
##
##
##    def _write(self, question, correct):
##        self.writer.writerow(question+[correct])
##
##
##    def _error(self, error_text):
##        Messagebox.showerror(title='Error', message=error_text) 
##    
##    
##    def destroy(self):
##        with open(self.config_file, 'w') as configfile:
##            self.config.write(configfile)
##        self.results.close()
##        super().destroy()
##
##
##if __name__ == '__main__':
##    app = App()
##    app.geometry('500x200')
##    app.mainloop()
##
