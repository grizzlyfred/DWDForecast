#!/usr/bin/env python3
from dwdpro2flux import *
from my_dwdforecast import dwdfc

if __name__ == "__main__":
    myForeCast  = dwdfc()
    myFluxFcGet = FluxForeCastGetter()
    myFluxes    = FluxMaker( myFluxFcGet.data)
    myPusher    = FluxPusher()
