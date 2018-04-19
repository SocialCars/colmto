# -*- coding: utf-8 -*-
# @package tests.cse
# @cond LICENSE
# #############################################################################
# # LGPL License                                                              #
# #                                                                           #
# # This file is part of the Cooperative Lane Management and Traffic flow     #
# # Optimisation project.                                                     #
# # Copyright (c) 2018, Malte Aschermann (malte.aschermann@tu-clausthal.de)   #
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
'''
colmto: Test module for environment.rule.
'''
import random

from nose.tools import assert_equal
from nose.tools import assert_false
from nose.tools import assert_is_instance
from nose.tools import assert_raises
from nose.tools import assert_true
from nose.tools import assert_tuple_equal

import colmto.cse.rule
import colmto.environment.vehicle
import colmto.common.helper


def test_base_rule():
    '''
    Test BaseRule class
    '''
    colmto.cse.rule.BaseRule()

def test_sumo_rule():
    '''
    Test SumoRule class
    '''
    with assert_raises(TypeError):
        colmto.cse.rule.SUMORule()  # pylint: disable=abstract-class-instantiated

    assert_equal(colmto.cse.rule.SUMORule.to_disallowed_class(), 'custom1')
    assert_equal(colmto.cse.rule.SUMORule.to_allowed_class(), 'custom2')


def test_sumo_null_rule():
    '''
    Test SumoNullRule class
    '''
    l_sumo_rule = colmto.cse.rule.SUMONullRule()
    assert_is_instance(l_sumo_rule, colmto.cse.rule.SUMONullRule)

    l_vehicles = [
        colmto.environment.vehicle.SUMOVehicle(
            environment={'gridlength': 200, 'gridcellwidth': 4}
        ) for _ in range(23)
    ]

    for i_vehicle in l_vehicles:
        i_vehicle.change_vehicle_class(
            random.choice(
                [
                    colmto.cse.rule.SUMORule.to_disallowed_class(),
                    colmto.cse.rule.SUMORule.to_allowed_class()
                ]
            )
        )

    l_results = l_sumo_rule.apply(l_vehicles)

    for i, i_result in enumerate(l_results):
        assert_equal(l_vehicles[i].vehicle_class, i_result.vehicle_class)
        assert_false(l_sumo_rule.applies_to(l_vehicles[i]))


def test_sumo_vtype_rule():
    '''Test SUMOVTypeRule class'''
    assert_is_instance(colmto.cse.rule.SUMOVTypeRule('passenger'), colmto.cse.rule.SUMOVTypeRule)

    assert_equal(
        str(
            colmto.cse.rule.ExtendableSUMOVTypeRule(
                vehicle_type='passenger'
            ).add_subrule(
                colmto.cse.rule.SUMOPositionRule(
                    bounding_box=((0., -1.), (100., 1.))
                )
            )
        ),
        "<class 'colmto.cse.rule.ExtendableSUMOVTypeRule'>: vehicle_type = VehicleType.PASSENGER, subrule_operator: RuleOperator.ANY, subrules: <class 'colmto.cse.rule.SUMOPositionRule'>"
    )

    assert_true(
        colmto.cse.rule.SUMOVTypeRule(
            vehicle_type='passenger'
        ).applies_to(
            colmto.environment.vehicle.SUMOVehicle(
                environment={'gridlength': 200, 'gridcellwidth': 4},
                vehicle_type='passenger'
            )
        )
    )

    assert_false(
        colmto.cse.rule.SUMOVTypeRule(
            vehicle_type='truck'
        ).applies_to(
            colmto.environment.vehicle.SUMOVehicle(
                environment={'gridlength': 200, 'gridcellwidth': 4},
                vehicle_type='passenger'
            )
        )
    )

    assert_equal(
        next(
            colmto.cse.rule.SUMOVTypeRule(
                vehicle_type='passenger'
            ).apply(
                (
                    colmto.environment.vehicle.SUMOVehicle(
                        environment={'gridlength': 200, 'gridcellwidth': 4},
                        vehicle_type='passenger'
                    ),
                )
            )
        ).vehicle_class,
        colmto.common.helper.Behaviour.DENY.value
    )

    assert_equal(
        next(
            colmto.cse.rule.SUMOVTypeRule(
                vehicle_type='passenger'
            ).apply(
                (
                    colmto.environment.vehicle.SUMOVehicle(
                        environment={'gridlength': 200, 'gridcellwidth': 4},
                        vehicle_type='passenger'
                    ),
                )
            )
        ).vehicle_class,
        colmto.common.helper.Behaviour.DENY.value
    )

    assert_equal(
        next(
            colmto.cse.rule.SUMOVTypeRule(
                vehicle_type='truck'
            ).apply(
                (
                    colmto.environment.vehicle.SUMOVehicle(
                        environment={'gridlength': 200, 'gridcellwidth': 4},
                        vehicle_type='passenger'
                    ),
                )
            )
        ).vehicle_class,
        colmto.common.helper.Behaviour.ALLOW.value
    )


