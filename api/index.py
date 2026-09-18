from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from typing import Dict, Any, List
import math
import swisseph as swe

app = FastAPI(title="Astrovani Astrology API", version="2.0.0")

SIGNS=["Mesha","Vrishabha","Mithuna","Karka","Simha","Kanya","Tula","Vrischika","Dhanu","Makara","Kumbha","Meena"]
SIGN_HI=["मेष","वृषभ","मिथुन","कर्क","सिंह","कन्या","तुला","वृश्चिक","धनु","मकर","कुंभ","मीन"]
NAK=["Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra","Punarvasu","Pushya","Ashlesha","Magha","Purva Phalguni","Uttara Phalguni","Hasta","Chitra","Swati","Vishakha","Anuradha","Jyeshtha","Mula","Purva Ashadha","Uttara Ashadha","Shravana","Dhanishtha","Shatabhisha","Purva Bhadrapada","Uttara Bhadrapada","Revati"]
NL=["Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury"]
DURS={"Ketu":7,"Venus":20,"Sun":6,"Moon":10,"Mars":7,"Rahu":18,"Jupiter":16,"Saturn":19,"Mercury":17}
PLANETS={"Sun":swe.SUN,"Moon":swe.MOON,"Mars":swe.MARS,"Mercury":swe.MERCURY,"Jupiter":swe.JUPITER,"Venus":swe.VENUS,"Saturn":swe.SATURN,"Rahu":swe.MEAN_NODE}

# Ashtakoota data: compact traditional lookup tables for Moon-sign/nakshatra matching.
VARNA=[0,1,2,3,3,3,2,1,0,0,1,2]
VASHYA=["chatushpada","chatushpada","manushya","jalachara","vanachara","manushya","manushya","keeta","chatushpada","manushya","manushya","jalachara"]
GANA=["deva","manushya","rakshasa","manushya","deva","manushya","rakshasa","deva","rakshasa","rakshasa","manushya","deva","deva","rakshasa","deva","rakshasa","deva","rakshasa","rakshasa","manushya","manushya","deva","rakshasa","rakshasa","manushya","deva","deva"]
YONI=["horse","elephant","sheep","serpent","serpent","dog","cat","sheep","cat","rat","rat","buffalo","buffalo","tiger","buffalo","tiger","deer","deer","dog","monkey","mongoose","monkey","lion","horse","lion","cow","cow"]
NADI=["adi","madhya","antya"]*9


def norm(x): return float(x)%360

def jd(date,time):
    dt=datetime.fromisoformat(f"{date}T{time}")
    return swe.julday(dt.year,dt.month,dt.day,dt.hour+dt.minute/60+dt.second/3600)

