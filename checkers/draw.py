from tkinter import Canvas, Event, messagebox
from PIL import Image, ImageTk
from pathlib import Path
from time import sleep


from checkers.field import Field
from checkers.move import Move
from checkers.constants import *
from checkers.enums import CheckerType, SideType
from checkers.game import Game

class UI:
    def __init__(self, canvas: Canvas, game: Game):
        self.__canvas = canvas
        self.__game = game

        self.__hovered_cell = Point()
        self.__selected_cell = Point()
        self.__animated_cell = Point()

        self.__init_images()

        self.__draw()


    def __init_images(self):
        '''Инициализация изображений'''
        self.__images = {
            CheckerType.WHITE_REGULAR: ImageTk.PhotoImage(
                Image.open(Path('assets', 'white-regular.png')).resize((CELL_SIZE, CELL_SIZE), Image.ANTIALIAS)),
            CheckerType.BLACK_REGULAR: ImageTk.PhotoImage(
                Image.open(Path('assets', 'black-regular.png')).resize((CELL_SIZE, CELL_SIZE), Image.ANTIALIAS)),
            CheckerType.WHITE_QUEEN: ImageTk.PhotoImage(
                Image.open(Path('assets', 'white-queen.png')).resize((CELL_SIZE, CELL_SIZE), Image.ANTIALIAS)),
            CheckerType.BLACK_QUEEN: ImageTk.PhotoImage(
                Image.open(Path('assets', 'black-queen.png')).resize((CELL_SIZE, CELL_SIZE), Image.ANTIALIAS)),
        }

    def __animate_move(self, move: Move):
        '''Анимация перемещения шашки'''
        self.__animated_cell = Point(move.from_x, move.from_y)
        self.__draw()

        # Создание шашки для анимации
        animated_checker = self.__canvas.create_image(move.from_x * CELL_SIZE, move.from_y * CELL_SIZE,
                                                      image=self.__images.get(
                                                          self.__game.field.type_at(move.from_x, move.from_y)), anchor='nw',
                                                      tag='animated_checker')

        # Вектора движения
        dx = 1 if move.from_x < move.to_x else -1
        dy = 1 if move.from_y < move.to_y else -1

        # Анимация
        for distance in range(abs(move.from_x - move.to_x)):
            for _ in range(100 // ANIMATION_SPEED):
                self.__canvas.move(animated_checker, ANIMATION_SPEED / 100 * CELL_SIZE * dx,
                                   ANIMATION_SPEED / 100 * CELL_SIZE * dy)
                self.__canvas.update()
                sleep(0.01)

        self.__animated_cell = Point()

    def __draw(self):
        '''Отрисовка сетки поля и шашек'''
        self.__canvas.delete('all')
        self.__draw_field_grid()
        self.__draw_checkers()

    def __draw_field_grid(self):
        '''Отрисовка сетки поля'''
        for y in range(self.__game.field.y_size):
            for x in range(self.__game.field.x_size):
                self.__canvas.create_rectangle(x * CELL_SIZE, y * CELL_SIZE, x * CELL_SIZE + CELL_SIZE,
                                               y * CELL_SIZE + CELL_SIZE, fill=FIELD_COLORS[(y + x) % 2], width=0,
                                               tag='boards')

                # Отрисовка рамок у необходимых клеток
                if (x == self.__selected_cell.x and y == self.__selected_cell.y):
                    self.__canvas.create_rectangle(x * CELL_SIZE + BORDER_WIDTH // 2, y * CELL_SIZE + BORDER_WIDTH // 2,
                                                   x * CELL_SIZE + CELL_SIZE - BORDER_WIDTH // 2,
                                                   y * CELL_SIZE + CELL_SIZE - BORDER_WIDTH // 2,
                                                   outline=SELECT_BORDER_COLOR, width=BORDER_WIDTH, tag='border')
                elif (x == self.__hovered_cell.x and y == self.__hovered_cell.y):
                    self.__canvas.create_rectangle(x * CELL_SIZE + BORDER_WIDTH // 2, y * CELL_SIZE + BORDER_WIDTH // 2,
                                                   x * CELL_SIZE + CELL_SIZE - BORDER_WIDTH // 2,
                                                   y * CELL_SIZE + CELL_SIZE - BORDER_WIDTH // 2,
                                                   outline=HOVER_BORDER_COLOR, width=BORDER_WIDTH, tag='border')

                # Отрисовка возможных точек перемещения, если есть выбранная ячейка
                if (self.__selected_cell):
                    player_moves_list = self.__game.get_moves_list(PLAYER_SIDE)
                    for move in player_moves_list:
                        if (self.__selected_cell.x == move.from_x and self.__selected_cell.y == move.from_y):
                            self.__canvas.create_oval(move.to_x * CELL_SIZE + CELL_SIZE / 3,
                                                      move.to_y * CELL_SIZE + CELL_SIZE / 3,
                                                      move.to_x * CELL_SIZE + (CELL_SIZE - CELL_SIZE / 3),
                                                      move.to_y * CELL_SIZE + (CELL_SIZE - CELL_SIZE / 3),
                                                      fill=POSIBLE_MOVE_CIRCLE_COLOR, width=0,
                                                      tag='posible_move_circle')

    def __draw_checkers(self):
        '''Отрисовка шашек'''
        for y in range(self.__game.field.y_size):
            for x in range(self.__game.field.x_size):
                # Не отрисовывать пустые ячейки и анимируемую шашку
                if (self.__game.field.type_at(x, y) != CheckerType.NONE and not (
                        x == self.__animated_cell.x and y == self.__animated_cell.y)):
                    self.__canvas.create_image(x * CELL_SIZE, y * CELL_SIZE,
                                               image=self.__images.get(self.__game.field.type_at(x, y)), anchor='nw',
                                               tag='checkers')

    def mouse_move(self, event: Event):
        '''Событие перемещения мышки'''
        x, y = (event.x) // CELL_SIZE, (event.y) // CELL_SIZE
        if (x != self.__hovered_cell.x or y != self.__hovered_cell.y):
            self.__hovered_cell = Point(x, y)

            # Если ход игрока, то перерисовать
            if (self.__game.player_turn):
                self.__draw()

    def mouse_down(self, event: Event):
        '''Событие нажатия мышки'''
        if not (self.__game.player_turn): return

        x, y = (event.x) // CELL_SIZE, (event.y) // CELL_SIZE

        # Если точка не внутри поля
        if not (self.__game.field.is_within(x, y)): return

        if (PLAYER_SIDE == SideType.WHITE):
            player_checkers = WHITE_CHECKERS
        elif (PLAYER_SIDE == SideType.BLACK):
            player_checkers = BLACK_CHECKERS
        else:
            return

        # Если нажатие по шашке игрока, то выбрать её
        if self.__game.field.type_at(x, y) in player_checkers:
            self.__selected_cell = Point(x, y)
            self.__draw()
        elif self.__game.player_turn:
            move = Move(self.__selected_cell.x, self.__selected_cell.y, x, y)

            # Если нажатие по ячейке, на которую можно походить
            if move in self.__game.get_moves_list(PLAYER_SIDE):
                self.__handle_player_turn(move)

                # Если не ход игрока, то ход противника
                if not self.__game.player_turn:
                    self.__handle_enemy_turn()

    def __handle_move(self, move: Move, draw: bool = True) -> bool:
        '''Совершение хода'''
        if draw: self.__animate_move(move)

        # Изменение типа шашки, если она дошла до края
        if move.to_y == 0 and self.__game.field.type_at(move.from_x, move.from_y) == CheckerType.WHITE_REGULAR:
            self.__game.field.at(move.from_x, move.from_y).change_type(CheckerType.WHITE_QUEEN)
        elif (move.to_y == self.__game.field.y_size - 1 and self.__game.field.type_at(move.from_x,
                                                                            move.from_y) == CheckerType.BLACK_REGULAR):
            self.__game.field.at(move.from_x, move.from_y).change_type(CheckerType.BLACK_QUEEN)

        # Изменение позиции шашки
        self.__game.field.at(move.to_x, move.to_y).change_type(self.__game.field.type_at(move.from_x, move.from_y))
        self.__game.field.at(move.from_x, move.from_y).change_type(CheckerType.NONE)

        # Вектора движения
        dx = -1 if move.from_x < move.to_x else 1
        dy = -1 if move.from_y < move.to_y else 1

        # Удаление съеденных шашек
        has_killed_checker = False
        x, y = move.to_x, move.to_y
        while (x != move.from_x or y != move.from_y):
            x += dx
            y += dy
            if (self.__game.field.type_at(x, y) != CheckerType.NONE):
                self.__game.field.at(x, y).change_type(CheckerType.NONE)
                has_killed_checker = True

        if (draw): self.__draw()

        return has_killed_checker

    def __handle_player_turn(self, move: Move):
        '''Обработка хода игрока'''
        self.__game.player_turn = False

        # Была ли убита шашка
        has_killed_checker = self.__handle_move(move)

        required_moves_list = list(
            filter(lambda required_move: move.to_x == required_move.from_x and move.to_y == required_move.from_y,
                   self.__game.get_required_moves_list(PLAYER_SIDE)))

        # Если есть ещё ход этой же шашкой
        if has_killed_checker and required_moves_list:
            self.__game.player_turn = True

        self.__selected_cell = Point()

    def __handle_enemy_turn(self):
        '''Обработка хода противника (компьютера)'''
        self.__game.player_turn = False

        optimal_moves_list = self.__game.predict_optimal_moves(SideType.opposite(PLAYER_SIDE))

        for move in optimal_moves_list:
            self.__handle_move(move)

        self.__game.player_turn = True

        self.__check_for_game_over()

    def __check_for_game_over(self):
        '''Проверка на конец игры'''
        game_over = False

        white_moves_list = self.__game.get_moves_list(SideType.WHITE)
        if not (white_moves_list):
            # Белые проиграли
            answer = messagebox.showinfo('Конец игры', 'Чёрные выиграли')
            game_over = True

        black_moves_list = self.__game.get_moves_list(SideType.BLACK)
        if not (black_moves_list):
            # Чёрные проиграли
            answer = messagebox.showinfo('Конец игры', 'Белые выиграли')
            game_over = True

        if game_over:
            # Новая игра
            self.__game.__init__(self.__game.field.x_size, self.__game.field.y_size)