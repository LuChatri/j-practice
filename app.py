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
    settings = ConfigParser()
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
    category: str
    question: str
    answer: str
    value: float
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
            reader = csv.reader(q_file, *args, **kwargs)
            for row in reader:
                
                if len(row) < 5:
                    if on_bad_line is None:
                        raise IndexError('Row Too Short: {}'.format(row))
                    else:
                        on_bad_line(row)
                        continue
                elif len(row) == 5:
                    tags = []
                else:
                    tags = row[5:]
                    
                # Some values passed to Question must be floats.
                try:
                    value = float(row[4])
                except ValueError:
                    if on_bad_line is None:
                        raise ValueError('Bad Float Value in Row: {}'.format(row))
                    else:
                        on_bad_line(row)
                        continue
                
                # Get the rest of the values passed to Question.
                id, category, question, answer = row[:4]
                # The *[] syntax is needed since starred expressions must
                # follow positional arguments. Thus, tags must be passed
                # not as a positional argument, but as a starred expression.
                question = Question(id, category, question, answer, value, tags)
                self._questions.append(question)


    def random_question(self) -> Question:
        '''Choose a random question from the loaded questions.

        Return (Question): Chosen question.
        '''
        return random.choice(self._questions)


    def random_category(self) -> str:
        '''Choose a category tag from the loaded questions.

        Args:
            ignore_frequency (bool): Whether to weight category choice by category frequency.

        Note:
            Raises IndexError if no questions are loaded.

        Return (str): Chosen category.
        '''
        # I think generating a set outright rather than generating a list, then a set if
        # needed might prevent full evaluation of the list, conserving memory.
        if ignore_frequency:
            cats = set(q.category for q in self.questions)
        else:
            cats = [q.category for q in self.questions]
        return random.choice(tags)


    def next_question(self) -> Question:
        queue = []
        last_q = None
        while True:
            if not queue:
                cat = self.random_category()
                queue = list(sorted([q for q in self.questions if q.category == cat],
                                    key=lambda x: x.value))
            # A more advanced question-choosing algorithm can go here.
            yield queue.pop(0)


########## End Question Manager
########## GUI

class JPractice(WindowedApplication):
    '''J-Practice App

    Args:
        *args, **kwargs: Parameters to pass to WindowedApplication.
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._settings = load_jeopardy_settings()
        title = self._settings.get('Settings', 'Title')
        self.title(title)
        self.show_page(Main)
    

    def destroy(self):
        save_jeopardy_settings(self._settings)
        super().destroy()


class Main(Page):
    '''J-Practice Main page

    Args:
        *args, **kwargs: Parameters to pass to Page.
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        headline = ttk.Label(self, text='J-Practice', anchor=tk.CENTER)
        practice = ttk.Button(self, text='Practice',
                              command=lambda: self.show_page(Practice))
        analyze = ttk.Button(self, text='Analyze',
                             command=lambda: self.show_page(Analyze))
        settings = ttk.Button(self, text='Settings',
                              command=lambda: self.show_page(Settings))
        quit_b = ttk.Button(self, text='Quit', command=self.master.destroy)

        headline.grid(row=0, column=0, sticky='nesw')
        practice.grid(row=1, column=0, sticky='nesw')
        analyze.grid(row=2, column=0, sticky='nesw')
        settings.grid(row=3, column=0, sticky='nesw')
        quit_b.grid(row=4, column=0, sticky='nesw')

        self.grid_columnconfigure(0, weight=1)


class Practice(Page):
    '''Page for answering trivia questions.

    Args:
        *args, **kwargs: Parameters to pass to Page.
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._q_manager = QuestionManager()
        self._load_questions()

        leave = ttk.Button(self, text='Main Menu',
                           command=lambda: self.show_page(Main))
        leave.grid(row=1, column=0, sticky='nesw')


    def _load_questions(self):
        '''Load questions from files specified in J-Practice settings.'''
        settings = self.master._settings
        
        # ignorebadlines must be a boolean. Warn if it isn't.
        try:
            ibl = settings.getboolean('Questions', 'ignorebadlines')
        except (KeyError, ValueError):
            # Give a warning.
            ibl = settings.get('Questions', 'ignorebadlines')
            messagebox.showwarning('Warning', 'Invalid IgnoreBadLines Setting: {}.'.format(ibl))
            # Set a default value for ibl.
            ibl = DEFAULTS['Questions']['ignorebadlines']

        # Set on_bad_line callback based on ignorebadlines.
        if ibl:
            obl = lambda line: None
        else:
            obl = lambda line: messagebox.showwarning('Warning', 'Invalid Line: {}'.format(line))

        # Iterate through question files and load questions.
        paths = settings.get('Questions', 'files').split(',')
        for path in paths:
            if not os.path.isfile(path):
                messagebox.showerror('Error', 'Nonexistent Question File: {}'.format(path))
                continue
            self._q_manager.load(path, on_bad_line=obl)


class Analyze(Page):
    pass


class Settings(Page):
    pass


if __name__ == '__main__':
    app = JPractice()
    app.mainloop()
