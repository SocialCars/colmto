# -*- coding: utf-8 -*-
# @package colmto.sumo
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
'''Runtime to control SUMO.'''


import os
import subprocess
import sys
import typing

from colmto.environment.vehicle import SUMOVehicle

import colmto.common.io
import colmto.common.log
import colmto.cse.cse
import colmto.cse.rule

try:
    sys.path.append(os.path.join('sumo', 'tools'))
    sys.path.append(os.path.join(os.environ.get('SUMO_HOME', os.path.join('..', '..')), 'tools'))
    import traci
except ImportError:  # pragma: no cover
    raise ImportError('please declare environment variable \'SUMO_HOME\' as the root')


class Runtime(object):
    '''Runtime class'''

    def __init__(self, args, sumo_config, sumo_binary):
        '''Initialisation.'''
        self._args = args
        self._sumo_config = sumo_config
        self._sumo_binary = sumo_binary
        self._log = colmto.common.log.logger(__name__, args.loglevel, args.quiet, args.logfile)

    def run_standalone(self, run_config: dict):
        '''
        Run provided scenario in one shot.

        :param run_config: run configuration object
        '''

        self._log.info(
            'Running scenario %s: run %d',
            run_config.get('scenarioname'), run_config.get('runnumber')
        )

        l_sumoprocess = subprocess.check_output(
            [
                self._sumo_binary,
                '-c', run_config.get('configfile'),
                '--gui-settings-file', run_config.get('settingsfile'),
                '--time-to-teleport', '-1',
                '--no-step-log',
                '--fcd-output', run_config.get('fcdfile')
            ],
            stderr=subprocess.STDOUT,
            bufsize=-1
        )

        self._log.debug(
            '%s : %s',
            self._sumo_binary,
            l_sumoprocess.decode('utf8').replace('\n', '')
        )

    def run_traci(self, run_config: dict, cse: colmto.cse.cse.SumoCSE) -> typing.Dict[str, SUMOVehicle]:
        '''
        Run provided scenario with TraCI by providing a ref to an optimisation entity and execute the CSE protocol.

        *CSE protocol*

            1. observe traffic
            2. apply active policy, i.e. rules on vehicles:
               Tell vehicles whether they are allowed to use OTL or not

        :param run_config: run configuration
        :param cse: central optimisation entity instance of colmto.cse.cse.SumoCSE

        :return: list of vehicles, containing travel stats
        '''

        if not isinstance(cse, colmto.cse.cse.SumoCSE):
            raise AttributeError('Provided CSE object is not of type SumoCSE.')

        self._log.debug('starting sumo process')
        self._log.debug('CSE %s with rules %s', cse, cse.rules)
        l_traci_start = traci.start(
            [
                self._sumo_binary,
                '-c', run_config.get('configfile'),
                '--gui-settings-file', run_config.get('settingsfile'),
                '--time-to-teleport', '-1',
                '--no-step-log'
            ]
        )

        self._log.debug('subscribing to TraCI')

        # subscribe to global simulation vars
        traci.simulation.subscribe(
            (
                traci.constants.VAR_TIME_STEP,
                traci.constants.VAR_DEPARTED_VEHICLES_IDS,
                traci.constants.VAR_ARRIVED_VEHICLES_IDS,
                traci.constants.VAR_MIN_EXPECTED_VEHICLES,
            )
        )

        # subscribe to lane stats to allow CSE to 'observe' traffic
        traci.lane.subscribe(
            '21edge_0',
            (
                traci.constants.LAST_STEP_OCCUPANCY,
            )
        )
        traci.lane.subscribe(
            '21edge_1',
            (
                traci.constants.LAST_STEP_OCCUPANCY,
            )
        )

        # provide CSE with traci reference
        cse.traci(traci)

        # add polygon of otl denied positions if --gui enabled
        # and cse contains instance objects of colmto.cse.rule.SUMOPositionRule
        if self._args.gui:
            for i_rule in cse.rules:
                if isinstance(i_rule, colmto.cse.rule.SUMOPositionRule):
                    traci.polygon.add(
                        polygonID=str(i_rule),
                        shape=(
                            (i_rule.bounding_box.p1.x, 2 * (i_rule.bounding_box.p1.y) + 10),
                            (i_rule.bounding_box.p2.x, 2 * (i_rule.bounding_box.p1.y) + 10),
                            (i_rule.bounding_box.p2.x, 2 * (i_rule.bounding_box.p2.y) + 10),
                            (i_rule.bounding_box.p1.x, 2 * (i_rule.bounding_box.p2.y) + 10)
                        ),
                        color=(255, 0, 0, 255),
                        fill=True,
                    )

        # initial fetch of subscription results
        l_simulation_subscription_results = traci.simulation.getSubscriptionResults()

        # main loop through traci driven simulation runs
        while l_simulation_subscription_results.get(traci.constants.VAR_MIN_EXPECTED_VEHICLES) > 0:

            # set initial attribute start_time of newly entering vehicles
            # and subscribe to parameters
            for i_vehicle_id in l_simulation_subscription_results.get(traci.constants.VAR_DEPARTED_VEHICLES_IDS):
                # set TraCI -> vehicle.start_time
                run_config.get('vehicles').get(i_vehicle_id).start_time = l_simulation_subscription_results.get(traci.constants.VAR_TIME_STEP)/1000.
                # subscribe to parameters
                traci.vehicle.subscribe(
                    i_vehicle_id, (
                        traci.constants.VAR_POSITION,
                        traci.constants.VAR_LANE_INDEX,
                        traci.constants.VAR_VEHICLECLASS,
                        traci.constants.VAR_MAXSPEED,
                        traci.constants.VAR_SPEED
                    )
                )
                # set TraCI -> vehicle.start_position
                run_config.get('vehicles').get(i_vehicle_id).start_position = traci.vehicle.getSubscriptionResults(i_vehicle_id).get(traci.constants.VAR_POSITION)


            # retrieve vehicle subscription results
            l_vehicle_subscription_results = traci.vehicle.getSubscriptionResults()

            # retrieve results and update vehicle objects
            for i_vehicle_id, i_results in l_vehicle_subscription_results.items():
                # update vehicle position, speed and pass timestep to let vehicle calculate statistics
                run_config.get('vehicles').get(i_vehicle_id).update(
                    i_results.get(traci.constants.VAR_POSITION),
                    i_results.get(traci.constants.VAR_LANE_INDEX),
                    i_results.get(traci.constants.VAR_SPEED),
                    l_simulation_subscription_results.get(traci.constants.VAR_TIME_STEP)/1000.
                )

            # BEGIN CSE protocol
            # 1. CSE observes traffic
            cse.observe_traffic(
                traci.lane.getSubscriptionResults(),
                l_vehicle_subscription_results,
                run_config.get('vehicles')
            )
            # 2. apply active policy, i.e. rules on vehicles:
            # Tell CSE to tell vehicles whether they are allowed to use OTL or not
            for i_vehicle_id in l_vehicle_subscription_results:
                cse.apply_one(run_config.get('vehicles').get(i_vehicle_id))
            # END CSE protocol

            traci.simulationStep()

            # fetch new results for next simulation step/cycle
            l_simulation_subscription_results = traci.simulation.getSubscriptionResults()

        traci.close()

        self._log.info(
            'TraCI run of scenario %s, run %d completed.',
            run_config.get('scenarioname'), run_config.get('runnumber')
        )
        if self._args is not None and self._args.writefulloccupancies:
            self._log.info(
                'Writing occupancy stats to %s',
                self._sumo_config.resultsdir/f'occupancy-{run_config.get("runnumber")}-{run_config.get("initialsorting")}.json'
            )
            colmto.common.io.Writer().write_json(
                dict(cse.occupancy()),
                self._sumo_config.resultsdir/f'occupancy-{run_config.get("runnumber")}-{run_config.get("initialsorting")}.json'
            )

        return run_config.get('vehicles')

    # pylint: enable=too-few-public-methods