def sign(lon):
    n=int(norm(lon)//30)
    return {"sign_no":n+1,"sign":SIGNS[n],"sign_hi":SIGN_HI[n],"degree":round(norm(lon)%30,6)}

def nak(lon):
    span=360/27; i=min(26,int(norm(lon)/span)); within=norm(lon)-i*span
    return {"nakshatra":NAK[i],"pada":min(4,int(within/(span/4))+1),"lord":NL[i],"nakshatra_no":i+1}

def nav(lon):
    s=int(norm(lon)//30); part=min(8,int((norm(lon)%30)/(30/9)))
    start=s if s%3==0 else ((s+8)%12 if s%3==1 else (s+4)%12)
    return (start+part)%12

def houses(j,lat,lon):
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    r=swe.houses_ex(j,float(lat),float(lon),b"P",swe.FLG_SIDEREAL)
    return r[0],norm(r[1][0])

def house(lon,asc): return int(norm(lon-asc)//30)+1

def dasha(moon,date):
    n=nak(moon); idx=NL.index(n["lord"]); span=360/27
    balance=1-(norm(moon)%span)/span; cur=datetime.fromisoformat(date); out=[]
    for k in range(9):
        lord=NL[(idx+k)%9]; days=DURS[lord]*365.2425*(balance if k==0 else 1)
        end=cur+timedelta(days=days); mdays=(end-cur).total_seconds()/86400
        ads=[]; order=list(DURS); oi=order.index(lord); astart=cur
        for j in range(9):
            al=order[(oi+j)%9]; aend=min(end,astart+timedelta(days=mdays*DURS[al]/120))
            pds=[]; pdays=(aend-astart).total_seconds()/86400; pi=order.index(al); ps=astart
            for q in range(9):
                pl=order[(pi+q)%9]; pe=min(aend,ps+timedelta(days=pdays*DURS[pl]/120))
                pds.append({"lord":pl,"start":ps.date().isoformat(),"end":pe.date().isoformat()}); ps=pe
                if ps>=aend: break
            ads.append({"lord":al,"start":astart.date().isoformat(),"end":aend.date().isoformat(),"pratyantardasha":pds})
            astart=aend
            if astart>=end: break
        out.append({"lord":lord,"start":cur.date().isoformat(),"end":end.date().isoformat(),"antardasha":ads})
        cur=end
    return out

def planet_payload(j):
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    ps={}
    for name,pid in PLANETS.items():
        r=swe.calc_ut(j,pid,swe.FLG_SWIEPH|swe.FLG_SPEED|swe.FLG_SIDEREAL)
        lon=norm(r[0][0]); v=sign(lon); v.update(nak(lon)); v["longitude"]=round(lon,6); v["retrograde"]=bool(r[0][3] < 0); ps[name]=v
    kl=norm(ps["Rahu"]["longitude"]+180); v=sign(kl); v.update(nak(kl)); v["longitude"]=round(kl,6); v["retrograde"]=True; ps["Ketu"]=v
    return ps

def calculate_core(x):
    if not (-90<=x.lat<=90 and -180<=x.lon<=180): raise HTTPException(400,"Invalid latitude/longitude")
    j=jd(x.date,x.time); ps=planet_payload(j); _,asc=houses(j,x.lat,x.lon)
    li=sign(asc); li.update(nak(asc)); li["longitude"]=round(asc,6)
    for v in ps.values(): v["house"]=house(v["longitude"],asc)
    d1={str(i):[] for i in range(1,13)}
    for k,v in ps.items(): d1[str(v["house"])].append(k)
    d9={k:{"sign_no":nav(v["longitude"])+1,"sign":SIGNS[nav(v["longitude"])],"sign_hi":SIGN_HI[nav(v["longitude"])]} for k,v in ps.items()}
    yog=[]
    if ps["Sun"]["sign_no"]==ps["Mercury"]["sign_no"]: yog.append({"name":"Budhaditya Yoga","description":"Sun and Mercury occupy the same sign."})
    if ps["Mars"]["sign_no"]==ps["Rahu"]["sign_no"]: yog.append({"name":"Angarak Yoga","description":"Mars and Rahu occupy the same sign."})
    if ps["Jupiter"]["sign_no"]==ps["Rahu"]["sign_no"]: yog.append({"name":"Guru Chandal Yoga","description":"Jupiter and Rahu occupy the same sign."})
    return {"person":{"name":x.name,"date":x.date,"time":x.time,"place":x.place,"lat":x.lat,"lon":x.lon,"timezone":x.timezone},"ayanamsa":"Lahiri","lagna":li,"planets":ps,"d1":d1,"d9":d9,"yogas":yog,"dasha":dasha(ps["Moon"]["longitude"],x.date),"engine":"Swiss Ephemeris","sidereal":True}

class Req(BaseModel):
    name:str="Guest"; date:str; time:str; place:str=""; lat:float; lon:float; timezone:str="Asia/Kolkata"

class MatchReq(BaseModel):
    a_nakshatra:int=Field(ge=1,le=27); a_sign:int=Field(ge=1,le=12); b_nakshatra:int=Field(ge=1,le=27); b_sign:int=Field(ge=1,le=12)

def matching(m:MatchReq):
    # Traditional component maxima: Varna 1, Vashya 2, Tara 3, Yoni 4, Graha Maitri 5, Gana 6, Bhakoot 7, Nadi 8.
    a,b=m.a_sign-1,m.b_sign-1; an,bn=m.a_nakshatra-1,m.b_nakshatra-1
    varna=1 if VARNA[a]==VARNA[b] else (0.5 if abs(VARNA[a]-VARNA[b])==1 else 0)
    vashya=2 if VASHYA[a]==VASHYA[b] else (1 if {VASHYA[a],VASHYA[b]} <= {"manushya","chatushpada"} else 0)
    tara=3 if ((bn-an)%9) in (0,2,4,6,8) else 1.5
    yoni=4 if YONI[an]==YONI[bn] else (2 if {YONI[an],YONI[bn]} in [{"horse","buffalo"},{"elephant","lion"},{"sheep","monkey"},{"serpent","mongoose"},{"dog","deer"},{"cat","rat"},{"tiger","cow"}] else 0)
    # Sign lords for Graha Maitri, reduced to a compact relationship table.
    lord=["Mars","Venus","Mercury","Moon","Sun","Mercury","Venus","Mars","Jupiter","Saturn","Saturn","Jupiter"]
    friends={"Sun":{"Moon","Mars","Jupiter"},"Moon":{"Sun","Mercury"},"Mars":{"Sun","Moon","Jupiter"},"Mercury":{"Sun","Venus"},"Jupiter":{"Sun","Moon","Mars"},"Venus":{"Mercury","Saturn"},"Saturn":{"Mercury","Venus"}}
    lm1,lm2=lord[a],lord[b]
    maitri=5 if lm1==lm2 or lm2 in friends.get(lm1,set()) else (3 if lm1 in friends.get(lm2,set()) or lm2 in friends.get(lm1,set()) else 1)
    gana=6 if GANA[an]==GANA[bn] else (3 if {GANA[an],GANA[bn]}=={"deva","manushya"} else 0)
    bhakoot=7 if ((b-a)%12) not in (2,6,8,12-2,12-6) else 0
    nadi=8 if NADI[an]==NADI[bn] else 0
    total=round(varna+vashya+tara+yoni+maitri+gana+bhakoot+nadi,1)
    return {"success":True,"total":total,"out_of":36,"components":[{"name":"Varna","score":varna,"max":1},{"name":"Vashya","score":vashya,"max":2},{"name":"Tara","score":tara,"max":3},{"name":"Yoni","score":yoni,"max":4},{"name":"Graha Maitri","score":maitri,"max":5},{"name":"Gana","score":gana,"max":6},{"name":"Bhakoot","score":bhakoot,"max":7},{"name":"Nadi","score":nadi,"max":8}],"note":"Kundli matching should be interpreted with the complete charts, not score alone."}

@app.get("/")
def root(): return {"success":True,"service":"Astrovani Astrology API","version":"2.0.0"}

@app.get("/api/health")
def health(): return {"success":True,"engine":"Swiss Ephemeris","sidereal":"Lahiri"}

@app.get("/api/calculate")
def help_api(): return {"success":True,"message":"Use POST /api/calculate","method":"POST"}

@app.post("/api/calculate")
def calculate(x:Req):
    try: return {"success":True,**calculate_core(x)}
    except HTTPException: raise
    except Exception as e: return JSONResponse(500,{"success":False,"error":str(e)})

@app.post("/api/match")
def match(x:MatchReq):
    try: return matching(x)
    except Exception as e: return JSONResponse(500,{"success":False,"error":str(e)})

@app.post("/api/panchang")
def panchang(x:Req):
    try:
        j=jd(x.date,x.time); ps=planet_payload(j); sun=ps["Sun"]["longitude"]; moon=ps["Moon"]["longitude"]
        elong=norm(moon-sun); tithi=int(elong/12)+1; paksha="Shukla" if tithi<=15 else "Krishna"; tithi_name=(tithi if tithi<=15 else tithi-15)
        naksh=nak(moon)
        yoga_no=int(norm(sun+moon)/(360/27))+1
        return {"success":True,"date":x.date,"place":x.place,"tithi":{"number":tithi,"paksha":paksha,"name_no":tithi_name},"nakshatra":naksh,"yoga_number":yoga_no,"note":"Exact sunrise-based Panchang values depend on the location and local sunrise/sunset; this endpoint provides the astronomical core and the UI flags location-specific fields for full Panchang integration."}
    except Exception as e: return JSONResponse(500,{"success":False,"error":str(e)})