def test_sumo_extendable_rule():
    '''Test SUMOExtendableRule class'''
    with assert_raises(TypeError):
        colmto.cse.rule.ExtendableSUMORule(
            subrules=['foo'],
        )

    with assert_raises(KeyError):
        colmto.cse.rule.ExtendableSUMORule(
            subrule_operator='foo'
        )

    assert_equal(
        colmto.cse.rule.ExtendableSUMORule(
            subrule_operator='any'
        ).subrule_operator,
        colmto.common.helper.RuleOperator.ANY
    )

    assert_equal(
        colmto.cse.rule.ExtendableSUMORule(
            subrules=[colmto.cse.rule.SUMOMinimalSpeedRule(minimal_speed=60.)],
            subrule_operator='any'
        ).subrule_operator,
        colmto.common.helper.RuleOperator.ANY
    )

    l_sumo_rule = colmto.cse.rule.ExtendableSUMORule(
        subrules=[colmto.cse.rule.SUMOMinimalSpeedRule(minimal_speed=60.)],
        subrule_operator=colmto.common.helper.RuleOperator.ANY
    )

    assert_equal(l_sumo_rule.subrule_operator, colmto.common.helper.RuleOperator.ANY)
    l_sumo_rule.subrule_operator = colmto.common.helper.RuleOperator.ALL
    assert_equal(l_sumo_rule.subrule_operator, colmto.common.helper.RuleOperator.ALL)

    with assert_raises(ValueError):
        l_sumo_rule.subrule_operator = 'foo'
        l_sumo_rule.add_subrule(l_sumo_rule)

    l_sumo_rule.add_subrule(colmto.cse.rule.SUMOPositionRule())

    with assert_raises(TypeError):
        l_sumo_rule.add_subrule('foo')
        l_sumo_rule.add_subrule(colmto.cse.rule.ExtendableRule())

    l_sumo_rule = colmto.cse.rule.ExtendableSUMORule(subrules=[])
    l_sumo_sub_rule = colmto.cse.rule.SUMOMinimalSpeedRule(minimal_speed=40.)
    l_sumo_rule.add_subrule(l_sumo_sub_rule)

    assert_true(
        l_sumo_rule.applies_to_subrules(
            colmto.environment.vehicle.SUMOVehicle(
                environment={'gridlength': 200, 'gridcellwidth': 4},
                speed_max=30.
            )
        )
    )

    assert_true(
        l_sumo_sub_rule.applies_to(
            colmto.environment.vehicle.SUMOVehicle(
                environment={'gridlength': 200, 'gridcellwidth': 4},
                speed_max=30.
            )
        )
    )

    l_sumo_rule = colmto.cse.rule.ExtendableSUMORule(
        subrules=[],
        subrule_operator=colmto.common.helper.RuleOperator.ALL
    )
    l_sumo_rule.add_subrule(l_sumo_sub_rule)

    assert_true(
        l_sumo_rule.applies_to_subrules(
            colmto.environment.vehicle.SUMOVehicle(
                environment={'gridlength': 200, 'gridcellwidth': 4},
                speed_max=30.
            )
        )
    )

    assert_false(
        l_sumo_rule.applies_to_subrules(
            colmto.environment.vehicle.SUMOVehicle(
                environment={'gridlength': 200, 'gridcellwidth': 4},
                speed_max=60.
            )
        )
    )

    assert_true(
        l_sumo_sub_rule.applies_to(
            colmto.environment.vehicle.SUMOVehicle(
                environment={'gridlength': 200, 'gridcellwidth': 4},
                speed_max=30.
            )
        )
    )

    assert_false(
        l_sumo_sub_rule.applies_to(
            colmto.environment.vehicle.SUMOVehicle(
                environment={'gridlength': 200, 'gridcellwidth': 4},
                speed_max=60.
            )
        )
    )


