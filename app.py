from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import yfinance as yf
import pandas as pd
import os
import time
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime, timedelta, timezone 
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin.base import AdminIndexView
from flask import redirect, url_for
from flask_login import current_user
from flask_admin import Admin
from flask_admin.base import AdminIndexView
from wtforms.validators import DataRequired
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired
import re
from flask import request, flash, redirect, url_for
from collections import defaultdict
import secrets
import string
from flask_admin.actions import action
import requests
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from datetime import datetime, timezone
current_time = datetime.now(timezone.utc)



# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or 'your-super-secret-key-here'


# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trading.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'

db = SQLAlchemy(app)

# Store the IP counts for account creation
ip_account_counts = defaultdict(int)

# Function to validate password with regex
def is_valid_password(password):
    # Minimum 8 characters, 1 capital letter, 1 number, 1 special character
    password_regex = r'^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
    return re.match(password_regex, password) is not None

# TRON Payment Constants
TRONGRID_API_KEY = "46ac6e1b-712b-47b2-99c2-f13dd680994b"
# Define the receiving TRON address (replace with your actual address)
RECEIVING_TRON_ADDRESS = "TUEXUqCdgMT2EqruDcWE7qJvbNVJYjgRyM"

TRC20_USDT_CONTRACT_ADDRESS = "TUEXUqCdgMT2EqruDcWE7qJvbNVJYjgRyM"
USDT_SUBSCRIPTION_AMOUNT = 10.0

# Trading signal constants
STATE_FILE_TEMPLATE = "last_signal_state_{}_{}.txt"
price_cache = {}
price_cache_time = {}
PRICE_CACHE_TTL = 120  # 2 minutes
ohlc_cache = {}
ohlc_cache_time = {}
OHLC_CACHE_TTL = 900  # 15 minutes

STOCK_LIST= [("RELIANCE.BO", "Reliance Industries Limited"),
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
    ("TATAINVEST.BO", "Tata Investment Corporation Limited"),
    ("ENDURANCE.BO", "Endurance Technologies Limited"),
    ("ENDURANCE.NS", "Endurance Technologies Limited"),
    ("APOLLOTYRE.NS", "Apollo Tyres Limited"),
    ("APOLLOTYRE.BO", "Apollo Tyres Limited"),
    ("AIAENG.BO", "AIA Engineering Limited"),
    ("AIAENG.NS", "AIA Engineering Limited"),
    ("POONAWALLA.NS", "Poonawalla Fincorp Limited"),
    ("CDSL.NS", "Central Depository Services (India) Limited"),
    ("POONAWALLA.BO", "Poonawalla Fincorp Limited"),
    ("TATATECH.NS", "TATA TECHNOLOGIES LIMITED"),
    ("TATATECH.BO", "Tata Technologies Limited"),
    ("IRB.NS", "IRB Infrastructure Developers Limited"),
    ("IRB.BO", "IRB Infrastructure Developers Limited"),
    ("NBCC.NS", "NBCC (India) Limited"),
    ("NBCC.BO", "NBCC (India) Limited"),
    ("APARINDS.NS", "APAR Industries Limited"),
    ("APARINDS.BO", "APAR Industries Limited"),
    ("ABFRL.NS", "Aditya Birla Fashion and Retail Limited"),
    ("ABFRL.BO", "Aditya Birla Fashion and Retail Limited"),

]

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Define models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    trial_end_date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc) + timedelta(days=7))
    is_subscribed = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    referral_code = db.Column(db.String(20), unique=True, nullable=True)
    referral_credits = db.Column(db.Float, default=0.0)
    payments = db.relationship('Payment', back_populates='user', lazy=True)
    subscription_end_date = db.Column(db.DateTime, nullable=True)
   
    # Explicitly list all columns we want to show
    column_list = ['id', 'username', 'email', 'is_subscribed', 'trial_end_date', 'is_admin', 'referral_code']
    
    # Make these columns searchable
    column_searchable_list = ['username', 'email']
    
    # Allow these columns to be filtered
    column_filters = ['is_subscribed', 'is_admin', 'email']
    
    # Allow these columns to be edited directly in the list view
    column_editable_list = ['is_subscribed', 'is_admin']
    
    # Exclude password hash from display
    column_exclude_list = ['password_hash']
    
    # Don't show password hash in forms
    form_excluded_columns = ['password_hash']
    
    # Set default sorting
    column_default_sort = ('id', True)
    
    # Customize form to include email
    form_extra_fields = {
        'email': StringField('Email', validators=[DataRequired()])
    }
    
    def on_model_change(self, form, model, is_created):
        if 'password' in form:
            model.set_password(form.password.data)
    
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', back_populates='payments')
    amount = db.Column(db.Float, nullable=False)
    tron_address = db.Column(db.String(64), nullable=False)
    transaction_hash = db.Column(db.String(66), nullable=True)
    verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    verified_at = db.Column(db.DateTime, nullable=True)
    column_list = ('user.username', 'amount', 'tron_address', 'transaction_hash', 'verified', 'created_at')

        # Optionally, you can add an action for manual subscription activation
    @action('activate_subscription', 'Activate Subscription', 'Are you sure you want to activate the subscription for the selected payment(s)?')
    def activate_subscription(self, ids):
        payments = Payment.query.filter(Payment.id.in_(ids)).all()
        for payment in payments:
            if payment.verified and not payment.user.is_subscribed:
                payment.user.is_subscribed = True
                payment.user.subscription_end_date = datetime.now(timezone.utc) + relativedelta(months=1)  # Set subscription end date
                db.session.commit()
                flash('Subscription activated for the selected user(s).', 'success')
    
    def on_model_change(self, form, model, is_created):
        if model.verified and not model.verified_at:
            model.verified_at = datetime.now(timezone.utc)  # Mark payment as verified
            model.user.is_subscribed = True  # Activate user's subscription
            verify_referral_conversion(model.user.id)  # Handle referral rewards
    

class ReferralProgram(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    is_active = db.Column(db.Boolean, default=True)
    reward_amount = db.Column(db.Float, default=5.0)  # USDT reward amount
    min_referrals_for_reward = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))

class UserReferral(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    referrer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    referred_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    referral_code = db.Column(db.String(20), nullable=False)
    is_converted = db.Column(db.Boolean, default=False)  # Whether referred user subscribed
    reward_paid = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    
    referrer = db.relationship('User', foreign_keys=[referrer_id], backref='referrals_made')
    referred = db.relationship('User', foreign_keys=[referred_id], backref='referrals_received')

# Custom Admin Index View with authentication
class MyAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))

# Create admin views with authentication
class UserModelView(ModelView):
    column_exclude_list = ['password_hash']
    form_excluded_columns = ['password_hash']
    column_searchable_list = ['username', 'email']
    
    # Make is_subscribed editable
    column_editable_list = ['is_subscribed']
    
    def on_model_change(self, form, model, is_created):
        if 'password' in form:
            model.set_password(form.password.data)
    
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin
    
        # Add a custom action for activating subscription
    @action('activate_subscription', 'Activate Subscription', 'Are you sure you want to activate the subscription for the selected user(s)?')
    def activate_subscription(self, ids):
        users = User.query.filter(User.id.in_(ids)).all()
        for user in users:
            user.is_subscribed = True
        db.session.commit()
        flash('Selected users have been subscribed successfully.', 'success')


class PaymentModelView(ModelView):
    column_list = ('user.username', 'amount', 'tron_address', 'transaction_hash', 'verified', 'created_at')
    column_filters = ('verified',)
    column_searchable_list = ['transaction_hash', 'tron_address']
    column_labels = {
        'user.username': 'User'
    }

     # Add action to manually verify payments
    @action('activate_subscription', 'Activate Subscription', 'Are you sure you want to activate the subscription for the selected payment(s)?')
    def activate_subscription(self, ids):
        payments = Payment.query.filter(Payment.id.in_(ids)).all()
        for payment in payments:
            if not payment.verified:
                payment.verified = True  # Manually mark payment as verified
                payment.user.is_subscribed = True  # Activate the user's subscription
                payment.user.subscription_end_date = datetime.utcnow() + relativedelta(months=1)  # Set subscription end date to 1 month from today
                db.session.commit()
                flash('Subscription activated for the selected payment(s).', 'success')
            else:
                flash(f"Payment for user {payment.user.username} is already verified.", 'info')
    
    # Other configurations (e.g., allowing actions on the admin panel)
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin
    
    def on_model_change(self, form, model, is_created):
        if model.verified and not model.verified_at:
            model.verified_at = datetime.now(timezone.utc)
            model.user.is_subscribed = True
            verify_referral_conversion(model.user.id)
    
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin

class ReferralProgramModelView(ModelView):
    can_create = True
    can_edit = True
    column_list = ['is_active', 'reward_amount', 'min_referrals_for_reward', 'created_at']
    
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin

class UserReferralModelView(ModelView):
    can_create = False
    can_edit = True
    column_list = ['referrer.username', 'referred.username', 'referral_code', 
                  'is_converted', 'reward_paid', 'created_at']
    column_labels = {
        'referrer.username': 'Referrer',
        'referred.username': 'Referred User'
    }
    
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin
    


# Initialize admin with custom index view
admin = Admin(app, name='Trading Signals Admin', template_mode='bootstrap3', index_view=MyAdminIndexView())

