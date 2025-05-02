import pygame
import sys

pygame.init()

# Konstanten
WIDTH, HEIGHT = 640, 640
ROWS, COLS = 8, 8
SQUARE_SIZE = WIDTH // COLS


# Farben
WHITE = (245, 245, 220)
BLACK = (139, 69, 19)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

# Fenster
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Schach - Besser!")

# Figuren laden
pieces = {}
piece_types = ['bR', 'bN', 'bB', 'bQ', 'bK', 'bP', 'wR', 'wN', 'wB', 'wQ', 'wK', 'wP']
for piece in piece_types:

    img = pygame.image.load(f"images/{piece}.png")

    pieces[piece] = pygame.transform.scale(img, (SQUARE_SIZE, SQUARE_SIZE))

# Start-Board
board = [
    ['bR', 'bN', 'bB', 'bQ', 'bK', 'bB', 'bN', 'bR'],
    ['bP', 'bP', 'bP', 'bP', 'bP', 'bP', 'bP', 'bP'],
    ['', '', '', '', '', '', '', ''],
    ['', '', '', '', '', '', '', ''],
    ['', '', '', '', '', '', '', ''],
    ['', '', '', '', '', '', '', ''],
    ['wP', 'wP', 'wP', 'wP', 'wP', 'wP', 'wP', 'wP'],
    ['wR', 'wN', 'wB', 'wQ', 'wK', 'wB', 'wN', 'wR'],
]

#Überprüfen ob der König/Turm schon bewegt hat
has_moved = {
    'wK': False,
    'wR_left': False,   # Weiser Trum a1 (row 7, col 0)
    'wR_right': False,  #Weiser Turn h1 (row 7, col 7)
    'bK': False,
    'bR_left': False,   #Schwarzer Turm a8 (row 0, col 0)
    'bR_right': False,  #Schwarzer Turm h8 (Reihe 0, Spalte 7)

}

#Check für einen en-passat zug
en_passant_target = None
# Auswahl
selected = None
valid_moves = []
turn = 'w'  # Weiß startet


def draw_board(win):
    win.fill(WHITE)
    for row in range(ROWS):
        for col in range(COLS):
            if (row + col) % 2 == 1:
                pygame.draw.rect(win, BLACK, (col*SQUARE_SIZE, row*SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))


def draw_pieces(win, board):
    for row in range(ROWS):
        for col in range(COLS):
            piece = board[row][col]
            if piece != '':
                win.blit(pieces[piece], (col*SQUARE_SIZE, row*SQUARE_SIZE))

def get_row_col_from_mouse(pos):
    x, y = pos
    return y // SQUARE_SIZE, x // SQUARE_SIZE

def is_enemy(piece1, piece2):
    return (piece1.startswith('w') and piece2.startswith('b')) or (piece1.startswith('b') and piece2.startswith('w'))

def is_square_attacked(board, row, col, attacker_color):
    for r in range(ROWS):
        for c in range(COLS):
            piece = board[r][c]
            if piece.startswith(attacker_color):
                possible = get_possible_moves(board, r, c)
                if (row, col) in possible:
                    return True
    return False

def can_castle(board, color, side):
    row = 7 if color == 'w' else 0
    king_col = 4
    if side == 'left':
        rook_col = 0
        between_squares = [1,2,3]
        king_path = [3,2]
        rook_key = color + 'R_left'
    else:
        rook_col = 7
        between_squares = [5,6]
        king_path = [5,6]
        rook_key = color + 'R_right'

    king_key = color + 'K'

    if has_moved.get(king_key, True):
        return False

    if has_moved.get(rook_key, True):
        return False

    if board[row][king_col] != king_key:
        return False

    if board[row][rook_col] != color + 'R':
        return False

    for c in between_squares:
        if board[row][c] != '':
            return False


    if is_in_check(board, color):
        return False

    enemy_color = 'b' if color == 'w' else 'w'

    for c in king_path:
        if is_square_attacked(board, row, c, enemy_color):
            return False

    return True