def test_sumo_universal_rule():
    '''Test SUMOUniversalRule class'''

    assert_true(
        colmto.cse.rule.SUMOUniversalRule().applies_to(
            colmto.environment.vehicle.SUMOVehicle(environment={'gridlength': 200, 'gridcellwidth': 4})
        )
    )

    assert_equal(
        next(
            colmto.cse.rule.SUMOUniversalRule().apply(
                (colmto.environment.vehicle.SUMOVehicle(environment={'gridlength': 200, 'gridcellwidth': 4}),)
            )
        ).vehicle_class,
        'custom1'
    )


def test_sumo_speed_rule():
    '''
    Test SUMOMinimalSpeedRule class
    '''
    l_sumo_rule = colmto.cse.rule.SUMOMinimalSpeedRule(minimal_speed=60.)
    assert_is_instance(l_sumo_rule, colmto.cse.rule.SUMOMinimalSpeedRule)

    l_vehicles = [
        colmto.environment.vehicle.SUMOVehicle(
            environment={'gridlength': 200, 'gridcellwidth': 4},
            speed_max=random.randrange(0, 120)
        ) for _ in range(4711)
        ]

    l_results = l_sumo_rule.apply(l_vehicles)

    for i, i_results in enumerate(l_results):
        if l_vehicles[i].speed_max < 60.0:
            assert_equal(
                i_results.vehicle_class,
                colmto.cse.rule.SUMORule.to_disallowed_class()
            )
        else:
            assert_equal(
                i_results.vehicle_class,
                colmto.cse.rule.SUMORule.to_allowed_class()
            )

    assert_equal(
        str(
            colmto.cse.rule.ExtendableSUMOMinimalSpeedRule(
                minimal_speed=60.,
            ).add_subrule(
                colmto.cse.rule.SUMOPositionRule(
                    bounding_box=((0., -1.), (100., 1.))
                )
            )
        ),
        "<class 'colmto.cse.rule.ExtendableSUMOMinimalSpeedRule'>: minimal_speed = 60.0, subrule_operator: RuleOperator.ANY, subrules: <class 'colmto.cse.rule.SUMOPositionRule'>"
    )


def test_sumo_position_rule():
    '''
    Test SUMOPositionRule class
    '''
    l_sumo_rule = colmto.cse.rule.SUMOPositionRule(bounding_box=((0., -1.), (100., 1.)))
    assert_is_instance(l_sumo_rule, colmto.cse.rule.SUMOPositionRule)

    l_vehicles = [
        colmto.environment.vehicle.SUMOVehicle(environment={'gridlength': 200, 'gridcellwidth': 4})
        for _ in range(4711)
    ]
    for i_vehicle in l_vehicles:
        i_vehicle.position = (random.randrange(0, 200), 0.)

    l_results = l_sumo_rule.apply(l_vehicles)

    for i, i_results in enumerate(l_results):
        if 0. <= l_vehicles[i].position[0] <= 100.0:
            assert_true(
                l_sumo_rule.applies_to(l_vehicles[i])
            )
            assert_equal(
                i_results.vehicle_class,
                colmto.cse.rule.SUMORule.to_disallowed_class()
            )
        else:
            assert_false(
                l_sumo_rule.applies_to(l_vehicles[i])
            )
            assert_equal(
                i_results.vehicle_class,
                colmto.cse.rule.SUMORule.to_allowed_class()
            )

    assert_tuple_equal(
        colmto.cse.rule.SUMOPositionRule(
            bounding_box=((0., -1.), (100., 1.)),
        ).bounding_box,
        ((0., -1.), (100., 1.))
    )

    assert_equal(
        str(
            colmto.cse.rule.ExtendableSUMOPositionRule(
                bounding_box=((0., -1.), (100., 1.)),
            ).add_subrule(
                colmto.cse.rule.SUMOMinimalSpeedRule(
                    minimal_speed=60.
                )
            )
        ),
        "<class 'colmto.cse.rule.ExtendableSUMOPositionRule'>: bounding_box = BoundingBox(p1=Position(x=0.0, y=-1.0), p2=Position(x=100.0, y=1.0)), subrule_operator: RuleOperator.ANY, subrules: <class 'colmto.cse.rule.SUMOMinimalSpeedRule'>"
    )
