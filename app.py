from flask import Flask, render_template_string, request
import yfinance as yf
import pandas as pd
import os
import time

app = Flask(__name__)

STATE_FILE_TEMPLATE = "last_signal_state_{}_{}.txt"  # Symbol + timeframe

# Caching globals
price_cache = {}
price_cache_time = {}
PRICE_CACHE_TTL = 120  # seconds

ohlc_cache = {}
ohlc_cache_time = {}
OHLC_CACHE_TTL = 900  # seconds

STOCK_LIST= [
    ("RELIANCE.BO", "Reliance Industries Limited"),
    ("RELIANCE.NS", "Reliance Industries Limited"),
    ("HDFCBANK.BO", "HDFC Bank Limited"),
    ("HDFCBANK.NS", "HDFC Bank Limited"),
    ("TCS.BO", "Tata Consultancy Services Limited"),
    ("TCS.NS", "Tata Consultancy Services Limited"),
    ("BHARTIARTL.BO", "Bharti Airtel Limited"),
    ("BHARTIARTL.NS", "Bharti Airtel Limited"),
    ("ICICIBANK.BO", "ICICI Bank Limited"),
    ("ICICIBANK.NS", "ICICI Bank Limited"),
    ("SBIN.BO", "State Bank of India"),
    ("SBIN.NS", "State Bank of India"),
    ("INFY.BO", "Infosys Limited"),
    ("INFY.NS", "Infosys Limited"),
    ("BAJFINANCE.BO", "Bajaj Finance Limited"),
    ("BAJFINANCE.NS", "Bajaj Finance Limited"),
    ("HINDUNILVR.BO", "Hindustan Unilever Limited"),
    ("HINDUNILVR.NS", "Hindustan Unilever Limited"),
    ("ITC.NS", "ITC Limited"),
    ("ITC.BO", "ITC Limited"),
    ("LICI.NS", "Life Insurance Corporation of India"),
    ("LICI.BO", "Life Insurance Corporation of India"),
    ("LT.NS", "Larsen & Toubro Limited"),
    ("LT.BO", "Larsen & Toubro Limited"),
    ("HCLTECH.BO", "HCL Technologies Limited"),
    ("HCLTECH.NS", "HCL Technologies Limited"),
    ("KOTAKBANK.NS", "Kotak Mahindra Bank Limited"),
    ("KOTAKBANK.BO", "Kotak Mahindra Bank Limited"),
    ("SUNPHARMA.BO", "Sun Pharmaceutical Industries Limited"),
    ("SUNPHARMA.NS", "Sun Pharmaceutical Industries Limited"),
    ("MARUTI.BO", "Maruti Suzuki India Limited"),
    ("MARUTI.NS", "Maruti Suzuki India Limited"),
    ("AXISBANK.NS", "Axis Bank Limited"),
    ("AXISBANK.BO", "Axis Bank Limited"),
    ("M&M.BO", "Mahindra & Mahindra Limited"),
    ("M&M.NS", "Mahindra & Mahindra Limited"),
    ("ULTRACEMCO.NS", "UltraTech Cement Limited"),
    ("ULTRACEMCO.BO", "UltraTech Cement Limited"),
    ("NTPC.NS", "NTPC Limited"),
    ("NTPC.BO", "NTPC Limited"),
    ("HAL.NS", "Hindustan Aeronautics Limited"),
    ("HAL.BO", "Hindustan Aeronautics Limited"),
    ("BAJAJFINSV.NS", "Bajaj Finserv Ltd."),
    ("BAJAJFINSV.BO", "Bajaj Finserv Ltd."),
    ("TITAN.BO", "Titan Company Limited"),
    ("TITAN.NS", "Titan Company Limited"),
    ("ONGC.NS", "Oil and Natural Gas Corporation Limited"),
    ("ONGC.BO", "Oil and Natural Gas Corporation Limited"),
    ("ADANIPORTS.NS", "Adani Ports and Special Economic Zone Limited"),
    ("ADANIPORTS.BO", "Adani Ports and Special Economic Zone Limited"),
    ("ADANIENT.NS", "Adani Enterprises Limited"),
    ("ADANIENT.BO", "Adani Enterprises Limited"),
    ("POWERGRID.NS", "Power Grid Corporation of India Limited"),
    ("POWERGRID.BO", "Power Grid Corporation of India Limited"),
    ("BEL.NS", "Bharat Electronics Limited"),
    ("BEL.BO", "Bharat Electronics Limited"),
    ("DMART.NS", "Avenue Supermarts Limited"),
    ("DMART.BO", "Avenue Supermarts Limited"),
    ("TATAMOTORS.NS", "Tata Motors Limited"),
    ("TATAMOTORS.BO", "Tata Motors Limited"),
    ("WIPRO.NS", "Wipro Limited"),
    ("WIPRO.BO", "Wipro Limited"),
    ("COALINDIA.BO", "Coal India Limited"),
    ("COALINDIA.NS", "Coal India Limited"),
    ("JSWSTEEL.BO", "JSW Steel Limited"),
    ("JSWSTEEL.NS", "JSW Steel Limited"),
    ("BAJAJ-AUTO.NS", "Bajaj Auto Limited"),
    ("BAJAJ-AUTO.BO", "Bajaj Auto Limited"),
    ("NESTLEIND.BO", "Nestlé India Limited"),
    ("NESTLEIND.NS", "Nestlé India Limited"),
    ("ASIANPAINT.BO", "Asian Paints Limited"),
    ("ASIANPAINT.NS", "Asian Paints Limited"),
    ("ADANIPOWER.NS", "Adani Power Limited"),
    ("ADANIPOWER.BO", "Adani Power Limited"),
    ("INDIGO.BO", "InterGlobe Aviation Limited"),
    ("INDIGO.NS", "InterGlobe Aviation Limited"),
    ("IOC.BO", "Indian Oil Corporation Limited"),
    ("IOC.NS", "Indian Oil Corporation Limited"),
    ("TATASTEEL.NS", "Tata Steel Limited"),
    ("TATASTEEL.BO", "Tata Steel Limited"),
    ("TRENT.NS", "Trent Limited"),
    ("TRENT.BO", "Trent Limited"),
    ("DLF.NS", "DLF Limited"),
    ("DLF.BO", "DLF Limited"),
    ("HINDZINC.BO", "Hindustan Zinc Limited"),
    ("HINDZINC.NS", "Hindustan Zinc Limited"),
    ("GRASIM.BO", "Grasim Industries Limited"),
    ("GRASIM.NS", "Grasim Industries Limited"),
    ("IRFC.NS", "Indian Railway Finance Corporation Limited"),
    ("IRFC.BO", "Indian Railway Finance Corporation Limited"),
    ("SBILIFE.NS", "SBI Life Insurance Company Limited"),
    ("SBILIFE.BO", "SBI Life Insurance Company Limited"),
    ("JIOFIN.NS", "Jio Financial Services Limited"),
    ("JIOFIN.BO", "Jio Financial Services Limited"),
    ("DIVISLAB.NS", "Divi's Laboratories Limited"),
    ("DIVISLAB.BO", "Divi's Laboratories Limited"),
    ("VEDL.BO", "Vedanta Limited"),
    ("VEDL.NS", "Vedanta Limited"),
    ("VBL.BO", "Varun Beverages Limited"),
    ("VBL.NS", "Varun Beverages Limited"),
    ("HDFCLIFE.NS", "HDFC Life Insurance Company Limited"),
    ("HDFCLIFE.BO", "HDFC Life Insurance Company Limited"),
    ("ADANIGREEN.BO", "Adani Green Energy Limited"),
    ("ADANIGREEN.NS", "Adani Green Energy Limited"),
    ("HYUNDAI.BO", "HYUNDAI MOTOR INDIA LIMITED"),
    ("PIDILITIND.BO", "Pidilite Industries Limited"),
    ("HYUNDAI.NS", "HYUNDAI MOTOR INDIA LTD"),
    ("PIDILITIND.NS", "Pidilite Industries Limited"),
    ("LTIM.NS", "LTIMindtree Limited"),
    ("LTIM.BO", "LTIMindtree Limited"),
    ("EICHERMOT.BO", "Eicher Motors Limited"),
    ("EICHERMOT.NS", "Eicher Motors Limited"),
    ("HINDALCO.BO", "Hindalco Industries Limited"),
    ("HINDALCO.NS", "Hindalco Industries Limited"),
    ("BAJAJHLDNG.BO", "Bajaj Holdings & Investment Limited"),
    ("BAJAJHLDNG.NS", "Bajaj Holdings & Investment Limited"),
    ("TECHM.NS", "Tech Mahindra Limited"),
    ("TECHM.BO", "Tech Mahindra Limited"),
    ("AMBUJACEM.NS", "Ambuja Cements Limited"),
    ("AMBUJACEM.BO", "Ambuja Cements Limited"),
    ("LODHA.BO", "Macrotech Developers Limited"),
    ("LODHA.NS", "Macrotech Developers Limited"),
    ("BPCL.NS", "Bharat Petroleum Corporation Limited"),
    ("BPCL.BO", "Bharat Petroleum Corporation Limited"),
    ("CHOLAFIN.NS", "Cholamandalam Investment and Finance Company Limited"),
    ("CHOLAFIN.BO", "Cholamandalam Investment and Finance Company Limited"),
    ("PFC.BO", "Power Finance Corporation Limited"),
    ("PFC.NS", "Power Finance Corporation Limited"),
    ("BRITANNIA.BO", "Britannia Industries Limited"),
    ("BRITANNIA.NS", "Britannia Industries Limited"),
    ("TVSMOTOR.NS", "TVS Motor Company Limited"),
    ("TVSMOTOR.BO", "TVS Motor Company Limited"),
    ("GODREJCP.BO", "Godrej Consumer Products Limited"),
    ("GODREJCP.NS", "Godrej Consumer Products Limited"),
    ("TATAPOWER.NS", "The Tata Power Company Limited"),
    ("TATAPOWER.BO", "The Tata Power Company Limited"),
    ("GAIL.BO", "GAIL (India) Limited"),
    ("GAIL.NS", "GAIL (India) Limited"),
    ("BANKBARODA.NS", "Bank of Baroda Limited"),
    ("BANKBARODA.BO", "Bank of Baroda Limited"),
    ("SOLARINDS.BO", "Solar Industries India Limited"),
    ("SOLARINDS.NS", "Solar Industries India Limited"),
    ("ABB.NS", "ABB India Limited"),
    ("ABB.BO", "ABB India Limited"),
    ("CIPLA.NS", "Cipla Limited"),
    ("CIPLA.BO", "Cipla Limited"),
    ("PNB.BO", "Punjab National Bank"),
    ("PNB.NS", "Punjab National Bank"),
    ("SHREECEM.NS", "Shree Cement Limited"),
    ("SHREECEM.BO", "Shree Cement Limited"),
    ("MAXHEALTH.BO", "Max Healthcare Institute Limited"),
    ("UNITDSPR.BO", "United Spirits Limited"),
    ("MAXHEALTH.NS", "Max Healthcare Institute Limited"),
    ("UNITDSPR.NS", "UNITED SPIRITS LIMITED"),
    ("TATACONSUM.NS", "Tata Consumer Products Limited"),
    ("TATACONSUM.BO", "Tata Consumer Products Limited"),
    ("SIEMENS.BO", "Siemens Limited"),
    ("SIEMENS.NS", "Siemens Limited"),
    ("TORNTPHARM.BO", "Torrent Pharmaceuticals Limited"),
    ("TORNTPHARM.NS", "Torrent Pharmaceuticals Limited"),
    ("INDHOTEL.NS", "The Indian Hotels Company Limited"),
    ("INDHOTEL.BO", "The Indian Hotels Company Limited"),
    ("UNIONBANK.NS", "Union Bank of India"),
    ("CGPOWER.NS", "CG Power and Industrial Solutions Limited"),
    ("UNIONBANK.BO", "Union Bank of India"),
    ("CGPOWER.BO", "CG Power and Industrial Solutions Limited"),
    ("ADANIENSOL.NS", "Adani Energy Solutions Limited"),
    ("ADANIENSOL.BO", "Adani Energy Solutions Limited"),
    ("RECLTD.NS", "REC Limited"),
    ("RECLTD.BO", "REC Limited"),
    ("BAJAJHFL.BO", "Bajaj Housing Finance Limited"),
    ("BAJAJHFL.NS", "BAJAJ HOUSING FINANCE LTD"),
    ("MOTHERSON.BO", "Samvardhana Motherson International Limited"),
    ("MOTHERSON.NS", "Samvardhana Motherson International Limited"),
    ("MANKIND.NS", "Mankind Pharma Limited"),
    ("MANKIND.BO", "Mankind Pharma Limited"),
    ("DRREDDY.BO", "Dr. Reddy's Laboratories Limited"),
    ("HDFCAMC.BO", "HDFC Asset Management Company Limited"),
    ("DRREDDY.NS", "Dr. Reddy's Laboratories Limited"),
    ("INDUSTOWER.NS", "Indus Towers Limited"),
    ("INDUSTOWER.BO", "Indus Towers Limited"),
    ("HDFCAMC.NS", "HDFC Asset Management Company Limited"),
    ("BSE.NS", "BSE Limited"),
    ("DIXON.NS", "Dixon Technologies (India) Limited"),
    ("DIXON.BO", "Dixon Technologies (India) Limited"),
    ("APOLLOHOSP.BO", "Apollo Hospitals Enterprise Limited"),
    ("APOLLOHOSP.NS", "Apollo Hospitals Enterprise Limited"),
    ("IDBI.NS", "IDBI Bank Limited"),
    ("IDBI.BO", "IDBI Bank Limited"),
    ("HAVELLS.NS", "Havells India Limited"),
    ("HAVELLS.BO", "Havells India Limited"),
    ("CANBK.BO", "Canara Bank"),
    ("CANBK.NS", "Canara Bank"),
    ("JINDALSTEL.NS", "Jindal Steel & Power Limited"),
    ("JINDALSTEL.BO", "Jindal Steel & Power Limited"),
    ("BOSCHLTD.NS", "Bosch Limited"),
    ("ICICIGI.BO", "ICICI Lombard General Insurance Company Limited"),
    ("BOSCHLTD.BO", "Bosch Limited"),
    ("ICICIGI.NS", "ICICI Lombard General Insurance Company Limited"),
    ("MARICO.BO", "Marico Limited"),
    ("MARICO.NS", "Marico Limited"),
    ("POLYCAB.BO", "Polycab India Limited"),
    ("POLYCAB.NS", "Polycab India Limited"),
    ("LUPIN.NS", "Lupin Limited"),
    ("LUPIN.BO", "Lupin Limited"),
    ("ZYDUSLIFE.NS", "Zydus Lifesciences Limited"),
    ("ZYDUSLIFE.BO", "Zydus Lifesciences Limited"),
    ("ICICIPRULI.NS", "ICICI Prudential Life Insurance Company Limited"),
    ("ICICIPRULI.BO", "ICICI Prudential Life Insurance Company Limited"),
    ("JSWENERGY.NS", "JSW Energy Limited"),
    ("JSWENERGY.BO", "JSW Energy Limited"),
    ("SRF.NS", "SRF Limited"),
    ("SRF.BO", "SRF Limited"),
    ("NHPC.NS", "NHPC Limited"),
    ("NHPC.BO", "NHPC Limited"),
    ("NTPCGREEN.NS", "NTPC GREEN ENERGY LIMITED"),
    ("PERSISTENT.BO", "Persistent Systems Limited"),
    ("RVNL.NS", "Rail Vikas Nigam Limited"),
    ("PERSISTENT.NS", "Persistent Systems Limited"),
    ("RVNL.BO", "Rail Vikas Nigam Limited"),
    ("SBICARD.NS", "SBI Cards and Payment Services Limited"),
    ("SBICARD.BO", "SBI Cards and Payment Services Limited"),
    ("BHEL.BO", "Bharat Heavy Electricals Limited"),
    ("BHEL.NS", "Bharat Heavy Electricals Limited"),
    ("HEROMOTOCO.BO", "Hero MotoCorp Limited"),
    ("HEROMOTOCO.NS", "Hero MotoCorp Limited"),
    ("HINDPETRO.BO", "Hindustan Petroleum Corporation Limited"),
    ("HINDPETRO.NS", "Hindustan Petroleum Corporation Limited"),
    ("DABUR.BO", "Dabur India Limited"),
    ("DABUR.NS", "Dabur India Limited"),
    ("WAAREEENER.NS", "WAAREE ENERGIES LIMITED"),
    ("WAAREEENER.BO", "Waaree Energies Limited"),
    ("BHARTIHEXA.BO", "Bharti Hexacom Limited"),
    ("BHARTIHEXA.NS", "BHARTI HEXACOM LIMITED"),
    ("SUZLON.BO", "Suzlon Energy Limited"),
    ("SUZLON.NS", "Suzlon Energy Limited"),
    ("INDIANB.BO", "Indian Bank"),
    ("INDIANB.NS", "Indian Bank"),
    ("CUMMINSIND.NS", "Cummins India Limited"),
    ("CUMMINSIND.BO", "Cummins India Limited"),
    ("MUTHOOTFIN.BO", "Muthoot Finance Limited"),
    ("MUTHOOTFIN.NS", "Muthoot Finance Limited"),
    ("GICRE.BO", "General Insurance Corporation of India"),
    ("GICRE.NS", "General Insurance Corporation of India"),
    ("POLICYBZR.NS", "PB Fintech Limited"),
    ("POLICYBZR.BO", "PB Fintech Limited"),
    ("OFSS.BO", "Oracle Financial Services Software Limited"),
    ("OFSS.NS", "Oracle Financial Services Software Limited"),
    ("ATGL.BO", "Adani Total Gas Limited"),
    ("ATGL.NS", "Adani Total Gas Limited"),
    ("COLPAL.BO", "Colgate-Palmolive (India) Limited"),
    ("COLPAL.NS", "Colgate-Palmolive (India) Limited"),
    ("IOB.BO", "Indian Overseas Bank"),
    ("IOB.NS", "Indian Overseas Bank"),
    ("ASHOKLEY.BO", "Ashok Leyland Limited"),
    ("ASHOKLEY.NS", "Ashok Leyland Limited"),
    ("COROMANDEL.BO", "Coromandel International Limited"),
    ("COROMANDEL.NS", "Coromandel International Limited"),
    ("TORNTPOWER.BO", "Torrent Power Limited"),
    ("TORNTPOWER.NS", "Torrent Power Limited"),
    ("SWIGGY.BO", "SWIGGY LIMITED"),
    ("SWIGGY.NS", "SWIGGY LIMITED"),
    ("LLOYDSME.NS", "Lloyds Metals and Energy Limited"),
    ("LLOYDSME.BO", "Lloyds Metals and Energy Limited"),
    ("AUROPHARMA.NS", "Aurobindo Pharma Limited"),
    ("AUROPHARMA.BO", "Aurobindo Pharma Limited"),
    ("OIL.NS", "Oil India Limited"),
    ("OIL.BO", "Oil India Limited"),
    ("POWERINDIA.NS", "Hitachi Energy India Limited"),
    ("POWERINDIA.BO", "Hitachi Energy India Limited"),
    ("MAZDOCK.NS", "Mazagon Dock Shipbuilders Limited"),
    ("MAZDOCK.BO", "Mazagon Dock Shipbuilders Limited"),
    ("BDL.BO", "Bharat Dynamics Limited"),
    ("BDL.NS", "Bharat Dynamics Limited"),
    ("ABBOTINDIA.NS", "Abbott India Limited"),
    ("ABBOTINDIA.BO", "Abbott India Limited"),
    ("GODREJPROP.BO", "Godrej Properties Limited"),
    ("GODREJPROP.NS", "Godrej Properties Limited"),
    ("YESBANK.BO", "Yes Bank Limited"),
    ("YESBANK.NS", "Yes Bank Limited"),
    ("BERGEPAINT.BO", "Berger Paints India Limited"),
    ("BERGEPAINT.NS", "Berger Paints India Limited"),
    ("SCHAEFFLER.NS", "Schaeffler India Limited"),
    ("SCHAEFFLER.BO", "Schaeffler India Limited"),
    ("ALKEM.BO", "Alkem Laboratories Limited"),
    ("ALKEM.NS", "Alkem Laboratories Limited"),
    ("IRCTC.NS", "Indian Railway Catering & Tourism Corporation Limited"),
    ("IRCTC.BO", "Indian Railway Catering & Tourism Corporation Limited"),
    ("OBEROIRLTY.BO", "Oberoi Realty Limited"),
    ("PATANJALI.BO", "Patanjali Foods Limited"),
    ("PATANJALI.NS", "Patanjali Foods Limited"),
    ("OBEROIRLTY.NS", "Oberoi Realty Limited"),
    ("PRESTIGE.NS", "Prestige Estates Projects Limited"),
    ("PRESTIGE.BO", "Prestige Estates Projects Limited"),
    ("INDUSINDBK.NS", "IndusInd Bank Limited"),
    ("INDUSINDBK.BO", "IndusInd Bank Limited"),
    ("LINDEINDIA.NS", "Linde India Limited"),
    ("LINDEINDIA.BO", "Linde India Limited"),
    ("JSWINFRA.BO", "JSW Infrastructure Limited"),
    ("JSWINFRA.NS", "JSW Infrastructure Limited"),
    ("MRF.BO", "MRF Limited"),
    ("MRF.NS", "MRF Limited"),
    ("TIINDIA.NS", "Tube Investments of India Limited"),
    ("TIINDIA.BO", "Tube Investments of India Limited"),
    ("FACT.NS", "The Fertilisers and Chemicals Travancore Limited"),
    ("FACT.BO", "The Fertilisers and Chemicals Travancore Limited"),
    ("BHARATFORG.NS", "Bharat Forge Limited"),
    ("BHARATFORG.BO", "Bharat Forge Limited"),
    ("NYKAA.NS", "FSN E-Commerce Ventures Limited"),
    ("NYKAA.BO", "FSN E-Commerce Ventures Limited"),
    ("PIIND.NS", "PI Industries Limited"),
    ("PIIND.BO", "PI Industries Limited"),
    ("PHOENIXLTD.NS", "The Phoenix Mills Limited"),
    ("UNOMINDA.NS", "Uno Minda Limited"),
    ("PHOENIXLTD.BO", "The Phoenix Mills Limited"),
    ("SUNDARMFIN.BO", "Sundaram Finance Limited"),
    ("UNOMINDA.BO", "Uno Minda Limited"),
    ("KALYANKJIL.BO", "Kalyan Jewellers India Limited"),
    ("KALYANKJIL.NS", "Kalyan Jewellers India Limited"),
    ("SUNDARMFIN.NS", "Sundaram Finance Limited"),
    ("ABCAPITAL.NS", "Aditya Birla Capital Limited"),
    ("ABCAPITAL.BO", "Aditya Birla Capital Limited"),
    ("COFORGE.NS", "Coforge Limited"),
    ("COFORGE.BO", "Coforge Limited"),
    ("PAYTM.NS", "One97 Communications Limited"),
    ("PAYTM.BO", "One97 Communications Limited"),
    ("UBL.BO", "United Breweries Limited"),
    ("UBL.NS", "United Breweries Limited"),
    ("JSL.NS", "Jindal Stainless Limited"),
    ("BANKINDIA.BO", "Bank of India Limited"),
    ("BANKINDIA.NS", "Bank of India Limited"),
    ("JSL.BO", "Jindal Stainless Limited"),
    ("PAGEIND.BO", "Page Industries Limited"),
    ("PAGEIND.NS", "Page Industries Limited"),
    ("FORTIS.BO", "Fortis Healthcare Limited"),
    ("FORTIS.NS", "Fortis Healthcare Limited"),
    ("AUBANK.NS", "AU Small Finance Bank Limited"),
    ("BALKRISIND.BO", "Balkrishna Industries Limited"),
    ("BALKRISIND.NS", "Balkrishna Industries Limited"),
    ("AUBANK.BO", "AU Small Finance Bank Limited"),
    ("SAIL.NS", "Steel Authority of India Limited"),
    ("SAIL.BO", "Steel Authority of India Limited"),
    ("APLAPOLLO.NS", "APL Apollo Tubes Limited"),
    ("APLAPOLLO.BO", "APL Apollo Tubes Limited"),
    ("GVT&D.NS", "GE Vernova T&D India Limited"),
    ("UPL.NS", "UPL Limited"),
    ("UPL.BO", "UPL Limited"),
    ("IDFCFIRSTB.NS", "IDFC First Bank Limited"),
    ("IDFCFIRSTB.BO", "IDFC First Bank Limited"),
    ("FEDERALBNK.BO", "The Federal Bank Limited"),
    ("FEDERALBNK.NS", "The Federal Bank Limited"),
    ("MPHASIS.BO", "Mphasis Limited"),
    ("MPHASIS.NS", "Mphasis Limited"),
    ("PREMIERENE.BO", "Premier Energies Limited"),
    ("COCHINSHIP.NS", "Cochin Shipyard Limited"),
    ("COCHINSHIP.BO", "Cochin Shipyard Limited"),
    ("PREMIERENE.NS", "PREMIER ENERGIES LIMITED"),
    ("PETRONET.NS", "Petronet LNG Limited"),
    ("PETRONET.BO", "Petronet LNG Limited"),
    ("SUPREMEIND.NS", "The Supreme Industries Limited"),
    ("MFSL.NS", "Max Financial Services Limited"),
    ("LTTS.BO", "L&T Technology Services Limited"),
    ("MFSL.BO", "Max Financial Services Limited"),
    ("LTTS.NS", "L&T Technology Services Limited"),
    ("SUPREMEIND.BO", "The Supreme Industries Limited"),
    ("NAM-INDIA.BO", "Nippon Life India Asset Management Limited"),
    ("NAM-INDIA.NS", "Nippon Life India Asset Management Limited"),
    ("GLAXO.BO", "GlaxoSmithKline Pharmaceuticals Limited"),
    ("GLAXO.NS", "GlaxoSmithKline Pharmaceuticals Limited"),
    ("TATACOMM.NS", "Tata Communications Limited"),
    ("TATACOMM.BO", "Tata Communications Limited"),
    ("PGHH.NS", "Procter & Gamble Hygiene and Health Care Limited"),
    ("PGHH.BO", "Procter & Gamble Hygiene and Health Care Limited"),
    ("MOTILALOFS.NS", "Motilal Oswal Financial Services Limited"),
    ("MOTILALOFS.BO", "Motilal Oswal Financial Services Limited"),
    ("IDEA.BO", "Vodafone Idea Limited"),
    ("IDEA.NS", "Vodafone Idea Limited"),
    ("IREDA.NS", "Indian Renewable Energy Development Agency Limited"),
    ("IREDA.BO", "Indian Renewable Energy Development Agency Limited"),
    ("HUDCO.BO", "Housing and Urban Development Corporation Limited"),
    ("HUDCO.NS", "Housing and Urban Development Corporation Limited"),
    ("JUBLFOOD.NS", "Jubilant FoodWorks Limited"),
    ("GODFRYPHLP.NS", "Godfrey Phillips India Limited"),
    ("GODFRYPHLP.BO", "Godfrey Phillips India Limited"),
    ("JUBLFOOD.BO", "Jubilant FoodWorks Limited"),
    ("CONCOR.NS", "Container Corporation of India Limited"),
    ("CONCOR.BO", "Container Corporation of India Limited"),
    ("FLUOROCHEM.BO", "Gujarat Fluorochemicals Limited"),
    ("FLUOROCHEM.NS", "Gujarat Fluorochemicals Limited"),
    ("LTF.NS", "L&T Finance Limited"),
    ("LTF.BO", "L&T Finance Limited"),
    ("KPRMILL.NS", "K.P.R. Mill Limited"),
    ("KPRMILL.BO", "K.P.R. Mill Limited"),
    ("VOLTAS.BO", "Voltas Limited"),
    ("VOLTAS.NS", "Voltas Limited"),
    ("GLENMARK.BO", "Glenmark Pharmaceuticals Limited"),
    ("GLENMARK.NS", "Glenmark Pharmaceuticals Limited"),
    ("SJVN.BO", "SJVN Limited"),
    ("SJVN.NS", "SJVN Limited"),
    ("BIOCON.BO", "Biocon Limited"),

    ("BIOCON.NS", "Biocon Limited"),
    ("JKCEMENT.BO", "J.K. Cement Limited"),
    ("JKCEMENT.NS", "J.K. Cement Limited"),
    ("MAHABANK.NS", "Bank of Maharashtra"),
    ("THERMAX.BO", "Thermax Limited"),
    ("MAHABANK.BO", "Bank of Maharashtra"),
    ("THERMAX.NS", "Thermax Limited"),
    ("GODREJIND.BO", "Godrej Industries Limited"),
    ("GODREJIND.NS", "Godrej Industries Limited"),
    ("ESCORTS.NS", "Escorts Kubota Limited"),
    ("ESCORTS.BO", "Escorts Kubota Limited"),
    ("TATAELXSI.BO", "Tata Elxsi Limited"),
    ("TATAELXSI.NS", "Tata Elxsi Limited"),
    ("DALBHARAT.NS", "Dalmia Bharat Limited"),
    ("360ONE.NS", "360 One Wam Limited"),
    ("360ONE.BO", "360 One Wam Limited"),
    ("DALBHARAT.BO", "Dalmia Bharat Limited"),
    ("KAYNES.NS", "Kaynes Technology India Limited"),
    ("KAYNES.BO", "Kaynes Technology India Limited"),
    ("AIIL.NS", "Authum Investment & Infrastructure Limited"),
    ("AIIL.BO", "Authum Investment & Infrastructure Limited"),
    ("UCOBANK.BO", "UCO Bank"),
    ("UCOBANK.NS", "UCO Bank"),
    ("IPCALAB.NS", "Ipca Laboratories Limited"),
    ("EMBASSY.BO", "Embassy Office Parks REIT"),
    ("CRISIL.NS", "CRISIL Limited"),
    ("IPCALAB.BO", "Ipca Laboratories Limited"),
    ("CRISIL.BO", "CRISIL Limited"),
    ("ASTRAL.NS", "Astral Limited"),
    ("ASTRAL.BO", "Astral Limited"),
    ("ACC.BO", "ACC Limited"),
    ("ACC.NS", "ACC Limited"),
    ("KPITTECH.BO", "KPIT Technologies Limited"),
    ("KPITTECH.NS", "KPIT Technologies Limited"),
    ("NH.NS", "Narayana Hrudayalaya Limited"),
    ("NH.BO", "Narayana Hrudayalaya Limited"),
    ("CHOLAHLDNG.NS", "Cholamandalam Financial Holdings Limited"),
    ("CHOLAHLDNG.BO", "Cholamandalam Financial Holdings Limited"),
    ("RADICO.NS", "Radico Khaitan Limited"),
    ("RADICO.BO", "Radico Khaitan Limited"),
    ("AWL.NS", "AWL Agri Business Limited"),
    ("AWL.BO", "AWL Agri Business Limited"),
    ("NLCINDIA.BO", "NLC India Limited"),
    ("NLCINDIA.NS", "NLC India Limited"),
    ("BLUESTARCO.BO", "Blue Star Limited"),
    ("BLUESTARCO.NS", "Blue Star Limited"),
    ("KEI.BO", "KEI Industries Limited"),
    ("KEI.NS", "KEI Industries Limited"),
    ("3MINDIA.NS", "3M India Limited"),
    ("3MINDIA.BO", "3M India Limited"),
    ("NATIONALUM.BO", "National Aluminium Company Limited"),
    ("NATIONALUM.NS", "National Aluminium Company Limited"),
    ("HONAUT.NS", "Honeywell Automation India Limited"),
    ("HONAUT.BO", "Honeywell Automation India Limited"),
    ("SONACOMS.BO", "Sona BLW Precision Forgings Limited"),
    ("AEGISLOG.BO", "Aegis Logistics Limited"),
    ("AEGISLOG.NS", "AEGIS LOGISTICS LIMITED"),
    ("EXIDEIND.BO", "Exide Industries Limited"),
    ("SONACOMS.NS", "Sona BLW Precision Forgings Limited"),
    ("EXIDEIND.NS", "Exide Industries Limited"),
    ("AJANTPHARM.NS", "Ajanta Pharma Limited"),
    ("AJANTPHARM.BO", "Ajanta Pharma Limited"),
    ("LICHSGFIN.BO", "LIC Housing Finance Limited"),
    ("LICHSGFIN.NS", "LIC Housing Finance Limited"),
    ("MCX.NS", "Multi Commodity Exchange of India Limited"),
    ("MCX.BO", "Multi Commodity Exchange of India Limited"),
    ("LAURUSLABS.BO", "Laurus Labs Limited"),
    ("LAURUSLABS.NS", "Laurus Labs Limited"),
    ("CENTRALBK.BO", "Central Bank of India"),
    ("MEDANTA.NS", "Global Health Limited"),
    ("CENTRALBK.NS", "Central Bank of India"),
    ("MEDANTA.BO", "Global Health Limited"),
    ("M&MFIN.BO", "Mahindra & Mahindra Financial Services Limited"),
    ("M&MFIN.NS", "Mahindra & Mahindra Financial Services Limited"),
    ("METROBRAND.BO", "Metro Brands Limited"),
    ("METROBRAND.NS", "Metro Brands Limited"),
    ("GUJGASLTD.NS", "Gujarat Gas Limited"),
    ("GUJGASLTD.BO", "Gujarat Gas Limited"),
    ("TATAINVEST.NS", "Tata Investment Corporation Limited"),
  
]

