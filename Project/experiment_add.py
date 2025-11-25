import sys
import copy
from dataclasses import dataclass, field
from typing import Tuple, List, Optional
import pygame

pygame.init()
FONT = pygame.font.SysFont("arial", 18)



# Layout
WINDOW_W, WINDOW_H = pygame.display.Info().current_w - 200, pygame.display.Info().current_h - 200

print(f"Window size: {WINDOW_W + 200}x{WINDOW_H + 200}")

CANVAS_FRACTION: float = 0.7
CANVAS_W: int = int(WINDOW_W * CANVAS_FRACTION)
SANDBOX_W = WINDOW_W - CANVAS_W
FPS = 60

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

class Section:
    xpos: int
    ypos: int
    width: int
    height: int

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
    commands: List["Command"]

    def __init__(self, x: int, y: int, w: int, h: int):
        super().__init__(x, y, w, h)
        self.templates = []

    def get_xy(self) -> Tuple[int, int]:
        return super().get_xy()

    def get_rect(self) -> pygame.Rect:
        return super().get_rect()
    
    def append_command(self, cmd: "Command") -> None:
        self.commands.append(cmd)

    def remove_command(self, cmd: "Command") -> None:
        if cmd in self.commands:
            self.commands.remove(cmd)

class Sandbox(Section):
    templates: List["Command"]

    def __init__(self, x: int, y: int, w: int, h: int):
        super().__init__(x, y, w, h)
        self.templates = []

    def get_xy(self) -> Tuple[int, int]:
        return super().get_xy()
    
    def get_rect(self) -> pygame.Rect:
        return super().get_rect()
    
    def append_template(self, cmd: "Command") -> None:
        self.templates.append(cmd)

    def get_templates(self) -> List["Command"]:
        return self.templates

class Command:
    """
    Parent model type (internal only). Not shown directly in the sandbox.
    """
    color: pygame.Color
    label: str
    x: float
    y: float
    w: int
    h: int

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
    color: pygame.Color = field(default_factory=lambda: pygame.Color("#4CAF50"))
    label: str = "Echo"

    # Echo specific behavior or data could be added here


class Cat(Command):
    color: pygame.Color = field(default_factory=lambda: pygame.Color("#FF9800"))
    label: str = "Cat"

    # Cat specific behavior or data could be added here

canvas_blocks: List[Command] = []
dragging: Optional[Command] = None

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

def discard_if_in_sandbox(dragging: Optional["Command"], drag_origin: Optional[str], mx: int, my: int) -> Optional["Command"]:
    """
    If dragging is a clone from a template and the mouse is outside the canvas when released,
    discard the duplicate by returning None. Otherwise return the original dragging object.
    """
    if dragging is None:
        return None
    if drag_origin == "template" and not is_point_in_canvas(mx, my):
        if dragging in canvas_blocks:
            canvas_blocks.remove(dragging) 
        return None
    return dragging

def draw_section(section: Section, surf: pygame.Surface, alpha: Optional[int] = None) -> None:
    color = pygame.Color("gray")
    rect = section.get_rect()
    if (section.__class__ == Sandbox): 
        color = SANDBOX_BG
    elif (section.__class__ == Canvas):
        color = CANVAS_BG
    if alpha is not None:
        s = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        c = (*color[:3], alpha)
        s.fill(c)
        surf.blit(s, rect.topleft)
    else:
        pygame.draw.rect(surf, color, rect, border_radius=8)
    pygame.draw.rect(surf, BORDER, rect, width=2, border_radius=8)

def draw_command(command: Command, surf: pygame.Surface, alpha: Optional[int] = None) -> None:
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

