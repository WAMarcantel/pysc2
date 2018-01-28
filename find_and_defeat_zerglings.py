import numpy
import time
from pysc2.agents import base_agent
from pysc2.lib import actions
from pysc2.lib import features
# from pysc2.lib import environment

_PLAYER_RELATIVE = features.SCREEN_FEATURES.player_relative.index
_PLAYER_FRIENDLY = 1
_PLAYER_HOSTILE = 4
_NO_OP = actions.FUNCTIONS.no_op.id
_MOVE_SCREEN = actions.FUNCTIONS.Move_screen.id
_ATTACK_SCREEN = actions.FUNCTIONS.Attack_screen.id
_ATTACK_MINIMAP = actions.FUNCTIONS.Attack_minimap.id
_SELECT_ARMY = actions.FUNCTIONS.select_army.id
_MOVE_CAMERA = actions.FUNCTIONS.move_camera.id
_NOT_QUEUED = [0]
_SELECT_ALL = [0]

class FindAndDefeatZerglingsAgent(base_agent.BaseAgent):

    lastTarget = (63,0)
    moving = False
    lastPlayerPos = (-1, -1)
    movePlayer = False

    def step(self, obs):
        super(FindAndDefeatZerglingsAgent, self).step(obs)

        if self.movePlayer and _MOVE_SCREEN in obs.observation["available_actions"]:
            self.movePlayer = False
            self.moving = True
            return actions.FunctionCall(_ATTACK_SCREEN, [_NOT_QUEUED, (41,41)])

        if _ATTACK_SCREEN in obs.observation["available_actions"]:


          player_relative = obs.observation["screen"][_PLAYER_RELATIVE]
          ling_y, ling_x = (player_relative == _PLAYER_HOSTILE).nonzero()
          player_y, player_x = (player_relative == _PLAYER_FRIENDLY).nonzero()

          if not player_y.any():
            return actions.FunctionCall(_NO_OP, [])

          player = [int(player_x.mean()), int(player_y.mean())]

          if player == self.lastPlayerPos:
            self.moving = False
          
          self.lastPlayerPos = player

          if not ling_y.any():
             if not self.moving:
                return self.moveCameraToNewLocation()
             else:
                return actions.FunctionCall(_NO_OP, [])


          index = numpy.argmax(ling_y)
          target = [ling_x[index], ling_y[index]]

          distanceToTarget = numpy.linalg.norm(numpy.array(player) - numpy.array(target))

          if distanceToTarget < 5:
            return self.moveCameraToNewLocation()
        
          return actions.FunctionCall(_ATTACK_SCREEN, [_NOT_QUEUED, target])
        

        elif _SELECT_ARMY in obs.observation["available_actions"]:
          return actions.FunctionCall(_SELECT_ARMY, [_SELECT_ALL])
        else:
          return actions.FunctionCall(_NO_OP, [])


    def moveCameraToNewLocation(self):
        self.movePlayer = True

        if self.lastTarget == (0,0):
            target = (0,63)
        elif self.lastTarget == (0,63):
            target = (63,63)
        elif self.lastTarget == (63,63):
            target = (63,0)
        elif self.lastTarget == (63,0):
            target = (0,0)

        self.lastTarget = target
        return actions.FunctionCall(_MOVE_CAMERA, [target])