def fetch_current_price(symbol):
    global price_cache, price_cache_time
    now = time.time()
    if symbol in price_cache and (now - price_cache_time.get(symbol, 0)) < PRICE_CACHE_TTL:
        return price_cache[symbol]
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="1d", interval="1m")
        if not df.empty:
            price = df['Close'].iloc[-1]
            price_cache[symbol] = price
            price_cache_time[symbol] = now
            return price
    except Exception as e:
        app.logger.error(f"Error fetching current price for {symbol}: {e}")
    return price_cache.get(symbol, None)

def fetch_ohlc(symbol, interval="60m", period="60d"):
    global ohlc_cache, ohlc_cache_time
    key = f"{symbol}_{interval}_{period}"
    now = time.time()
    if key in ohlc_cache and (now - ohlc_cache_time.get(key, 0)) < OHLC_CACHE_TTL:
        return ohlc_cache[key]
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(interval=interval, period=period)
        if df.empty:
            return pd.DataFrame()
        df = df.reset_index()
        datetime_col = None
        for col in ['Datetime', 'Date']:
            if col in df.columns:
                datetime_col = col
                break
        if datetime_col is None:
            return pd.DataFrame()
        df.rename(columns={
            datetime_col: 'open_time',
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume'
        }, inplace=True)
        df['open_time'] = pd.to_datetime(df['open_time'])
        df['close'] = pd.to_numeric(df['close'], errors='coerce')
        df.dropna(subset=['close', 'open_time'], inplace=True)
        df = df.reset_index(drop=True)
        ohlc_cache[key] = df
        ohlc_cache_time[key] = now
        return df
    except Exception as e:
        app.logger.error(f"Error fetching OHLC data for {symbol}: {e}")
        return ohlc_cache.get(key, pd.DataFrame())

