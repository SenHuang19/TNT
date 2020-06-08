# -*- coding: utf-8 -*- {{{
# vim: set fenc=utf-8 ft=python sw=4 ts=4 sts=4 et:

# Copyright (c) 2017, Battelle Memorial Institute
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# 'AS IS' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# The views and conclusions contained in the software and documentation
# are those of the authors and should not be interpreted as representing
# official policies, either expressed or implied, of the FreeBSD
# Project.
#
# This material was prepared as an account of work sponsored by an
# agency of the United States Government.  Neither the United States
# Government nor the United States Department of Energy, nor Battelle,
# nor any of their employees, nor any jurisdiction or organization that
# has cooperated in the development of these materials, makes any
# warranty, express or implied, or assumes any legal liability or
# responsibility for the accuracy, completeness, or usefulness or any
# information, apparatus, product, software, or process disclosed, or
# represents that its use would not infringe privately owned rights.
#
# Reference herein to any specific commercial product, process, or
# service by trade name, trademark, manufacturer, or otherwise does not
# necessarily constitute or imply its endorsement, recommendation, or
# favoring by the United States Government or any agency thereof, or
# Battelle Memorial Institute. The views and opinions of authors
# expressed herein do not necessarily state or reflect those of the
# United States Government or any agency thereof.
#
# PACIFIC NORTHWEST NATIONAL LABORATORY
# operated by BATTELLE for the UNITED STATES DEPARTMENT OF ENERGY
# under Contract DE-AC05-76RL01830

# }}}

from datetime import datetime, timedelta, date, time
from reference import code
from code.vertex import Vertex
from code.neighbor_model import Neighbor
from code.local_asset_model import LocalAsset
from code.market import Market
from code.time_interval import TimeInterval
from code.interval_value import IntervalValue
from code.measurement_type import MeasurementType
from code.TransactiveNode import TransactiveNode
from dateutil import parser
from code.timer import Timer

from code.helpers import *
from code.measurement_unit import MeasurementUnit
from code.meter_point import MeterPoint
from code.market_state import MarketState

from code.temperature_forecast_model import TemperatureForecastModel
from code.solar_pv_resource_model import SolarPvResource
from code.openloop_richland_load_predictor import OpenLoopRichlandLoadPredictor
from code.bulk_supplier_dc import BulkSupplier_dc
from code.transactive_record import TransactiveRecord
from code.vertex import Vertex

from code.read_config import read_config

city_market = TransactiveNode()
city_config=read_config('../config/city_config')
market_cycle_in_min = int(city_config['market_cycle_in_min'])
duality_gap_threshold = float(city_config['duality_gap_threshold'])
supplier_loss_factor = float(city_config['supplier_loss_factor'])
demand_threshold_coef = float(city_config['demand_threshold_coef'])
monthly_peak_power = float(city_config['monthly_peak_power'])

simulation = city_config['simulation']
simulation_start_time = parser.parse(city_config['simulation_start_time'])
simulation_one_hour_in_seconds = int(city_config['simulation_one_hour_in_seconds'])

Timer.created_time = datetime.now()
Timer.simulation = simulation
Timer.sim_start_time = simulation_start_time
Timer.sim_one_hr_in_sec = simulation_one_hour_in_seconds

meter = MeterPoint()
meter.measurementType = MeasurementType.PowerReal
meter.name = 'CoRElectricMeter'
meter.measurementUnit = MeasurementUnit.kWh
city_market.meterPoints.append(meter)

# Add weather forecast service
config={'weather_file':city_config['weather_forecast']['weather_file']}
weather_service = TemperatureForecastModel(config)
city_market.informationServiceModels.append(weather_service)

# Add uncontrollable model
inelastive_load = LocalAsset()
inelastive_load.name = 'InelasticLoad'
inelastive_load.maximumPower = -50000  # Remember that a load is a negative power [kW]
inelastive_load.minimumPower = -200000  # Assume twice the average PNNL load [kW]
inelastive_load_model = OpenLoopRichlandLoadPredictor(weather_service)
inelastive_load_model.name = 'InelasticLoadModel'
inelastive_load_model.defaultPower = -100420  # [kW]
inelastive_load_model.defaultVertices = [Vertex(float("inf"), 0.0, -100420.0)]
inelastive_load_model.object = inelastive_load
inelastive_load.model = inelastive_load_model
city_market.localAssets.extend([inelastive_load])