def get_valid_moves(board, row, col):
    global en_passant_target
    moves = []
    piece = board[row][col]
    if piece == '':
        return moves

    possible_moves = get_possible_moves(board, row, col)
    legal_moves = []
    current_color = piece[0]

    for move in possible_moves:
        test_board = [r.copy() for r in board]
        mr, mc = move
        original_piece = test_board[mr][mc]
        moved_piece = test_board[row][col]
        test_board[mr][mc] = moved_piece
        test_board[row][col] = ''

        #Rochade
        if piece[1] == 'K' and abs(mc - col) == 2 and row == mr:
            if mc > col:
                rook_from_c = 7
                rook_to_c = 5
            else:
                rook_from_c = 0
                rook_to_c = 3
            test_board[row][rook_to_c] = test_board[row][rook_from_c]
            test_board[row][rook_from_c] = ''

        if piece[1] == 'P' and (mr, mc) == en_passant_target:
            #Entferne den geschlagenen Bauern beim En-Passant
            ep_row = row
            ep_col = mc
            test_board[ep_row][ep_col] = ''

        if not is_in_check(test_board, current_color):
            legal_moves.append(move)

    return legal_moves

def get_possible_moves(board, row, col):
    global en_passant_target
    moves = []
    piece = board[row][col]
    if piece == '':
        return moves

    directions = []

    if piece[1] == 'P':  #Bauer
        dir = -1 if piece[0] == 'w' else 1
        start_row = 6 if piece[0] == 'w' else 1
        #Normaler Zug nach vorne
        if 0 <= row+dir < ROWS and board[row+dir][col] == '':
            moves.append((row+dir, col))
            if row == start_row and board[row+2*dir][col] == '':
                moves.append((row+2*dir, col))

        #Schlagen
        for dc in [-1, 1]:
            if 0 <= col+dc < COLS and 0 <= row+dir < ROWS:
                target = board[row+dir][col+dc]
                if target != '' and is_enemy(piece, target):
                    moves.append((row+dir, col+dc))

        #Ein En-Passant-Schlag
        for dc in [-1, 1]:
            ep_row = row + dir
            ep_col = col + dc
            if (ep_row, ep_col) == en_passant_target:
                moves.append((ep_row, ep_col))

    elif piece[1] == 'R':
        directions = [(-1,0), (1,0), (0,-1), (0,1)]
    elif piece[1] == 'B':
        directions = [(-1,-1), (-1,1), (1,-1), (1,1)]
    elif piece[1] == 'Q':
        directions = [(-1,0), (1,0), (0,-1), (0,1), (-1,-1), (-1,1), (1,-1), (1,1)]
    elif piece[1] == 'N':
        knight_moves = [(-2,-1), (-2,1), (-1,-2), (-1,2), (1,-2), (1,2), (2,-1), (2,1)]
        for dr, dc in knight_moves:
            r, c = row + dr, col + dc
            if 0 <= r < ROWS and 0 <= c < COLS:
                target = board[r][c]
                if target == '' or is_enemy(piece, target):
                    moves.append((r, c))
    elif piece[1] == 'K':
        king_moves = [(-1,0), (1,0), (0,-1), (0,1), (-1,-1), (-1,1), (1,-1), (1,1)]
        for dr, dc in king_moves:
            r, c = row + dr, col + dc
            if 0 <= r < ROWS and 0 <= c < COLS:
                target = board[r][c]
                if target == '' or is_enemy(piece, target):
                    moves.append((r, c))

        color = piece[0]
        if can_castle(board, color, 'left'):
            moves.append((row, col - 2))
        if can_castle(board, color, 'right'):
            moves.append((row, col + 2))

    if directions:
        for dr, dc in directions:
            r, c = row, col
            while True:
                r += dr
                c += dc
                if 0 <= r < ROWS and 0 <= c < COLS:
                    target_piece = board[r][c]
                    if target_piece == '':
                        moves.append((r, c))
                    elif is_enemy(piece, target_piece):
                        moves.append((r, c))
                        break
                    else:
                        break
                else:
                    break

    return moves

