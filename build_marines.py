import numpy
import time
from pysc2.agents import base_agent
from pysc2.lib import actions
from pysc2.lib import features
# from pysc2.lib import environment

_UNIT_TYPE = features.SCREEN_FEATURES.unit_type.index

_PLAYER_RELATIVE = features.SCREEN_FEATURES.player_relative.index
_PLAYER_BACKGROUND = 0
_PLAYER_FRIENDLY = 1
_PLAYER_NEUTRAL = 3
_PLAYER_HOSTILE = 4

_MINERAL_COUNT = 1
_FOOD_USED = 3
_FOOD_CAP = 4
_IDLE_WORKER_COUNT = 7

_NO_OP = actions.FUNCTIONS.no_op.id
_MOVE_SCREEN = actions.FUNCTIONS.Move_screen.id
_HARVEST_GATHER_SCREEN = actions.FUNCTIONS.Harvest_Gather_screen.id
_HARVEST_GATHER_SCREEN_SCV = actions.FUNCTIONS.Harvest_Gather_SCV_screen.id
_SELECT_ARMY = actions.FUNCTIONS.select_army.id
_SELECT_CONTROL_GROUP = actions.FUNCTIONS.select_control_group.id
_SELECT_IDLE_WORKER = actions.FUNCTIONS.select_idle_worker.id
_SELECT_POINT = actions.FUNCTIONS.select_point.id
_SELECT_RECT = actions.FUNCTIONS.select_rect.id
_SELECT_UNIT = actions.FUNCTIONS.select_unit.id
_TRAIN_SCV_QUICK = actions.FUNCTIONS.Train_SCV_quick.id
_BUILD_SUPPLY_DEPOT_SCREEN = actions.FUNCTIONS.Build_SupplyDepot_screen.id
_BUILD_BARRACKS_SCREEN = actions.FUNCTIONS.Build_Barracks_screen.id


_TRAIN_MARINE = actions.FUNCTIONS.Train_Marine_quick.id
_TERRAN_SCV = 45
_TERRAN_BARRACKS = 21
_TERRAN_COMMAND_CENTER = 18
_MINERAL_FIELD = 341

_BARRACKS_SCV_CONTROL_GROUP = [7]
_SUPPLY_DEPOT_SCV_CONTROL_GROUP = [6]

_NOT_QUEUED = [0]
_QUEUED = [1]
_IDLE_WORKER_ACTION_SET = [0]
_CONTROL_GROUP_SET = [1]
_CONTROL_GROUP_RECALL = [0]
_SELECT_ALL = [0]
_SELECT_ALL_OF_TYPE = 2


