import pygame
import sys
import copy
import random

# ---------------- SETTINGS -----------------
BOARD_WIDTH, BOARD_HEIGHT = 800, 800
SIDEBAR_WIDTH = 220
WINDOW_WIDTH = BOARD_WIDTH + SIDEBAR_WIDTH
WINDOW_HEIGHT = BOARD_HEIGHT

ROWS = 8
COLS = 8
SQUARE_SIZE = BOARD_WIDTH // COLS

pygame.init()
FONT  = pygame.font.SysFont("Arial", 28)
SMALL = pygame.font.SysFont("Arial", 20)
WIN = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Checkers")


BLACK = (0, 0, 0)

# ----THEME SYSTEM -----
THEMES = {
    "Classic": {
        "BG": (240, 240, 240),
        "LIGHT": (255, 255, 255),
        "DARK": (128, 128, 128),
        "HINT_NORMAL": (0, 200, 0),
        "HINT_CAPTURE": (255, 165, 0),
        "PANEL": (235, 235, 235),
        "ACCENT": (20, 20, 20),
    },
    "Wood": {
        "BG": (230, 220, 200),
        "LIGHT": (210, 180, 140),   
        "DARK": (139, 69, 19),      
        "HINT_NORMAL": (0, 150, 0),
        "HINT_CAPTURE": (255, 140, 0),
        "PANEL": (220, 205, 175),
        "ACCENT": (60, 30, 10),
    },
    "Neon": {
        "BG": (18, 18, 22),
        "LIGHT": (60, 60, 70),
        "DARK": (20, 20, 28),
        "HINT_NORMAL": (0, 255, 180),
        "HINT_CAPTURE": (255, 80, 120),
        "PANEL": (28, 28, 35),
        "ACCENT": (230, 230, 240),
    },
}

current_theme_name = "Classic"
current_theme = THEMES[current_theme_name]

def set_theme(name):
    
    global current_theme_name, current_theme
    current_theme_name = name
    current_theme = THEMES[name]


RED   = (255, 0, 0)
BLACK_PIECE = (0, 0, 0)  

# ---- UTILS ----
def get_scores(board):
    """Score = number of opponent pieces captured (simple 1 point each)."""
    red_score   = 12 - board.black_left  # red has captured these
    black_score = 12 - board.red_left    # black has captured these
    return red_score, black_score

def player_has_any_moves(board, color):
    """Detect stalemate/immobility: if current player has zero legal moves."""
    for r in range(ROWS):
        for c in range(COLS):
            p = board.get_piece(r, c)
            if p != 0 and p.color == color:
                if board.get_valid_moves(p):
                    return True
    return False

