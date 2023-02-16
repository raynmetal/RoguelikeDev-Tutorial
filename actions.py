from __future__ import annotations 

from typing import TYPE_CHECKING, Optional, Tuple

if TYPE_CHECKING:
    from engine import Engine
    from entity import Entity

class Action:
    def __init__(self, entity: Entity) -> None:
        super().__init__()
        self.entity = entity
    
    @property
    def engine(self) -> Engine:
        """
        Return the engine this action belongs to.
        """
        return self.entity.gamemap.engine

    def perform(self) -> None:
        """
        Perform this action with the objects needed to determine its scope

        This method must be overridden by Action subclasses.
        """
        raise NotImplementedError()

class EscapeAction(Action):
    def perform(self) -> None:
        raise SystemExit()

class ActionWithDirection(Action):
    def __init__(self, entity: Entity, dx:int, dy:int):
        super().__init__(entity)

        self.dx = dx
        self.dy = dy
    
    @property
    def dest_xy(self) -> Tuple[int, int]:
        """
        Returns this actions destination.
        """
        return self.entity.x + self.dx, self.entity.y + self.dy
    
    @property
    def blocking_entity(self) -> Optional[Entity]:
        """
        Return the blocking entity at this action's destination.
        """
        return self.engine.game_map.get_blocking_entity_at_location(*self.dest_xy)

    def perform(self) -> None:
        raise NotImplementedError()

class MeleeAction(ActionWithDirection):
    def perform(self) -> None:
        target = self.blocking_entity

        # No entity to attack
        if not target:
            return
        
        print(f"You kick the {target.name}, much to its annoyance!")

class MovementAction(ActionWithDirection):

    def perform(self) ->  None:
        dest_x, dest_y = self.dest_xy

        # Destination is out of bounds
        if not self.engine.game_map.in_bounds(dest_x, dest_y):
            return
        
        # Destination is blocked by a tile
        if not self.engine.game_map.tiles["walkable"][dest_x, dest_y]:
            return

        # Destination is blocked by an entity
        if self.blocking_entity:
            return 

        self.entity.move(self.dx, self.dy)

class BumpAction(ActionWithDirection):
    def perform(self) -> None:
        if self.blocking_entity:
            return MeleeAction(self.entity, self.dx, self.dy).perform()
        else:
            return MovementAction(self.entity, self.dx, self.dy).perform()