# Add views to admin
admin.add_view(UserModelView(User, db.session, name='User Management'))
admin.add_view(PaymentModelView(Payment, db.session, name='Payment Management'))
admin.add_view(ReferralProgramModelView(ReferralProgram, db.session, name='Referral Program'))
admin.add_view(UserReferralModelView(UserReferral, db.session, name='User Referrals'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Helper functions for referral program
def generate_referral_code(user_id, username):
    """Generate a unique referral code"""
    # Create a base code from username and user_id
    base = f"{username[:3]}{user_id}".upper()
    # Add some random characters for uniqueness
    random_part = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(4))
    return f"{base}-{random_part}"

def get_active_referral_program():
    """Get the currently active referral program"""
    return ReferralProgram.query.filter_by(is_active=True).first()

def apply_referral_credit(user, amount):
    """Apply referral credit to user's account"""
    user.referral_credits += amount
    db.session.commit()

def verify_referral_conversion(user_id):
    """Check if this user was referred and mark as converted if so"""
    referral = UserReferral.query.filter_by(referred_id=user_id, is_converted=False).first()
    if referral:
        program = get_active_referral_program()
        if program:
            referral.is_converted = True
            
            # Check if referrer has enough conversions for reward
            successful_referrals = UserReferral.query.filter_by(
                referrer_id=referral.referrer_id,
                is_converted=True
            ).count()
            
            if successful_referrals >= program.min_referrals_for_reward:
                referral.reward_paid = True
                apply_referral_credit(referral.referrer, program.reward_amount)
                
                # Notify referrer
                if referral.referrer.is_subscribed:
                    flash(f"Congratulations! You've earned ${program.reward_amount} for your referral!", "success")
    
        db.session.commit()

# Trading signal functions
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
        try:
            with open(filename, "r") as f:
                line = f.read().strip()
                parts = line.split(',')
                if len(parts) == 3:
                    state, price_str, index_str = parts
                    if state in ["BUY", "SELL"]:
                        price = float(price_str)
                        index = int(index_str)
                        return state, price, index
                elif len(parts) == 2:
                    state, price_str = parts
                    if state in ["BUY", "SELL"]:
                        price = float(price_str)
                        return state, price, None
                elif len(parts) == 1:
                    state = parts[0]
                    if state in ["BUY", "SELL"]:
                        return state, None, None
        except Exception as e:
            app.logger.error(f"Error loading last state file {filename}: {e}")
    return None, None, None

def save_last_state(symbol, timeframe, state, price, index):
    filename = STATE_FILE_TEMPLATE.format(symbol, timeframe)
    try:
        with open(filename, "w") as f:
            f.write(f"{state},{price},{index}")
    except Exception as e:
        app.logger.error(f"Error saving last state file {filename}: {e}")

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

def is_trial_active(user):
    return datetime.utcnow() < user.trial_end_date

def check_tron_payment(user):
    verified_payment = Payment.query.filter_by(
        user_id=user.id,
        verified=True
    ).first()
    
    if verified_payment:
        user.is_subscribed = True
        db.session.commit()
        return True
    return False

# Create admin user and initialize referral program if not exists
def initialize_app():
    with app.app_context():
        db.create_all()
        
        # Create admin user if not exists
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                is_admin=True,
                trial_end_date=datetime.now(timezone.utc) + timedelta(days=365),
                is_subscribed=True
            )
            admin_user.set_password('admin123')  # Change this password in production!
            db.session.add(admin_user)
            db.session.commit()
            print("Admin user created with username 'admin' and password 'admin123'")
        
        # Initialize referral program if not exists
        if not ReferralProgram.query.first():
            program = ReferralProgram(
                is_active=True,
                reward_amount=5.0,
                min_referrals_for_reward=1
            )
            db.session.add(program)
            db.session.commit()
            print("Default referral program created")

initialize_app()

