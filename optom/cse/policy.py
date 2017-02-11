# -*- coding: utf-8 -*-
# @package optom.cse
# @cond LICENSE
# #############################################################################
# # LGPL License                                                              #
# #                                                                           #
# # This file is part of the Optimisation of Overtaking Manoeuvres project.   #
# # Copyright (c) 2016, Malte Aschermann (malte.aschermann@tu-clausthal.de)   #
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
"""Policy related classes"""
import numpy

import optom.common.helper

BEHAVIOUR = optom.common.helper.Enum(["deny", "allow"])

SUMO_VCLASS = {
    BEHAVIOUR.allow: "custom2",
    BEHAVIOUR.deny: "custom1"
}


class BasePolicy(object):
    """Base Policy"""

    def __init__(self, behaviour=BEHAVIOUR.deny):
        """
        C'tor
        Args:
            behaviour: Default, i.e. baseline policy.
                       Enum of optom.cse.policy.BEHAVIOUR.deny/allow
        """
        self._behaviour = behaviour

    @staticmethod
    def behaviour_from_string_or_else(behaviour, or_else):
        """
        Transforms string argument of behaviour, i.e. "allow", "deny" case insensitive to
        BEHAVIOUR enum value. Otherwise return passed or_else argument.
        Args:
            behaviour: string "allow", "deny"
            or_else: otherwise returned argument
        Returns:
            BEHAVIOUR.allow, BEHAVIOUR.deny, or_else
        """
        if behaviour.lower() == "allow":
            return BEHAVIOUR.allow
        if behaviour.lower() == "deny":
            return BEHAVIOUR.deny
        return or_else

    @property
    def behaviour(self):
        """
        Returns behaviour
        Returns:
            behaviour
        """
        return self._behaviour


class SUMOPolicy(BasePolicy):
    """
    Policy class to encapsulate SUMO's 'custom2'/'custom1' vehicle classes
    for allowing/disallowing access to overtaking lane (OTL)
    """

    def __init__(self, behaviour=BEHAVIOUR.deny):
        """C'tor"""
        super(SUMOPolicy, self).__init__(behaviour)

    @staticmethod
    def to_allowed_class():
        """Get the SUMO class for allowed vehicles"""
        return SUMO_VCLASS.get(BEHAVIOUR.allow)

    @staticmethod
    def to_disallowed_class():
        """Get the SUMO class for disallowed vehicles"""
        return SUMO_VCLASS.get(BEHAVIOUR.deny)


class SUMOUniversalPolicy(SUMOPolicy):
    """
    Universal policy, i.e. always applies to any vehicle
    """

    def __init__(self, behaviour=BEHAVIOUR.deny):
        """C'tor"""
        super(SUMOUniversalPolicy, self).__init__(behaviour)

    @staticmethod
    def applies_to(vehicle):
        """
        Test whether this policy applies to given vehicle
        Args:
            vehicle: Vehicle
        Returns:
            boolean
        """
        if vehicle:
            return True

        return True

    def apply(self, vehicles):
        """
        apply policy to vehicles
        Args:
            vehicles: iterable object containing BaseVehicles, or inherited objects
        Returns:
            List of vehicles with applied, i.e. set attributes, whether they can use otl or not
        """

        return [
            i_vehicle.change_vehicle_class(
                self.to_disallowed_class()
            ) for i_vehicle in vehicles
        ]


class SUMONullPolicy(SUMOPolicy):
    """
    Null policy, i.e. no restrictions: Applies to no vehicle
    """

    def __init__(self, behaviour=BEHAVIOUR.deny):
        """C'tor"""
        super(SUMONullPolicy, self).__init__(behaviour)

    @staticmethod
    def applies_to(vehicle):
        """
        Test whether this policy applies to given vehicle
        Args:
            vehicle: Vehicle
        Returns:
            boolean
        """
        if vehicle:
            return False

        return False

    @staticmethod
    def apply(vehicles):
        """
        apply policy to vehicles
        Args:
            vehicles: iterable object containing BaseVehicles, or inherited objects
        Returns:
            List of vehicles with applied, i.e. set attributes, whether they can use otl or not
        """
        return vehicles


class SUMOSpeedPolicy(SUMOPolicy):
    """Speed based policy: Applies to vehicles within a given speed range"""

    def __init__(self, speed_range=(0, 120), behaviour=BEHAVIOUR.deny):
        """C'tor"""
        super(SUMOSpeedPolicy, self).__init__(behaviour)
        self._speed_range = numpy.array(speed_range)

    def __str__(self):
        return "SUMOSpeedPolicy: speed_range = {}, behaviour = {}".format(
            self._speed_range, self._behaviour
        )

    def applies_to(self, vehicle):
        """
        Test whether this policy applies to given vehicle
        Args:
            vehicle: Vehicle
        Returns:
            boolean
        """
        if self._speed_range[0] <= vehicle.speed_max <= self._speed_range[1]:
            return True
        return False

    def apply(self, vehicles):
        """
        apply policy to vehicles
        Args:
            vehicles: iterable object containing BaseVehicles, or inherited objects
        Returns:
            List of vehicles with applied, i.e. set attributes, whether they can use otl or not
        """

        return [
            i_vehicle.change_vehicle_class(
                SUMO_VCLASS.get(self._behaviour)
            ) if self.applies_to(i_vehicle) else i_vehicle
            for i_vehicle in vehicles
        ]


class SUMOPositionPolicy(SUMOPolicy):
    """
    Position based policy: Applies to vehicles which are located inside a given bounding box, i.e.
    [(left_lane_0, right_lane_0) -> (left_lane_1, right_lane_1)]
    """

    def __init__(self, position_box=numpy.array(((0.0, 0), (100.0, 1))),
                 behaviour=BEHAVIOUR.deny):
        """C'tor"""
        super(SUMOPositionPolicy, self).__init__(behaviour)
        self._position_box = position_box

    def applies_to(self, vehicle):
        """
        Test whether this policy applies to given vehicle
        Args:
            vehicle: Vehicle
        Returns:
            boolean
        """
        if numpy.all(numpy.logical_and(self._position_box[0] <= vehicle.position,
                                       vehicle.position <= self._position_box[1])):
            return True
        return False

    def apply(self, vehicles):
        """
        apply policy to vehicles
        Args:
            vehicles: iterable object containing BaseVehicles, or inherited objects
        Returns:
            List of vehicles with applied, i.e. set attributes, whether they can use otl or not
        """

        return [
            i_vehicle.change_vehicle_class(
                SUMO_VCLASS.get(self._behaviour)
            ) if self.applies_to(i_vehicle) else i_vehicle
            for i_vehicle in vehicles
        ]