# Add Market
market = Market()
market.name = 'dayAhead'
market.commitment = False
market.converged = False
market.defaultPrice = 0.0428  # [$/kWh]
market.dualityGapThreshold = duality_gap_threshold  # [0.02 = 2#]
market.initialMarketState = MarketState.Inactive
market.marketOrder = 1  # This is first and only market
market.intervalsToClear = 1  # Only one interval at a time
market.futureHorizon = timedelta(hours=24)  # Projects 24 hourly future intervals
market.intervalDuration = timedelta(hours=1)  # [h] Intervals are 1 h long
market.marketClearingInterval = timedelta(hours=1)  # [h]
market.marketClearingTime = Timer.get_cur_time().replace(hour=0,
                                                         minute=0,
                                                         second=0,
                                                         microsecond=0)  # Aligns with top of hour
market.nextMarketClearingTime = market.marketClearingTime + timedelta(hours=1)
city_market.markets.append(market)

# Add Campus
campus_model = Neighbor()
campus_model.name = 'PNNL_Campus_Model'

campus_model.defaultPower = -10000  # [avg.kW]
campus_model.defaultVertices = [Vertex(0.045, 0.0, -10000.0)]
campus_model.transactive = True
campus_model.maximumPower = 0.0  # Remember loads have negative power [avg.kW]
campus_model.minimumPower = -20000  # [avg.kW]

# Add Supplier
supplierModel = BulkSupplier_dc()
supplierModel.name = 'BPA'
        #supplierModel.demandThreshold = 0.75 * supplier.maximumPower
supplierModel.converged = False  # Dynamically assigned
supplierModel.convergenceThreshold = 0  # Not yet implemented
supplierModel.effectiveImpedance = 0.0  # Not yet implemented
supplierModel.friend = False  # Separate business entity from COR

supplierModel.transactive = False  # Not a transactive neighbor
supplierModel.demand_threshold_coef = demand_threshold_coef
supplierModel.demandThreshold = monthly_peak_power
supplierModel.lossFactor = supplier_loss_factor
supplierModel.maximumPower = 200800  # [avg.kW, twice the average COR load]
supplierModel.minimumPower = 0.0  # [avg.kW, will not export]

# Add vertices
# The first default vertex is, for now, based on the flat COR rate to
# PNNL. The second vertex includes 2# losses at a maximum power that
# is twice the average electric load for COR. This is helpful to
 # ensure that a unique price, power point will be found. In this
# model the recipient pays the cost of energy losses.
# The first vertex is based on BPA Jan HLH rate at zero power
# importation.
d1 = Vertex(0, 0, 0)  # create first default vertex
d1.marginalPrice = 0.04196  # HLH BPA rate Jan 2018 [$/kWh]
d1.cost = 2000.0  # Const. price shift to COR customer rate [$/h]
d1.power = 0.0  # [avg.kW]
# The second default vertex represents imported and lost power at a power
# value presumed to be the maximum deliverable power from BPA to COR.
d2 = Vertex(0, 0, 0)  # create second default vertex
# COR pays for all sent power but receives an amount reduced by
# losses. This creates a quadratic term in the production cost and
# a slope to the marginal price curve.
d2.marginalPrice = d1.marginalPrice / (1 - supplierModel.lossFactor)  # [$/kWh]
# From the perspective of COR, it receives the power sent by BPA,
# less losses.
d2.power = (1 - supplierModel.lossFactor) * supplierModel.maximumPower  # [avg.kW]
# The production costs can be estimated by integrating the
# marginal-price curve.
d2.cost = d1.cost + d2.power * (d1.marginalPrice + 0.5 * (d2.marginalPrice - d1.marginalPrice))  # [$/h]
supplierModel.defaultVertices = [d1, d2]


supplierModel.costParameters[0] = 2000.0  # [$/h]

bpaElectricityMeter = MeterPoint()  # Instantiate an electricity meter
bpaElectricityMeter.name = 'BpaElectricityMeter'
bpaElectricityMeter.description = 'BPA electricity to COR'
bpaElectricityMeter.measurementType = MeasurementType.PowerReal
bpaElectricityMeter.measurementUnit = MeasurementUnit.kWh
supplierModel.meterPoints = [bpaElectricityMeter]

# Add campus and supplier as city's neighbor
city_market.neighbors.extend([campus_model, supplierModel])


