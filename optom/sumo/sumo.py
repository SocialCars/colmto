# -*- coding: utf-8 -*-
from __future__ import print_function

from configuration.sumocfg import SumoConfig
from sumolib import checkBinary

from runtime.runtime import Runtime
from common.visualisation import Visualisation
from common.resultswriter import ResultsWriter
from common.statistics import Statistics

import os

class Sumo(object):

    def __init__(self, p_args):
        self._visualisation = Visualisation()
        self._resultswriter = ResultsWriter()
        self._statistics = Statistics()
        self._allscenarioruns = {} # map scenarios -> runid -> files
        self._sumocfg = SumoConfig(p_args, self._visualisation, checkBinary("netconvert"), checkBinary("duarouter"))
        self._runtime = Runtime(self._sumocfg, self._visualisation,
                                        checkBinary("sumo")
                                            if self._sumocfg.get("headless")
                                            else checkBinary("sumo-gui"))


    def _runScenario(self, p_scenarioname):
        if self._sumocfg.getScenarioConfig().get(p_scenarioname) == None:
            print("/!\ scenario {} not found in configuration".format(p_scenarioname))
            return

        self._allscenarioruns[p_scenarioname] = l_scenarioruns = self._sumocfg.generateScenario(p_scenarioname)

        for i_initialsorting in self._sumocfg.getRunConfig().get("initialsortings"):

            l_scenarioruns.get("runs")[i_initialsorting] = {}

            for i_run in xrange(self._sumocfg.getRunConfig().get("runs")):
                l_run = self._sumocfg.generateRun(l_scenarioruns, i_initialsorting, i_run)
                self._runtime.run(l_run)

        # dump scenarioruns to yaml.gz file
        self._resultswriter.writeYAML(l_scenarioruns, os.path.join(self._sumocfg.getSUMOConfigDir(), "runs-{}.yaml.gz".format(p_scenarioname)))

        # do statistics
        l_stats = self._statistics.computeSUMOResults(p_scenarioname, l_scenarioruns, p_queries=["duration","timeLoss"])

        # dump statistic results to yaml.gz file
        self._resultswriter.writeYAML(l_stats, os.path.join(self._sumocfg.getSUMOConfigDir(), "results-{}.yaml.gz".format(p_scenarioname)))

        self._visualisation.boxplot(os.path.join(self._sumocfg.getSUMOConfigDir(), "Traveltime-{}_{}_vehicles_{}runs_one21segment.{}".format(p_scenarioname, l_stats.get("nbvehicles"), l_stats.get("nbruns"), "pdf")),
                                    l_stats.get("data").get("duration"),
                                    "{}: Travel time for \n{} vehicles, {} runs for each mode, one 2+1 segment".format(p_scenarioname, l_stats.get("nbvehicles"), l_stats.get("nbruns")),
                                    "initial ordering of vehicles\n(maximum speed)",
                                    "travel time in seconds"
                                    )
        self._visualisation.boxplot(os.path.join(self._sumocfg.getSUMOConfigDir(), "TimeLoss-{}_{}_vehicles_{}runs_one21segment.{}".format(p_scenarioname, l_stats.get("nbvehicles"), l_stats.get("nbruns"), "pdf")),
                                    l_stats.get("data").get("timeLoss"),
                                    "{}: Time loss for \n{} vehicles, {} runs for each mode, one 2+1 segment".format(p_scenarioname, l_stats.get("nbvehicles"), l_stats.get("nbruns")),
                                    "initial ordering of vehicles\n(maximum speed)",
                                    "time loss in seconds"
                                    )


    def runScenarios(self):
        for i_scenarioname in self._sumocfg.getRunConfig().get("scenarios"):
            self._runScenario(i_scenarioname)