def calculate_bollinger_bands(df, period=200, std_multiplier=3):
    df = df.copy()
    df["MA"] = df["close"].rolling(window=period, min_periods=period).mean()
    df["STD"] = df["close"].rolling(window=period, min_periods=period).std()
    df["Upper"] = df["MA"] + (std_multiplier * df["STD"])
    df["Lower"] = df["MA"] - (std_multiplier * df["STD"])
    return df

def crossover(series1, series2):
    return (series1.iloc[-2] <= series2.iloc[-2]) and (series1.iloc[-1] > series2.iloc[-1])

def crossunder(series1, series2):
    return (series1.iloc[-2] >= series2.iloc[-2]) and (series1.iloc[-1] < series2.iloc[-1])

def load_last_state(symbol, timeframe):
    filename = STATE_FILE_TEMPLATE.format(symbol, timeframe)
    if os.path.exists(filename):
        with open(filename, "r") as f:
            line = f.read().strip()
            parts = line.split(',')
            if len(parts) == 3:
                state, price_str, index_str = parts
                if state in ["BUY", "SELL"]:
                    try:
                        price = float(price_str)
                        index = int(index_str)
                        return state, price, index
                    except ValueError:
                        pass
            elif len(parts) == 2:
                state, price_str = parts
                if state in ["BUY", "SELL"]:
                    try:
                        price = float(price_str)
                        return state, price, None
                    except ValueError:
                        pass
            elif len(parts) == 1:
                state = parts[0]
                if state in ["BUY", "SELL"]:
                    return state, None, None
    return None, None, None

