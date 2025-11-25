from enum import Enum
import sys
import copy
from dataclasses import dataclass, field
from typing import Tuple, List, Optional
import pygame

pygame.init()
FONT = pygame.font.SysFont("arial",pygame.display.Info().current_w // 50)

# Layout - using fractions for proper scaling
WINDOW_W, WINDOW_H = pygame.display.Info().current_w - 200, pygame.display.Info().current_h - 200
print(f"Window size: {WINDOW_W}x{WINDOW_H}")

CANVAS_FRACTION = 0.7
CANVAS_W = int(WINDOW_W * CANVAS_FRACTION)
SANDBOX_W = WINDOW_W - CANVAS_W
FPS = 60

# Template positioning constants (as fractions of sandbox)
TEMPLATE_X_MARGIN = 0.1  # 10% margin from left edge of sandbox
TEMPLATE_Y_START = 0.1   # Start 10% down from top
TEMPLATE_SPACING = 0.15  # 15% of window height between templates
TEMPLATE_WIDTH_FRACTION = 0.7  # Template width as fraction of sandbox width
TEMPLATE_HEIGHT_FRACTION = 0.08  # Template height as fraction of window height

# Derived template dimensions
TEMPLATE_W = int(SANDBOX_W * TEMPLATE_WIDTH_FRACTION)
TEMPLATE_H = int(WINDOW_H * TEMPLATE_HEIGHT_FRACTION)
TEMPLATE_X = CANVAS_W + int(SANDBOX_W * TEMPLATE_X_MARGIN)
TEMPLATE_Y_SPACING = int(WINDOW_H * TEMPLATE_SPACING)

# Colors
BG = pygame.Color("#F0F0F0")
CANVAS_BG = pygame.Color("white")
BORDER = pygame.Color("#333333")
SANDBOX_BG = pygame.Color("#EDEDED")
ECHO_COLOR = pygame.Color("#4CAF50")
CAT_COLOR = pygame.Color("#FF9800")
TEMPLATE_BORDER = pygame.Color("#666666")
DRAG_ALPHA = 200

screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
clock = pygame.time.Clock()

class Origin(Enum):
    TEMPLATE = 1
    CANVAS = 2

class Section:
    def __init__(self, x: int, y: int, w: int, h: int):
        self.xpos = x
        self.ypos = y
        self.width = w
        self.height = h

    def get_xy(self) -> Tuple[int, int]:
        return (self.xpos, self.ypos)
    
    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(self.xpos, self.ypos, self.width, self.height)


class Canvas(Section):
    def __init__(self, x: int, y: int, w: int, h: int):
        super().__init__(x, y, w, h)
        self.commands = []

    def append_command(self, cmd: "Command") -> None:
        self.commands.append(cmd)

    def remove_command(self, cmd: "Command") -> None:
        if cmd in self.commands:
            self.commands.remove(cmd)

    def get_commands(self) -> List["Command"]:
        return self.commands


class Sandbox(Section):
    def __init__(self, x: int, y: int, w: int, h: int):
        super().__init__(x, y, w, h)
        self.templates = []

    def append_template(self, cmd: "Command") -> None:
        self.templates.append(cmd)

    def get_templates(self) -> List["Command"]:
        return self.templates


class Command:
    """Parent command type."""
    def __init__(self, x: float, y: float, w: int, h: int):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.color = pygame.Color("gray")
        self.label = "Command"

    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def clone(self) -> "Command":
        return copy.deepcopy(self)


class Echo(Command):
    def __init__(self, x: float, y: float, w: int, h: int):
        super().__init__(x, y, w, h)
        self.color = pygame.Color("#4CAF50")
        self.label = "Echo"


class Cat(Command):
    def __init__(self, x: float, y: float, w: int, h: int):
        super().__init__(x, y, w, h)
        self.color = pygame.Color("#FF9800")
        self.label = "Cat"


def is_point_in_canvas(px: int, py: int) -> bool:
    return 0 <= px < CANVAS_W and 0 <= py < WINDOW_H


def clamp_to_canvas(rect: pygame.Rect) -> pygame.Rect:
    r = rect.copy()
    if r.left < 0:
        r.left = 0
    if r.top < 0:
        r.top = 0
    if r.right > CANVAS_W:
        r.right = CANVAS_W
    if r.bottom > WINDOW_H:
        r.bottom = WINDOW_H
    return r



def discard_if_in_sandbox(dragging: Optional[Command], drag_origin: Origin, 
                         mx: int, my: int, canvas_blocks: List[Command]) -> Optional[Command]:
    """
    If dragging is a clone from a template and the mouse is outside the canvas when released,
    discard the duplicate by returning None. Otherwise return the original dragging object.
    """
    if dragging is None:
        return None
    if drag_origin == Origin.TEMPLATE and not is_point_in_canvas(mx, my):
        if dragging in canvas_blocks:
            canvas_blocks.remove(dragging)
        return None
    return dragging


def draw_command(command: Command, surf: pygame.Surface, alpha: Optional[int] = None) -> None:
    """Draw a command block with optional transparency."""
    rect = command.get_rect()
    color = command.color
    
    if alpha is not None:
        s = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        c = (*color[:3], alpha)
        s.fill(c)
        surf.blit(s, rect.topleft)
    else:
        pygame.draw.rect(surf, color, rect, border_radius=8)
    
    pygame.draw.rect(surf, BORDER, rect, width=2, border_radius=8)
    
    text = FONT.render(command.label, True, pygame.Color("black"))
    txt_r = text.get_rect(center=rect.center)
    surf.blit(text, txt_r)


def draw_scene(canvas: Canvas, sandbox: Sandbox, canvas_blocks: List[Command], 
               dragging: Optional[Command], drag_origin: Origin) -> None:
    """Draw the entire scene including canvas, sandbox, and all commands."""
    # Draw background
    screen.fill(BG)

    # Draw canvas area
    canvas_rect = canvas.get_rect()
    pygame.draw.rect(screen, CANVAS_BG, canvas_rect)
    pygame.draw.rect(screen, BORDER, canvas_rect, width=3)

    # Draw sandbox area
    sandbox_rect = sandbox.get_rect()
    pygame.draw.rect(screen, SANDBOX_BG, sandbox_rect)
    pygame.draw.rect(screen, BORDER, sandbox_rect, width=3)

    # Labels
    lbl_canvas = FONT.render("Canvas", True, pygame.Color("black"))
    screen.blit(lbl_canvas, (10, 10))
    lbl_sandbox = FONT.render("Sandbox", True, pygame.Color("black"))
    screen.blit(lbl_sandbox, (CANVAS_W + 20, 10))

    # Draw template blocks in sandbox
    for t in sandbox.get_templates():
        draw_command(t, screen)

    # Draw blocks on canvas
    for b in canvas_blocks:
        draw_command(b, screen)

    # Draw dragging object on top (semi-transparent if from template)
    if dragging is not None:
        alpha = DRAG_ALPHA if drag_origin == Origin.TEMPLATE else None
        draw_command(dragging, screen, alpha=alpha)

    # Instructions
    instruct = FONT.render("Drag a block from the Sandbox into the Canvas. If dropped outside, it'll disappear.", 
                          True, pygame.Color("black"))
    screen.blit(instruct, (CANVAS_W + 10, WINDOW_H - 30))


def main():
    # Initialize canvas and sandbox
    canvas = Canvas(x=0, y=0, w=CANVAS_W, h=WINDOW_H)
    sandbox = Sandbox(x=CANVAS_W, y=0, w=SANDBOX_W, h=WINDOW_H)

    # Create template blocks with automatic spacing
    template_y = int(WINDOW_H * TEMPLATE_Y_START)
    
    echo_template = Echo(x=TEMPLATE_X, y=template_y, w=TEMPLATE_W, h=TEMPLATE_H)
    sandbox.append_template(echo_template)
    
    template_y += TEMPLATE_Y_SPACING
    cat_template = Cat(x=TEMPLATE_X, y=template_y, w=TEMPLATE_W, h=TEMPLATE_H)
    sandbox.append_template(cat_template)

    # State variables
    canvas_blocks: List[Command] = []
    dragging: Optional[Command] = None
    drag_offset: Tuple[float, float] = (0.0, 0.0)
    drag_origin: Origin = Origin.TEMPLATE
    original_pos: Tuple[float, float] = (0.0, 0.0)

    running = True
    while running:
        mx, my = pygame.mouse.get_pos()
        
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
                
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                # Check templates first (right pane)
                clicked_template = None
                for t in sandbox.get_templates():
                    if t.get_rect().collidepoint(ev.pos):
                        clicked_template = t
                        break
                        
                if clicked_template:
                    # Create duplicate which will follow the mouse until dropped
                    dragging = clicked_template.clone()
                    drag_origin = Origin.TEMPLATE
                    # Center the block under the mouse
                    dragging.x = mx - dragging.w // 2
                    dragging.y = my - dragging.h // 2
                    drag_offset = (mx - dragging.x, my - dragging.y)
                else:
                    # Check canvas blocks (allow moving existing blocks)
                    if is_point_in_canvas(mx, my):
                        hit = None
                        for b in reversed(canvas_blocks):
                            if b.get_rect().collidepoint(ev.pos):
                                hit = b
                                break
                        if hit:
                            dragging = hit
                            drag_origin = Origin.CANVAS
                            original_pos = (hit.x, hit.y)
                            drag_offset = (mx - hit.x, my - hit.y)
                            # Remove from list while dragging (will re-add on drop)
                            canvas_blocks.remove(hit)

            elif ev.type == pygame.MOUSEMOTION:
                if dragging is not None:
                    dragging.x = mx - drag_offset[0]
                    dragging.y = my - drag_offset[1]
                    
            elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                if dragging is not None:
                    # Check if block should be discarded
                    dragging = discard_if_in_sandbox(dragging, drag_origin, mx, my, canvas_blocks)
                    
                    if dragging is not None:
                        if drag_origin == Origin.TEMPLATE:
                            # New clone from template
                            if is_point_in_canvas(mx, my):
                                rect = clamp_to_canvas(dragging.get_rect())
                                dragging.x, dragging.y = rect.x, rect.y
                                canvas_blocks.append(dragging)
                        elif drag_origin == Origin.CANVAS:
                            # Existing block being moved
                            if is_point_in_canvas(mx, my):
                                rect = clamp_to_canvas(dragging.get_rect())
                                dragging.x, dragging.y = rect.x, rect.y
                                canvas_blocks.append(dragging)
                            else:
                                # Restore to original position
                                dragging.x, dragging.y = original_pos
                                canvas_blocks.append(dragging)
                    
                    dragging = None
                    drag_origin = Origin.TEMPLATE

        # Draw everything
        draw_scene(canvas, sandbox, canvas_blocks, dragging, drag_origin)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()