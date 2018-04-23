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
colmto: Test module for environment.cse.
'''
import random
from types import SimpleNamespace

import unittest

import colmto.cse.cse
import colmto.cse.rule
import colmto.environment.vehicle


class TestCSE(unittest.TestCase):
    '''
    Test cases for CSE
    '''

    def test_base_cse(self):
        '''
        Test BaseCSE class
        '''
        self.assertIsInstance(colmto.cse.cse.BaseCSE(), colmto.cse.cse.BaseCSE)
        self.assertIsInstance(
            colmto.cse.cse.BaseCSE(
                SimpleNamespace(
                    loglevel='debug', quiet=False, logfile='foo.log'
                )
            ),
            colmto.cse.cse.BaseCSE
        )
    
    
    def test_sumo_cse(self):
        '''
        Test SumoCSE class
        '''
        self.assertIsInstance(
            colmto.cse.cse.SumoCSE(
                SimpleNamespace(
                    loglevel='debug', quiet=False, logfile='foo.log'
                )
            ),
            colmto.cse.cse.SumoCSE
        )
    
        l_rule_speed = colmto.cse.rule.SUMOMinimalSpeedRule(80.)
    
        l_rule_outside_position = colmto.cse.rule.SUMOPositionRule(
            bounding_box=((0., 0), (64.0, 1)),
            outside=True
        )
    
        l_sumo_cse = colmto.cse.cse.SumoCSE().add_rule(l_rule_outside_position).add_rule(l_rule_speed)
    
        self.assertIsInstance(l_sumo_cse, colmto.cse.cse.SumoCSE)
        self.assertIsInstance(l_sumo_cse.rules, frozenset)
        self.assertIn(l_rule_speed, l_sumo_cse.rules)
        self.assertIn(l_rule_outside_position, l_sumo_cse.rules)
    
        with self.assertRaises(TypeError):
            l_sumo_cse.add_rule('foo')
    
        l_vehicles = [
            colmto.environment.vehicle.SUMOVehicle(
                environment={'gridlength': 200, 'gridcellwidth': 4},
                speed_max=random.randrange(0, 250)
            ) for _ in range(1000)
        ]
    
        for i_vehicle in l_vehicles:
            i_vehicle.position = (random.randrange(0, 120), random.randint(0, 1))
    
        l_sumo_cse.apply(l_vehicles)
    
        for i_vehicle in l_vehicles:
            if 0 <= i_vehicle.position.x <= 64.0 and 0 <= i_vehicle.position.y <= 1 and \
                    i_vehicle.speed_max >= 80.0:
                self.assertEqual(
                    i_vehicle.vehicle_class,
                    colmto.cse.rule.SUMORule.to_allowed_class()
                )
            else:
                self.assertEqual(
                    i_vehicle.vehicle_class,
                    colmto.cse.rule.SUMORule.to_disallowed_class()
                )
    
        self.assertEqual(
            len(colmto.cse.cse.SumoCSE().add_rules_from_cfg({}).rules),
            0
        )
    
        l_sumo_cse = colmto.cse.cse.SumoCSE().add_rules_from_cfg(
            [
                {
                    'type': 'ExtendableSUMOPositionRule',
                    'args': {
                        'bounding_box': ((1350., -2.), (2500., 2.))
                    },
                    'subrule_operator': 'ANY',
                    'subrules': [
                        {
                            'type': 'SUMOMinimalSpeedRule',
                            'args': {
                                'minimal_speed': 85/3.6
                            },
                        }
                    ]
                }
            ]
        )
    
        self.assertIsInstance(tuple(l_sumo_cse.rules)[0], colmto.cse.rule.ExtendableSUMOPositionRule)
    
        # self.assertIsInstance(tuple(tuple(l_sumo_cse.rules)[0].subrules)[0], colmto.cse.rule.SUMOMinimalSpeedRule)
    
        l_rule_speed = colmto.cse.rule.SUMOMinimalSpeedRule.from_configuration(
            {
                'type': 'SUMOMinimalSpeedRule',
                'args': {
                    'minimal_speed': 30/3.6
                }
            }
        )
    
        l_sumo_cse.add_rule(
            l_rule_speed
        )
    
        self.assertIn(l_rule_speed, l_sumo_cse.rules)


if __name__ == '__main__':
    unittest.main()
