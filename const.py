from enum import Enum


class Commodities(Enum):
    ENERGY = {
        "Crude Oil": "CL=F",
        "Natural Gas": "NG=F",
        "Brent": "BZ=F",
        "Gasoline": "RB=F",
        "Heating Oil": "HO=F",
        "Coal": "MTF=F",
        "TTF Gas": "TTF=F",
        "UK Gas": "UKGAS=F",
        "Ethanol": "ETH=F",
        "Naphtha": "NPH=F",
        "Uranium": "UX=F",
        "Propane": "PROPANE=F",
        "Methanol": "MEOH=F",
        "Urals Oil": "URAL=F"
    }

    METALS = {
        "Gold": "GC=F",
        "Silver": "SI=F",
        "Copper": "HG=F",
        "Steel": "STL=F",
        "Iron Ore": "IRO=F",
        "Lithium": "LTH=F",
        "Platinum": "PL=F",
        "Titanium": "TIT=F",
        "HRC Steel": "HRC=F"
    }

    AGRICULTURE = {
        "Soyabean": "ZS=F",
        "Wheat": "ZW=F",
        "Lumber": "LB=F",
        "Palm Oil": "PML=F",
        "Cheese": "CHS=F",
        "Milk": "MLK=F",
        "Rubber": "RB=F",
        "Orange Juice": "OJ=F",
        "Coffee": "KC=F",
        "Cotton": "CT=F",
        "Cocoa": "CC=F",
        "Rice": "ZR=F",
        "Canola": "RS=F",
        "Oat": "ZO=F",
        "Wool": "WOL=F",
        "Sugar": "SB=F",
        "Tea": "TEA=F",
        "Sunflower Oil": "SUN=F",
        "Rapeseed": "RAP=F",
        "Butter": "BTR=F",
        "Potatoes": "POT=F",
        "Corn": "ZC=F"
    }

