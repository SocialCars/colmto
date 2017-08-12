# -*- coding: utf-8 -*-
# @package colmto.cse
# @cond LICENSE
# #############################################################################
# # LGPL License                                                              #
# #                                                                           #
# # This file is part of the Cooperative Lane Management and Traffic flow     #
# # Optimisation project.                                                     #
# # Copyright (c) 2017, Malte Aschermann (malte.aschermann@tu-clausthal.de)   #
# # This program is free software: you can redistribute it and/or modify      #
# # it under the terms of the GNU Lesser General Public License as            #
# # published by the Free Software Foundation, either version 3 of the        #
# # License, or (at your option) any later version.                           #
# #                                                                           #
# # This program is distributed in the hope that it will be useful,           #
# # but WITHOUT ANY WARRANTY; without even the implied warranty of            #
# # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the             #
# # GNU Lesser General Public License for more details.                       #
# #                                                                           #
# # You should have received a copy of the GNU Lesser General Public License  #
# # along with this program. If not, see http://www.gnu.org/licenses/         #
# #############################################################################
# @endcond
# pylint: disable=too-few-public-methods
"""Rule related classes"""

import typing

import enum
import numpy

from colmto.environment import SUMOVehicle


@enum.unique
class Behaviour(enum.Enum):
    """Behaviour enum for enumerating allow/deny states and corresponding vehicle classes."""
    ALLOW = "custom2"
    DENY = "custom1"

    @property
    def vclass(self) -> str:
        """returns vehicle class string"""
        return self.value


@enum.unique
class RuleOperator(enum.Enum):
    """
    Operator to be applied to logical rule expressions.

    Denotes whether an iterable with boolean expressions is True,
    iff all elements are True (all()) or iff at least one element has to be True (any())
    """
    ALL = all
    ANY = any

    def evaluate(self, args: typing.Iterable):
        """evaluate iterable args"""
        return self.value(args)  # pylint: disable=too-many-function-args


class BaseRule(object):
    """Base Rule"""

    def __init__(self, behaviour=Behaviour.DENY):
        """
        C'tor
        @param behaviour Default, i.e. baseline rule.
                       Enum of colmto.cse.rule.Behaviour.DENY/ALLOW
        """
        self._behaviour = behaviour

    @staticmethod
    def behaviour_from_string(behaviour: str, or_else: Behaviour) -> Behaviour:
        """
        Transforms string argument of behaviour, i.e. "allow", "deny" case insensitive to
        Behaviour enum value. Otherwise return passed or_else argument.
        @param behaviour string "allow", "deny"
        @param or_else otherwise returned argument
        @type or_else Behaviour
        @retval Behaviour.ALLOW, Behaviour.DENY, or_else
        """
        try:
            return Behaviour[behaviour.upper()]
        except KeyError:
            return or_else

    @staticmethod
    def ruleoperator_from_string(
            rule_operator: str, or_else: RuleOperator) -> RuleOperator:
        """
        Transforms string argument of rule operator, i.e. "any", "all" case insensitive to
        RuleOperator enum value. Otherwise return passed or_else argument.
        @param RuleOperator string ("any"|"all")
        @param or_else otherwise returned argument
        @type or_else RuleOperator
        @retval RuleOperator.ANY, RuleOperator.ALL, or_else
        """
        try:
            return RuleOperator[rule_operator.upper()]
        except KeyError:
            return or_else

    @property
    def behaviour(self) -> Behaviour:
        """
        Returns behaviour
        @retval behaviour
        """
        return self._behaviour

    # pylint: disable=unused-argument,no-self-use
    def applies_to(self, vehicle: SUMOVehicle) -> bool:
        """
        Test whether this rule applies to given vehicle
        @param vehicle Vehicle
        @retval boolean
        """
        return False


class SUMORule(BaseRule):
    """
    Rule class to encapsulate SUMO's 'custom2'/'custom1' vehicle classes
    for allowing/disallowing access to overtaking lane (OTL)
    """

    @staticmethod
    def to_allowed_class() -> str:
        """Get the SUMO class for allowed vehicles"""
        return Behaviour.ALLOW.vclass

    @staticmethod
    def to_disallowed_class() -> str:
        """Get the SUMO class for disallowed vehicles"""
        return Behaviour.DENY.vclass


