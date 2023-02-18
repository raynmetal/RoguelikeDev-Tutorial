from __future__ import annotations 

from typing import TYPE_CHECKING, Optional, Tuple

import color

if TYPE_CHECKING:
    from engine import Engine
    from entity import Entity, Actor

class Action:
    def __init__(self, entity: Actor) -> None:
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

class WaitAction(Action):
    def perform(self) -> None:
        pass

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
    
    @property
    def target_actor(self) -> Optional[Actor]:
        """
        Return the actor at this actions destination.
        """
        return self.engine.game_map.get_actor_at_location(*self.dest_xy)

    def perform(self) -> None:
        raise NotImplementedError()

class MeleeAction(ActionWithDirection):
    def perform(self) -> None:
        target = self.target_actor

        # No entity to attack
        if not target:
            return
        
        damage = self.entity.fighter.power - target.fighter.defense

        attack_desc = f"{self.entity.name.capitalize()} attacks {target.name}"
        if self.entity is self.engine.player:
            attack_color = color.player_atk
        else:
            attack_color = color.enemy_atk

        if damage > 0:
            self.engine.message_log.add_message(
                f"{attack_desc} for {damage} hit points.",
                attack_color,
            )
            target.fighter.hp -= damage
        else:
            self.engine.message_log.add_message(
                f"{attack_desc} but does no damage",
                attack_color,
            )

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
        if self.target_actor:
            return MeleeAction(self.entity, self.dx, self.dy).perform()
        else:
            return MovementAction(self.entity, self.dx, self.dy).perform()
