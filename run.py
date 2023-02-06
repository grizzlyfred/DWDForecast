#!/bin/python
import dwdpro2flux
import my-dwdforecast

if __name__ == "__main__":
    myForeCast  = dwdforecast()
    myFluxFcGet = FluxForeCastGetter()
    myFluxes    = FluxMaker( myFluxFcGet.data)
    myPusher    = FluxPusher()