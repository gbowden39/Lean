 # QUANTCONNECT.COM - Democratizing Finance, Empowering Individuals.
# Lean Algorithmic Trading Engine v2.0. Copyright 2014 QuantConnect Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from clr import AddReference
AddReference("System")
AddReference("QuantConnect.Algorithm")
AddReference("QuantConnect.Indicators")
AddReference("QuantConnect.Common")

from System import *
from QuantConnect import *
from QuantConnect.Algorithm import *
from QuantConnect.Indicators import *
from QuantConnect.Data import SubscriptionDataSource
from QuantConnect.Python import PythonData
from datetime import date, timedelta, datetime
import numpy as np
import math
import json


### <summary>
### Strategy example algorithm using CAPE - a bubble indicator dataset saved in dropbox. CAPE is based on a macroeconomic indicator(CAPE Ratio),
### we are looking for entry/exit points for momentum stocks CAPE data: January 1990 - December 2014
### Goals:
### Capitalize in overvalued markets by generating returns with momentum and selling before the crash
### Capitalize in undervalued markets by purchasing stocks at bottom of trough
### </summary>
### <meta name="tag" content="strategy example" />
### <meta name="tag" content="custom data" />
class CAPEAlgorithm(QCAlgorithm):

    def Initialize(self):

        self.SetCash(100000)
        self.SetStartDate(1935,6,30)
        # self.SetStartDate(2018,6,30)
        self.SetEndDate(2019,5,1)
        self._symbols = []
        self._currCape = None
        self._symbols.append("SPX")
        # add CAPE data
        self.AddData(Cape, "CAPE")
        self.rebal_flag = True
        
        for stock in self._symbols:
            self.AddSecurity(SecurityType.Equity, stock, Resolution.Daily)
        # Set reblancing schedule as monthly    
        self.Schedule.On(self.DateRules.MonthEnd("SPX"), self.TimeRules.AfterMarketOpen("SPX"), Action(self.Rebalancing))

        # Note need to set benchmark after adding data!
        self.SetBenchmark("SPX")

    def OnData(self, data):
        
        if self._currCape is not None:   
            try:
                # Check if it is the start of the month and if so, rebalance
                if self.rebal_flag:
                    weight = 1 - self._currCape
                    # Set upper and lower bounds
                    if weight < 0.5: weight = 0.5
                    if weight > 1.5: weight = 1.5
                    for stock in self._symbols:
                        self.SetHoldings(stock, weight)
                        s = self.Securities[stock].Holdings
                        self.Debug("Rebalancing: " + str(stock)
                            + "   Price: " + str(round(self.Securities[stock].Price, 2)) + "   Weight: " + str(weight) 
                            + "   Quantity: " + str(s.Quantity) + " on " + str(self.Time))
                    self.rebal_flag = False # Turn off rebal flag 

                
            except:
                # Do nothing
                return None       

        if not data.ContainsKey("CAPE"): return
        self._currCape = data["CAPE"].Cape
        self.Debug("Current CAPE: " + str(self._currCape) + " on " + str(self.Time))

    def Rebalancing(self):
        self.rebal_flag = True  
        # self.Debug("Time for Rebal:" + str(self.Time))

# CAPE Ratio for SP500 PE Ratio for avg inflation adjusted earnings for previous ten years Custom Data
class Cape(PythonData):
    
    # Return the URL string source of the file. This will be converted to a stream
    # <param name="config">Configuration object</param>
    # <param name="date">Date of this source file</param>
    # <param name="isLiveMode">true if we're in live mode, false for backtesting mode</param>
    # <returns>String URL of source file.</returns>

    def GetSource(self, config, date, isLiveMode):
        import os
        # return SubscriptionDataSource("/Users/gavin/Dropbox/Data/Daily/cape_data.csv", SubscriptionTransportMedium.RemoteFile)
        # Don't forget to add the ?download=1 to end of URL to make the link direct downloadable
        fn = os.environ['HOME'] + '/OneDrive - Funds_SA/Data/Daily/' + 'cape_data.csv'
        # fn = "/Users/gavin/Dropbox/Data/Daily/cape_data.csv"
        # return SubscriptionDataSource("https://fundssa-my.sharepoint.com/:x:/g/personal/gavin_bowden_funds_sa_gov_au/EbCe5isidyZIoQPhp72v7I8BxYJHbp0vzLJ7hPGu2oBYBg?download=1", SubscriptionTransportMedium.RemoteFile)
        return SubscriptionDataSource(fn, SubscriptionTransportMedium.RemoteFile)

    
    ''' Reader Method : using set of arguments we specify read out type. Enumerate until 
        the end of the data stream or file. E.g. Read CSV file line by line and convert into data types. '''
        
    # <returns>BaseData type set by Subscription Method.</returns>
    # <param name="config">Config.</param>
    # <param name="line">Line.</param>
    # <param name="date">Date.</param>
    # <param name="isLiveMode">true if we're in live mode, false for backtesting mode</param>
    
    def Reader(self, config, line, date, isLiveMode):
        if not (line.strip() and line[0].isdigit()): return None
    
        # New CAPE object
        index = Cape()
        index.Symbol = config.Symbol
    
        try:
            data = line.split(',')
            index.Time = datetime.strptime(data[0], "%Y-%m-%d")
            index["Cape"] = float(data[16]) 
            index.Value = data[16]
            
    
        except ValueError:
                # Do nothing
                return None
    
        return index