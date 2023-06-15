from random import choice
from math import inf

from checkers.field import Field
from checkers.move import Move
from checkers.constants import *
from checkers.enums import CheckerType, SideType


class Game:
    def __init__(self, x_field_size: int, y_field_size: int):
        self.field = Field(x_field_size, y_field_size)

        self.player_turn = True



    def __handle_move(self, move: Move, draw: bool = True) -> bool:
        '''Совершение хода'''

        # Изменение типа шашки, если она дошла до края
        if (move.to_y == 0 and self.field.type_at(move.from_x, move.from_y) == CheckerType.WHITE_REGULAR):
            self.field.at(move.from_x, move.from_y).change_type(CheckerType.WHITE_QUEEN)
        elif (move.to_y == self.field.y_size - 1 and self.field.type_at(move.from_x,
                                                                        move.from_y) == CheckerType.BLACK_REGULAR):
            self.field.at(move.from_x, move.from_y).change_type(CheckerType.BLACK_QUEEN)

        # Изменение позиции шашки
        self.field.at(move.to_x, move.to_y).change_type(self.field.type_at(move.from_x, move.from_y))
        self.field.at(move.from_x, move.from_y).change_type(CheckerType.NONE)

        # Вектора движения
        dx = -1 if move.from_x < move.to_x else 1
        dy = -1 if move.from_y < move.to_y else 1

        # Удаление съеденных шашек
        has_killed_checker = False
        x, y = move.to_x, move.to_y
        while (x != move.from_x or y != move.from_y):
            x += dx
            y += dy
            if (self.field.type_at(x, y) != CheckerType.NONE):
                self.field.at(x, y).change_type(CheckerType.NONE)
                has_killed_checker = True


        return has_killed_checker

    def predict_optimal_moves(self, side):
        '''Предсказать оптимальный ход'''
        best_result = 0
        optimal_moves = []
        predicted_moves_list = self.get_predicted_moves_list(side)

        if (predicted_moves_list):
            field_copy = Field.copy(self.field)
            for moves in predicted_moves_list:
                for move in moves:
                    self.__handle_move(move, draw=False)

                try:
                    if (side == SideType.WHITE):
                        result = self.field.white_score / self.field.black_score
                    elif (side == SideType.BLACK):
                        result = self.field.black_score / self.field.white_score
                except ZeroDivisionError:
                    result = inf

                if (result > best_result):
                    best_result = result
                    optimal_moves.clear()
                    optimal_moves.append(moves)
                elif (result == best_result):
                    optimal_moves.append(moves)

                self.field = Field.copy(field_copy)

        optimal_move = []
        if (optimal_moves):
            # Фильтрация хода
            for move in choice(optimal_moves):
                if (side == SideType.WHITE and self.field.type_at(move.from_x, move.from_y) in BLACK_CHECKERS):
                    break
                elif (side == SideType.BLACK and self.field.type_at(move.from_x, move.from_y) in WHITE_CHECKERS):
                    break

                optimal_move.append(move)

        return optimal_move

    def get_predicted_moves_list(self, side, current_prediction_depth: int = 0,
                                 all_moves_list=[], current_moves_list=[],
                                 required_moves_list=[]):
        '''Предсказать все возможные ходы'''

        if (current_moves_list):
            all_moves_list.append(current_moves_list)
        else:
            all_moves_list.clear()

        if (required_moves_list):
            moves_list = required_moves_list
        else:
            moves_list = self.get_moves_list(side)

        if (moves_list and current_prediction_depth < MAX_PREDICTION_DEPTH):
            field_copy = Field.copy(self.field)
            for move in moves_list:
                has_killed_checker = self.__handle_move(move, draw=False)

                required_moves_list = list(filter(
                    lambda required_move: move.to_x == required_move.from_x and move.to_y == required_move.from_y,
                    self.get_required_moves_list(side)))

                # Если есть ещё ход этой же шашкой
                if (has_killed_checker and required_moves_list):
                    self.get_predicted_moves_list(side, current_prediction_depth, all_moves_list,
                                                  current_moves_list + [move], required_moves_list)
                else:
                    self.get_predicted_moves_list(SideType.opposite(side), current_prediction_depth + 1,
                                                  all_moves_list, current_moves_list + [move])

                self.field = Field.copy(field_copy)

        return all_moves_list

    def get_moves_list(self, side):
        '''Получение списка ходов'''
        moves_list = self.get_required_moves_list(side)
        if not (moves_list):
            moves_list = self.get_optional_moves_list(side)
        return moves_list

    def get_required_moves_list(self, side):
        '''Получение списка обязательных ходов'''
        moves_list = []

        # Определение типов шашек
        if (side == SideType.WHITE):
            friendly_checkers = WHITE_CHECKERS
            enemy_checkers = BLACK_CHECKERS
        elif (side == SideType.BLACK):
            friendly_checkers = BLACK_CHECKERS
            enemy_checkers = WHITE_CHECKERS
        else:
            return moves_list

        for y in range(self.field.y_size):
            for x in range(self.field.x_size):

                # Для обычной шашки
                if (self.field.type_at(x, y) == friendly_checkers[0]):
                    for offset in MOVE_OFFSETS:
                        if not (self.field.is_within(x + offset.x * 2, y + offset.y * 2)): continue

                        if self.field.type_at(x + offset.x, y + offset.y) in enemy_checkers and self.field.type_at(
                                x + offset.x * 2, y + offset.y * 2) == CheckerType.NONE:
                            moves_list.append(Move(x, y, x + offset.x * 2, y + offset.y * 2))

                # Для дамки
                elif (self.field.type_at(x, y) == friendly_checkers[1]):
                    for offset in MOVE_OFFSETS:
                        if not (self.field.is_within(x + offset.x * 2, y + offset.y * 2)): continue

                        has_enemy_checker_on_way = False

                        for shift in range(1, self.field.size):
                            if not (self.field.is_within(x + offset.x * shift, y + offset.y * shift)): continue

                            # Если на пути не было вражеской шашки
                            if (not has_enemy_checker_on_way):
                                if (self.field.type_at(x + offset.x * shift, y + offset.y * shift) in enemy_checkers):
                                    has_enemy_checker_on_way = True
                                    continue
                                # Если на пути союзная шашка - то закончить цикл
                                elif (self.field.type_at(x + offset.x * shift,
                                                         y + offset.y * shift) in friendly_checkers):
                                    break

                            # Если на пути была вражеская шашка
                            if (has_enemy_checker_on_way):
                                if (self.field.type_at(x + offset.x * shift,
                                                       y + offset.y * shift) == CheckerType.NONE):
                                    moves_list.append(Move(x, y, x + offset.x * shift, y + offset.y * shift))
                                else:
                                    break

        return moves_list

    def get_optional_moves_list(self, side):
        '''Получение списка необязательных ходов'''
        moves_list = []

        # Определение типов шашек
        if (side == SideType.WHITE):
            friendly_checkers = WHITE_CHECKERS
        elif (side == SideType.BLACK):
            friendly_checkers = BLACK_CHECKERS
        else:
            return moves_list

        for y in range(self.field.y_size):
            for x in range(self.field.x_size):
                # Для обычной шашки
                if (self.field.type_at(x, y) == friendly_checkers[0]):
                    for offset in MOVE_OFFSETS[:2] if side == SideType.WHITE else MOVE_OFFSETS[2:]:
                        if not (self.field.is_within(x + offset.x, y + offset.y)): continue

                        if (self.field.type_at(x + offset.x, y + offset.y) == CheckerType.NONE):
                            moves_list.append(Move(x, y, x + offset.x, y + offset.y))

                # Для дамки
                elif (self.field.type_at(x, y) == friendly_checkers[1]):
                    for offset in MOVE_OFFSETS:
                        if not (self.field.is_within(x + offset.x, y + offset.y)): continue

                        for shift in range(1, self.field.size):
                            if not (self.field.is_within(x + offset.x * shift, y + offset.y * shift)): continue

                            if (self.field.type_at(x + offset.x * shift, y + offset.y * shift) == CheckerType.NONE):
                                moves_list.append(Move(x, y, x + offset.x * shift, y + offset.y * shift))
                            else:
                                break
        return moves_list