class SUMOExtendableRule(object):
    """Add ability to policies to be extended, i.e. to add sub-policies to them"""

    def __init__(self, policies: typing.Iterable[SUMORule], rule=RuleOperator.ANY):
        """
        C'tor.

        @param policies List of policies
        @param rule Rule of RuleOperator enum for applying sub-policies ANY|ALL
        """

        # check rule types
        for i_rule in policies:
            if not isinstance(i_rule, SUMORule):
                raise TypeError(
                    "%s is not of colmto.cse.rule.SUMORule", i_rule
                )

        self._vehicle_policies = list(policies)

        if rule not in RuleOperator:
            raise ValueError

        self._rule = rule

        super(SUMOExtendableRule, self).__init__()

    @property
    def vehicle_policies(self):
        """
        Return vehicle related sub-policies.

        Returns:
            vehicle_policies
        """
        return self._vehicle_policies

    @property
    def rule(self) -> RuleOperator:
        """
        Returns rule.

        Returns:
            rule
        """
        return self._rule

    @rule.setter
    def rule(self, rule: RuleOperator):
        """
        Sets rule for applying sub-policies (ANY|ALL).

        @param rule Rule for applying sub-policies (ANY|ALL)
        """
        if rule not in RuleOperator:
            raise ValueError
        self._rule = rule

    def add_rule(self, vehicle_rule: SUMORule):
        """
        Adds a rule, specifically for SUMO attributes.

        Rule must derive from colmto.cse.rule.SUMORule.

        @param vehicle_rule A rule

        @retval self
        """

        if not isinstance(vehicle_rule, SUMOExtendableRule):
            raise TypeError("%s is not of colmto.cse.rule.SUMOExtendableRule", vehicle_rule)

        self._vehicle_policies.append(vehicle_rule)

        return self

    def subpolicies_apply_to(self, vehicle: SUMOVehicle) -> bool:
        """
        Check whether sub-policies apply to this vehicle.

        @param vehicle vehicle object
        @retval boolean
        """

        # pylint: disable=no-member
        return self.rule.evaluate(
            [i_subrule.applies_to(vehicle) for i_subrule in self._vehicle_policies]
        )


class SUMOUniversalRule(SUMORule):
    """
    Universal rule, i.e. always applies to any vehicle
    """

    # pylint: disable=unused-argument
    def applies_to(self, vehicle: SUMOVehicle):
        """
        Test whether this rule applies to given vehicle
        @param vehicle Vehicle
        @retval boolean
        """
        return True

    def apply(self, vehicles: typing.Iterable[SUMOVehicle]):
        """
        apply rule to vehicles
        @param vehicles iterable object containing BaseVehicles, or inherited objects
        @retval List of vehicles with applied, i.e. set attributes, whether they can use otl or not
        """

        return [
            i_vehicle.change_vehicle_class(
                self.to_disallowed_class()
            ) for i_vehicle in vehicles
        ]


class SUMONullRule(SUMORule):
    """
    Null rule, i.e. no restrictions: Applies to no vehicle
    """

    # pylint: disable=unused-argument
    def applies_to(self, vehicle: SUMOVehicle):
        """
        Test whether this rule applies to given vehicle
        @param vehicle Vehicle
        @retval boolean
        """
        return False

    # pylint: disable=no-self-use
    def apply(self, vehicles: typing.Iterable[SUMOVehicle]) -> typing.Iterable[SUMOVehicle]:
        """
        apply rule to vehicles
        @param vehicles iterable object containing BaseVehicles, or inherited objects
        @retval List of vehicles with applied, i.e. set attributes, whether they can use otl or not
        """
        return vehicles


class SUMOVehicleRule(SUMORule, SUMOExtendableRule):
    """Base class for vehicle attribute specific policies."""

    def __init__(self, behaviour=Behaviour.DENY, rule=RuleOperator.ANY):
        """C'tor."""
        self._vehicle_policies = []
        self._rule = rule
        super(SUMOVehicleRule, self).__init__(behaviour)


