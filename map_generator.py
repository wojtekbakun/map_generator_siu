import pygame
import sys
import math

# --- CONFIGURATION ---
WIDTH, HEIGHT = 1920, 1080
MENU_WIDTH = 250
TILE_SIZE = 66
SCALE = 0.5 

API_COLORS = {
    "Grass":  (200, 255, 200),
    "Up":     (200, 255, 250),
    "Down":   (200, 255, 150),
    "Right":  (250, 255, 200),
    "Left":   (150, 255, 200),
    "Corner": (200, 0, 200)
}

class Editor:
    def __init__(self):
        pygame.init()
        self.win_width = int(WIDTH * SCALE) + MENU_WIDTH
        self.win_height = int(HEIGHT * SCALE)
        self.screen = pygame.display.set_mode((self.win_width, self.win_height), pygame.RESIZABLE)
        self.canvas_api = pygame.Surface((WIDTH, HEIGHT))
        self.canvas_api.fill(API_COLORS["Grass"])
        
        self.font = pygame.font.SysFont("Arial", 14)
        self.big_font = pygame.font.SysFont("Arial", 42, bold=True)
        self.tool = "brush" 
        self.track_dir = "Right"
        self.brush_tiles = set()
        self.arcs = []
        self.arc_pts = []
        self.filename_map = "map_api"
        self.filename_scenario = "scenario"
        self.typing_filename = False
        self.last_painted_tile = None

        self.mode = "MAP"
        self.scenario_stages = []
        self.scenario_state = "IDLE"
        self.drag_start = None
        self.current_rect = None

    def draw_arc_logic(self, surf, pts, mode, color_c1, color_c2=None, color_cmid=None, alpha=255):
        if len(pts) < 2: return
        p1, p2 = pts
        
        diameter = abs(p1[1] - p2[1]) if mode in ["arc_left", "arc_right"] else abs(p1[0] - p2[0])
        if diameter == 0: return
        
        radius = diameter / 2
        
        if mode in ["arc_left", "arc_right"]:
            cx = p1[0]
            cy = min(p1[1], p2[1]) + radius
            if mode == "arc_left":
                start_a, end_a = math.pi/2, 3*math.pi/2
            else:
                start_a, end_a = -math.pi/2, math.pi/2
        else:
            cy = p1[1]
            cx = min(p1[0], p2[0]) + radius
            if mode == "arc_top":
                start_a, end_a = 0, math.pi
            else:
                start_a, end_a = math.pi, 2*math.pi

        steps = max(10, int(abs(end_a - start_a) * radius))
        if color_c2 is None: color_c2 = color_c1
        if color_cmid is None: color_cmid = color_c1
            
        start_x = int(cx + radius * math.cos(start_a))
        start_y = int(cy - radius * math.sin(start_a))
        end_x = int(cx + radius * math.cos(end_a))
        end_y = int(cy - radius * math.sin(end_a))
        
        if mode == "arc_left":
            rect1 = (start_x, start_y - TILE_SIZE//2, TILE_SIZE//2, TILE_SIZE)
            rect2 = (end_x, end_y - TILE_SIZE//2, TILE_SIZE//2, TILE_SIZE)
        elif mode == "arc_right":
            rect1 = (start_x - TILE_SIZE//2, start_y - TILE_SIZE//2, TILE_SIZE//2, TILE_SIZE)
            rect2 = (end_x - TILE_SIZE//2, end_y - TILE_SIZE//2, TILE_SIZE//2, TILE_SIZE)
        elif mode == "arc_top":
            rect1 = (start_x - TILE_SIZE//2, start_y, TILE_SIZE, TILE_SIZE//2)
            rect2 = (end_x - TILE_SIZE//2, end_y, TILE_SIZE, TILE_SIZE//2)
        else: # arc_bottom
            rect1 = (start_x - TILE_SIZE//2, start_y - TILE_SIZE//2, TILE_SIZE, TILE_SIZE//2)
            rect2 = (end_x - TILE_SIZE//2, end_y - TILE_SIZE//2, TILE_SIZE, TILE_SIZE//2)

        if alpha < 255:
            temp = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            pygame.draw.rect(temp, (*color_c1[:3], 255), rect1)
            pygame.draw.rect(temp, (*color_c2[:3], 255), rect2)
            for i in range(steps + 1):
                t = i / steps
                a = start_a + (end_a - start_a) * t
                x = cx + radius * math.cos(a)
                y = cy - radius * math.sin(a)
                pygame.draw.circle(temp, (*color_c1[:3], 255), (int(x), int(y)), TILE_SIZE // 2)
            temp.set_alpha(alpha)
            surf.blit(temp, (0, 0))
        else:
            pygame.draw.rect(surf, color_c1, rect1)
            pygame.draw.rect(surf, color_c2, rect2)
            for i in range(steps + 1):
                t = i / steps
                a = start_a + (end_a - start_a) * t
                x = cx + radius * math.cos(a)
                y = cy - radius * math.sin(a)
                if t <= 0.5:
                    tr = t * 2
                    r = color_c1[0]*(1-tr) + color_cmid[0]*tr
                    g = color_c1[1]*(1-tr) + color_cmid[1]*tr
                    b = color_c1[2]*(1-tr) + color_cmid[2]*tr
                else:
                    tr = (t - 0.5) * 2
                    r = color_cmid[0]*(1-tr) + color_c2[0]*tr
                    g = color_cmid[1]*(1-tr) + color_c2[1]*tr
                    b = color_cmid[2]*(1-tr) + color_c2[2]*tr
                pygame.draw.circle(surf, (int(r), int(g), int(b)), (int(x), int(y)), TILE_SIZE // 2)

    def auto_color(self):
        self.canvas_api.fill(API_COLORS["Grass"])
        
        all_x = [t[0] for t in self.brush_tiles]
        all_y = [t[1] for t in self.brush_tiles]
        for (mode, pts) in self.arcs:
            all_x.extend([pts[0][0], pts[1][0]])
            all_y.extend([pts[0][1], pts[1][1]])
            
        mid_x = (min(all_x) + max(all_x)) // 2 if all_x else WIDTH // 2
        mid_y = (min(all_y) + max(all_y)) // 2 if all_y else HEIGHT // 2
        
        def is_road(x, y):
            if (x - 33, y - 33) in self.brush_tiles: return True
            for (mode, pts) in self.arcs:
                if pts[0] == (x, y) or pts[1] == (x, y): return True
            return False

        for (x, y) in self.brush_tiles:
            cx, cy = x + TILE_SIZE//2, y + TILE_SIZE//2
            N = is_road(cx, cy - TILE_SIZE)
            S = is_road(cx, cy + TILE_SIZE)
            W = is_road(cx - TILE_SIZE, cy)
            E = is_road(cx + TILE_SIZE, cy)
            
            is_vertical = (N or S) and not (W or E)
            is_horizontal = (W or E) and not (N or S)
            neighbors_count = N + S + W + E
            
            if self.track_dir == "Right":
                v_color = API_COLORS["Up"] if x < mid_x else API_COLORS["Down"]
                h_color = API_COLORS["Right"] if y < mid_y else API_COLORS["Left"]
            else:
                v_color = API_COLORS["Down"] if x < mid_x else API_COLORS["Up"]
                h_color = API_COLORS["Left"] if y < mid_y else API_COLORS["Right"]
            
            if is_vertical:
                pygame.draw.rect(self.canvas_api, v_color, (x, y, TILE_SIZE, TILE_SIZE))
            elif is_horizontal:
                pygame.draw.rect(self.canvas_api, h_color, (x, y, TILE_SIZE, TILE_SIZE))
            elif neighbors_count == 2 and not (N and S) and not (W and E):
                r1, g1, b1 = v_color[:3]
                r2, g2, b2 = h_color[:3]
                
                # Manual radial gradient interpolation to precisely match edge colors
                for dy in range(TILE_SIZE):
                    for dx in range(TILE_SIZE):
                        if N and W:
                            v_val, h_val = dy, dx
                        elif N and E:
                            v_val, h_val = dy, TILE_SIZE - 1 - dx
                        elif S and W:
                            v_val, h_val = TILE_SIZE - 1 - dy, dx
                        else:  # S and E
                            v_val, h_val = TILE_SIZE - 1 - dy, TILE_SIZE - 1 - dx
                            
                        if v_val == 0 and h_val == 0:
                            t = 0.5
                        else:
                            t = math.atan2(v_val, h_val) / (math.pi / 2)
                            
                        # Safe boundaries
                        t = max(0.0, min(1.0, t))
                        
                        r = int(r1*(1-t) + r2*t)
                        g = int(g1*(1-t) + g2*t)
                        b = int(b1*(1-t) + b2*t)
                        self.canvas_api.set_at((x + dx, y + dy), (r, g, b))
            else:
                pygame.draw.rect(self.canvas_api, API_COLORS["Corner"], (x, y, TILE_SIZE, TILE_SIZE))

        # Draw arcs as gradient shapes with a middle state
        for (mode, pts) in self.arcs:
            if self.track_dir == "Right":
                if mode == "arc_left": c1, c_mid, c2 = API_COLORS["Right"], API_COLORS["Up"], API_COLORS["Left"]
                elif mode == "arc_right": c1, c_mid, c2 = API_COLORS["Left"], API_COLORS["Down"], API_COLORS["Right"]
                elif mode == "arc_top": c1, c_mid, c2 = API_COLORS["Down"], API_COLORS["Right"], API_COLORS["Up"]
                else: c1, c_mid, c2 = API_COLORS["Up"], API_COLORS["Left"], API_COLORS["Down"]
            else:
                if mode == "arc_left": c1, c_mid, c2 = API_COLORS["Left"], API_COLORS["Down"], API_COLORS["Right"]
                elif mode == "arc_right": c1, c_mid, c2 = API_COLORS["Right"], API_COLORS["Up"], API_COLORS["Left"]
                elif mode == "arc_top": c1, c_mid, c2 = API_COLORS["Up"], API_COLORS["Left"], API_COLORS["Down"]
                else: c1, c_mid, c2 = API_COLORS["Down"], API_COLORS["Right"], API_COLORS["Up"]
                
            self.draw_arc_logic(self.canvas_api, pts, mode, c1, c2, c_mid)

        # Draw Direction arrow
        arrow_len = 40
        arr_col = (40, 40, 40)
        
        if self.track_dir == "Right":
            arr_cx = 12 + TILE_SIZE // 2
            arr_cy = 12 + TILE_SIZE // 2
            pygame.draw.line(self.canvas_api, arr_col, (arr_cx - arrow_len//2, arr_cy), (arr_cx + arrow_len//2, arr_cy), 5)
            pygame.draw.polygon(self.canvas_api, arr_col, [
                (arr_cx + arrow_len//2 + 5, arr_cy),
                (arr_cx + arrow_len//2 - 10, arr_cy - 10),
                (arr_cx + arrow_len//2 - 10, arr_cy + 10)
            ])
        else:
            # Bottom right tile completely visible
            max_x_idx = (WIDTH - 12 - TILE_SIZE) // TILE_SIZE
            max_y_idx = (HEIGHT - 12 - TILE_SIZE) // TILE_SIZE
            arr_cx = 12 + max_x_idx * TILE_SIZE + TILE_SIZE // 2
            arr_cy = 12 + max_y_idx * TILE_SIZE + TILE_SIZE // 2
            
            pygame.draw.line(self.canvas_api, arr_col, (arr_cx + arrow_len//2, arr_cy), (arr_cx - arrow_len//2, arr_cy), 5)
            pygame.draw.polygon(self.canvas_api, arr_col, [
                (arr_cx - arrow_len//2 - 5, arr_cy),
                (arr_cx - arrow_len//2 + 10, arr_cy - 10),
                (arr_cx - arrow_len//2 + 10, arr_cy + 10)
            ])

    def run(self):
        while True:
            mx, my = pygame.mouse.get_pos()
            
            map_w = self.win_width - MENU_WIDTH
            map_h = self.win_height
            current_scale = min(map_w / WIDTH, map_h / HEIGHT)
            drawn_w = int(WIDTH * current_scale)
            drawn_h = int(HEIGHT * current_scale)
            
            canvas_mx = mx / current_scale
            canvas_my = my / current_scale

            OFFSET_X = 12
            OFFSET_Y = 12

            on_map = (OFFSET_X <= canvas_mx < WIDTH - OFFSET_X) and (OFFSET_Y <= canvas_my < HEIGHT - OFFSET_Y)
            if on_map:
                gx = int((canvas_mx - OFFSET_X) // TILE_SIZE) * TILE_SIZE + OFFSET_X
                gy = int((canvas_my - OFFSET_Y) // TILE_SIZE) * TILE_SIZE + OFFSET_Y
                cx, cy = gx + TILE_SIZE // 2, gy + TILE_SIZE // 2
            else:
                gx, gy, cx, cy = -100, -100, -100, -100
                
            mouse_btns = pygame.mouse.get_pressed()
            if on_map and not self.typing_filename:
                if self.mode == "MAP":
                    if mouse_btns[0] and self.tool == "brush":
                        if (gx, gy) != self.last_painted_tile:
                            self.brush_tiles.add((gx, gy))
                            self.last_painted_tile = (gx, gy)
                            self.auto_color()
                    elif mouse_btns[2]:
                        if (gx, gy) != self.last_painted_tile:
                            self.last_painted_tile = (gx, gy)
                            changed = False
                            if (gx, gy) in self.brush_tiles:
                                self.brush_tiles.discard((gx, gy))
                                changed = True
                                
                            new_arcs = []
                            for arc in self.arcs:
                                _, pts = arc
                                if (pts[0][0] == cx and pts[0][1] == cy) or (pts[1][0] == cx and pts[1][1] == cy):
                                    changed = True
                                    continue
                                new_arcs.append(arc)
                            if changed:
                                self.arcs = new_arcs
                                self.auto_color()
                    elif not mouse_btns[0] and not mouse_btns[2]:
                        self.last_painted_tile = None

            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); sys.exit()
                elif event.type == pygame.VIDEORESIZE:
                    self.win_width = max(800, event.w)
                    self.win_height = max(600, event.h)
                    self.screen = pygame.display.set_mode((self.win_width, self.win_height), pygame.RESIZABLE)
                
                if event.type == pygame.KEYDOWN:
                    if self.typing_filename:
                        if event.key == pygame.K_RETURN:
                            self.typing_filename = False
                        elif event.key == pygame.K_BACKSPACE:
                            if self.mode == "MAP": self.filename_map = self.filename_map[:-1]
                            else: self.filename_scenario = self.filename_scenario[:-1]
                        else:
                            if self.mode == "MAP": self.filename_map += event.unicode
                            else: self.filename_scenario += event.unicode

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if on_map:
                        if self.mode == "MAP":
                            if event.button == 1 and self.tool != "brush" and not self.typing_filename:
                                self.arc_pts.append((cx, cy))
                                if len(self.arc_pts) == 2:
                                    self.arcs.append((self.tool, self.arc_pts.copy()))
                                    self.arc_pts = []
                                self.auto_color()
                        elif self.mode == "SCENARIO":
                            if event.button == 1 and not self.typing_filename:
                                if self.scenario_state == "IDLE":
                                    if len(self.scenario_stages) < 8:
                                        self.scenario_state = "DRAWING_START"
                                        self.drag_start = (gx, gy)
                                        self.current_rect = (gx, gy, TILE_SIZE, TILE_SIZE)
                                elif self.scenario_state == "WAITING_TARGET":
                                    stage = {"start": self.current_rect, "target": (canvas_mx, canvas_my)}
                                    self.scenario_stages.append(stage)
                                    self.scenario_state = "IDLE"
                                    self.current_rect = None
                                    self.drag_start = None
                    else:
                        self.handle_menu(mx, my)

                if event.type == pygame.MOUSEMOTION:
                    if self.mode == "SCENARIO" and self.scenario_state == "DRAWING_START":
                        end_x = int((canvas_mx - 12) // TILE_SIZE) * TILE_SIZE + 12
                        end_y = int((canvas_my - 12) // TILE_SIZE) * TILE_SIZE + 12
                        rx = min(self.drag_start[0], end_x)
                        ry = min(self.drag_start[1], end_y)
                        rw = max(self.drag_start[0], end_x) - rx + TILE_SIZE
                        rh = max(self.drag_start[1], end_y) - ry + TILE_SIZE
                        self.current_rect = (rx, ry, rw, rh)

                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1 and self.mode == "SCENARIO" and self.scenario_state == "DRAWING_START":
                        if self.current_rect and self.current_rect[2] > 5 and self.current_rect[3] > 5:
                            self.scenario_state = "WAITING_TARGET"
                        else:
                            self.scenario_state = "IDLE"
                            self.drag_start = None
                            self.current_rect = None

            self.render(gx, gy, on_map, canvas_mx, canvas_my, cx, cy, current_scale, drawn_w, drawn_h)

    def handle_menu(self, mx, my):
        x_off = self.win_width - MENU_WIDTH + 20
        
        if pygame.Rect(x_off, 20, 210, 35).collidepoint(mx, my):
            self.mode = "SCENARIO" if self.mode == "MAP" else "MAP"
            self.scenario_state = "IDLE"
            self.current_rect = None
            self.drag_start = None

        if self.mode == "MAP":
            if pygame.Rect(x_off, 60, 210, 35).collidepoint(mx, my): 
                self.track_dir = "Left" if self.track_dir == "Right" else "Right"
                self.auto_color()
                
            tools = ["brush", "arc_left", "arc_right", "arc_top", "arc_bottom"]
            for i, tool_id in enumerate(tools):
                if pygame.Rect(x_off, 125 + i * 30, 210, 25).collidepoint(mx, my):
                    self.tool = tool_id
                    self.arc_pts = []
                    
            if pygame.Rect(x_off, 290, 210, 35).collidepoint(mx, my):
                self.brush_tiles.clear()
                self.arcs.clear()
                self.arc_pts.clear()
                self.auto_color()
        else:
            if pygame.Rect(x_off, 130, 210, 35).collidepoint(mx, my):
                self.scenario_stages.clear()
                self.scenario_state = "IDLE"
                self.current_rect = None
                self.drag_start = None
            
        save_btn_y = max(470, self.win_height - 60)
        filename_y = save_btn_y - 45
        
        if pygame.Rect(x_off, filename_y, 210, 35).collidepoint(mx, my):
            self.typing_filename = True
        else:
            self.typing_filename = False
            
        if pygame.Rect(x_off, save_btn_y, 210, 40).collidepoint(mx, my):
            if self.mode == "MAP":
                pygame.image.save(self.canvas_api, f"{self.filename_map}.png")
                print(f"Saved {self.filename_map}.png")
            else:
                self.save_scenario_csv()

    def save_scenario_csv(self):
        try:
            with open(f"{self.filename_scenario}.csv", "w") as f:
                f.write("stage_id;sequence_id;start_x;start_y;start_width;start_height;target_x;target_y\n")
                for i, stage in enumerate(self.scenario_stages):
                    sx, sy, sw, sh = stage["start"]
                    tx, ty = stage["target"]
                    mx_val = sx / 22.0
                    my_val = (HEIGHT - sy) / 22.0
                    mw_val = sw / 22.0
                    mh_val = sh / 22.0
                    mtx_val = tx / 22.0
                    mty_val = (HEIGHT - ty) / 22.0
                    f.write(f"{i+1};1;{mx_val:.3f};{my_val:.3f};{mw_val:.3f};{mh_val:.3f};{mtx_val:.3f};{mty_val:.3f}\n")
            print(f"Saved {self.filename_scenario}.csv")
        except Exception as e:
            print(f"Failed to save CSV: {e}")

    def render(self, gx, gy, on_map, canvas_mx, canvas_my, cx, cy, current_scale, drawn_w, drawn_h):
        self.screen.fill((30, 30, 30))
        display_surface = self.canvas_api.copy()
        
        if self.mode == "MAP":
            if on_map:
                darken = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                darken.fill((0, 0, 0, 60))
                display_surface.blit(darken, (gx, gy))

                if self.tool != "brush":
                    pygame.draw.circle(display_surface, (255, 0, 0), (cx, cy), 8)
                    if len(self.arc_pts) == 1:
                        self.draw_arc_logic(display_surface, [self.arc_pts[0], (cx, cy)], self.tool, (0, 0, 0), alpha=100)
        elif self.mode == "SCENARIO":
            scene_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            for i, stage in enumerate(self.scenario_stages):
                rx, ry, rw, rh = stage["start"]
                tx, ty = stage["target"]
                pygame.draw.rect(scene_overlay, (0, 0, 255, 255), (rx, ry, rw, rh), 4)
                pygame.draw.circle(scene_overlay, (255, 0, 0, 200), (int(tx), int(ty)), 8)
                txt = self.big_font.render(str(i+1), True, (255, 255, 255))
                txt_rect = txt.get_rect(center=(int(rx + rw/2), int(ry + rh/2)))
                bg_rect = txt_rect.inflate(16, 8)
                pygame.draw.rect(scene_overlay, (0, 0, 255, 200), bg_rect, border_radius=4)
                scene_overlay.blit(txt, txt_rect)

            if self.current_rect:
                rx, ry, rw, rh = self.current_rect
                pygame.draw.rect(scene_overlay, (0, 255, 0, 255), (rx, ry, rw, rh), 4)
                
                if self.scenario_state == "WAITING_TARGET" and on_map:
                    pygame.draw.circle(scene_overlay, (255, 0, 0, 200), (int(canvas_mx), int(canvas_my)), 6)
            
            display_surface.blit(scene_overlay, (0, 0))

        view = pygame.transform.scale(display_surface, (drawn_w, drawn_h))
        
        OFFSET_X = 12
        OFFSET_Y = 12
        
        scaled_offset_x = int(OFFSET_X * current_scale)
        scaled_offset_y = int(OFFSET_Y * current_scale)
        scaled_tile = TILE_SIZE * current_scale
        
        py_start = scaled_offset_y
        py_end = int(scaled_offset_y + (HEIGHT // TILE_SIZE) * scaled_tile)
        for x_idx in range((WIDTH // TILE_SIZE) + 1):
            px = int(scaled_offset_x + x_idx * scaled_tile)
            pygame.draw.line(view, (60, 60, 60), (px, py_start), (px, py_end), 1)

        px_start = scaled_offset_x
        px_end = int(scaled_offset_x + (WIDTH // TILE_SIZE) * scaled_tile)
        for y_idx in range((HEIGHT // TILE_SIZE) + 1):
            py = int(scaled_offset_y + y_idx * scaled_tile)
            pygame.draw.line(view, (60, 60, 60), (px_start, py), (px_end, py), 1)
            
        self.screen.blit(view, (0, 0))
        
        # Menu background
        pygame.draw.rect(self.screen, (40, 40, 40), (self.win_width - MENU_WIDTH, 0, MENU_WIDTH, self.win_height))
        self.draw_ui()
        pygame.display.flip()

    def draw_ui(self):
        mx, my = pygame.mouse.get_pos()
        x = self.win_width - MENU_WIDTH + 20
        
        def btn(txt, rect, active, hover=False):
            bg_color = (0, 150, 0) if active else ((120, 120, 120) if hover else (80, 80, 80))
            pygame.draw.rect(self.screen, bg_color, rect)
            self.screen.blit(self.font.render(txt, True, (255, 255, 255)), (rect[0]+10, rect[1]+10))

        mode_rect = pygame.Rect(x, 20, 210, 35)
        btn(f"MODE: {self.mode}", mode_rect, True, mode_rect.collidepoint(mx, my))

        if self.mode == "MAP":
            dir_rect = pygame.Rect(x, 60, 210, 35)
            btn(f"DIRECTION: {self.track_dir}", dir_rect, True, dir_rect.collidepoint(mx, my))
            
            self.screen.blit(self.font.render("SELECT TILE:", True, (200, 200, 200)), (x, 100))
            
            tools = [
                ("Road", "brush"), ("Arc Left", "arc_left"), ("Arc Right", "arc_right"),
                ("Arc Top", "arc_top"), ("Arc Bottom", "arc_bottom")
            ]
            for i, (name, tool_id) in enumerate(tools):
                rect = pygame.Rect(x, 125 + i * 30, 210, 25)
                hover = rect.collidepoint(mx, my)
                active = self.tool == tool_id
                cb_color = (0, 255, 0) if active else ((200, 200, 200) if hover else (150, 150, 150))
                pygame.draw.rect(self.screen, cb_color, (x, 125 + i * 30 + 3, 16, 16), 0 if active else 2)
                txt_color = (255, 255, 255) if hover or active else (200, 200, 200)
                self.screen.blit(self.font.render(name, True, txt_color), (x + 25, 125 + i * 30 + 3))

            cb_rect = pygame.Rect(x, 290, 210, 35)
            btn("CLEAR BOARD", cb_rect, False, cb_rect.collidepoint(mx, my))
            
            ly = 340
            self.screen.blit(self.font.render("COLOR LEGEND:", True, (200, 200, 200)), (x, ly))
            legend_items = [
                ("Up", API_COLORS["Up"]), ("Down", API_COLORS["Down"]),
                ("Right", API_COLORS["Right"]), ("Left", API_COLORS["Left"]),
                ("Intersection", API_COLORS["Corner"])
            ]
            for i, (name, color) in enumerate(legend_items):
                pygame.draw.rect(self.screen, color, (x, ly + 25 + i*25, 20, 20))
                self.screen.blit(self.font.render(name, True, (255, 255, 255)), (x + 30, ly + 27 + i*25))

        elif self.mode == "SCENARIO":
            self.screen.blit(self.font.render(f"STAGES (Max 8): {len(self.scenario_stages)}/8", True, (200, 200, 200)), (x, 70))
            if self.scenario_state == "IDLE":
                status = "Drag to create area"
            elif self.scenario_state == "DRAWING_START":
                status = "Release to finish area"
            else:
                status = "Click to set target point"
            self.screen.blit(self.font.render(f"P: {status}", True, (255, 255, 50)), (x, 100))
            
            cb_rect = pygame.Rect(x, 130, 210, 35)
            btn("CLEAR SCENARIOS", cb_rect, False, cb_rect.collidepoint(mx, my))
            
            info_y = 180
            self.screen.blit(self.font.render("CSV Unit: Meters (scale=22)", True, (150, 150, 150)), (x, info_y))
            self.screen.blit(self.font.render("Y-Axis: Turtlesim (Inverted)", True, (150, 150, 150)), (x, info_y+20))

        save_btn_y = max(470, self.win_height - 60)
        filename_y = save_btn_y - 45
        
        # TEXT INPUT FILENAME
        hover_file = pygame.Rect(x, filename_y, 210, 35).collidepoint(mx, my)
        bg_col = (50, 50, 50) if hover_file else (30, 30, 30)
        if self.typing_filename: bg_col = (80, 80, 80)
        pygame.draw.rect(self.screen, bg_col, (x, filename_y, 210, 35))
        pygame.draw.rect(self.screen, (150, 150, 150), (x, filename_y, 210, 35), 1)
        current_name = self.filename_map if self.mode == "MAP" else self.filename_scenario
        name_surf = self.font.render(f"{current_name}" + ("|" if self.typing_filename else ""), True, (255, 255, 255))
        self.screen.blit(name_surf, (x + 10, filename_y + 10))

        save_rect = pygame.Rect(x, save_btn_y, 210, 40)
        btn("SAVE IMAGE" if self.mode == "MAP" else "SAVE SCENARIO", save_rect, False, save_rect.collidepoint(mx, my))

if __name__ == "__main__":
    Editor().run()