def save_last_state(symbol, timeframe, state, price, index):
    filename = STATE_FILE_TEMPLATE.format(symbol, timeframe)
    with open(filename, "w") as f:
        f.write(f"{state},{price},{index}")

def infer_initial_state(df):
    close = df["close"]
    lower = df["Lower"]
    upper = df["Upper"]

    last_state = None
    last_signal_index = None
    for i in range(1, len(df)):
        if (close.iloc[i - 1] <= lower.iloc[i - 1]) and (close.iloc[i] > lower.iloc[i]):
            last_state = "BUY"
            last_signal_index = i
        elif (close.iloc[i - 1] >= upper.iloc[i - 1]) and (close.iloc[i] < upper.iloc[i]):
            last_state = "SELL"
            last_signal_index = i

    if last_state is None:
        return "SELL", df["close"].iloc[0], 0

    return last_state, df["close"].iloc[last_signal_index], last_signal_index

def generate_state(df, symbol, timeframe):
    df = df.dropna(subset=["Lower", "Upper", "close"]).reset_index(drop=True)
    if len(df) < 2:
        return "DATA INSUFFICIENT", None

    last_state, last_price, last_index = load_last_state(symbol, timeframe)
    close = df["close"]
    lower = df["Lower"]
    upper = df["Upper"]

    buy_signal = crossover(close, lower)
    sell_signal = crossunder(close, upper)

    if last_state is None or last_price is None or last_index is None or last_index >= len(df):
        last_state, last_price, last_index = infer_initial_state(df)
        save_last_state(symbol, timeframe, last_state, last_price, last_index)

    if buy_signal and last_state != "BUY":
        last_state = "BUY"
        last_index = len(df) - 1
        last_price = close.iloc[last_index]
        save_last_state(symbol, timeframe, last_state, last_price, last_index)
    elif sell_signal and last_state != "SELL":
        last_state = "SELL"
        last_index = len(df) - 1
        last_price = close.iloc[last_index]
        save_last_state(symbol, timeframe, last_state, last_price, last_index)
    else:
        if last_index < len(df):
            last_price = close.iloc[last_index]
            save_last_state(symbol, timeframe, last_state, last_price, last_index)
        else:
            last_state, last_price, last_index = infer_initial_state(df)
            save_last_state(symbol, timeframe, last_state, last_price, last_index)

    return last_state, last_price