# Password recovery routes
@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        username = request.form.get("username")
        user = User.query.filter_by(username=username).first()

        if user:
            # Store user ID in session to allow password reset directly
            session['reset_user_id'] = user.id
            return redirect(url_for("reset_password"))
        else:
            flash("No account with that username exists.", "error")
            return redirect(url_for("forgot_password"))

    return render_template_string("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Forgot Password</title>
    <style>
        body {font-family: Arial, sans-serif; background-color: #f4f7fc; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0;}
        .form-container {background-color: #fff; padding: 40px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); width: 100%; max-width: 400px;}
        h2 {text-align: center; color: #333;}
        label {display: block; margin-bottom: 10px; color: #555; font-size: 14px;}
        input[type="text"] {width: 100%; padding: 12px; margin-bottom: 20px; border: 1px solid #ddd; border-radius: 6px; font-size: 16px;}
        input[type="text"]:focus {border-color: #5b9bd5; outline: none;}
        button {width: 100%; padding: 12px; background-color: #4CAF50; color: #fff; border: none; border-radius: 6px; font-size: 16px; cursor: pointer;}
        button:hover {background-color: #45a049;}
        .message {text-align: center; margin-top: 20px;}
        .message a {color: #007BFF; text-decoration: none;}
        .message a:hover {text-decoration: underline;}
    </style>
</head>
<body>
    <div class="form-container">
        <h2>Forgot Password</h2>
        <form method="post">
            <label for="username">Enter your username:</label>
            <input type="text" id="username" name="username" required>
            <button type="submit">Next</button>
        </form>
        <div class="message">
            <p>Remembered your password? <a href="/login">Login here</a></p>
        </div>
    </div>
</body>
</html>
    """)

@app.route("/reset_password", methods=["GET", "POST"])
def reset_password():
    user_id = session.get('reset_user_id')
    if not user_id:
        flash("Invalid reset request.", "error")
        return redirect(url_for("forgot_password"))
    
    user = User.query.get(user_id)
    if not user:
        flash("User not found.", "error")
        return redirect(url_for("forgot_password"))

    if request.method == "POST":
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        if new_password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for('reset_password'))

        if not is_valid_password(new_password):
            flash("Password must be at least 8 characters long, contain a capital letter, a number, and a special character.", "error")
            return redirect(url_for('reset_password'))

        user.set_password(new_password)
        db.session.commit()
        
        # Clear session after successful reset
        session.pop('reset_user_id', None)
        
        flash("Your password has been updated successfully.", "success")
        return redirect(url_for("login"))

    return render_template_string("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reset Password</title>
    <style>
        body {font-family: Arial, sans-serif; background-color: #f4f7fc; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0;}
        .form-container {background-color: #fff; padding: 40px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); width: 100%; max-width: 400px;}
        h2 {text-align: center; color: #333;}
        label {display: block; margin-bottom: 10px; color: #555; font-size: 14px;}
        input[type="password"] {width: 100%; padding: 12px; margin-bottom: 20px; border: 1px solid #ddd; border-radius: 6px; font-size: 16px;}
        input[type="password"]:focus {border-color: #5b9bd5; outline: none;}
        button {width: 100%; padding: 12px; background-color: #4CAF50; color: #fff; border: none; border-radius: 6px; font-size: 16px; cursor: pointer;}
        button:hover {background-color: #45a049;}
        .flash-messages {list-style-type: none; padding: 0; margin-bottom: 20px;}
        .flash-messages li {padding: 10px; border-radius: 5px; margin-bottom: 10px;}
        .flash-messages .error {background-color: #ffebee; color: #c62828; border: 1px solid #ef9a9a;}
        .flash-messages .success {background-color: #e8f5e9; color: #2e7d32; border: 1px solid #a5d6a7;}
    </style>
</head>
<body>
    <div class="form-container">
        <h2>Reset Your Password</h2>
        
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                <ul class="flash-messages">
                {% for category, message in messages %}
                    <li class="{{ category }}">{{ message }}</li>
                {% endfor %}
                </ul>
            {% endif %}
        {% endwith %}

        <form method="post">
            <label for="new_password">New Password:</label>
            <input type="password" id="new_password" name="new_password" required>
            
            <label for="confirm_password">Confirm New Password:</label>
            <input type="password" id="confirm_password" name="confirm_password" required>
            
            <button type="submit">Reset Password</button>
        </form>
    </div>
</body>
</html>
    """)

@app.route("/signup", methods=["GET", "POST"])
def signup():
    ip_address = request.remote_addr  # Get user's IP address

    # Check if the IP has already reached the limit for account creation
    if ip_account_counts[ip_address] >= 5:
        flash("You have reached the maximum number of accounts allowed from this IP address.", "error")
        return redirect(url_for("login"))

    # Check for referral code in query params
    referral_code = request.args.get('ref', '').strip()
    referrer = None
    if referral_code:
        referrer = User.query.filter_by(referral_code=referral_code).first()
        if not referrer:
            flash("Invalid referral code. Please check the link and try again.", "error")
            return redirect(url_for("signup"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")
        form_referral_code = request.form.get("referral_code", "").strip()

        # Use form referral code if provided, otherwise use from query params
        referral_code = form_referral_code if form_referral_code else referral_code
        referrer = User.query.filter_by(referral_code=referral_code).first() if referral_code else None

        # Validate password
        if not is_valid_password(password):
            flash("Password must be at least 8 characters long, contain a capital letter, a number, and a special character.", "error")
            return redirect(url_for("signup"))

        if not username or not email or not password or not confirm:
            flash("Please fill all fields.", "error")
        elif password != confirm:
            flash("Passwords do not match.", "error")
        elif User.query.filter_by(username=username).first():
            flash("Username already exists. Please choose another.", "error")
        elif User.query.filter_by(email=email).first():
            flash("Email already registered. Please use another email.", "error")
        else:
            user = User(username=username, email=email)
            user.set_password(password)
            
            # Generate referral code for new user
            user.referral_code = generate_referral_code(user.id, username)
            
            db.session.add(user)
            db.session.commit()

            # Create referral record if applicable
            if referrer:
                referral = UserReferral(
                    referrer_id=referrer.id,
                    referred_id=user.id,
                    referral_code=referral_code
                )
                db.session.add(referral)
                db.session.commit()
                
                flash(f"Thanks for signing up with {referrer.username}'s referral!", "success")

            # Increment the IP account creation counter
            ip_account_counts[ip_address] += 1

            flash("Registration successful! Enjoy your 7-day free trial!", "success")
            return redirect(url_for("login"))

    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <title>Sign Up - Stock Signals</title>
      <style>
        body {
          font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
          background: #f7f9fc;
          display: flex;
          justify-content: center;
          align-items: center;
          min-height: 100vh;
          margin: 0;
        }
        .auth-container {
          background: white;
          border-radius: 10px;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
          padding: 30px;
          width: 100%;
          max-width: 400px;
          text-align: center;
        }
        h2 {
          color: #333;
          margin-bottom: 15px;
        }
        p.intro {
          color: #555;
          margin-bottom: 25px;
          line-height: 1.6;
        }
        .flash-messages {
          list-style-type: none;
          padding: 0;
          margin-bottom: 20px;
        }
        .flash-messages li {
          padding: 10px;
          border-radius: 5px;
          margin-bottom: 10px;
          font-weight: bold;
        }
        .flash-messages .error {
          background-color: #ffebee;
          color: #c62828;
          border: 1px solid #ef9a9a;
        }
        .flash-messages .success {
          background-color: #e8f5e9;
          color: #2e7d32;
          border: 1px solid #a5d6a7;
        }
        form {
          display: flex;
          flex-direction: column;
          gap: 15px;
        }
        label {
          text-align: left;
          font-weight: 500;
          color: #444;
        }
        input[type="text"],
        input[type="email"],
        input[type="password"] {
          width: calc(100% - 20px);
          padding: 10px;
          border: 1px solid #ddd;
          border-radius: 5px;
          font-size: 16px;
        }
        button {
          background-color: #4CAF50;
          color: white;
          padding: 12px 20px;
          border: none;
          border-radius: 5px;
          font-size: 18px;
          cursor: pointer;
          transition: background-color 0.3s ease;
        }
        button:hover {
          background-color: #45a049;
        }
        a {
          color: #007bff;
          text-decoration: none;
          margin-top: 15px;
          display: block;
        }
        a:hover {
          text-decoration: underline;
        }
        .referral-banner {
          background-color: #e3f2fd;
          padding: 10px;
          border-radius: 5px;
          margin-bottom: 15px;
          font-size: 14px;
        }
      </style>
    </head>
    <body>
      <div class="auth-container">
        <h2>Join Stock Signals</h2>
        <p class="intro">
          Sign up for a **7-day free trial** to unlock powerful swing and long-term trade signals
          for your favorite assets. Discover smarter trading today!
        </p>
        
        {% if referral_code and referrer %}
        <div class="referral-banner">
          Signing up with {{ referrer.username }}'s referral
        </div>
        {% endif %}
        
        {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            <ul class="flash-messages">
            {% for category, message in messages %}
              <li class="{{ category }}">{{ message }}</li>
            {% endfor %}
            </ul>
          {% endif %}
        {% endwith %}
        
        <form method="post">
          <input type="hidden" name="referral_code" value="{{ referral_code }}">
          
          <label for="username">Username:</label>
          <input type="text" id="username" name="username" required>
          
          <label for="email">Email:</label>
          <input type="email" id="email" name="email" required>
          
          <label for="password">Password:</label>
          <input type="password" id="password" name="password" required>
          
          <label for="confirm">Confirm Password:</label>
          <input type="password" id="confirm" name="confirm" required>
          
          {% if not referral_code %}
          <label for="referral_code">Referral Code (optional):</label>
          <input type="text" id="referral_code" name="referral_code">
          {% endif %}
          
          <button type="submit">Sign Up</button>
        </form>
        <p>Already have an account? <a href="{{ url_for('login') }}">Login here</a>.</p>
      </div>
    </body>
    </html>
    """, referral_code=referral_code, referrer=referrer)

def user_navigation():
    return f"""
    <div class="user-info">
        Logged in as <strong>{current_user.username}</strong> | 
        <a href="{url_for('dashboard')}">Dashboard</a> | 
        <a href="{url_for('index')}">Signals</a> | 
        <a href="{url_for('subscribe')}">Subscription</a> | 
        <a href="{url_for('logout')}">Logout</a> | 
        
    </div>
    """

@app.route("/dashboard")
@login_required
def dashboard():
    # Get referral program details
    program = get_active_referral_program()
    
    # Get user's referral stats
    referrals = UserReferral.query.filter_by(referrer_id=current_user.id).all()
    successful_referrals = [r for r in referrals if r.is_converted]
    
    # Calculate counts before passing to template
    total_referrals = len(referrals)
    successful_count = len(successful_referrals)
    
    # Generate the full referral URL
    base_url = request.host_url.rstrip('/')
    referral_url = f"{base_url}{url_for('signup')}?ref={current_user.referral_code}"

    # Display subscription information for users without enough credits
    is_trial = is_trial_active(current_user)
    has_subscribed = current_user.is_subscribed

    def subscribe():
        # Check if the user has enough credits to activate subscription
        if current_user.referral_credits >= USDT_SUBSCRIPTION_AMOUNT:
            # If the user has enough credits, activate their subscription
            current_user.is_subscribed = True
            current_user.referral_credits -= USDT_SUBSCRIPTION_AMOUNT  # Deduct the credits
            current_user.subscription_end_date = datetime.utcnow() + relativedelta(months=1)  # Set subscription end date to 1 month from today
            db.session.commit()
            
            return redirect(url_for("dashboard"))

        # If the user does not have enough credits, they must pay
        if request.method == "POST":
            tron_address = request.form.get("tron_address")
            transaction_hash = request.form.get("transaction_hash")
            
            if not tron_address or not transaction_hash:
                flash("Please provide both TRON address and transaction hash", "error")
            else:
                # Verify the payment using the TRON transaction hash
                if verify_tron_payment(tron_address, transaction_hash):
                    # If payment is verified, activate the subscription
                    current_user.is_subscribed = True
                    current_user.subscription_end_date = datetime.utcnow() + relativedelta(months=1)  # Set subscription end date to 1 month from today
                    db.session.commit()
                    flash("Your subscription has been activated successfully.", "success")
                    return redirect(url_for("dashboard"))
                else:
                    flash("Invalid transaction or insufficient amount. Please try again.", "error")

    # Trial status logic
    if is_trial:
        days_left = (current_user.trial_end_date - datetime.utcnow()).days + 1
        trial_status = f"Your free trial is active! You have {days_left} day(s) left."
        if days_left <= 0:
            trial_status = "Your free trial has ended."
            flash("Your free trial has ended. Please subscribe to continue accessing signals.", "warning")
    else:
        trial_status = "Your free trial has ended."

    # Subscription end date logic
    subscription_end = current_user.subscription_end_date.strftime('%Y-%m-%d') if current_user.subscription_end_date else "N/A"

    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Your Dashboard</title>
        <style>
            body {
                font-family: 'Arial', sans-serif;
                max-width: 1000px;
                margin: 0 auto;
                padding: 20px;
                background: linear-gradient(135deg, #f5f5f5, #e2e2e2);
            }
            .dashboard-container {
                background: #ffffff;
                padding: 30px;
                border-radius: 15px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                overflow: hidden;
            }
            h1 {
                color: #333;
                border-bottom: 3px solid #eee;
                padding-bottom: 15px;
                font-size: 2em;
            }
            .referral-section {
                margin-top: 40px;
                padding: 25px;
                background: #f9f9f9;
                border-radius: 12px;
                box-shadow: 0 4px 10px rgba(0,0,0,0.05);
            }
            .referral-url {
                background: #f0f0f0;
                padding: 12px;
                border-radius: 8px;
                word-break: break-all;
                margin: 15px 0;
                font-family: 'Courier New', monospace;
                color: #333;
            }
            .stats {
                display: flex;
                gap: 30px;
                margin-top: 20px;
                justify-content: space-between;
            }
            .stat-box {
                flex: 1;
                background: #e1f5fe;
                padding: 20px;
                border-radius: 12px;
                text-align: center;
                box-shadow: 0 3px 8px rgba(0,0,0,0.1);
            }
            .stat-value {
                font-size: 30px;
                font-weight: bold;
                color: #039be5;
            }
            .button-container {
                text-align: center;
                margin-top: 25px;
            }
            button {
                background: #4CAF50;
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 8px;
                cursor: pointer;
                transition: background 0.3s ease;
                font-size: 1.1em;
            }
            button:hover {
                background: #388e3c;
            }
            .progress-bar-container {
                margin-top: 20px;
                background: #f2f2f2;
                border-radius: 12px;
                overflow: hidden;
            }
            .progress-bar {
                height: 10px;
                width: 0%;
                background: #4caf50;
            }
            .trial-status {
                background: #ff9800;
                color: white;
                padding: 10px;
                text-align: center;
                border-radius: 8px;
                font-size: 1.1em;
            }
        </style>
    </head>
    <body>
        {{ user_navigation|safe }}
        
        <div class="dashboard-container">
            <h1>Welcome, {{ current_user.username }}!</h1>
        
            <div class="subscription-info">
                <div class="trial-status">{{ trial_status }}</div>
                <div class="progress-bar-container">
                    <div class="progress-bar" style="width: {{ '0%' if days_left <= 0 else (days_left / 30) * 100 }};"></div>
                </div>
                <p><strong>Subscription Status:</strong> {{ 'Active' if has_subscribed or current_user.subscription_end_date else 'Inactive' }}</p>
                <p><strong>Subscription Ends On:</strong> {{ current_user.subscription_end_date.strftime('%Y-%m-%d') if current_user.subscription_end_date else 'N/A' }}</p>
            </div>
            
            <div class="referral-section">
                <h2>Your Referral Program</h2>
                <p>Earn ${{ program.reward_amount }} for each friend who subscribes using your referral link!</p>
                
                <p><strong>Your Referral Code:</strong> {{ current_user.referral_code }}</p>
                
                <p><strong>Share this link:</strong></p>
                <div class="referral-url" id="referralUrl">{{ referral_url }}</div>
                
                <button onclick="copyReferralLink()">Copy Referral Link</button>
                
                <div class="stats">
                    <div class="stat-box">
                        <div class="stat-value">{{ total_referrals }}</div>
                        <div>Total Referrals</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value">{{ successful_count }}</div>
                        <div>Successful Referrals</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value">${{ "%.2f"|format(current_user.referral_credits) }}</div>
                        <div>Earned Credits</div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            function copyReferralLink() {
                const referralUrl = document.getElementById('referralUrl');
                navigator.clipboard.writeText(referralUrl.textContent)
                    .then(() => alert('Referral link copied to clipboard!'))
                    .catch(err => console.error('Failed to copy: ', err));
            }
        </script>
    </body>
    </html>
    """, 
    user_navigation=user_navigation(),
    program=program,
    referral_url=referral_url,
    total_referrals=total_referrals,
    successful_count=successful_count,
    days_left=days_left
    )

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash("Logged in successfully!", "success")
            if not is_trial_active(user) and not user.is_subscribed:
                return redirect(url_for("subscribe"))
            return redirect(url_for("dashboard"))  # Changed from index to dashboard
        else:
            flash("Invalid username or password.", "error")
    
    # Rest of the login route remains the same

    return render_template_string("""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Login - Stock Signals</title>
          <!-- Google Analytics Script -->
        <script async src="https://www.googletagmanager.com/gtag/js?id=G-658KJS0QED"></script>
        <script>
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());
            gtag('config', 'G-658KJS0QED');
        </script>                                
  <style>
    body {
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      background: linear-gradient(135deg, #00bcd4, #004d40);
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      margin: 0;
      color: white;
    }
    .auth-container {
      background: white;
      border-radius: 15px;
      box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
      padding: 40px;
      width: 100%;
      max-width: 450px;
      text-align: center;
      transition: all 0.3s ease-in-out;
    }
    .auth-container:hover {
      transform: scale(1.05);
      box-shadow: 0 12px 24px rgba(0, 0, 0, 0.3);
    }
    h2 {
      color: #333;
      margin-bottom: 20px;
      font-size: 2rem;
      font-weight: bold;
    }
    p.intro {
      color: #444;
      margin-bottom: 30px;
      line-height: 1.8;
      font-size: 1.1rem;
    }
    .flash-messages {
      list-style-type: none;
      padding: 0;
      margin-bottom: 25px;
    }
    .flash-messages li {
      padding: 12px;
      border-radius: 5px;
      margin-bottom: 15px;
      font-weight: bold;
      text-transform: uppercase;
    }
    .flash-messages .error {
      background-color: #ffebee;
      color: #c62828;
      border: 1px solid #ef9a9a;
    }
    .flash-messages .success {
      background-color: #e8f5e9;
      color: #2e7d32;
      border: 1px solid #a5d6a7;
    }
    form {
      display: flex;
      flex-direction: column;
      gap: 20px;
    }
    label {
      text-align: left;
      font-weight: 500;
      color: #444;
    }
    input[type="text"],
    input[type="password"] {
      width: calc(100% - 20px);
      padding: 12px;
      border: 2px solid #ddd;
      border-radius: 10px;
      font-size: 16px;
      background-color: #f7f7f7;
      transition: border 0.3s ease-in-out;
    }
    input[type="text"]:focus,
    input[type="password"]:focus {
      border-color: #007bff;
    }
    button {
      background-color: #007bff;
      color: white;
      padding: 15px 25px;
      border: none;
      border-radius: 10px;
      font-size: 18px;
      cursor: pointer;
      transition: background-color 0.3s ease;
    }
    button:hover {
      background-color: #0056b3;
    }
    a {
      color: #4CAF50;
      text-decoration: none;
      margin-top: 15px;
      display: block;
      font-size: 1rem;
    }
    a:hover {
      text-decoration: underline;
    }
    .marketing-message {
      margin-top: 30px;
      font-size: 1.1rem;
      color: #444;
      background-color: #f7f7f7;
      padding: 10px;
      border-radius: 8px;
      font-weight: bold;
    }
    .cta-message {
      color: #007bff;
      font-size: 1.1rem;
      font-weight: 600;
      text-transform: uppercase;
    }
  </style>
</head>
<body>
  <div class="auth-container">
    <h2>Welcome Back, Trader!</h2>
    <p class="intro">
      Log in now to access your personalized Indian stocks signals and stay ahead of market trends. 
      With real-time insights, you're just a click away from making smarter decisions and maximizing your profits.
    </p>

    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        <ul class="flash-messages">
          {% for category, message in messages %}
            <li class="{{ category }}">{{ message }}</li>
          {% endfor %}
        </ul>
      {% endif %}
    {% endwith %}

    <form method="post">
      <label for="username">Username:</label>
      <input type="text" id="username" name="username" required>
      <label for="password">Password:</label>
      <input type="password" id="password" name="password" required>
      <button type="submit">Login</button>
    </form>

    <p>Don't have an account? <a href="{{ url_for('signup') }}">Sign up here</a>.</p>
    <p><a href="{{ url_for('forgot_password') }}">Forgot your password?</a></p>

    <div class="marketing-message">
      <p class="cta-message">Get ahead in the world of crypto today. Make smarter trades with real-time signals!</p>
    </div>
  </div>
</body>
</html>
    </body>
<a href="https://wa.me/message/XZEBHBEWMSHJD1" target="_blank" class="whatsapp-btn">
    <div class="icon">
        <!-- WhatsApp SVG Icon (No External Image Needed) -->
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="28" height="28">
            <path fill="currentColor" d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
        </svg>
    </div>
    <!-- Optional Notification Badge -->
    <span class="notification-badge">1</span>
    <!-- Optional Hover Tooltip -->
    <span class="tooltip">Message Us</span>
</a>

<style>
    .whatsapp-btn {
        position: fixed;
        bottom: 25px;
        right: 25px;
        width: 56px;
        height: 56px;
        background: #25D366;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 4px 16px rgba(37, 211, 102, 0.3);
        z-index: 9999;
        transition: all 0.3s ease;
    }
    .whatsapp-btn:hover {
        background: #128C7E;
        transform: scale(1.1);
        box-shadow: 0 6px 20px rgba(18, 140, 126, 0.4);
    }
    .whatsapp-btn .icon {
        color: white;
        margin-top: 2px; /* Minor icon alignment tweak */
    }
    /* Notification Badge (Optional) */
    .notification-badge {
        position: absolute;
        top: -5px;
        right: -5px;
        background: #FF3B30;
        color: white;
        width: 20px;
        height: 20px;
        border-radius: 50%;
        font-size: 12px;
        font-weight: bold;
        display: flex;
        align-items: center;
        justify-content: center;
        animation: pulse 1.5s infinite;
    }
    /* Tooltip (Optional) */
    .tooltip {
        position: absolute;
        right: 70px;
        background: #333;
        color: white;
        padding: 6px 12px;
        border-radius: 4px;
        font-size: 14px;
        font-family: Arial, sans-serif;
        opacity: 0;
        pointer-events: none;
        transition: opacity 0.3s ease;
        white-space: nowrap;
    }
    .whatsapp-btn:hover .tooltip {
        opacity: 1;
    }
    /* Pulse Animation for Badge */
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.1); }
        100% { transform: scale(1); }
    }
</style>

                                  
</html>
    """)
  
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "success")
    return redirect(url_for("login"))

@app.route("/assign_credits", methods=["GET", "POST"])
@login_required
def assign_credits():
    if not current_user.is_admin:
        flash("You must be an admin to access this page.", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        # Get the selected user and credit amount
        user_id = request.form.get("user_id")
        credit_amount = float(request.form.get("credit_amount"))
        
        # Ensure the credit amount is valid
        if credit_amount <= 0:
            flash("Credit amount must be greater than zero.", "error")
            return redirect(url_for("assign_credits"))

        # Find the user by ID and update their referral credits
        user = User.query.get(user_id)
        if user:
            user.referral_credits += credit_amount  # Add credits to user's account
            db.session.commit()
            flash(f"{credit_amount} USDT credits have been successfully assigned to {user.username}.", "success")
        else:
            flash("User not found.", "error")
        
        return redirect(url_for("assign_credits"))

    # Get the list of users to display in the form
    users = User.query.all()
    
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Admin - Assign Referral Credits</title>
    </head>
    <body>
        <h1>Assign Referral Credits</h1>

        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                <ul class="flash-messages">
                {% for category, message in messages %}
                    <li class="{{ category }}">{{ message }}</li>
                {% endfor %}
                </ul>
            {% endif %}
        {% endwith %}

        <form method="POST" action="{{ url_for('assign_credits') }}">
            <label for="user_id">Select Customer:</label>
            <select name="user_id" id="user_id" required>
                {% for user in users %}
                    <option value="{{ user.id }}">{{ user.username }}</option>
                {% endfor %}
            </select><br><br>

            <label for="credit_amount">Enter Credit Amount to Assign:</label>
            <input type="number" id="credit_amount" name="credit_amount" min="0" step="any" required /><br><br>

            <button type="submit">Assign Credits</button>
        </form>

        <footer>
            <a href="{{ url_for('dashboard') }}">Back to Dashboard</a>
        </footer>
    </body>
    </html>
    """, users=users)



import requests
from datetime import datetime, timedelta

# Ensure that the verify_tron_payment function is defined before it is used
def verify_tron_payment(tron_address, transaction_hash):
    """Verify if the transaction exists and the amount is correct using TronGrid API"""
    
    url = f"https://api.trongrid.io/v1/transactions/{transaction_hash}"
    response = requests.get(url)

    if response.status_code != 200:
        app.logger.error(f"Error fetching transaction details: {response.status_code}")
        return False

    data = response.json()

    # Ensure the transaction is successful and matches the expected receiving address and amount
    if data['data']:
        transaction = data['data'][0]

        # Check if the transaction is for the correct TRON address
        if transaction['to'] == RECEIVING_TRON_ADDRESS:
            # Check if the amount is correct (in sun, 1 TRX = 1,000,000 SUN)
            amount_in_sun = transaction['amount']
            if amount_in_sun >= USDT_SUBSCRIPTION_AMOUNT * 1000000:  # Assuming 1 USDT = 1 TRX in this context
                return True
    return False


def verify_tron_payment(tron_address, transaction_hash):
    """Verify if the transaction exists and the amount is correct using TronGrid API for USDT TRC20"""
    
    # Fetch transaction details from TronGrid API
    url = f"https://api.trongrid.io/v1/transactions/{transaction_hash}"
    response = requests.get(url)

    if response.status_code != 200:
        app.logger.error(f"Error fetching transaction details: {response.status_code}")
        return False

    data = response.json()

    # Ensure the transaction is valid and exists
    if data['data']:
        transaction = data['data'][0]
        
        # Check if the transaction is for the correct TRON address (to address should be the receiving address)
        if transaction['to'] == RECEIVING_TRON_ADDRESS:
            # Check if the transaction involves USDT TRC20 (based on contract address)
            if transaction['token_info']['contract_address'] == TRC20_USDT_CONTRACT_ADDRESS:
                # Check if the amount is correct (in sun, 1 USDT = 1,000,000 SUN)
                amount_in_sun = transaction['token_info']['amount']
                if amount_in_sun >= USDT_SUBSCRIPTION_AMOUNT * 1000000:  # Assuming 1 USDT = 1 TRC20 USDT
                    return True
    return False

# Check if current_user is not None before proceeding
if current_user:
    # Get the current UTC time in a timezone-aware format
    current_time = datetime.now(timezone.utc)

    # Set the subscription end date to one month from the current time
    current_user.subscription_end_date = current_time + relativedelta(months=1)
else:
    print("current_user is None, please ensure the user is logged in or initialized.")


from flask import render_template_string, flash, request, redirect, url_for
from datetime import datetime
from dateutil.relativedelta import relativedelta
from flask_login import login_required, current_user
import re

# Dummy constants for illustration purposes
USDT_SUBSCRIPTION_AMOUNT = 10.0  # Example subscription amount
RECEIVING_TRON_ADDRESS = "TUEXUqCdgMT2EqruDcWE7qJvbNVJYjgRyM"  # Replace with actual TRON address

@app.route("/subscribe", methods=["GET", "POST"])
@login_required
def subscribe():
    # Helper function for TRON address validation
    def is_valid_tron_address(address):
        # Regex to validate TRON address (simplified for demonstration)
        return bool(re.match(r"^T[a-zA-Z0-9]{33}$", address))

    # Check if the user has enough credits to activate subscription
    if current_user.referral_credits >= USDT_SUBSCRIPTION_AMOUNT:
        # If the user has enough credits, activate their subscription
        current_user.is_subscribed = True
        current_user.referral_credits -= USDT_SUBSCRIPTION_AMOUNT  # Deduct credits
        current_user.subscription_end_date = datetime.utcnow() + relativedelta(months=1)  # Set subscription end date
        db.session.commit()

        flash("Your subscription has been activated successfully using your credits.", "success")
        return redirect(url_for("dashboard"))

    # If the user does not have enough credits, they must pay
    if request.method == "POST":
        tron_address = request.form.get("tron_address")
        transaction_hash = request.form.get("transaction_hash")

        # Input validation
        if not tron_address or not transaction_hash:
            flash("Please provide both TRON address and transaction hash.", "error")
        elif not is_valid_tron_address(tron_address):
            flash("Invalid TRON address. Please check the format and try again.", "error")
        else:
            # Verify the payment using the TRON transaction hash
            try:
                if verify_tron_payment(tron_address, transaction_hash):
                    # If payment is verified, activate the subscription
                    current_user.is_subscribed = True
                    current_user.subscription_end_date = datetime.utcnow() + relativedelta(months=1)  # Set subscription end date
                    db.session.commit()

                    flash("Your payment was successful. Subscription activated!", "success")
                    return redirect(url_for("dashboard"))
                else:
                    flash("Invalid transaction or insufficient amount. Please try again.", "error")
            except Exception as e:
                flash(f"Error verifying payment: {str(e)}", "error")
                
    # Display subscription information for users without enough credits
    is_trial = is_trial_active(current_user)
    has_subscribed = current_user.is_subscribed

    if is_trial:
        days_left = (current_user.trial_end_date - datetime.utcnow()).days + 1
        trial_status = f"Your free trial is active! You have {days_left} day(s) left."
        if days_left <= 0:
            trial_status = "Your free trial has ended."
            flash("Your free trial has ended. Please subscribe to continue accessing signals.", "warning")
    else:
        trial_status = "Your free trial has ended."

    # Subscription end date logic
    subscription_end = current_user.subscription_end_date.strftime('%Y-%m-%d') if current_user.subscription_end_date else "N/A"

    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Subscription - Stock Signals</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #f4f7fc;
                padding: 20px;
            }
            .container {
                background-color: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            }
            .flash-messages {
                list-style-type: none;
                padding: 0;
            }
            .flash-messages li {
                margin: 10px 0;
                padding: 10px;
                border-radius: 5px;
                background-color: #f4f7fc;
                font-weight: bold;
            }
            .success {
                background-color: #e8f5e9;
                color: #2e7d32;
            }
            .error {
                background-color: #ffebee;
                color: #c62828;
            }
            .subscription-info {
                margin-top: 20px;
            }
            .subscription-info p {
                font-size: 18px;
                color: #555;
            }
            button {
                padding: 10px 20px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                transition: background-color 0.3s;
            }
            button:hover {
                background-color: #45a049;
            }
        </style>
    </head>
    <body>
        <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Subscription Status - Advanced</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        /* Basic Reset & Body Styling */
        body {
            font-family: 'Poppins', sans-serif;
            background-color: #f0f2f5; /* Light gray background */
            margin: 0;
            padding: 20px;
            display: flex;
            justify-content: center;
            align-items: flex-start; /* Align to top */
            min-height: 100vh;
            color: #333;
        }

        .container {
            background-color: #ffffff;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
            padding: 35px 40px;
            width: 100%;
            max-width: 650px;
            box-sizing: border-box;
            animation: fadeIn 0.8s ease-out; /* Simple fade-in animation */
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* User Info / Navigation Bar */
        .user-info {
            text-align: right;
            margin-bottom: 25px;
            font-size: 0.95em;
            color: #555;
            padding-bottom: 15px;
            border-bottom: 1px solid #eee;
            display: flex;
            justify-content: flex-end;
            align-items: center;
            flex-wrap: wrap; /* Allow wrapping on small screens */
            gap: 10px; /* Space between links */
        }

        .user-info strong {
            color: #2c3e50;
            font-weight: 600;
        }

        .user-info a {
            color: #007bff;
            text-decoration: none;
            font-weight: 500;
            transition: color 0.2s ease;
        }

        .user-info a:hover {
            color: #0056b3;
            text-decoration: underline;
        }

        h2 {
            text-align: center;
            color: #2c3e50;
            margin-bottom: 30px;
            font-weight: 600;
            font-size: 2em;
        }

        /* Flash Messages */
        .flash-messages {
            list-style: none;
            padding: 0;
            margin-bottom: 25px;
            text-align: center;
        }

        .flash-messages li {
            padding: 12px 20px;
            border-radius: 8px;
            margin-bottom: 10px;
            font-weight: 500;
            display: inline-block; /* Center messages */
            max-width: 80%;
            word-wrap: break-word;
        }

        .flash-messages .success {
            background-color: #e6f7ed;
            color: #28a745;
            border: 1px solid #28a745;
        }

        .flash-messages .error {
            background-color: #fde8ec;
            color: #dc3545;
            border: 1px solid #dc3545;
        }

        .flash-messages .info {
            background-color: #e7f5ff;
            color: #007bff;
            border: 1px solid #007bff;
        }

        /* Subscription Info Section */
        .subscription-info {
            background-color: #f7f9fb;
            border-radius: 10px;
            padding: 25px;
            margin-bottom: 35px;
            border: 1px solid #e0e6ed;
        }

        .subscription-info p {
            display: flex;
            align-items: center;
            margin-bottom: 12px;
            font-size: 1.1em;
            color: #555;
        }

        .subscription-info p strong {
            color: #333;
            min-width: 160px; /* Align text nicely */
            font-weight: 500;
        }

        .subscription-info p i {
            margin-right: 10px;
            color: #6c757d;
        }

        .subscription-info p:last-child {
            margin-bottom: 0;
        }

        /* Call to Action Buttons */
        .action-button {
            background-color: #007bff;
            color: white;
            border: none;
            padding: 15px 25px;
            border-radius: 8px;
            font-size: 1.1em;
            font-weight: 600;
            cursor: pointer;
            transition: background-color 0.3s ease, transform 0.2s ease;
            display: block;
            width: fit-content; /* Adjust to content size */
            margin: 20px auto 0 auto; /* Center button */
            box-shadow: 0 4px 10px rgba(0, 123, 255, 0.2);
        }

        .action-button:hover {
            background-color: #0056b3;
            transform: translateY(-2px);
        }

        .action-button:active {
            transform: translateY(0);
        }

        /* Payment Info Section */
        .payment-info {
            background-color: #ffffff;
            border-radius: 10px;
            padding: 30px;
            border: 1px solid #e0e6ed;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.05);
            margin-top: 35px; /* Spacing from info section */
        }

        .payment-info h3 {
            color: #2c3e50;
            text-align: center;
            margin-bottom: 25px;
            font-weight: 600;
            font-size: 1.6em;
        }

        .payment-info p {
            margin-bottom: 15px;
            line-height: 1.6;
            color: #444;
            font-size: 1.05em;
        }

        .payment-info p strong {
            color: #007bff; /* Highlight amount */
            font-weight: 700;
        }

        .address-box {
            background-color: #e9ecef;
            border-radius: 8px;
            padding: 15px 20px;
            margin-bottom: 20px;
            font-size: 1.1em;
            font-weight: 500;
            color: #333;
            text-align: center;
            cursor: pointer;
            transition: background-color 0.3s ease, box-shadow 0.3s ease;
            position: relative;
            user-select: none; /* Prevent text selection on click */
            display: flex;
            justify-content: center;
            align-items: center;
            flex-wrap: wrap; /* Allow content to wrap on smaller screens */
        }

        .address-box:hover {
            background-color: #dfe3e7;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }

        .address-box i {
            margin-left: 10px;
            color: #007bff;
            transition: color 0.3s ease;
            flex-shrink: 0; /* Prevent icon from shrinking */
        }
        
        .address-box.copied i {
            color: #28a745; /* Green checkmark when copied */
        }

        #tron-address-display {
            word-break: break-all; /* Ensure long addresses break correctly */
        }

        .form-group {
            margin-bottom: 20px;
        }

        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
            color: #444;
            font-size: 0.95em;
        }

        .form-group input[type="text"] {
            width: calc(100% - 24px); /* Account for padding */
            padding: 12px;
            border: 1px solid #ced4da;
            border-radius: 8px;
            font-size: 1em;
            color: #333;
            transition: border-color 0.3s ease, box-shadow 0.3s ease;
        }

        .form-group input[type="text"]:focus {
            border-color: #007bff;
            box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
            outline: none;
        }

        .submit-button {
            background-color: #28a745; /* Green for submission */
            color: white;
            border: none;
            padding: 15px 25px;
            border-radius: 8px;
            font-size: 1.1em;
            font-weight: 600;
            cursor: pointer;
            transition: background-color 0.3s ease, transform 0.2s ease;
            display: block;
            width: fit-content;
            margin: 30px auto 0 auto; /* Center button */
            box-shadow: 0 4px 10px rgba(40, 167, 69, 0.2);
        }

        .submit-button:hover {
            background-color: #218838;
            transform: translateY(-2px);
        }

        .submit-button:active {
            transform: translateY(0);
        }

        /* Responsive adjustments */
        @media (max-width: 768px) {
            .container {
                padding: 25px 25px;
                margin: 15px;
            }

            .user-info {
                justify-content: center; /* Center links on small screens */
                text-align: center;
            }

            h2 {
                font-size: 1.8em;
            }

            .subscription-info p {
                flex-direction: column; /* Stack on small screens */
                align-items: flex-start;
            }

            .subscription-info p strong {
                min-width: unset;
                margin-bottom: 5px;
            }

            .address-box {
                font-size: 0.95em;
                padding: 12px 15px;
                flex-direction: column; /* Stack address and icon on very small screens */
            }

            .address-box i {
                margin-left: 0;
                margin-top: 10px; /* Add space above icon when stacked */
            }

            .action-button, .submit-button {
                width: 100%; /* Full width on small screens */
                padding: 12px 20px;
                font-size: 1em;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="user-info">
            Logged in as <strong>{{ current_user.username }}</strong> 
            <span style="color: #ccc;">|</span>
            <a href="{{ url_for('dashboard') }}">Dashboard</a> 
            <span style="color: #ccc;">|</span>
            <a href="{{ url_for('index') }}">Signals</a> 
            <span style="color: #ccc;">|</span>
            <a href="{{ url_for('subscribe') }}">Subscription</a> 
            <span style="color: #ccc;">|</span>
            <a href="{{ url_for('logout') }}">Logout</a>
        </div>
        
        <h2><i class="fas fa-gem" style="color: #007bff; margin-right: 10px;"></i> Your Subscription Status</h2>

        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                <ul class="flash-messages">
                    {% for category, message in messages %}
                        <li class="{{ category }}">{{ message }}</li>
                    {% endfor %}
                </ul>
            {% endif %}
        {% endwith %}

        <section class="subscription-info">
            <p><i class="fas fa-hourglass-half"></i><strong>Trial Status:</strong> <span>{{ trial_status }}</span></p>
            <p><i class="fas fa-credit-card"></i><strong>Subscription Status:</strong> <span>{{ 'Active' if has_subscribed else 'Inactive' }}</span></p>
            <p><i class="fas fa-calendar-alt"></i><strong>Subscription Ends On:</strong> <span>{{ subscription_end }}</span></p>
        </section>

        {% if not has_subscribed %}
            {% if current_user.referral_credits >= USDT_SUBSCRIPTION_AMOUNT %}
                <p style="text-align: center; font-size: 1.1em; color: #4CAF50; font-weight: 500;">
                    <i class="fas fa-check-circle" style="margin-right: 8px;"></i>Great news! You have enough credits to activate your subscription instantly.
                </p>
                <form method="POST">
                    <button type="submit" class="action-button">
                        <i class="fas fa-bolt" style="margin-right: 8px;"></i>Activate Subscription Now
                    </button>
                </form>
            {% else %}
                <section class="payment-info">
                    <h3><i class="fas fa-chart-line" style="margin-right: 10px;"></i> Unlock Premium Stock Signals</h3>
                    <p>Gain continuous access to all exclusive trade signals for only <strong>{{ USDT_SUBSCRIPTION_AMOUNT }} USDT per month.</strong></p>
                    <p>To subscribe, please send exactly {{ USDT_SUBSCRIPTION_AMOUNT }} USDT (TRC20 network) to the following TRON address:</p>
                    
                    <div class="address-box" id="tron-address-box">
                        <span id="tron-address-display">{{ RECEIVING_TRON_ADDRESS }}</span> <i class="far fa-copy"></i>
                    </div>
                    <p style="font-size: 0.9em; color: #777; text-align: center; margin-top: -10px; margin-bottom: 25px;">
                        (Click the address to quickly copy it to your clipboard)
                    </p>
                    
                    <form method="post">
                        <div class="form-group">
                            <label for="tron_address"><i class="fas fa-wallet" style="margin-right: 5px;"></i> Your TRON Address (from which you sent payment):</label>
                            <input type="text" id="tron_address" name="tron_address" placeholder="e.g., TWxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" required>
                        </div>
                        <div class="form-group">
                            <label for="transaction_hash"><i class="fas fa-receipt" style="margin-right: 5px;"></i> Transaction Hash (TxID):</label>
                            <input type="text" id="transaction_hash" name="transaction_hash" placeholder="e.g., 296xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" required>
                        </div>
                        <button type="submit" class="submit-button">
                            <i class="fas fa-paper-plane" style="margin-right: 8px;"></i> Submit Payment Details
                        </button>
                    </form>
                </section>
            {% endif %}
        {% endif %}
    </div>

    <script>
        // JavaScript for copy-to-clipboard functionality
        document.getElementById('tron-address-box').addEventListener('click', function() {
            // Get the text from the span element that contains the actual Jinja2 variable
            const addressText = document.getElementById('tron-address-display').innerText;
            
            navigator.clipboard.writeText(addressText).then(() => {
                const icon = this.querySelector('i');
                const originalClass = icon.className;
                const originalColor = icon.style.color;

                // Change icon to checkmark and color to green
                icon.className = 'fas fa-check-circle';
                icon.style.color = '#28a745';
                this.classList.add('copied'); // Add a class for CSS styling

                // Revert after 2 seconds
                setTimeout(() => {
                    icon.className = originalClass; // Revert to original icon
                    icon.style.color = originalColor; // Revert to original color
                    this.classList.remove('copied');
                }, 2000);

            }).catch(err => {
                console.error('Failed to copy text: ', err);
                // Fallback for browsers that don't support clipboard API or if permission is denied
                alert('Failed to copy address. Please copy manually: ' + addressText);
            });
        });
    </script>
</body>
</html>
    </body>
    <a href="https://wa.me/message/XZEBHBEWMSHJD1" target="_blank" class="whatsapp-btn">
    <div class="icon">
        <!-- WhatsApp SVG Icon (No External Image Needed) -->
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="28" height="28">
            <path fill="currentColor" d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
        </svg>
    </div>
    <!-- Optional Notification Badge -->
    <span class="notification-badge">1</span>
    <!-- Optional Hover Tooltip -->
    <span class="tooltip">Message Us</span>
</a>

<style>
    .whatsapp-btn {
        position: fixed;
        bottom: 25px;
        right: 25px;
        width: 56px;
        height: 56px;
        background: #25D366;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 4px 16px rgba(37, 211, 102, 0.3);
        z-index: 9999;
        transition: all 0.3s ease;
    }
    .whatsapp-btn:hover {
        background: #128C7E;
        transform: scale(1.1);
        box-shadow: 0 6px 20px rgba(18, 140, 126, 0.4);
    }
    .whatsapp-btn .icon {
        color: white;
        margin-top: 2px; /* Minor icon alignment tweak */
    }
    /* Notification Badge (Optional) */
    .notification-badge {
        position: absolute;
        top: -5px;
        right: -5px;
        background: #FF3B30;
        color: white;
        width: 20px;
        height: 20px;
        border-radius: 50%;
        font-size: 12px;
        font-weight: bold;
        display: flex;
        align-items: center;
        justify-content: center;
        animation: pulse 1.5s infinite;
    }
    /* Tooltip (Optional) */
    .tooltip {
        position: absolute;
        right: 70px;
        background: #333;
        color: white;
        padding: 6px 12px;
        border-radius: 4px;
        font-size: 14px;
        font-family: Arial, sans-serif;
        opacity: 0;
        pointer-events: none;
        transition: opacity 0.3s ease;
        white-space: nowrap;
    }
    .whatsapp-btn:hover .tooltip {
        opacity: 1;
    }
    /* Pulse Animation for Badge */
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.1); }
        100% { transform: scale(1); }
    }
</style>

                              
    </html>
    """, trial_status=trial_status, has_subscribed=has_subscribed, USDT_SUBSCRIPTION_AMOUNT=USDT_SUBSCRIPTION_AMOUNT, RECEIVING_TRON_ADDRESS=RECEIVING_TRON_ADDRESS, subscription_end=subscription_end)

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    if not is_trial_active(current_user) and not current_user.is_subscribed:
        flash("Your free trial has expired or you are not subscribed. Please subscribe to continue.", "warning")
        return redirect(url_for("subscribe"))
    elif is_trial_active(current_user) and not current_user.is_subscribed:
        days_left = (current_user.trial_end_date - datetime.utcnow()).days + 1
        flash(f"You are on a free trial. {days_left} day(s) left. <a href='{url_for('subscribe')}'>Subscribe now!</a>", "info")

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

    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1" />
              <!-- Google Analytics Script -->
        <script async src="https://www.googletagmanager.com/gtag/js?id=G-658KJS0QED"></script>
        <script>
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());
            gtag('config', 'G-658KJS0QED');
        </script>
      <title>{{ selected_symbol }} Swing and Long Term Trade Signals</title>
      <link href="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/css/select2.min.css" rel="stylesheet" />
      <style>
        body {
          font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
          max-width: 900px;
          margin: 40px auto;
          padding: 20px;
          background: #f7f9fc;
          border-radius: 10px;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
          color: #333;
        }
        h1 {
          text-align: center;
          margin-bottom: 1rem;
        }
        form {
          text-align: center;
          margin-bottom: 30px;
        }
        select {
          width: 100%;
          max-width: 300px;
        }
        button {
          font-size: 16px;
          padding: 6px 12px;
          margin-top: 10px;
          cursor: pointer;
        }
        .signals-container {
          display: flex;
          justify-content: space-around;
          flex-wrap: wrap;
          margin-top: 30px;
          gap: 30px;
        }
        .signal-box {
          background: white;
          border-radius: 8px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
          padding: 20px;
          width: 400px;
        }
        .signal-label {
          font-size: 20px;
          font-weight: 600;
          margin-bottom: 10px;
          text-align: center;
        }
        .state-value {
          font-size: 48px;
          font-weight: 700;
          text-align: center;
          margin: 20px 0 10px 0;
          user-select: none;
        }
        .close-label, .time-label {
          font-size: 16px;
          text-align: center;
          color: #555;
          margin-bottom: 6px;
        }
        .current-price-container {
          text-align: center;
          margin-top: 30px;
        }
        .instructions {
          max-width: 700px;
          margin: 40px auto 0 auto;
          padding: 15px 20px;
          background-color: #ffffff;
          border-radius: 8px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
          color: #333;
          font-size: 16px;
          line-height: 1.5;
        }
        .instructions h2 {
          text-align: center;
          margin-bottom: 15px;
          color: #222;
        }
        .instructions ul {
          list-style-type: disc;
          padding-left: 20px;
        }
        footer {
          margin-top: 40px;
          font-size: 14px;
          color: #999;
          text-align: center;
        }
        .user-info {
          text-align: right;
          margin-bottom: 20px;
          font-size: 14px;
          color: #666;
        }
        .user-info a {
          color: #c62828;
          text-decoration: none;
          margin-left: 10px;
        }
        .flash-messages {
            list-style-type: none;
            padding: 0;
            margin-bottom: 20px;
        }
        .flash-messages li {
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 10px;
            font-weight: bold;
        }
        .flash-messages .error {
            background-color: #ffebee;
            color: #c62828;
            border: 1px solid #ef9a9a;
        }
        .flash-messages .success {
            background-color: #e8f5e9;
            color: #2e7d32;
            border: 1px solid #a5d6a7;
        }
        .flash-messages .warning {
            background-color: #fffde7;
            color: #ffb300;
            border: 1px solid #ffe082;
        }
        .flash-messages .info {
            background-color: #e0f2f7;
            color: #00838f;
            border: 1px solid #b2ebf2;
        }
      </style>
    </head>
    <body>
      <div class="user-info">
        Logged in as <strong>{{ current_user.username }}</strong> | <a href="{{ url_for('dashboard') }}">Go to Dashboard</a> | <a href="{{ url_for('logout') }}">Logout</a>

      </div>

      <h1>{{ selected_symbol }} Swing and Long Term Trade Signals</h1>

      {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
          <ul class="flash-messages">
          {% for category, message in messages %}
            <li class="{{ category }}">{{ message | safe }}</li>
          {% endfor %}
          </ul>
        {% endif %}
      {% endwith %}

      <form method="post">
        <label for="symbol">Select Stock Symbol (Searchable Dropdown):</label><br>
        <select name="symbol" id="symbol" class="select2" required>
          {% for symbol, name in STOCK_LIST %}
            <option value="{{ symbol }}" {% if symbol == selected_symbol %} selected{% endif %}>{{ symbol }} - {{ name }}</option>
          {% endfor %}
        </select>
        <br>
        <button type="submit">Get Signals</button>
      </form>

      <div class="signals-container">
        <div class="signal-box">
          <div class="signal-label">Swing Trade Signal </div>
          <div class="state-value" style="color:{{ color_for(swing_state) }}">{{ swing_display }}</div>
          <div class="close-label">Latest Close: ${{ swing_close if swing_close is string else "%.2f"|format(swing_close) }}</div>
          <div class="time-label">As of: {{ swing_time }}</div>
        </div>

        <div class="signal-box">
          <div class="signal-label">Long Term Signal </div>
          <div class="state-value" style="color:{{ color_for(long_state) }}">{{ long_display }}</div>
          <div class="close-label">Latest Close: ${{ long_close if long_close is string else "%.2f"|format(long_close) }}</div>
          <div class="time-label">As of: {{ long_time }}</div>
        </div>
      </div>

      <div class="current-price-container">
        <h3>Current Price of {{ selected_symbol }}:</h3>
        <p>{{ current_price_display }}</p>
      </div>

      <div class="instructions">
        <h2>Instructions for Traders</h2>
        <ul>
          <li><strong>BUY:</strong> Enter a long position when the signal switches to BUY.</li>
          <li><strong>SELL (Close Position):</strong> Exit your long position when the signal switches to SELL.</li>
          <li>Hold your position until the signal changes to the opposite state.</li>
          
                                 
        </ul>
      </div>

      <p>Signals are based on proprietary analysis.<br>Always trade responsibly.</p>
      <footer>&copy; {{ current_year }} Stock Signals</footer>

      <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
      <script src="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/js/select2.min.js"></script>
      <script>
        $(document).ready(function() {
            $('.select2').select2({
                placeholder: "Select or search stock symbol",
                allowClear: true,
                width: 'resolve'
            });
        });
      </script>
            <!-- Footer with Legal Links -->
        <footer>
            <a href="{{ url_for('privacy_policy') }}">Privacy Policy</a> |
            <a href="{{ url_for('terms_of_service') }}">Terms of Service</a> |
            <a href="{{ url_for('disclaimer') }}">Disclaimer</a>
        </footer>                              
    </body>
<a href="https://wa.me/message/XZEBHBEWMSHJD1" target="_blank" class="whatsapp-btn">
    <div class="icon">
        <!-- WhatsApp SVG Icon (No External Image Needed) -->
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="28" height="28">
            <path fill="currentColor" d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
        </svg>
    </div>
    <!-- Optional Notification Badge -->
    <span class="notification-badge">1</span>
    <!-- Optional Hover Tooltip -->
    <span class="tooltip">Message Us</span>
</a>

<style>
    .whatsapp-btn {
        position: fixed;
        bottom: 25px;
        right: 25px;
        width: 56px;
        height: 56px;
        background: #25D366;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 4px 16px rgba(37, 211, 102, 0.3);
        z-index: 9999;
        transition: all 0.3s ease;
    }
    .whatsapp-btn:hover {
        background: #128C7E;
        transform: scale(1.1);
        box-shadow: 0 6px 20px rgba(18, 140, 126, 0.4);
    }
    .whatsapp-btn .icon {
        color: white;
        margin-top: 2px; /* Minor icon alignment tweak */
    }
    /* Notification Badge (Optional) */
    .notification-badge {
        position: absolute;
        top: -5px;
        right: -5px;
        background: #FF3B30;
        color: white;
        width: 20px;
        height: 20px;
        border-radius: 50%;
        font-size: 12px;
        font-weight: bold;
        display: flex;
        align-items: center;
        justify-content: center;
        animation: pulse 1.5s infinite;
    }
    /* Tooltip (Optional) */
    .tooltip {
        position: absolute;
        right: 70px;
        background: #333;
        color: white;
        padding: 6px 12px;
        border-radius: 4px;
        font-size: 14px;
        font-family: Arial, sans-serif;
        opacity: 0;
        pointer-events: none;
        transition: opacity 0.3s ease;
        white-space: nowrap;
    }
    .whatsapp-btn:hover .tooltip {
        opacity: 1;
    }
    /* Pulse Animation for Badge */
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.1); }
        100% { transform: scale(1); }
    }
</style>

    </html>
    """,
    selected_symbol=selected_symbol,
    current_price_display=current_price_display,
    swing_state=swing_state,
    swing_display=swing_display,
    swing_close=swing_close,
    swing_time=swing_time,
    long_state=long_state,
    long_display=long_display,
    long_close=long_close,
    long_time=long_time,
    color_for=color_for,
    STOCK_LIST=STOCK_LIST,
    current_year=datetime.now(timezone.utc).year)

@app.route("/privacy-policy")
def privacy_policy():
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Privacy Policy - Stock Signals</title>
        <style>
            body {
                font-family: 'Arial', sans-serif;
                margin: 0;
                padding: 0;
                background: #f9f9f9;
                color: #333;
                line-height: 1.6;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 30px;
                background: #fff;
                box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
                border-radius: 12px;
                margin-top: 60px;
                border: 1px solid #eee;
            }
            h1 {
                text-align: center;
                color: #004b87;
                font-size: 36px;
                margin-bottom: 30px;
            }
            p {
                font-size: 16px;
                color: #555;
                margin-bottom: 20px;
            }
            .section-title {
                font-size: 24px;
                color: #444;
                margin-top: 40px;
                border-bottom: 2px solid #004b87;
                padding-bottom: 5px;
                text-transform: uppercase;
            }
            footer {
                background-color: #fafafa;
                padding: 20px;
                text-align: center;
                margin-top: 40px;
                border-top: 1px solid #ddd;
            }
            footer a {
                color: #004b87;
                text-decoration: none;
                margin: 0 15px;
                font-size: 14px;
                font-weight: bold;
            }
            footer a:hover {
                color: #007bff;
                text-decoration: underline;
            }
            /* Responsive Design */
            @media (max-width: 768px) {
                .container {
                    padding: 20px;
                }
                h1 {
                    font-size: 28px;
                }
                .section-title {
                    font-size: 20px;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Privacy Policy</h1>
            <p>Welcome to Stock Signals. Your privacy is important to us. This Privacy Policy explains how we collect, use, and protect your personal information.</p>
            
            <div class="section-title">1. Information We Collect</div>
            <p>We collect information when you sign up, use our services, or interact with our site. This may include personal details like your name, email, and payment information.</p>

            <div class="section-title">2. How We Use Your Information</div>
            <p>Your information is used to provide personalized trading signals and improve your experience on our platform. We may also use your information to send service updates or marketing messages, though you can opt out of these communications.</p>

            <div class="section-title">3. Data Protection</div>
            <p>We take your privacy seriously and have implemented reasonable measures to protect your data from unauthorized access, alteration, and disclosure.</p>

            <div class="section-title">4. Third-Party Services</div>
            <p>We may share your data with trusted third-party service providers who help us operate our platform, process payments, and provide services to you.</p>

            <div class="section-title">5. Your Rights</div>
            <p>You have the right to access, correct, or delete your personal data. You can also opt out of marketing communications at any time.</p>

            <footer>
                <a href="{{ url_for('terms_of_service') }}">Terms of Service</a> | 
                <a href="{{ url_for('disclaimer') }}">Disclaimer</a> |
                <a href="{{ url_for('index') }}">Back to Home</a>
            </footer>
        </div>
    </body>
    </html>
    """)

@app.route("/terms-of-service")
def terms_of_service():
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Terms of Service - Stock Signals</title>
        <style>
            body {
                font-family: 'Arial', sans-serif;
                margin: 0;
                padding: 0;
                background: #f9f9f9;
                color: #333;
                line-height: 1.6;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 30px;
                background: #fff;
                box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
                border-radius: 12px;
                margin-top: 60px;
                border: 1px solid #eee;
            }
            h1 {
                text-align: center;
                color: #004b87;
                font-size: 36px;
                margin-bottom: 30px;
            }
            p {
                font-size: 16px;
                color: #555;
                margin-bottom: 20px;
            }
            .section-title {
                font-size: 24px;
                color: #444;
                margin-top: 40px;
                border-bottom: 2px solid #004b87;
                padding-bottom: 5px;
                text-transform: uppercase;
            }
            footer {
                background-color: #fafafa;
                padding: 20px;
                text-align: center;
                margin-top: 40px;
                border-top: 1px solid #ddd;
            }
            footer a {
                color: #004b87;
                text-decoration: none;
                margin: 0 15px;
                font-size: 14px;
                font-weight: bold;
            }
            footer a:hover {
                color: #007bff;
                text-decoration: underline;
            }
            /* Responsive Design */
            @media (max-width: 768px) {
                .container {
                    padding: 20px;
                }
                h1 {
                    font-size: 28px;
                }
                .section-title {
                    font-size: 20px;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Terms of Service</h1>
            <p>By using our website, you agree to the following terms and conditions:</p>
            
            <div class="section-title">1. Acceptable Use</div>
            <p>You may not use our service for any unlawful purpose or engage in any activities that may harm others or our service.</p>

            <div class="section-title">2. Subscription and Payments</div>
            <p>Users must make payments to access premium features. Subscription fees are non-refundable, except where required by law.</p>

            <div class="section-title">3. Limitation of Liability</div>
            <p>We are not responsible for any financial loss or damages that may result from using our service.</p>

            <div class="section-title">4. Modification of Terms</div>
            <p>We may update or change these terms at any time. It is your responsibility to review these terms regularly.</p>

            <footer>
                <a href="{{ url_for('privacy_policy') }}">Privacy Policy</a> | 
                <a href="{{ url_for('disclaimer') }}">Disclaimer</a> |
                <a href="{{ url_for('index') }}">Back to Home</a>
            </footer>
        </div>
    </body>
    </html>
    """)

@app.route("/disclaimer")
def disclaimer():
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Disclaimer - Stock Signals</title>
        <style>
            body {
                font-family: 'Arial', sans-serif;
                margin: 0;
                padding: 0;
                background: #f9f9f9;
                color: #333;
                line-height: 1.6;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 30px;
                background: #fff;
                box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
                border-radius: 12px;
                margin-top: 60px;
                border: 1px solid #eee;
            }
            h1 {
                text-align: center;
                color: #004b87;
                font-size: 36px;
                margin-bottom: 30px;
            }
            p {
                font-size: 16px;
                color: #555;
                margin-bottom: 20px;
            }
            .section-title {
                font-size: 24px;
                color: #444;
                margin-top: 40px;
                border-bottom: 2px solid #004b87;
                padding-bottom: 5px;
                text-transform: uppercase;
            }
            footer {
                background-color: #fafafa;
                padding: 20px;
                text-align: center;
                margin-top: 40px;
                border-top: 1px solid #ddd;
            }
            footer a {
                color: #004b87;
                text-decoration: none;
                margin: 0 15px;
                font-size: 14px;
                font-weight: bold;
            }
            footer a:hover {
                color: #007bff;
                text-decoration: underline;
            }
            /* Responsive Design */
            @media (max-width: 768px) {
                .container {
                    padding: 20px;
                }
                h1 {
                    font-size: 28px;
                }
                .section-title {
                    font-size: 20px;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Disclaimer</h1>
            <p>The information provided on this website is for informational purposes only and should not be construed as financial advice.</p>

            <div class="section-title">1. No Financial Advice</div>
            <p>We do not provide financial or investment advice. All content on this site is intended for informational purposes only.</p>

            <div class="section-title">2. Accuracy of Information</div>
            <p>We strive to provide accurate and timely information, but we do not guarantee its accuracy, completeness, or reliability.</p>

            <div class="section-title">3. Risks Involved</div>
            <p>Trading involves significant risk. You should consider seeking advice from a licensed financial advisor before making any trading decisions.</p>

            <footer>
                <a href="{{ url_for('privacy_policy') }}">Privacy Policy</a> | 
                <a href="{{ url_for('terms_of_service') }}">Terms of Service</a> |
                <a href="{{ url_for('index') }}">Back to Home</a>
            </footer>
        </div>
    </body>
    </html>
    """)



if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5009, debug=True)

       