class SUMOVTypeRule(SUMOVehicleRule):
    """Vehicle type based rule: Applies to vehicles with a given SUMO vehicle type"""

    def __init__(self, vehicle_type=None, behaviour=Behaviour.DENY):
        """C'tor."""
        super(SUMOVTypeRule, self).__init__(behaviour)
        self._vehicle_type = vehicle_type

    def __str__(self):
        return "{}: vehicle_type = {}, behaviour = {}, subpolicies: {}: {}".format(
            self.__class__, self._vehicle_type, self._behaviour.vclass,
            self._rule, ",".join([str(i_rule) for i_rule in self._vehicle_policies])
        )

    def applies_to(self, vehicle: SUMOVehicle) -> bool:
        """
        Test whether this (and sub)policies apply to given vehicle.
        @param vehicle Vehicle
        @retval boolean
        """
        if (self._vehicle_type == vehicle.vehicle_type) and \
                (self.subpolicies_apply_to(vehicle) if self._vehicle_policies else True):
            return True
        return False

    def apply(self, vehicles: typing.Iterable[SUMOVehicle]) -> typing.List[SUMOVehicle]:
        """
        apply rule to vehicles
        @param vehicles iterable object containing BaseVehicles, or inherited objects
        @retval List of vehicles with applied, i.e. set attributes, whether they can use otl or not
        """

        return [
            i_vehicle.change_vehicle_class(
                self._behaviour.vclass
            ) if self.applies_to(i_vehicle) else i_vehicle
            for i_vehicle in vehicles
        ]


class SUMOSpeedRule(SUMOVehicleRule):
    """Speed based rule: Applies to vehicles within a given speed range"""

    def __init__(self, speed_range=(0, 120), behaviour=Behaviour.DENY):
        """C'tor."""
        super(SUMOSpeedRule, self).__init__(behaviour)
        self._speed_range = numpy.array(speed_range)

    def __str__(self):
        return "{}: speed_range = {}, behaviour = {}, subpolicies: {}: {}".format(
            self.__class__, self._speed_range, self._behaviour.name,
            self._rule, ",".join([str(i_rule) for i_rule in self._vehicle_policies])
        )

    def applies_to(self, vehicle: SUMOVehicle) -> bool:
        """
        Test whether this (and sub)policies apply to given vehicle
        @param vehicle Vehicle
        @retval boolean
        """
        if (self._speed_range[0] <= vehicle.speed_max <= self._speed_range[1]) and \
                (self.subpolicies_apply_to(vehicle) if self._vehicle_policies else True):
            return True
        return False

    def apply(self, vehicles: typing.Iterable[SUMOVehicle]) -> typing.List[SUMOVehicle]:
        """
        apply rule to vehicles
        @param vehicles iterable object containing BaseVehicles, or inherited objects
        @retval List of vehicles with applied, i.e. set attributes, whether they can use otl or not
        """

        return [
            i_vehicle.change_vehicle_class(
                self._behaviour.vclass
            ) if self.applies_to(i_vehicle) else i_vehicle
            for i_vehicle in vehicles
        ]


class SUMOPositionRule(SUMOVehicleRule):
    """
    Position based rule: Applies to vehicles which are located inside a given bounding box, i.e.
    [(left_lane_0, right_lane_0) -> (left_lane_1, right_lane_1)]
    """

    def __init__(self, position_bbox=numpy.array(((0.0, 0), (100.0, 1))),
                 behaviour=Behaviour.DENY):
        """C'tor."""
        super(SUMOPositionRule, self).__init__(behaviour)
        self._position_bbox = position_bbox

    def __str__(self):
        return "{}: position_bbox = {}, behaviour = {}, subpolicies: {}: {}".format(
            self.__class__, self._position_bbox, self._behaviour.vclass,
            self._rule, ",".join([str(i_rule) for i_rule in self._vehicle_policies])
        )

    @property
    def position_bbox(self) -> numpy.array:
        """
        Returns position bounding box.
        @retval position bounding box
        """
        return self._position_bbox

    def applies_to(self, vehicle: SUMOVehicle) -> bool:
        """
        Test whether this (and sub)policies apply to given vehicle
        @param vehicle Vehicle
        @retval boolean
        """
        # pylint: disable=no-member
        if numpy.all(numpy.logical_and(self._position_bbox[0] <= vehicle.position,
                                       vehicle.position <= self._position_bbox[1])) and \
                (self.subpolicies_apply_to(vehicle) if self._vehicle_policies else True):
            return True
        return False
        # pylint: enable=no-member

    def apply(self, vehicles: typing.Iterable[SUMOVehicle]) \
            -> typing.List[SUMOVehicle]:
        """
        apply rule to vehicles
        @param vehicles iterable object containing BaseVehicles, or inherited objects
        @retval List of vehicles with applied, i.e. set attributes, whether they can use otl or not
        """

        return [
            i_vehicle.change_vehicle_class(
                self._behaviour.vclass
            ) if self.applies_to(i_vehicle) else i_vehicle
            for i_vehicle in vehicles
        ]