def invert_long_signal(state):
    if state == "BUY":
        return "SELL (Close Position)"
    elif state == "SELL":
        return "BUY"
    else:
        return state

def color_for(state):
    if state.startswith("BUY"):
        return "#2e7d32"
    elif state.startswith("SELL"):
        return "#c62828"
    else:
        return "#757575"

@app.route("/", methods=["GET", "POST"])
def index():
    # Important fix here: select symbol string only
    selected_symbol = request.form.get("symbol", STOCK_LIST[0][0])

    current_price = fetch_current_price(selected_symbol)
    current_price_display = f"${current_price:,.2f}" if current_price else "N/A"

    df_1h = fetch_ohlc(selected_symbol, interval="60m", period="60d")
    if df_1h.empty or len(df_1h) < 200:
        app.logger.warning(f"1h data insufficient for {selected_symbol}, falling back to daily for swing signal")
        df_1h = fetch_ohlc(selected_symbol, interval="1d", period="60d")
        if df_1h.empty or len(df_1h) < 200:
            swing_state = "DATA UNAVAILABLE"
            swing_price = None
            swing_close = "N/A"
            swing_time = "N/A"
        else:
            df_1h = calculate_bollinger_bands(df_1h, 200, 3)
            swing_state, swing_price = generate_state(df_1h, selected_symbol, "1d_swing_fallback")
            swing_close = df_1h["close"].iloc[-1]
            swing_time = df_1h["open_time"].iloc[-1].strftime("%Y-%m-%d")
    else:
        df_1h = calculate_bollinger_bands(df_1h, 200, 3)
        swing_state, swing_price = generate_state(df_1h, selected_symbol, "1h")
        swing_close = df_1h["close"].iloc[-1]
        swing_time = df_1h["open_time"].iloc[-1].strftime("%Y-%m-%d %H:%M")

    df_1d = fetch_ohlc(selected_symbol, interval="1d", period="1y")
    if df_1d.empty or len(df_1d) < 20:
        app.logger.warning(f"1d data insufficient for {selected_symbol}, falling back to weekly for long term signal")
        df_1d = fetch_ohlc(selected_symbol, interval="1wk", period="2y")
        if df_1d.empty or len(df_1d) < 10:
            long_state = "DATA UNAVAILABLE"
            long_price = None
            long_close = "N/A"
            long_time = "N/A"
        else:
            df_1d = calculate_bollinger_bands(df_1d, 20, 3)
            long_state_raw, long_price = generate_state(df_1d, selected_symbol, "1wk")
            long_state = invert_long_signal(long_state_raw)
            long_close = df_1d["close"].iloc[-1]
            long_time = df_1d["open_time"].iloc[-1].strftime("%Y-%m-%d")
    else:
        df_1d = calculate_bollinger_bands(df_1d, 20, 3)
        long_state_raw, long_price = generate_state(df_1d, selected_symbol, "1d")
        long_state = invert_long_signal(long_state_raw)
        long_close = df_1d["close"].iloc[-1]
        long_time = df_1d["open_time"].iloc[-1].strftime("%Y-%m-%d")

    swing_display = swing_state + (" (Close Position)" if swing_state == "SELL" else "")
    long_display = long_state

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <title>{selected_symbol} Swing and Long Term Trade Signals</title>

      <!-- Select2 CSS CDN -->
      <link href="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/css/select2.min.css" rel="stylesheet" />

      <style>
        body {{
          font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
          max-width: 900px;
          margin: 40px auto;
          padding: 20px;
          background: #f7f9fc;
          border-radius: 10px;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
          color: #333;
        }}
        h1 {{
          text-align: center;
          margin-bottom: 1rem;
        }}
        form {{
          text-align: center;
          margin-bottom: 30px;
        }}
        select {{
          width: 100%;
          max-width: 300px;
        }}
        button {{
          font-size: 16px;
          padding: 6px 12px;
          margin-top: 10px;
          cursor: pointer;
        }}
        .signals-container {{
          display: flex;
          justify-content: space-around;
          flex-wrap: wrap;
          margin-top: 30px;
          gap: 30px;
        }}
        .signal-box {{
          background: white;
          border-radius: 8px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
          padding: 20px;
          width: 400px;
        }}
        .signal-label {{
          font-size: 20px;
          font-weight: 600;
          margin-bottom: 10px;
          text-align: center;
        }}
        .state-value {{
          font-size: 48px;
          font-weight: 700;
          text-align: center;
          margin: 20px 0 10px 0;
          user-select: none;
        }}
        .close-label, .time-label {{
          font-size: 16px;
          text-align: center;
          color: #555;
          margin-bottom: 6px;
        }}
        .current-price-container {{
          text-align: center;
          margin-top: 30px;
        }}
        .instructions {{
          max-width: 700px;
          margin: 40px auto 0 auto;
          padding: 15px 20px;
          background-color: #ffffff;
          border-radius: 8px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
          color: #333;
          font-size: 16px;
          line-height: 1.5;
        }}
        .instructions h2 {{
          text-align: center;
          margin-bottom: 15px;
          color: #222;
        }}
        .instructions ul {{
          list-style-type: disc;
          padding-left: 20px;
        }}
        footer {{
          margin-top: 40px;
          font-size: 14px;
          color: #999;
          text-align: center;
        }}
      </style>
    </head>
    <body>
      <h1>{selected_symbol} Swing and Long Term Trade Signals</h1>

      <form method="post">
        <label for="symbol">Select Stock Symbol (Searchable Dropdown):</label><br>
        <select name="symbol" id="symbol" class="select2" required>
          {"".join([f'<option value="{symbol}"{" selected" if symbol == selected_symbol else ""}>{symbol} - {name}</option>' for symbol, name in STOCK_LIST])}
        </select>
        <br>
        <button type="submit">Get Signals</button>
      </form>

      <div class="signals-container">
        <div class="signal-box">
          <div class="signal-label">Swing Trade Signal </div>
          <div class="state-value" style="color:{color_for(swing_state)}">{swing_display}</div>
          <div class="close-label">Latest Close: ${swing_close if isinstance(swing_close, str) else f"{swing_close:,.2f}"}</div>
          <div class="time-label">As of: {swing_time}</div>
        </div>

        <div class="signal-box">
          <div class="signal-label">Long Term Signal </div>
          <div class="state-value" style="color:{color_for(long_state)}">{long_display}</div>
          <div class="close-label">Latest Close: ${long_close if isinstance(long_close, str) else f"{long_close:,.2f}"}</div>
          <div class="time-label">As of: {long_time}</div>
        </div>
      </div>

      <div class="current-price-container">
        <h3>Current Price of {selected_symbol}:</h3>
        <p>{current_price_display}</p>
      </div>

      <div class="instructions">
        <h2>Instructions for Traders</h2>
        <ul>
          <li><strong>BUY:</strong> Enter a long position when the signal switches to BUY.</li>
          <li><strong>SELL (Close Position):</strong> Exit your long position when the signal switches to SELL.</li>
          <li>Hold your position until the signal changes to the opposite state.</li>
          <li>Always use proper risk management and confirm signals with your own analysis.</li>
        </ul>
      </div>

      <p>Signals are based on proprietary analysis.<br>Always trade responsibly.</p>
      <footer>© {pd.Timestamp.now().year} Stock Signals</footer>

      <!-- JQuery -->
      <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
      <!-- Select2 JS -->
      <script src="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/js/select2.min.js"></script>
      <script>
        $(document).ready(function() {{
            $('.select2').select2({{
                placeholder: "Select or search stock symbol",
                allowClear: true,
                width: 'resolve'
            }});
        }});
      </script>
    </body>
    </html>
    """
    return render_template_string(html)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5009)