def is_in_check(board, color):
    king_pos = None
    for r in range(ROWS):
        for c in range(COLS):
            if board[r][c] == color + 'K':
                king_pos = (r, c)
                break

        if king_pos:
            break
    if not king_pos:
        return False

    enemy = 'b' if color == 'w' else 'w'
    for r in range(ROWS):
        for c in range(COLS):
            if board[r][c].startswith(enemy):
                if king_pos in get_possible_moves(board, r, c):
                    return True
    return False

def main():
    global selected, valid_moves, turn, has_moved, en_passant_target
    clock = pygame.time.Clock()
    run = True

    while run:
        clock.tick(60)
        draw_board(WIN)
        draw_pieces(WIN, board)

        if selected:
            r, c = selected
            pygame.draw.rect(WIN, BLUE, (c*SQUARE_SIZE, r*SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE), 3)
            for move in valid_moves:
                mr, mc = move
                pygame.draw.circle(WIN, GREEN, (mc*SQUARE_SIZE + SQUARE_SIZE//2, mr*SQUARE_SIZE + SQUARE_SIZE//2), 10)

        if is_in_check(board, turn):
            for r in range(ROWS):
                for c in range(COLS):
                    if board[r][c] == turn + 'K':
                        pygame.draw.rect(WIN, RED, (c*SQUARE_SIZE, r*SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE), 5)

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                row, col = get_row_col_from_mouse(pos)

                if selected:
                    if (row, col) in valid_moves:
                        piece_moved = board[selected[0]][selected[1]]

                        #Rochaden-Zug
                        if piece_moved[1] == 'K' and abs(col - selected[1]) == 2:
                            if col > selected[1]:
                                board[row][col] = piece_moved
                                board[selected[0]][selected[1]] = ''
                                board[row][5] = board[row][7]
                                board[row][7] = ''
                                has_moved[piece_moved[0] + 'K'] = True
                                has_moved[piece_moved[0] + 'R_right'] = True
                            else:
                                board[row][col] = piece_moved
                                board[selected[0]][selected[1]] = ''
                                board[row][3] = board[row][0]
                                board[row][0] = ''
                                has_moved[piece_moved[0] + 'K'] = True
                                has_moved[piece_moved[0] + 'R_left'] = True

                            en_passant_target = None  #Rochade

                        #En Passant Kram
                        elif piece_moved[1] == 'P' and (row, col) == en_passant_target:
                            board[row][col] = piece_moved
                            board[selected[0]][selected[1]] = ''
                            ep_pawn_row = row + (1 if piece_moved[0] == 'w' else -1)
                            board[ep_pawn_row][col] = ''
                            has_moved[piece_moved[0] + 'P'] = True
                            en_passant_target = None

                        else:
                            # Normaler Zug
                            board[row][col] = piece_moved
                            board[selected[0]][selected[1]] = ''
                            if not (piece_moved[1] == 'P' and abs(row - selected[0]) == 2):
                                en_passant_target = None

                            # Setze ein En-Passant Punkt 
                            if piece_moved[1] == 'P' and abs(row - selected[0]) == 2:
                                en_passant_target = ((row + selected[0]) // 2, col)
                            else:
                                en_passant_target = None

                            #Ich mag zuege 
                            if piece_moved[1] == 'K':
                                has_moved[piece_moved[0] + 'K'] = True
                            elif piece_moved[1] == 'R':
                                if selected == (7,0):
                                    has_moved[piece_moved[0] + 'R_left'] = True
                                elif selected == (7,7):
                                    has_moved[piece_moved[0] + 'R_right'] = True
                                elif selected == (0,0):
                                    has_moved[piece_moved[0] + 'R_left'] = True
                                elif selected == (0,7):
                                    has_moved[piece_moved[0] + 'R_right'] = True

                        selected = None
                        valid_moves = []
                        turn = 'b' if turn == 'w' else 'w'
                    else:
                        selected = None
                        valid_moves = []
                if board[row][col] != '' and board[row][col][0] == turn:
                    selected = (row, col)
                    valid_moves = get_valid_moves(board, row, col)

if __name__ == "__main__":
    main()