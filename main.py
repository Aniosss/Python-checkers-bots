from tkinter import Tk, Canvas

from checkers.game import Game
from checkers.constants import X_SIZE, Y_SIZE, CELL_SIZE
from checkers.draw import UI


def main():
    # Создание окна
    main_window = Tk()
    main_window.title('Шашки')
    main_window.resizable(0, 0)

    # Создание холста
    main_canvas = Canvas(main_window, width=CELL_SIZE * X_SIZE, height=CELL_SIZE * Y_SIZE)
    main_canvas.pack()
    game = Game(X_SIZE, Y_SIZE)
    ui = UI(main_canvas, game)

    main_canvas.bind("<Motion>", ui.mouse_move)
    main_canvas.bind("<Button-1>", ui.mouse_down)

    main_window.mainloop()


if __name__ == '__main__':
    main()