class BuildMarinesAgent(base_agent.BaseAgent):

    isSelected = dict()

    isSelected["Barracks"] = False
    isSelected["Idle SCV"] = False
    isSelected["Command Center"] = False
    isSelected["Supply Depot SCV"] = False
    isSelected["Barracks SCV"] = False

    lastSupplyDepotLocation = None
    lastBarracksLocation = None
    mineralCoordinate = None
    barracksSCVSet = False
    supplyDepotSCVSet = False
    SCVCount = 12
    supplyDepotCount = 0
    barracksCount = 0
    barracksSelected = 0
    foodCount = 0
    supplyDepotSCVIsBuildingSupplyDepot = False
    barracksSCVIsBuildingBarracks = False
    selectingBarracks = False
    barracksLocations = []

    def step(self, obs):
        super(BuildMarinesAgent, self).step(obs)

        print(obs.observation["available_actions"])

        player_relative_info = obs.observation["player"]
        player_relative_control_groups = obs.observation["control_groups"]
        player_relative_screen = obs.observation["screen"][_PLAYER_RELATIVE]
        available_actions = obs.observation["available_actions"]

        foodLeft = player_relative_info[
            _FOOD_CAP] - player_relative_info[_FOOD_USED]

        if self.isSelected["Barracks"]:
            self.isSelected["Barracks"] = False
            if _TRAIN_MARINE in obs.observation["available_actions"]:
                return actions.FunctionCall(_TRAIN_MARINE, [_QUEUED])

        if not self.barracksSCVSet:
            print("setting barracksSCV")
            if self.isSelected["Barracks SCV"]:
                self.isSelected["Barracks SCV"] = False
                self.barracksSCVSet = True
                if _SELECT_CONTROL_GROUP in available_actions:
                    return actions.FunctionCall(_SELECT_CONTROL_GROUP, [_CONTROL_GROUP_SET, _BARRACKS_SCV_CONTROL_GROUP])
            else:
                return self.selectSCV(obs, "Barracks SCV", 1)

        if not self.supplyDepotSCVSet:
            print("setting supplyDepotSCV")
            if self.isSelected["Supply Depot SCV"]:
                self.isSelected["Supply Depot SCV"] = False
                self.supplyDepotSCVSet = True
                if _SELECT_CONTROL_GROUP in available_actions:
                    return actions.FunctionCall(_SELECT_CONTROL_GROUP, [_CONTROL_GROUP_SET, _SUPPLY_DEPOT_SCV_CONTROL_GROUP])
            else:
                return self.selectSCV(obs, "Supply Depot SCV")

        if self.isSelected["Idle SCV"]:
            print("moving idle workers")
            self.isSelected["Idle SCV"] = False
            if self.supplyDepotSCVIsBuildingSupplyDepot:
              if self.barracksCount < 5:
                return self.buildBarracks(obs)
            else:
              if self.supplyDepotCount < 16:
                return self.buildSupplyDepot(obs)

        if player_relative_info[_IDLE_WORKER_COUNT] > 0 and self.supplyDepotCount < 16 and self.barracksCount < 5:

            if self.foodCount != player_relative_info[_FOOD_CAP]:
                self.foodCount = player_relative_info[_FOOD_CAP]
                self.supplyDepotSCVIsBuildingSupplyDepot = False
            else:
                self.barracksSCVIsBuildingBarracks = False

            if _SELECT_IDLE_WORKER in available_actions:
                self.isSelected["Idle SCV"] = True
                return actions.FunctionCall(_SELECT_IDLE_WORKER, [_IDLE_WORKER_ACTION_SET])

        if player_relative_info[_MINERAL_COUNT] >= 50:

            if foodLeft > 3:

                if self.SCVCount < 18:

                    return self.carryOutSCVTraining(obs)

                else:
                      return self.carryOutBarracksOperations(obs)

            if self.supplyDepotCount < 16:
              return self.carryOutSupplyDepotBuilding(foodLeft, obs)

        return actions.FunctionCall(_NO_OP, [])

    def selectSCV(self, obs, scvName, offset=0):

        print("SCV BEING SELECTED")

        if self.supplyDepotSCVSet and self.barracksSCVSet:

          if scvName == "Barracks SCV":
            controlGroup = _BARRACKS_SCV_CONTROL_GROUP
          if scvName == "Supply Depot SCV":
            controlGroup = _SUPPLY_DEPOT_SCV_CONTROL_GROUP

          self.isSelected[scvName] = True

          return actions.FunctionCall(_SELECT_CONTROL_GROUP, [_CONTROL_GROUP_RECALL, controlGroup])

        if _SELECT_POINT in obs.observation["available_actions"]:

            unit_type = obs.observation["screen"][_UNIT_TYPE]
            unit_y, unit_x = (unit_type == _TERRAN_SCV).nonzero()
            if(unit_y.any()):
                target = (unit_x[offset], unit_y[offset])

                self.isSelected[scvName] = True

                return actions.FunctionCall(_SELECT_POINT, [_NOT_QUEUED, target])

        return actions.FunctionCall(_NO_OP, [])

    def selectCommandCenter(self, obs):

        if _SELECT_POINT in obs.observation["available_actions"]:

            unit_type = obs.observation["screen"][_UNIT_TYPE]
            unit_y, unit_x = (unit_type == _TERRAN_COMMAND_CENTER).nonzero()
            if(unit_y.any()):

                
                target1 = (int(unit_x.mean()), int(unit_y.mean()))
                target2 = (target1[0] + 6, target1[1] + 6)
                self.isSelected["Command Center"] = True
                print("COMMAND CENTER BEING SELECTED")
                return actions.FunctionCall(_SELECT_RECT, [_NOT_QUEUED, target1, target2])
                

        return actions.FunctionCall(_NO_OP, [])

    def selectBarracks(self, obs):
        if _SELECT_POINT in obs.observation["available_actions"]:
            self.isSelected["Barracks"] = True

            index = numpy.random.randint(0, len(self.barracksLocations))
            target = self.barracksLocations[index]

            return actions.FunctionCall(_SELECT_POINT, [_NOT_QUEUED, target])

        return actions.FunctionCall(_NO_OP, [])

    def getMineralsCoordinates(self, obs):
        if self.mineralCoordinate == None:
            self.mineralCoordinate = (12, 20)

    def buildSupplyDepot(self, obs):

        if not self.supplyDepotSCVIsBuildingSupplyDepot:
            if _BUILD_SUPPLY_DEPOT_SCREEN in obs.observation["available_actions"]:

                if self.lastSupplyDepotLocation == None:
                    target = (0, 8)
                else:
                    target = (self.lastSupplyDepotLocation[
                              0] + 8, self.lastSupplyDepotLocation[1])
                    if target[0] > 84:
                      self.lastSupplyDepotLocation = (0, 64)
                      target = (self.lastSupplyDepotLocation[
                              0] + 8, self.lastSupplyDepotLocation[1])
                    print("setting new supply depot location to: ", target)
                self.supplyDepotSCVIsBuildingSupplyDepot = True
                self.lastSupplyDepotLocation = target
                self.supplyDepotCount = self.supplyDepotCount + 1
                return actions.FunctionCall(_BUILD_SUPPLY_DEPOT_SCREEN, [_NOT_QUEUED, target])

        return actions.FunctionCall(_NO_OP, [])

    def buildBarracks(self, obs):

        if not self.barracksSCVIsBuildingBarracks:
            if _BUILD_BARRACKS_SCREEN in obs.observation["available_actions"]:

                if self.lastBarracksLocation == None:
                    target = (50, 16)
                else:
                    target = (self.lastBarracksLocation[
                              0] + 12, self.lastBarracksLocation[1])
                    if target[0] > 84:
                      self.lastBarracksLocation = (50, self.lastBarracksLocation[1] + 12)
                      target = (self.lastBarracksLocation[
                              0] + 12, self.lastBarracksLocation[1])

                self.lastBarracksLocation = target
                self.barracksSCVIsBuildingBarracks = True
                self.barracksLocations.append(target)
                self.barracksCount = self.barracksCount + 1

                return actions.FunctionCall(_BUILD_BARRACKS_SCREEN, [_NOT_QUEUED, target])

        return actions.FunctionCall(_NO_OP, [])

    def carryOutSCVTraining(self, obs):

        if self.isSelected["Command Center"]:
            self.isSelected["Command Center"] = False
            if _TRAIN_SCV_QUICK in obs.observation["available_actions"]:
                self.SCVCount = self.SCVCount + 1
                return actions.FunctionCall(_TRAIN_SCV_QUICK, [_QUEUED])
            else:
                return actions.FunctionCall(_NO_OP, [])
        else:
            return self.selectCommandCenter(obs)

    def carryOutBarracksOperations(self, obs):
        print("Barracks ops: ")
        if self.barracksCount > 4:
            return self.selectBarracks(obs)
        else:

            if obs.observation["player"][_MINERAL_COUNT] >= 150 and not self.barracksSCVIsBuildingBarracks:

                if self.isSelected["Barracks SCV"]:
                    return self.buildBarracks(obs)
                else:
                    return self.selectSCV(obs, "Barracks SCV")

        return actions.FunctionCall(_NO_OP, [])

    def carryOutSupplyDepotBuilding(self, foodLeft, obs):
        if obs.observation["player"][_MINERAL_COUNT] > 100 and foodLeft < 6 and not self.supplyDepotSCVIsBuildingSupplyDepot:
            print("tryingt to construct supply depot")
            if self.isSelected["Supply Depot SCV"]:
                return self.buildSupplyDepot(obs)
            else:
                return self.selectSCV(obs, "Supply Depot SCV")

        return actions.FunctionCall(_NO_OP, [])