# ---- PIECE CLASS -----
class Piece:
    PADDING = 15
    OUTLINE = 2

    def __init__(self, row, col, color):
        self.row = row
        self.col = col
        self.color = color          # RED or BLACK PIECE
        self.king = False

    def make_king(self):
        self.king = True

    def draw(self, win):
        """Draw this piece. Uses image sprites for all four piece types."""
        x = self.col * SQUARE_SIZE
        y = self.row * SQUARE_SIZE
        
        scale = int(SQUARE_SIZE * 1.50)

        # Load images once and scale to current square size
        if not hasattr(Piece, "images_loaded") or getattr(Piece, "img_scale", None) != scale:
            def load_and_scale(name):
                img = pygame.image.load(name).convert_alpha()
                
                size = min(img.get_width(), img.get_height())
                sq = pygame.Surface((size, size), pygame.SRCALPHA)
                sq.blit(img, ((size - img.get_width())//2, (size - img.get_height())//2))
                return pygame.transform.smoothscale(sq, (scale, scale))

            Piece.red_img     = load_and_scale("red_piece.png")
            Piece.redK_img    = load_and_scale("red_king.png")
            Piece.black_img   = load_and_scale("black_piece.png")
            Piece.blackK_img  = load_and_scale("black_king.png")
            Piece.images_loaded = True
            Piece.img_scale = scale

        # Choose correct image
        if self.color == RED:
            img = Piece.redK_img if self.king else Piece.red_img
        else:
            img = Piece.blackK_img if self.king else Piece.black_img

        win.blit(img, (x + (SQUARE_SIZE - scale)//2,
                       y + (SQUARE_SIZE - scale)//2))

# ------ BOARD CLASS ------
class Board:
    def __init__(self):
        self.board = []
        self.red_left = self.black_left = 12
        self.red_kings = self.black_kings = 0
        self.create_board()

    def create_board(self):
        """Setup starting positions."""
        self.board = []
        for r in range(ROWS):
            self.board.append([])
            for c in range(COLS):
                if (r + c) % 2 == 1:
                    if r < 3:
                        self.board[r].append(Piece(r, c, BLACK_PIECE))
                    elif r > 4:
                        self.board[r].append(Piece(r, c, RED))
                    else:
                        self.board[r].append(0)
                else:
                    self.board[r].append(0)

    def draw_squares(self, win):
        """Draw checkerboard with themed colors."""
        light = current_theme["LIGHT"]
        dark  = current_theme["DARK"]
        for r in range(ROWS):
            for c in range(COLS):
                color = light if (r + c) % 2 == 0 else dark
                pygame.draw.rect(win, color, (c*SQUARE_SIZE, r*SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

    def move(self, piece, row, col):
        """Move a piece; crown if reaching the end."""
        self.board[piece.row][piece.col], self.board[row][col] = 0, piece
        piece.row = row
        piece.col = col
        
        if (piece.color == RED and row == 0) or (piece.color == BLACK_PIECE and row == ROWS-1):
            if not piece.king:
                piece.make_king()
                if piece.color == RED:   self.red_kings += 1
                else:                    self.black_kings += 1

    def remove(self, pieces):
        """Remove captured pieces from board & update counts."""
        for p in pieces:
            self.board[p.row][p.col] = 0
            if p.color == RED:
                self.red_left -= 1
            else:
                self.black_left -= 1

    def winner(self):
        if self.red_left <= 0:   return "Black"
        if self.black_left <= 0: return "Red"
        return None

    def get_piece(self, r, c):
        return self.board[r][c]

    def get_valid_moves(self, piece):
        
        moves = {}

        # Movement directions for this piece
        dirs = []
        if piece.color == RED or piece.king:
            dirs.extend([(-1, -1), (-1, 1)])  
        if piece.color == BLACK_PIECE or piece.king:
            dirs.extend([(1, -1), (1, 1)])    

        
        for dr, dc in dirs:
            r = piece.row + dr
            c = piece.col + dc
            if 0 <= r < ROWS and 0 <= c < COLS and self.board[r][c] == 0:
                moves[(r, c)] = []

        # Recursive capture search
        def explore(r, c, skipped, visited):
            found_capture = False
            for dr, dc in dirs:
                r1, c1 = r + dr, c + dc       
                r2, c2 = r + 2*dr, c + 2*dc   
                if 0 <= r2 < ROWS and 0 <= c2 < COLS and 0 <= r1 < ROWS and 0 <= c1 < COLS:
                    mid = self.board[r1][c1]
                    if mid != 0 and mid.color != piece.color and self.board[r2][c2] == 0 and (r2, c2) not in visited:
                        found_capture = True
                        new_skipped = skipped + [mid]
                        moves[(r2, c2)] = new_skipped
                        explore(r2, c2, new_skipped, visited | {(r2, c2)})
            return found_capture

        explore(piece.row, piece.col, [], set())

        
        capture_moves = {dst: caps for dst, caps in moves.items() if caps}
        return capture_moves if capture_moves else moves

# ----- AI -----
def evaluate(b):
    """
    Simple but stronger evaluation:
    - material: men=1, kings=1.6 (via king counts + captured counts)
    - mobility: number of available moves
    """
    red_material   = (12 - b.black_left) + 1.6 * b.red_kings
    black_material = (12 - b.red_left)   + 1.6 * b.black_kings

    def mobility(color):
        cnt = 0
        for r in range(ROWS):
            for c in range(COLS):
                p = b.get_piece(r, c)
                if p != 0 and p.color == color:
                    cnt += len(b.get_valid_moves(p))
        return cnt

    red_mob   = mobility(RED)
    black_mob = mobility(BLACK_PIECE)

    return (red_material - black_material) + 0.03 * (red_mob - black_mob)

def get_all_moves(b, color):
    capture_states = []
    quiet_states = []
    for r in range(ROWS):
        for c in range(COLS):
            P = b.get_piece(r, c)
            if P != 0 and P.color == color:
                vm = b.get_valid_moves(P)
                for (nr, nc), skip in vm.items():
                    temp = copy.deepcopy(b)
                    cp = temp.get_piece(r, c)
                    temp.move(cp, nr, nc)
                    if skip:
                        temp.remove(skip)
                        capture_states.append(temp)
                    else:
                        quiet_states.append(temp)
    return capture_states if capture_states else quiet_states

def minimax(pos, depth, maximizing, color):
    
    if depth == 0 or pos.winner():
        return evaluate(pos), pos

    if maximizing:
        best_val = float('-inf')
        best_move = pos
        moves = get_all_moves(pos, color)
        if not moves:
            return evaluate(pos), pos
        for m in moves:
            val, _ = minimax(m, depth - 1, False, color)
            if val > best_val:
                best_val, best_move = val, m
        return best_val, best_move
    else:
        opp = RED if color == BLACK_PIECE else BLACK_PIECE
        best_val = float('inf')
        best_move = pos
        moves = get_all_moves(pos, opp)
        if not moves:
            return evaluate(pos), pos
        for m in moves:
            val, _ = minimax(m, depth - 1, True, color)
            if val < best_val:
                best_val, best_move = val, m
        return best_val, best_move

# ----- DRAW BOARD + SIDEBAR -----
def draw_screen(win, board, valid, turn, ai_mode):
    """Main render: board, pieces, hints, sidebar, scores."""
    board.draw_squares(win)
    for r in range(ROWS):
        for c in range(COLS):
            p = board.get_piece(r, c)
            if p:
                p.draw(win)

    # Hints: green (normal), orange (capture)
    for (rr, cc), caps in [(k, v) for k, v in valid.items() if k != '_selected']:
        color = current_theme["HINT_NORMAL"] if not caps else current_theme["HINT_CAPTURE"]
        pygame.draw.circle(win, color,
            (cc*SQUARE_SIZE + SQUARE_SIZE//2, rr*SQUARE_SIZE + SQUARE_SIZE//2), 14)

    # Sidebar
    pygame.draw.rect(win, current_theme["PANEL"], (BOARD_WIDTH, 0, SIDEBAR_WIDTH, WINDOW_HEIGHT))
    accent = current_theme["ACCENT"]
    t = SMALL.render(f"Turn: {'Red' if turn == RED else 'Black'}", True, accent)
    win.blit(t, (BOARD_WIDTH + 20, 20))

    # Scores
    red_score, black_score = get_scores(board)
    sr = SMALL.render(f"Red:   {red_score}", True, accent)
    sb = SMALL.render(f"Black: {black_score}", True, accent)
    win.blit(sr, (BOARD_WIDTH + 20, 48))
    win.blit(sb, (BOARD_WIDTH + 20, 70))

    # Buttons (including themes)
    buttons = {
        "Restart": pygame.Rect(BOARD_WIDTH+30, 110, 160, 40),
        "Quit":    pygame.Rect(BOARD_WIDTH+30, 160, 160, 40),
    }
    if ai_mode:
        buttons["Change AI"] = pygame.Rect(BOARD_WIDTH+30, 210, 160, 40)

    # Theme buttons
    buttons["Theme: Classic"] = pygame.Rect(BOARD_WIDTH+30, 270, 160, 34)
    buttons["Theme: Wood"]    = pygame.Rect(BOARD_WIDTH+30, 310, 160, 34)
    buttons["Theme: Neon"]    = pygame.Rect(BOARD_WIDTH+30, 350, 160, 34)

    for lbl, r in buttons.items():
        pygame.draw.rect(win, (210,210,210), r, border_radius=6)
        pygame.draw.rect(win, (50,50,50), r, 2, border_radius=6)
        tx = SMALL.render(lbl, True, (20,20,20))
        win.blit(tx, (r.x + (r.width - tx.get_width())//2,
                      r.y + (r.height - tx.get_height())//2))

    pygame.display.update()
    return buttons

def draw_winner_overlay(text):
    """On-board overlay with Play Again / Main Menu buttons. Returns 'restart' or 'menu'."""
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
    overlay.set_alpha(160)
    overlay.fill((0,0,0))
    WIN.blit(overlay, (0, 0))

    box = pygame.Rect(WINDOW_WIDTH//2 - 220, WINDOW_HEIGHT//2 - 120, 440, 240)
    pygame.draw.rect(WIN, (255,255,255), box, border_radius=12)
    pygame.draw.rect(WIN, (30,30,30), box, 2, border_radius=12)

    title = FONT.render(text, True, (20,20,20))
    WIN.blit(title, (box.x + (box.w - title.get_width())//2, box.y + 30))

    btn_restart = pygame.Rect(box.x + 40, box.y + 140, 150, 44)
    btn_menu    = pygame.Rect(box.x + box.w - 190, box.y + 140, 150, 44)
    for r, label in [(btn_restart, "Play Again"), (btn_menu, "Main Menu")]:
        pygame.draw.rect(WIN, (230,230,230), r, border_radius=8)
        pygame.draw.rect(WIN, (40,40,40), r, 2, border_radius=8)
        t = SMALL.render(label, True, (10,10,10))
        WIN.blit(t, (r.x + (r.w - t.get_width())//2, r.y + (r.h - t.get_height())//2))

    pygame.display.update()

    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.MOUSEBUTTONDOWN:
                if btn_restart.collidepoint(ev.pos):
                    return "restart"
                if btn_menu.collidepoint(ev.pos):
                    return "menu"

# ------ MAIN MENU -------
def main_menu():
    
    while True:
        WIN.fill(current_theme["BG"])
        title = FONT.render("Checkers", True, (20,20,20))
        WIN.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, 250))

        b1 = pygame.Rect(WINDOW_WIDTH//2 - 150, 350, 300, 54)
        b2 = pygame.Rect(WINDOW_WIDTH//2 - 150, 420, 300, 54)

        for rect, txt in [(b1, "Human vs Human"), (b2, "Human vs AI")]:
            pygame.draw.rect(WIN, (220,220,220), rect, border_radius=8)
            pygame.draw.rect(WIN, (40,40,40), rect, 2, border_radius=8)
            label = SMALL.render(txt, True, (10,10,10))
            WIN.blit(label, (rect.x + (rect.width - label.get_width())//2,
                             rect.y + (rect.height - label.get_height())//2))

        pygame.display.update()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                sys.exit()
            if e.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                if b1.collidepoint(mx, my):
                    main(False)
                if b2.collidepoint(mx, my):
                    lvl = ai_select()
                    main(True, lvl)

def ai_select():
    """Difficulty chooser: Easy / Medium / Hard."""
    while True:
        WIN.fill(current_theme["BG"])
        title = FONT.render("Select AI Difficulty", True, (20,20,20))
        WIN.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, 250))

        btns = [pygame.Rect(WINDOW_WIDTH//2 - 150, y, 300, 54)
                for y in (350, 420, 490)]
        tags = ["Easy", "Medium", "Hard"]

        for r, t in zip(btns, tags):
            pygame.draw.rect(WIN, (220,220,220), r, border_radius=8)
            pygame.draw.rect(WIN, (40,40,40), r, 2, border_radius=8)
            lb = SMALL.render(t, True, (10,10,10))
            WIN.blit(lb, (r.x + (r.width - lb.get_width())//2,
                          r.y + (r.height - lb.get_height())//2))

        pygame.display.update()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                sys.exit()
            if e.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                for i, r in enumerate(btns):
                    if r.collidepoint(mx, my):
                        return i + 1

# ------ MAIN GAME LOOP -------
def main(ai_mode=False, ai_level=1):
    board = Board()
    turn = RED
    selected = None
    valid_moves = {}

    while True:
        buttons = draw_screen(WIN, board, valid_moves, turn, ai_mode)

        # Immediate win by capture count
        if board.winner():
            choice = draw_winner_overlay(f"{board.winner()} wins!")
            if choice == "restart":
                return main(ai_mode, ai_level)
            else:
                return

        # Stalemate / no moves for current player
        if not player_has_any_moves(board, turn):
            winner = "Black" if turn == RED else "Red"
            choice = draw_winner_overlay(f"{winner} wins!")
            if choice == "restart":
                return main(ai_mode, ai_level)
            else:
                return

        # AI turn
        if ai_mode and turn == BLACK_PIECE:
            moves = get_all_moves(board, BLACK_PIECE)
            if not moves:
                # Red wins by immobility
                choice = draw_winner_overlay("Red wins!")
                if choice == "restart":
                    return main(ai_mode, ai_level)
                else:
                    return
            if ai_level == 1:
                board = random.choice(moves)
            else:
                depth = 2 if ai_level == 2 else 4
                _, board = minimax(board, depth, True, BLACK_PIECE)
            turn = RED
            selected = None
            valid_moves = {}
            continue

        # Human input
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                sys.exit()
            if e.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()

                # Sidebar buttons
                for name, r in buttons.items():
                    if r.collidepoint(mx, my):
                        if name == "Quit":
                            sys.exit()
                        if name == "Restart":
                            return main(ai_mode, ai_level)
                        if name == "Change AI":
                            ai_level = ai_select()
                            return main(True, ai_level)
                        if name == "Theme: Classic":
                            set_theme("Classic")
                        if name == "Theme: Wood":
                            set_theme("Wood")
                        if name == "Theme: Neon":
                            set_theme("Neon")

                # Board clicks
                if mx < BOARD_WIDTH:
                    row = my // SQUARE_SIZE
                    col = mx // SQUARE_SIZE
                    if selected:
                        # Try to move
                        if (row, col) in valid_moves:
                            board.move(selected, row, col)
                            skipped = valid_moves[(row, col)]
                            if skipped:
                                board.remove(skipped)
                            selected = None
                            valid_moves = {}
                            turn = BLACK_PIECE if turn == RED else RED
                        else:
                            # Deselect if clicked illegal target
                            selected = None
                            valid_moves = {}
                    else:
                        p = board.get_piece(row, col)
                        if p != 0 and p.color == turn:
                            selected = p
                            valid_moves = board.get_valid_moves(p)
                            
                            valid_moves['_selected'] = selected

if __name__ == "__main__":
    main_menu()
