from __future__ import annotations

from typing import Optional, Iterable, Any, TYPE_CHECKING

import tcod.event

from actions import (
    Action, 
    EscapeAction, 
    BumpAction, 
    WaitAction,
)
import color
import exceptions

if TYPE_CHECKING:
    from engine import Engine

MOVE_KEYS = {
    # Arrow keys.
    tcod.event.K_UP: (0, -1),
    tcod.event.K_DOWN: (0, 1),
    tcod.event.K_LEFT: (-1, 0),
    tcod.event.K_RIGHT: (1, 0),
    tcod.event.K_HOME: (-1, -1),
    tcod.event.K_END: (-1, 1),
    tcod.event.K_PAGEUP: (1, -1),
    tcod.event.K_PAGEDOWN: (1, 1),

    # Numpad keys.
    tcod.event.K_KP_1: (-1, 1), 
    tcod.event.K_KP_2: (0, 1), 
    tcod.event.K_KP_3: (1, 1), 
    tcod.event.K_KP_4: (-1, 0), 
    tcod.event.K_KP_6: (1, 0), 
    tcod.event.K_KP_7: (-1, -1), 
    tcod.event.K_KP_8: (0, -1), 
    tcod.event.K_KP_9: (1, -1), 
}

WAIT_KEYS = {
    tcod.event.K_PERIOD,
    tcod.event.K_KP_5,
    tcod.event.K_CLEAR,
}

class EventHandler(tcod.event.EventDispatch[Action]):
    def __init__(self, engine: Engine):
        self.engine = engine

    def handle_events(self, event: tcod.event.Event) -> None:
        self.handle_action(self.dispatch(event))

    def handle_action(self, action: Optional[Action]) -> bool:
        """
        Handle actions returned from event methods

        Returns True if the action will advance a turn
        """
        if action is None:
            return False

        try:
            action.perform()
        except exceptions.Impossible as exc:
            self.engine.message_log.add_message(exc.args[0], color.impossible)
            return False

        self.engine.handle_enemy_turns()

        self.engine.update_fov() # Update FOV before the player's next action
        return True

    def ev_mousemotion(self, event: tcod.event.MouseMotion) -> None:
        if self.engine.game_map.in_bounds(event.tile.x, event.tile.y):
            self.engine.mouse_location = event.tile.x, event.tile.y

    def ev_quit(self, event: tcod.event.Quit) -> Optional[Action]:
        raise SystemExit()
    
    def on_render(self, console: tcod.Console) -> None:
        self.engine.render(console)

class MainGameEventHandler(EventHandler):
    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[Action]:
        action: Optional[Action] = None

        key = event.sym 

        player = self.engine.player
        if key in MOVE_KEYS:
            dx, dy = MOVE_KEYS[key]
            action = BumpAction(player, dx, dy)

        elif key in WAIT_KEYS:
            action = WaitAction(player)

        elif key == tcod.event.K_v:
            self.engine.event_handler = HistoryViewer(self.engine)

        elif key == tcod.event.K_ESCAPE:
            action = EscapeAction(player)

        # No valid key was pressed
        return action

class GameOverEventHandler(EventHandler):

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[Action]:
        if event.sym == tcod.event.K_ESCAPE:
            raise SystemExit()

CURSOR_Y_KEYS = {
    tcod.event.K_UP: -1,
    tcod.event.K_DOWN: 1,
    tcod.event.K_PAGEUP: -10,
    tcod.event.K_PAGEDOWN: 10,
}

class HistoryViewer(EventHandler):
    """
    Print the history on a larger window which can be navigated.
    """

    def __init__(self, engine: Engine):
        super().__init__(engine)
        self.log_length = len(engine.message_log.messages)
        self.cursor = self.log_length - 1

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console) # Draw the main state as the background

        log_console = tcod.Console(console.width -6, console.height - 6)

        # Draw a frame with a custom banner title.
        log_console.draw_frame(0, 0, log_console.width, log_console.height)

        # Render the message log using the cursor parameter
        self.engine.message_log.render_messages(
            log_console,
            1,
            1,
            log_console.width - 2,
            log_console.height - 2,
            self.engine.message_log.messages[:self.cursor + 1],
        )

        log_console.blit(console, 3, 3)

    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
        # Fancy conditional movement to make it feel right.
        if event.sym in CURSOR_Y_KEYS:
            adjust = CURSOR_Y_KEYS[event.sym]

            # Only move from the top to the bottom when you're on
            # the edge.
            if adjust < 0 and self.cursor == 0:
                self.cursor = self.log_length
            
            # Same with bottom to top movement
            elif adjust > 0 and self.cursor == self.log_length - 1:
                self.cursor = 0

            # Otherwise move while staying clamped to the bounds of the history log
            else:
                self.cursor = max(0, min(self.cursor + adjust, self.log_length - 1))
        # Home takes us to the top
        elif event.sym == tcod.event.K_HOME:
            self.cursor = 0

        # End takes us to the bottom
        elif event.sym == tcod.event.K_END:
            self.cursor = self.log_length - 1
        
        # Anything else takes us back to the regular game
        else:
            self.engine.event_handler = MainGameEventHandler(self.engine)