def main():
    # Sandbox templates (kept on the right)
    templates: List[Command] = []
    templates_x = CANVAS_W + 20
    templates_y = 50
    button_default_w: int = int(SANDBOX_W * 0.8)
    button_default_h: int = int(WINDOW_H * 0.1)
    button_default_x: int = CANVAS_W + (SANDBOX_W - button_default_w) // 2
    button_default_y: int = int(WINDOW_H * 0.2)

    canvas = Canvas(x=0, y=0,w=CANVAS_W, h=WINDOW_H)

    canvas_xy = canvas.get_xy()

    echo_template = Echo(x=templates_x, y=50, w=100, h=50)
    cat_template = Cat(x=templates_x, y=50, w=100, h=50)

    sandbox = Sandbox(x=CANVAS_W, y=0, w=SANDBOX_W, h=WINDOW_H)
    sandbox.append_template(echo_template)
    sandbox.append_template(cat_template)    

    drag_offset: Tuple[float, float] = (0.0, 0.0)
    drag_origin: Optional[str] = None  # "template" or "canvas"
    dragging: Optional[Command] = None

    running = True
    while running:
        mx, my = pygame.mouse.get_pos()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                # Check templates first (right pane)
                clicked_template = None
                for t in templates:
                    if t.get_rect().collidepoint(ev.pos):
                        clicked_template = t
                        break
                if clicked_template:
                    # Create duplicate which will follow the mouse until dropped
                    dragging = clicked_template.clone()
                    drag_origin = "template"
                    # place where mouse is over the block
                    dragging.x = mx - dragging.w // 2
                    dragging.y = my - dragging.h // 2
                    drag_offset = (mx - dragging.x, my - dragging.y)
                else:
                    # Check canvas blocks (allow moving)
                    if is_point_in_canvas(mx, my):
                        hit = None
                        for b in reversed(canvas_blocks):
                            if b.get_rect().collidepoint(ev.pos):
                                hit = b
                                break
                        if hit:
                            dragging = hit
                            drag_origin = "canvas"
                            original_pos = (hit.x, hit.y)
                            drag_offset = (mx - hit.x, my - hit.y)
                            # remove from list while dragging (will re-add on drop)
                            canvas_blocks.remove(hit)

            elif ev.type == pygame.MOUSEMOTION:
                if dragging is not None:
                    dragging.x = mx - drag_offset[0]
                    dragging.y = my - drag_offset[1]
            elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                dragging = discard_if_in_sandbox(dragging, drag_origin, mx, my)
                if dragging is not None:
                    # If it was a new clone from template -> only keep if dropped in canvas
                    if is_point_in_canvas(mx, my):
                        # clamp so it fits in canvas
                        rect = clamp_to_canvas(dragging.get_rect())
                        dragging.x, dragging.y = rect.x, rect.y
                        canvas_blocks.append(dragging)
                    # else: discard (do nothing)
                    else:
                        if dragging in canvas_blocks:
                            canvas_blocks.remove(dragging)
                        dragging = None
                dragging = None
                drag_origin = None

        # Draw background
        screen.fill(BG)

        # Draw canvas area
        canvas_rect = pygame.Rect(0, 0, CANVAS_W, WINDOW_H)
        pygame.draw.rect(screen, CANVAS_BG, canvas_rect)
        pygame.draw.rect(screen, BORDER, canvas_rect, width=3)

        # Draw sandbox area
        sandbox_rect = pygame.Rect(CANVAS_W, 0, SANDBOX_W, WINDOW_H)
        pygame.draw.rect(screen, SANDBOX_BG, sandbox_rect)
        pygame.draw.rect(screen, BORDER, sandbox_rect, width=3)

        # Labels
        lbl_canvas = FONT.render("Canvas", True, pygame.Color("black"))
        screen.blit(lbl_canvas, (10, 10))
        lbl_sandbox = FONT.render("Sandbox", True, pygame.Color("black"))
        screen.blit(lbl_sandbox, (CANVAS_W + 20, 10))

        # Draw templates
        for t in sandbox.get_templates():
            draw_command(t, screen)
            
        # Draw blocks already on canvas
        for b in canvas_blocks:
            draw_command(b, screen)

        # Draw dragging object on top (semi-transparent)
        if dragging is not None:
            # If dragging from template, render with alpha so user knows it's a new clone
            alpha = DRAG_ALPHA if drag_origin == "template" else None
            draw_command(dragging, screen, alpha=alpha) if hasattr(dragging, "draw") else None

        # Simple instruction
        instruct = FONT.render("Drag a block from the Sandbox into the Canvas. If dropped outside, it'll disappear.", True, pygame.Color("black"))
        screen.blit(instruct, (CANVAS_W + 10, WINDOW_H - 30))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()